from __future__ import annotations

from fastapi import Header, HTTPException

from insightbridge.config import settings


def optional_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> None:
    """When API_KEY is configured, require matching X-API-Key on mutating routes."""
    if not settings.api_key:
        return
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
