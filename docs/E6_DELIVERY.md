# E6 — Delivery & ops

## Features

| Capability | Description |
|------------|-------------|
| **Slack / Teams outbound** | Encrypted incoming webhook URLs per org (`POST /v1/delivery/channels`) |
| **Scheduled reports** | Cron + timezone; background APScheduler in API (or external cron) |
| **Slack slash command** | `POST /v1/integrations/slack/commands` with signing secret |
| **Usage metering** | Monthly query counts per org; optional cap (`MONTHLY_QUERY_CAP`) |

## API

| Method | Path | Role |
|--------|------|------|
| GET | `/v1/delivery/channels` | member |
| POST | `/v1/delivery/channels` | admin |
| POST | `/v1/delivery/channels/{id}/test` | admin |
| GET | `/v1/schedules` | member |
| POST | `/v1/schedules` | admin |
| PATCH | `/v1/schedules/{id}` | admin |
| POST | `/v1/schedules/run-due` | admin |
| GET | `/v1/orgs/{org_id}/usage` | member |

## Environment

```env
SCHEDULER_ENABLED=true
SCHEDULER_POLL_SECONDS=60
MONTHLY_QUERY_CAP=0          # 0 = unlimited
SLACK_SIGNING_SECRET=        # for /ask slash command
```

## Slack setup

1. Create Slack app → Incoming Webhook → paste URL in delivery channel API.
2. Optional slash command `/insight` pointing to `https://your-api/v1/integrations/slack/commands`.
3. Set `SLACK_SIGNING_SECRET` from app credentials.

## Teams setup

1. Incoming Webhook connector in channel → URL in `channel_type: teams`.

## Cron without in-process scheduler

```bash
cd apps/api
python -m insightbridge.cli_run_schedules
```

Schedule via Railway cron or GitHub Actions every minute.

## Migration

`infra/seed/08_e6_delivery.sql` (included in `migrate-docker.ps1`).

## Stripe (future)

Usage rows in `app.org_usage_monthly` are ready to map to Stripe metered billing; wire webhooks in a dedicated billing service when going commercial.
