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
            f"Lock para instalación {instalacion_id} no disponible "
            f"(otro worker procesándola)"
        )
        return None

    logger.debug(f"Lock adquirido para instalación {instalacion_id}")
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
        f"Orquestando instalación {instalacion_sif_id}"
        f" | correlation_id={correlation_id}"
    )

    lock: Optional[RedisLock] = None
    db: Session = session_factory_sync()

    try:
        # PASO 1: Adquirir lock exclusivo (non-blocking)
        lock = adquirir_lock_instalacion(instalacion_sif_id)

        if not lock:
            logger.info(
                f"⏭️ Instalación {instalacion_sif_id} bloqueada, "
                f"otro worker la está procesando (skip)"
            )
            return  # No es error, simplemente ya está siendo procesada

        # PASO 2: Doble verificación de condiciones (dentro del lock)
        servicio_lote = LoteService(db)

        if not servicio_lote.control_flujo(instalacion_sif_id, max_registros=1000):
            logger.info(
                f"⏭️ Instalación {instalacion_sif_id} ya no cumple condiciones "
                f"(cambió entre scheduler y orquestador)"
            )
            return  # Condiciones cambiaron, skip sin error

        # PASO 3: Crear lote (flush, NO commit)
        lote = servicio_lote.crear_lote_para_instalacion(
            instalacion_sif_id, max_registros=1000
        )

        if not lote:
            logger.info(
                f"⏭️ Instalación {instalacion_sif_id} no generó lote "
                f"(sin registros disponibles)"
            )
            return  # Sin registros, skip sin error

        logger.info(
            f"Lote {lote.id} creado (flush) para instalación {instalacion_sif_id}"
        )

        # PASO 4: Crear evento outbox (flush, NO commit)
        servicio_outbox = OutboxService(db)
        evento = servicio_outbox.crear_evento(lote, correlation_id=correlation_id)

        logger.info(f"Evento outbox {evento.id} creado (flush) para lote {lote.id}")

        # PASO 5: ✅ COMMIT ATÓMICO (lote + evento en MISMA transacción)
        db.commit()

        logger.info(
            f"✅ COMMIT EXITOSO: Lote {lote.id} + Evento {evento.id} "
            f"persistidos atómicamente (instalación {instalacion_sif_id})"
        )

    except SQLAlchemyError as e:
        # Error de BD: rollback y reintentar
        db.rollback()
        logger.error(
            f"❌ Error de BD al orquestar instalación {instalacion_sif_id}: {e}",
            exc_info=True,
        )

        # Reintentar (Celery lo hará automáticamente)
        raise self.retry(exc=e)

    except Exception as e:
        # Error inesperado: rollback y reintentar
        db.rollback()
        logger.error(
            f"❌ Error inesperado al orquestar instalación {instalacion_sif_id}: {e}",
            exc_info=True,
        )

        # Reintentar
        raise self.retry(exc=e)

    finally:
        # PASO 6: Liberar lock DESPUÉS del commit
        if lock:
            try:
                lock.release()
                logger.debug(f"Lock liberado para instalación {instalacion_sif_id}")
            except Exception as e:
                logger.warning(
                    f"Error al liberar lock para instalación {instalacion_sif_id}: {e}"
                )

        db.close()
        logger.debug(f"Sesión cerrada para instalación {instalacion_sif_id}")
