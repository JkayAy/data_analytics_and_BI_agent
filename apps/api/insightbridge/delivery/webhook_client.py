from __future__ import annotations

import httpx


class WebhookDeliveryError(Exception):
    pass


def post_json(webhook_url: str, payload: dict, *, timeout: float = 15.0) -> None:
    if not webhook_url or not webhook_url.startswith("http"):
        raise WebhookDeliveryError("Webhook URL not configured")
    try:
        resp = httpx.post(webhook_url, json=payload, timeout=timeout)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise WebhookDeliveryError(str(exc)) from exc
