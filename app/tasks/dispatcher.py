"""
app/tasks/dispatcher.py

CAPA 3: Dispatcher de eventos outbox (Worker: dispatcher)

Responsabilidad:
- Leer eventos pendientes (FIFO por created_at)
- Encolar en worker AEAT con retry policy
- Marcar como 'encolado' en transacción SEPARADA

Garantías:
- FIFO estricto: ORDER BY created_at (cadena hash respetada)
- Transacción INDEPENDIENTE del orquestador
- Si falla, eventos siguen en 'pendiente' (reintento automático)
- SELECT FOR UPDATE SKIP LOCKED (concurrencia segura)

Ejecutar: Cada 10 segundos vía Celery Beat
"""

import json
import logging
from typing import List, cast

from celery import Task
from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.logging.logging_context import set_correlation_id
from app.domain.models.models import (
    EstadoLoteEnvio,
    EstadoOutboxEvent,
    LoteEnvio,
    OutboxEvent,
)
from app.domain.services.outbox_service import OutboxService
from app.infrastructure.database import session_factory_sync
from app.tasks.decorators import typed_task

logger = logging.getLogger(__name__)


@typed_task
def dispatch_outbox_event(
    batch_size: int = 10, correlation_id: str | None = None
) -> None:
    """
    Dispatcher: lee eventos pendientes y los encola al worker AEAT.

    GARANTÍA FIFO CRÍTICA (Art. 12):
    - ORDER BY created_at ASC: respeta orden de creación
    - Cadena hash nunca se rompe por procesamiento fuera de orden

    Args:
        batch_size: Número máximo de eventos a procesar por ejecución

    Flujo:
    1. SELECT FOR UPDATE SKIP LOCKED (eventos pendientes, FIFO)
    2. Para cada evento:
       a. Encolar en worker AEAT con retry policy
       b. Marcar evento y lote como ENCOLADO
    3. COMMIT (transacción SEPARADA del orquestador)

    Ejecutar: Cada 10 segundos vía Celery Beat
    """
    logger.info("Dispatcher outbox iniciado")

    stats = {
        "leidos": 0,
        "encolados": 0,
        "errores": 0,
    }

    db: Session = session_factory_sync()

    try:
        # PASO 1: Leer eventos pendientes (FIFO, con lock)
        eventos: List[OutboxEvent] = list(
            db.execute(
                select(OutboxEvent)
                .where(OutboxEvent.estado == EstadoOutboxEvent.PENDIENTE)
                .order_by(
                    OutboxEvent.created_at.asc(), OutboxEvent.id.asc()
                )  # FIFO crítico
                .limit(batch_size)
                .with_for_update(skip_locked=True)  # Concurrencia segura
            )
            .scalars()
            .all()
        )

        stats["leidos"] = len(eventos)

        if not eventos:
            logger.debug("No hay eventos pendientes para despachar")
            return

        logger.info(
            "Procesando eventos pendientes",
            extra={"eventos_leidos": stats["leidos"]},
        )

        # PASO 2: Encolar cada evento en worker AEAT
        servicio_outbox = OutboxService(db)

        from app.tasks.worker_aeat import enviar_lote_aeat

        for evento in eventos:
            try:
                # Parsear payload
                payload = json.loads(evento.payload)
                lote_id = payload["lote_id"]
                correlation_id = payload.get("correlation_id")
                set_correlation_id(correlation_id)

                # Encolar en worker AEAT con retry policy agresiva
                cast(Task, enviar_lote_aeat).apply_async(
                    args=[lote_id, evento.id],
                    kwargs={"correlation_id": correlation_id},
                    retry=True,
                    retry_policy={
                        "max_retries": evento.max_intentos,
                        "interval_start": 10,  # 10 segundos
                        "interval_step": 30,  # +30s por intento
                        "interval_max": 300,  # máximo 5 minutos
                    },
                )
                # Lote ENCOLADO
                db.execute(
                    update(LoteEnvio)
                    .where(LoteEnvio.id == evento.lote_id)
                    .values(estado=EstadoLoteEnvio.ENCOLADO)
                )
                # Evento ENCOLADO (flush, NO commit todavía)
                servicio_outbox.marcar_encolado(evento.id)
                stats["encolados"] += 1

                logger.info(
                    "Evento encolado para worker AEAT",
                    extra={
                        "evento_id": evento.id,
                        "lote_id": lote_id,
                        "instalacion_id": evento.instalacion_sif_id,
                    },
                )

            except json.JSONDecodeError as e:
                stats["errores"] += 1
                logger.error(
                    "Error parseando payload del evento",
                    extra={
                        "evento_id": evento.id,
                        "error": str(e),
                        "error_type": "JSONDecodeError",
                    },
                )
                # Marcar como error y continuar
                servicio_outbox.marcar_error(evento.id, f"Payload inválido: {e}")

            except Exception as e:
                stats["errores"] += 1
                logger.error(
                    "Error encolando evento",
                    extra={
                        "evento_id": evento.id,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                    exc_info=True,
                )
                # Continuar con otros eventos
                continue

        # PASO 3: Commit de todos los cambios de estado
        db.commit()

        logger.info(
            "Dispatcher commit exitoso",
            extra={"eventos_encolados": stats["encolados"]},
        )

    except SQLAlchemyError as e:
        # Error de BD: rollback (eventos vuelven a 'pendiente')
        db.rollback()
        logger.error(
            "Error de base de datos en dispatcher, rollback ejecutado",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )
        # No propagar error: siguiente ejecución lo reintentará

    except Exception as e:
        # Error inesperado: rollback
        db.rollback()
        logger.error(
            "Error inesperado en dispatcher, rollback ejecutado",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )

    finally:
        db.close()
        logger.debug("Sesión de base de datos cerrada en dispatcher")

    logger.info(
        "Dispatcher completado",
        extra={
            "eventos_leidos": stats["leidos"],
            "eventos_encolados": stats["encolados"],
            "errores": stats["errores"],
        },
    )
