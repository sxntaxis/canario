"""SQLite persistence bootstrap for Canario."""

from .database import (
    APPLICATION_ID,
    SCHEMA_VERSION,
    DatabaseIdentityError,
    ensure_schema_v1,
    open_readonly_v1,
    open_writable_v1,
)
from .runtime import RuntimeContractError, verify_runtime_contract

__all__ = [
    "APPLICATION_ID",
    "SCHEMA_VERSION",
    "DatabaseIdentityError",
    "RuntimeContractError",
    "ensure_schema_v1",
    "open_readonly_v1",
    "open_writable_v1",
    "verify_runtime_contract",
]
