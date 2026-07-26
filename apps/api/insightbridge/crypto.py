from __future__ import annotations

import json
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

from insightbridge.config import settings


class CryptoError(Exception):
    pass


def _fernet() -> Fernet:
    key = settings.encryption_key
    if not key:
        raise CryptoError("ENCRYPTION_KEY not configured")
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_json(data: dict[str, Any]) -> str:
    if settings.encryption_key:
        return _fernet().encrypt(json.dumps(data).encode()).decode()
    return "plain:" + json.dumps(data)


def decrypt_json(blob: str) -> dict[str, Any]:
    if blob.startswith("plain:"):
        return json.loads(blob[6:])
    try:
        raw = _fernet().decrypt(blob.encode()).decode()
        return json.loads(raw)
    except (InvalidToken, json.JSONDecodeError) as exc:
        raise CryptoError("Failed to decrypt connection config") from exc
