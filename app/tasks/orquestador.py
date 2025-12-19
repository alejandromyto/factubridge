"""
app/tasks/orquestador.py

CAPA 2: Orquestador por instalación (Worker: orquestador)

Responsabilidad CRÍTICA:
- Lock exclusivo por instalación (Redis)
- Doble verificación de condiciones de control de flujo
- Creación atómica: lote + evento outbox en MISMA transacción
- Commit: AMBAS ENTIDADES o NADA (garantía de integridad de cadena)

GARANTÍA ABSOLUTA (Art. 12 Reglamento Veri*factu):
- SI commit falla → NINGÚN lote persiste, NINGÚN evento persiste
- SI commit OK → SIEMPRE hay evento outbox para procesar el lote
- LA CADENA HASH NUNCA SE ROMPE por diseño
"""

import logging
from typing import Optional

from redis.lock import Lock as RedisLock
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.domain.services.lote_service import LoteService
from app.domain.services.outbox_service import OutboxService
from app.infrastructure.database import session_factory_sync
from app.infrastructure.redis_client import redis_client
from app.tasks.decorators import BindTask, typed_task

logger = logging.getLogger(__name__)


def adquirir_lock_instalacion(instalacion_id: int) -> Optional[RedisLock]:
    """
    Adquiere lock distribuido exclusivo para una instalación.

    Args:
        instalacion_id: ID de la instalación SIF

    Returns:
        RedisLock si se adquirió exitosamente
        None si ya está bloqueado (non-blocking)
    """
    lock_key = f"sif:{instalacion_id}"

    # Crear lock con timeout de 60 segundos (suficiente para crear lote)
    lock = redis_client.lock(
        lock_key,
        timeout=60,  # Auto-release si worker muere
        blocking=False,  # Non-blocking: retorna inmediatamente
    )

    acquired = lock.acquire(blocking=False)

    if not acquired:
        logger.debug(
            "Lock no disponible, otro worker procesando instalación",
            extra={"instalacion_id": instalacion_id},
        )
        return None

    logger.debug(
        "Lock adquirido para instalación",
        extra={"instalacion_id": instalacion_id},
    )
    return lock


@typed_task(bind=True, max_retries=3, default_retry_delay=30)
def orquestar_instalacion(
    self: BindTask, instalacion_sif_id: int, correlation_id: str | None = None
) -> None:
    """
    Orquesta la creación de lote + evento outbox para una instalación.

    FLUJO CRÍTICO (ATOMICIDAD GARANTIZADA):
    1. Adquirir lock Redis (exclusividad por instalación)
    2. Doble verificación de condiciones de control de flujo
    3. Crear lote (flush, NO commit)
    4. Crear evento outbox (flush, NO commit)
    5. COMMIT ATÓMICO: lote + evento = AMBAS ENTIDADES o NADA
    6. Liberar lock

    Args:
        instalacion_sif_id: ID de la instalación a procesar

    Reintentos:
    - Máximo 3 intentos
    - 30 segundos entre reintentos
    - Solo errores transitorios (BD, Redis)
    - Errores de negocio NO se reintentan
    """
    from app.core.logging.logging_context import set_correlation_id

    set_correlation_id(correlation_id)

    logger.info(
        "Orquestación de instalación iniciada",
        extra={"instalacion_id": instalacion_sif_id},
    )

    lock: Optional[RedisLock] = None
    db: Session = session_factory_sync()

    try:
        # PASO 1: Adquirir lock exclusivo (non-blocking)
        lock = adquirir_lock_instalacion(instalacion_sif_id)

        if not lock:
            logger.info(
                "Instalación bloqueada, otro worker procesándola",
                extra={"instalacion_id": instalacion_sif_id},
            )
            return  # No es error, simplemente ya está siendo procesada

        # PASO 2: Doble verificación de condiciones (dentro del lock)
        servicio_lote = LoteService(db)

        if not servicio_lote.control_flujo(instalacion_sif_id, max_registros=1000):
            logger.info(
                "Instalación no cumple condiciones tras verificación en lock",
                extra={"instalacion_id": instalacion_sif_id},
            )
            return  # Condiciones cambiaron, skip sin error

        # PASO 3: Crear lote (flush, NO commit)
        lote = servicio_lote.crear_lote_para_instalacion(
            instalacion_sif_id, max_registros=1000
        )

        if not lote:
            logger.info(
                "Instalación no generó lote, sin registros disponibles",
                extra={"instalacion_id": instalacion_sif_id},
            )
            return  # Sin registros, skip sin error

        logger.info(
            "Lote creado con flush pendiente de commit",
            extra={
                "lote_id": str(lote.id),
                "instalacion_id": instalacion_sif_id,
            },
        )

        # PASO 4: Crear evento outbox (flush, NO commit)
        servicio_outbox = OutboxService(db)
        evento = servicio_outbox.crear_evento(lote, correlation_id=correlation_id)

        logger.info(
            "Evento outbox creado con flush pendiente de commit",
            extra={
                "evento_id": evento.id,
                "lote_id": str(lote.id),
            },
        )

        # PASO 5: COMMIT ATÓMICO (lote + evento en MISMA transacción)
        db.commit()

        logger.info(
            "COMMIT EXITOSO: Lote y evento persistidos atómicamente",
            extra={
                "lote_id": str(lote.id),
                "evento_id": evento.id,
                "instalacion_id": instalacion_sif_id,
            },
        )

    except SQLAlchemyError as e:
        # Error de BD: rollback y reintentar
        db.rollback()
        logger.error(
            "Error de base de datos al orquestar instalación",
            extra={
                "instalacion_id": instalacion_sif_id,
                "error": str(e),
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )

        # Reintentar (Celery lo hará automáticamente)
        raise self.retry(exc=e)

    except Exception as e:
        # Error inesperado: rollback y reintentar
        db.rollback()
        logger.error(
            "Error inesperado al orquestar instalación",
            extra={
                "instalacion_id": instalacion_sif_id,
                "error": str(e),
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )

        # Reintentar
        raise self.retry(exc=e)

    finally:
        # PASO 6: Liberar lock DESPUÉS del commit
        if lock:
            try:
                lock.release()
                logger.debug(
                    "Lock liberado para instalación",
                    extra={"instalacion_id": instalacion_sif_id},
                )
            except Exception as e:
                logger.warning(
                    "Error al liberar lock para instalación",
                    extra={
                        "instalacion_id": instalacion_sif_id,
                        "error": str(e),
                    },
                )

        db.close()
        logger.debug(
            "Sesión de base de datos cerrada",
            extra={"instalacion_id": instalacion_sif_id},
        )
