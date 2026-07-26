from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass


@dataclass(frozen=True)
class AuthContext:
    user_id: str
    org_id: str
    role: str
    email: str


auth_context_var: ContextVar[AuthContext | None] = ContextVar("auth_context", default=None)


def current_auth() -> AuthContext | None:
    return auth_context_var.get()
