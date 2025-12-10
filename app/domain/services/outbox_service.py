"""
app/domain/services/outbox_service.py

Servicio para gestión de eventos del Outbox Pattern.
"""

import json
import logging
from datetime import datetime, timezone

from sqlalchemy import exists, select, update
from sqlalchemy.orm import Session

from app.domain.models.models import EstadoOutboxEvent, LoteEnvio, OutboxEvent

logger = logging.getLogger(__name__)


class OutboxService:
    """
    Servicio para gestión de eventos Outbox.

    Patrón Outbox garantiza:
    - Atomicidad: lote + evento en la MISMA transacción
    - FIFO: orden por created_at (respeta cadena hash)
    - Idempotencia: cada lote tiene exactamente 1 evento
    """

    def __init__(self, db: Session):
        self.db = db

    def crear_evento(
        self,
        lote: LoteEnvio,
        task_name: str = "app.tasks.worker_aeat.enviar_lote_aeat",
        max_intentos: int = 10,
    ) -> OutboxEvent:
        """
        Crea un evento outbox asociado a un lote.

        CRÍTICO: Este método debe ejecutarse en la MISMA transacción
        que la creación del lote. NO hace commit.

        Args:
            lote: Lote recién creado (debe tener ID después de flush)
            task_name: Nombre de la tarea Celery a ejecutar
            max_intentos: Número máximo de reintentos

        Returns:
            OutboxEvent creado (sin commitear)

        Raises:
            ValueError: Si el lote no tiene ID (falta flush)
        """
        if not lote.id:
            raise ValueError(
                "El lote debe tener ID antes de crear evento (ejecutar flush primero)"
            )

        # Crear payload (solo lote_id necesario)
        payload = json.dumps({"lote_id": lote.id})

        # Crear evento
        evento = OutboxEvent(
            lote_id=lote.id,
            instalacion_sif_id=lote.instalacion_sif_id,
            estado=EstadoOutboxEvent.PENDIENTE,
            task_name=task_name,
            payload=payload,
            intentos=0,
            max_intentos=max_intentos,
        )

        self.db.add(evento)
        self.db.flush()  # Obtener ID del evento sin commitear

        logger.info(
            f"Evento outbox {evento.id} creado para lote {lote.id} "
            f"(instalación {lote.instalacion_sif_id})"
        )

        return evento

    def marcar_encolado(self, evento_id: int) -> None:
        """
        Marca un evento como encolado en Celery.

        Args:
            evento_id: ID del evento
        """
        # evento = self.db.get(OutboxEvent, evento_id)
        # if not evento:
        #     logger.warning(f"Evento {evento_id} no encontrado para marcar encolado")
        #     return

        # evento.estado = EstadoOutboxEvent.ENCOLADO
        # evento.intentos += 1
        # evento.ultimo_intento_at = datetime.now(timezone.utc)
        exists_stmt = select(exists().where(OutboxEvent.id == evento_id))
        if not self.db.execute(exists_stmt).scalar():
            logger.warning(f"Evento {evento_id} no encontrado para marcar encolado")
            return
        stmt = (
            update(OutboxEvent)
            .where(OutboxEvent.id == evento_id)
            .values(
                estado=EstadoOutboxEvent.ENCOLADO,
                intentos=OutboxEvent.intentos + 1,
                ultimo_intento_at=datetime.now(timezone.utc),
            )
        )
        self.db.execute(stmt)

        # NO hacer commit aquí - el caller lo hará

    def marcar_procesado(self, evento_id: int) -> None:
        """
        Marca un evento como procesado exitosamente.

        Args:
            evento_id: ID del evento
        """
        evento = self.db.get(OutboxEvent, evento_id)
        if not evento:
            logger.warning(f"Evento {evento_id} no encontrado para marcar procesado")
            return

        evento.estado = EstadoOutboxEvent.PROCESADO
        evento.procesado_at = datetime.now(timezone.utc)

        logger.info(f"Evento {evento_id} marcado como procesado")

    def marcar_error(self, evento_id: int, error_mensaje: str) -> None:
        """
        Marca un evento como error final (después de todos los reintentos).

        Args:
            evento_id: ID del evento
            error_mensaje: Descripción del error
        """
        evento = self.db.get(OutboxEvent, evento_id)
        if not evento:
            logger.warning(f"Evento {evento_id} no encontrado para marcar error")
            return

        evento.estado = EstadoOutboxEvent.ERROR
        evento.error_mensaje = error_mensaje[:500]  # Limitar longitud
        evento.ultimo_intento_at = datetime.now(timezone.utc)

        logger.error(f"Evento {evento_id} marcado como error final: {error_mensaje}")
