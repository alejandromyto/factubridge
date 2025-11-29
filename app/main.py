import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.v1 import consulta_endpoint, factura_endpoint
from app.config.settings import settings
from app.infrastructure.database import Base, engine

# Configurar logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifecycle: startup y shutdown"""
    # Startup
    logger.info("Iniciando Factubridge...")

    # Crear tablas (en producción usar Alembic)
    if settings.debug:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Tablas de BD creadas/verificadas")

    yield

    # Shutdown
    logger.info("Cerrando Factubridge...")
    await engine.dispose()


# Crear app
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    debug=settings.debug,
    lifespan=lifespan,
)

# Rate limiter state
app.state.limiter = limiter


# Wrapper para que mypy esté contento
async def custom_rate_limit_handler(request: Request, exc: Exception) -> Response:
    """Handler personalizado para rate limit (type-safe)"""
    # Verificación explícita para satisfacer al type checker
    if not isinstance(exc, RateLimitExceeded):
        logger.error(f"Handler called with unexpected exception: {type(exc)}")
        raise exc

    # Llamada segura con el tipo correcto
    return _rate_limit_exceeded_handler(request, exc)


# Manejar excepción de rate limit
app.add_exception_handler(RateLimitExceeded, custom_rate_limit_handler)

# ===== Middlewares =====

# CORS (ajustar origins en producción)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else [],  # Configurar en prod
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Trusted Host (descomentar en producción con dominio real)
# app.add_middleware(
#     TrustedHostMiddleware,
#     allowed_hosts=["api.tudominio.com", "localhost"]
# )


# ===== Exception handlers =====


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Error no manejado: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Error interno del servidor",
            "detalle": str(exc) if settings.debug else None,
        },
    )


# ===== Rutas =====


@app.get("/")
async def root() -> Dict[str, Any]:
    return {
        "nombre": settings.api_title,
        "version": settings.api_version,
        "estado": "operativo",
        "documentacion": "/docs",
    }


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check para monitorización"""
    return {"status": "healthy"}


# Incluir routers
app.include_router(
    factura_endpoint.router, prefix=settings.api_prefix, tags=["Facturas"]
)

app.include_router(
    consulta_endpoint.router, prefix=settings.api_prefix, tags=["Consultas"]
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.debug)
