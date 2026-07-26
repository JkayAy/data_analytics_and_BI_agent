from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from insightbridge.config import settings
from insightbridge.db_tenancy import (
    consume_magic_link,
    ensure_org_member,
    get_member,
    issue_magic_link,
    log_audit,
    upsert_user_by_email,
)
from insightbridge.request_context import AuthContext, auth_context_var

_bearer = HTTPBearer(auto_error=False)

ROLE_RANK = {"viewer": 0, "member": 1, "admin": 2, "owner": 3}


def create_access_token(*, user_id: str, org_id: str, role: str, email: str) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": user_id,
        "org_id": org_id,
        "role": role,
        "email": email,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=settings.jwt_expire_hours)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc


def request_magic_link(email: str) -> dict[str, Any]:
    email_n = email.strip().lower()
    raw = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw.encode()).hexdigest()
    issue_magic_link(email_n, token_hash, settings.magic_link_expire_minutes)
    out: dict[str, Any] = {"ok": True, "email": email_n}
    if settings.magic_link_dev_expose:
        out["magic_link_token"] = raw
        out["verify_path"] = "/v1/auth/verify"
    return out


def verify_magic_link(raw_token: str) -> dict[str, Any]:
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    email = consume_magic_link(token_hash)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid or expired magic link")
    user = upsert_user_by_email(email)
    ensure_org_member(settings.default_org_id, user["id"], "member")
    member = get_member(user["id"], settings.default_org_id)
    if not member:
        raise HTTPException(status_code=403, detail="User has no organization membership")
    access = create_access_token(
        user_id=member["user_id"],
        org_id=member["org_id"],
        role=member["role"],
        email=user["email"],
    )
    log_audit(member["org_id"], member["user_id"], "auth.login", "user", member["user_id"])
    return {
        "access_token": access,
        "token_type": "bearer",
        "user": {"id": user["id"], "email": user["email"], "name": user.get("name")},
        "org": {"id": member["org_id"], "role": member["role"]},
    }


def get_auth_context(
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer),
) -> AuthContext:
    if credentials and credentials.credentials:
        payload = decode_access_token(credentials.credentials)
        ctx = AuthContext(
            user_id=payload["sub"],
            org_id=payload["org_id"],
            role=payload["role"],
            email=payload.get("email", ""),
        )
        auth_context_var.set(ctx)
        return ctx

    if settings.auth_required:
        raise HTTPException(status_code=401, detail="Authentication required")

    ctx = AuthContext(
        user_id=settings.default_user_id,
        org_id=settings.default_org_id,
        role="owner",
        email="demo@insightbridge.local",
    )
    auth_context_var.set(ctx)
    return ctx


def require_min_role(min_role: str):
    def _dep(ctx: AuthContext = Security(get_auth_context)) -> AuthContext:
        if ROLE_RANK.get(ctx.role, 0) < ROLE_RANK.get(min_role, 99):
            raise HTTPException(status_code=403, detail=f"Requires role {min_role} or higher")
        return ctx

    return _dep
