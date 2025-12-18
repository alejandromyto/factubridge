from contextvars import ContextVar
from typing import Optional

# Identificador de correlación por request / task
correlation_id_ctx: ContextVar[Optional[str]] = ContextVar(
    "correlation_id", default=None
)


def get_correlation_id() -> Optional[str]:
    return correlation_id_ctx.get()


def set_correlation_id(value: Optional[str]) -> None:
    correlation_id_ctx.set(value)
