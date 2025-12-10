from typing import Any, Callable, ParamSpec, Protocol, TypeVar

from app.celery import celery_app


class BindTaskRequest(Protocol):
    retries: int


class BindTask(Protocol):
    request: BindTaskRequest
    max_retries: int

    def retry(self, *args: Any, **kwargs: Any) -> Any: ...


P = ParamSpec("P")
R = TypeVar("R")
F = TypeVar("F", bound=Callable[..., object])


def typed_task(
    *task_args: Any, **task_kwargs: Any
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorador tipado para envolver celery_app.task y mantener tipos genéricos.

    Soporta bind=True, max_retries, rate_limit, etc.
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        decorated = celery_app.task(*task_args, **task_kwargs)(func)
        return decorated  # type: ignore[no-any-return]

    return decorator
