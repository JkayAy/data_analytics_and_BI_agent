from __future__ import annotations

from contextlib import asynccontextmanager

from typing import Literal

from uuid import UUID

from insightbridge.request_context import AuthContext

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field

from insightbridge.agent import run_agent
from insightbridge.audit_export import query_runs_to_csv
from insightbridge.auth_jwt import (
    get_auth_context,
    request_magic_link,
    require_min_role,
    verify_magic_link,
)
from insightbridge.config import settings
from insightbridge.db import (
    add_message,
    create_conversation,
    get_conversation_org,
    list_messages,
    list_query_runs,
    save_query_run,
    upsert_feedback,
)
from insightbridge.db_connections import (
    create_connection,
    get_connection_secrets,
    list_connections,
    set_active_connection,
)
from insightbridge.db_tenancy import get_me, log_audit
from insightbridge.connectors.registry import get_connector
from insightbridge.memory import messages_to_history
from insightbridge.multi_agent.graph import AGENT_CAPABILITIES, GRAPH_VERSION, PHASE_STATUS
from insightbridge.db_delivery import (
    create_delivery_channel,
    create_scheduled_report,
    get_channel_webhook,
    list_delivery_channels,
    list_scheduled_reports,
    set_schedule_enabled,
)
from insightbridge.delivery.runner import run_due_scheduled_reports
from insightbridge.delivery.webhook_client import WebhookDeliveryError
from insightbridge.integrations.slack_commands import (
    SlackSignatureError,
    handle_slash_command,
    parse_slash_command,
    verify_slack_signature,
)
from insightbridge.scheduler_service import start_scheduler, stop_scheduler
from insightbridge.usage import UsageQuotaExceeded, get_org_usage, record_query_usage, ensure_quota
from insightbridge.security import optional_api_key
from insightbridge.semantic import load_semantic_layer, semantic_context_for_prompt
from insightbridge.warehouse import active_connection_summary


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="InsightBridge API",
    description="Multi-agent conversational BI — delivery & schedules (E6)",
    version="0.7.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MagicLinkRequest(BaseModel):
    email: EmailStr


class VerifyRequest(BaseModel):
    token: str = Field(min_length=10)


class CreateConversationRequest(BaseModel):
    title: str | None = None


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=4000)


class FeedbackRequest(BaseModel):
    rating: int = Field(description="-1 downvote, 1 upvote")
    comment: str | None = Field(default=None, max_length=2000)


class CreateConnectionRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    dialect: Literal["postgres", "bigquery", "snowflake"]
    config_json: dict = Field(default_factory=dict)
    set_active: bool = False


class CreateDeliveryChannelRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    channel_type: Literal["slack", "teams"]
    webhook_url: str = Field(min_length=8, max_length=2000)


class CreateScheduleRequest(BaseModel):
    delivery_channel_id: str
    name: str = Field(min_length=1, max_length=200)
    question: str = Field(min_length=3, max_length=4000)
    cron_expr: str = Field(default="0 9 * * 1", max_length=100)
    timezone: str = Field(default="UTC", max_length=64)
    enabled: bool = True


class ScheduleEnableRequest(BaseModel):
    enabled: bool


@app.get("/health")
def health():
    return {
        "status": "ok",
        "demo_mode": not bool(settings.openai_api_key),
        "auth_required": settings.auth_required,
        "multi_agent": True,
        "active_connection": active_connection_summary(),
        "scheduler_enabled": settings.scheduler_enabled,
        "version": "0.7.0",
    }


@app.post("/v1/auth/magic-link")
def auth_magic_link(body: MagicLinkRequest):
    return request_magic_link(body.email)


@app.post("/v1/auth/verify")
def auth_verify(body: VerifyRequest):
    return verify_magic_link(body.token)


@app.get("/v1/me")
def me(ctx: AuthContext = Depends(get_auth_context)):
    profile = get_me(ctx.user_id)
    if not profile:
        return {"user_id": ctx.user_id, "email": ctx.email, "org_id": ctx.org_id, "role": ctx.role}
    return profile


@app.get("/v1/agent/capabilities")
def agent_capabilities():
    return {
        "graph_version": GRAPH_VERSION,
        "agents": AGENT_CAPABILITIES,
        "modes": ["standard", "investigation"],
        "phases": PHASE_STATUS,
        "features": {
            "conversation_memory": True,
            "connectors": ["postgres", "bigquery", "snowflake"],
            "connection_manager": True,
            "tenancy": True,
            "magic_link_auth": True,
            "audit_csv_export": True,
            "slack_teams_delivery": True,
            "scheduled_reports": True,
            "usage_metering": True,
        },
    }


@app.get("/v1/connections")
def get_connections(ctx: AuthContext = Depends(get_auth_context)):
    return {"items": list_connections(ctx.org_id)}


@app.post("/v1/connections", dependencies=[Depends(optional_api_key)])
def post_connection(
    body: CreateConnectionRequest,
    ctx: AuthContext = Depends(require_min_role("admin")),
):
    conn = create_connection(
        body.name, body.dialect, body.config_json, org_id=ctx.org_id, set_active=body.set_active
    )
    log_audit(ctx.org_id, ctx.user_id, "connection.create", "connection", conn["id"])
    return conn


@app.post("/v1/connections/{connection_id}/activate", dependencies=[Depends(optional_api_key)])
def activate_connection(connection_id: UUID, ctx: AuthContext = Depends(require_min_role("admin"))):
    result = set_active_connection(connection_id, ctx.org_id)
    if not result:
        raise HTTPException(status_code=404, detail="Connection not found")
    log_audit(ctx.org_id, ctx.user_id, "connection.activate", "connection", str(connection_id))
    return result


@app.post("/v1/connections/{connection_id}/test", dependencies=[Depends(optional_api_key)])
def test_connection(connection_id: UUID, ctx: AuthContext = Depends(require_min_role("admin"))):
    from insightbridge.connectors.postgres import ConnectorExecutionError

    rec = get_connection_secrets(connection_id, ctx.org_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Connection not found")
    try:
        msg = get_connector(rec["dialect"], rec["config_json"]).test()
        return {"status": "ok", "message": msg}
    except (ConnectorExecutionError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/v1/delivery/channels")
def get_delivery_channels(ctx: AuthContext = Depends(require_min_role("member"))):
    return {"items": list_delivery_channels(ctx.org_id)}


@app.post("/v1/delivery/channels", dependencies=[Depends(optional_api_key)])
def post_delivery_channel(
    body: CreateDeliveryChannelRequest,
    ctx: AuthContext = Depends(require_min_role("admin")),
):
    ch = create_delivery_channel(ctx.org_id, body.name, body.channel_type, body.webhook_url)
    log_audit(ctx.org_id, ctx.user_id, "delivery.channel.create", "delivery_channel", ch["id"])
    return ch


@app.post("/v1/delivery/channels/{channel_id}/test", dependencies=[Depends(optional_api_key)])
def test_delivery_channel(channel_id: UUID, ctx: AuthContext = Depends(require_min_role("admin"))):
    ch = get_channel_webhook(channel_id, ctx.org_id)
    if not ch:
        raise HTTPException(status_code=404, detail="Channel not found")
    try:
        if ch["channel_type"] == "teams":
            payload = {
                "@type": "MessageCard",
                "@context": "https://schema.org/extensions",
                "summary": "InsightBridge test",
                "title": "InsightBridge connection test",
                "text": "Webhook delivery is configured.",
            }
        else:
            payload = {"text": "InsightBridge: delivery channel test OK"}
        from insightbridge.delivery.webhook_client import post_json

        post_json(ch["webhook_url"], payload)
        return {"status": "ok"}
    except WebhookDeliveryError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/v1/schedules")
def get_schedules(ctx: AuthContext = Depends(require_min_role("member"))):
    return {"items": list_scheduled_reports(ctx.org_id)}


@app.post("/v1/schedules", dependencies=[Depends(optional_api_key)])
def post_schedule(body: CreateScheduleRequest, ctx: AuthContext = Depends(require_min_role("admin"))):
    try:
        sched = create_scheduled_report(
            ctx.org_id,
            body.delivery_channel_id,
            body.name,
            body.question,
            body.cron_expr,
            body.timezone,
            ctx.user_id,
            body.enabled,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    log_audit(ctx.org_id, ctx.user_id, "schedule.create", "scheduled_report", sched["id"])
    return sched


@app.patch("/v1/schedules/{schedule_id}", dependencies=[Depends(optional_api_key)])
def patch_schedule(
    schedule_id: UUID,
    body: ScheduleEnableRequest,
    ctx: AuthContext = Depends(require_min_role("admin")),
):
    result = set_schedule_enabled(schedule_id, ctx.org_id, body.enabled)
    if not result:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return result


@app.post("/v1/schedules/run-due", dependencies=[Depends(optional_api_key)])
def post_run_due_schedules(ctx: AuthContext = Depends(require_min_role("admin"))):
    """Manual trigger for cron worker (local ops / Railway cron)."""
    ran = run_due_scheduled_reports()
    log_audit(ctx.org_id, ctx.user_id, "schedule.run_due", "organization", ctx.org_id)
    return {"executed": ran}


@app.get("/v1/orgs/{org_id}/usage")
def org_usage(org_id: UUID, ctx: AuthContext = Depends(require_min_role("member"))):
    if str(org_id) != ctx.org_id:
        raise HTTPException(status_code=403, detail="Cross-org usage denied")
    return get_org_usage(ctx.org_id)


@app.post("/v1/integrations/slack/commands")
async def slack_slash_command(request: Request):
    body = await request.body()
    ts = request.headers.get("X-Slack-Request-Timestamp", "")
    sig = request.headers.get("X-Slack-Signature", "")
    try:
        verify_slack_signature(body, ts, sig)
    except SlackSignatureError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    form = parse_slash_command(body)
    text = form.get("text", "")
    try:
        return handle_slash_command(text)
    except UsageQuotaExceeded as exc:
        return {"response_type": "ephemeral", "text": str(exc)}


@app.get("/v1/semantic-layer")
def get_semantic_layer():
    layer = load_semantic_layer()
    return {
        "version": layer.get("version"),
        "description": layer.get("description"),
        "metrics": list((layer.get("metrics") or {}).keys()),
    }


@app.get("/v1/audit/query-runs")
def audit_query_runs(limit: int = 50, ctx: AuthContext = Depends(require_min_role("member"))):
    limit = min(max(limit, 1), 200)
    return {"items": list_query_runs(limit=limit, org_id=ctx.org_id)}


@app.get("/v1/orgs/{org_id}/audit/export.csv")
def export_audit_csv(org_id: UUID, ctx: AuthContext = Depends(require_min_role("admin"))):
    if str(org_id) != ctx.org_id:
        raise HTTPException(status_code=403, detail="Cross-org export denied")
    csv_data = query_runs_to_csv(str(org_id))
    log_audit(ctx.org_id, ctx.user_id, "audit.export_csv", "organization", str(org_id))
    return Response(content=csv_data, media_type="text/csv", headers={
        "Content-Disposition": f'attachment; filename="insightbridge-audit-{org_id}.csv"'
    })


@app.post("/v1/conversations", dependencies=[Depends(optional_api_key)])
def post_conversation(body: CreateConversationRequest, ctx: AuthContext = Depends(require_min_role("member"))):
    conv = create_conversation(body.title, org_id=ctx.org_id, created_by=ctx.user_id)
    if conv.get("created_at"):
        conv["created_at"] = conv["created_at"].isoformat()
    return conv


@app.get("/v1/conversations/{conversation_id}/messages")
def get_conversation_messages(
    conversation_id: UUID,
    ctx: AuthContext = Depends(require_min_role("member")),
):
    org = get_conversation_org(conversation_id)
    if org and org != ctx.org_id:
        raise HTTPException(status_code=403, detail="Conversation not in your organization")
    return list_messages(conversation_id)


@app.post("/v1/conversations/{conversation_id}/ask", dependencies=[Depends(optional_api_key)])
def ask(conversation_id: UUID, body: AskRequest, ctx: AuthContext = Depends(require_min_role("member"))):
    org = get_conversation_org(conversation_id)
    if org and org != ctx.org_id:
        raise HTTPException(status_code=403, detail="Conversation not in your organization")

    try:
        ensure_quota(ctx.org_id)
    except UsageQuotaExceeded as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc

    prior = list_messages(conversation_id)
    history = messages_to_history(prior, max_turns=settings.conversation_history_turns)
    user_msg = add_message(conversation_id, "user", {"text": body.question})
    result = run_agent(body.question, history=history)
    record_query_usage(ctx.org_id)

    assistant_content = {
        "text": result.insight.get("headline", ""),
        "insight": result.insight,
        "sql": result.sql,
        "assumptions": result.assumptions,
        "metrics_used": result.metrics_used,
        "sql_source": result.sql_source,
        "status": result.status,
        "row_count": result.row_count,
        "duration_ms": result.duration_ms,
        "columns": result.columns,
        "result_preview": result.result_preview,
        "chart_spec": result.chart_spec,
        "error": result.error,
        "error_code": result.error_code,
        "agent_trace": result.agent_trace,
        "intent": result.intent,
        "mode": result.mode,
        "plan_steps": result.plan_steps,
        "investigation_runs": result.investigation_runs,
        "driver_rankings": result.driver_rankings,
        "resolved_question": result.resolved_question,
    }
    assistant_msg = add_message(conversation_id, "assistant", assistant_content)
    run_metadata = {
        "intent": result.intent,
        "mode": result.mode,
        "plan_steps": result.plan_steps,
        "resolved_question": result.resolved_question,
        "driver_rankings": result.driver_rankings,
    }
    query_run = save_query_run(
        UUID(assistant_msg["id"]),
        question_text=body.question,
        sql_text=result.sql or "-- no sql",
        status=result.status,
        row_count=result.row_count,
        duration_ms=result.duration_ms,
        error_message=result.error,
        result_preview=result.result_preview,
        chart_spec=result.chart_spec,
        run_metadata=run_metadata,
        org_id=ctx.org_id,
    )
    log_audit(ctx.org_id, ctx.user_id, "query.ask", "query_run", query_run["id"])
    assistant_content["query_run_id"] = query_run["id"]
    return {
        "user_message": user_msg,
        "assistant_message": {**assistant_msg, "content": assistant_content},
        "query_run_id": query_run["id"],
    }


@app.post("/v1/query-runs/{query_run_id}/feedback", dependencies=[Depends(optional_api_key)])
def post_feedback(
    query_run_id: UUID,
    body: FeedbackRequest,
    ctx: AuthContext = Depends(require_min_role("member")),
):
    try:
        return upsert_feedback(query_run_id, body.rating, body.comment)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/v1/ask", dependencies=[Depends(optional_api_key)])
def ask_stateless(body: AskRequest, ctx: AuthContext = Depends(require_min_role("member"))):
    try:
        ensure_quota(ctx.org_id)
    except UsageQuotaExceeded as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    result = run_agent(body.question)
    record_query_usage(ctx.org_id)
    return {"question": body.question, "status": result.status, "insight": result.insight, "sql": result.sql}
