import uuid
from typing import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.logging.logging_context import set_correlation_id


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware que:

    - Lee X-Request-ID si existe
    - Genera uno nuevo si no
    - Lo guarda en contextvars
    - Lo devuelve en la respuesta
    """

    def __init__(self, app: ASGIApp, header_name: str = "X-Request-ID"):
        super().__init__(app)
        self.header_name = header_name

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        correlation_id = request.headers.get(self.header_name)

        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        # Guardar en contextvar
        set_correlation_id(correlation_id)

        response = await call_next(request)

        # Exponer en respuesta
        response.headers[self.header_name] = correlation_id

        return response
