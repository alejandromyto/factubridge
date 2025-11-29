# app.services.lote_service.py # construcción, cierre y guardar lote
import uuid
from datetime import datetime
from typing import Optional

from redis import Redis
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.domain.models.aeat_models import (
    EstadoRegistroFacturacion,
    LoteEnvio,
    RegistroFacturacion,
)

# Configuración de Redis para el Candado (ajustar host/port si hay Docker network)
redis_client = Redis(host="redis", port=6379, db=0, decode_responses=True)


class LoteService:
    """
    Servicio encargado de:

      - agrupar registros pendientes
      - crear el lote
      - asociarlos
      - marcar registros como ENCOLADO
    """

    def __init__(self, db: Session):
        self.db = db

    async def crear_lote_para_instalacion(
        self,
        instalacion_sif_id: int,
        max_registros: int,
    ) -> Optional[LoteEnvio]:
        lock_key = f"sif_lock:{instalacion_sif_id}"

        # Token único para asegurar que solo quien puso el candado lo pueda quitar
        lock_token = str(uuid.uuid4())  # Generar un token único para este proceso

        # Intentar adquirir candado
        lock_acquired = redis_client.set(lock_key, lock_token, nx=True, ex=300)

        if not lock_acquired:
            # El llamador decidirá si reintenta (por ejemplo, Celery retry)
            return None
        try:
            # Seleccionar registros pendientes (FOR UPDATE SKIP LOCKED)
            stmt = (
                select(RegistroFacturacion)
                .where(
                    RegistroFacturacion.instalacion_sif_id == instalacion_sif_id,
                    RegistroFacturacion.estado == EstadoRegistroFacturacion.PENDIENTE,
                )
                .order_by(RegistroFacturacion.created_at)
                .limit(max_registros)
                .with_for_update(skip_locked=True)  # no espera
            )

            registros = list(self.db.execute(stmt).scalars())

            if not registros:
                return None

            # Crear lote
            lote = LoteEnvio(
                instalacion_sif_id=instalacion_sif_id,
                num_registros=len(registros),
                xml_enviado="",  # se rellenará en el paso de generación XML
            )

            self.db.add(lote)
            self.db.flush()  # obtener ID del lote antes de asociar

            # Asociar registros al lote
            lote.registros.extend(registros)

            # Actualizar registros → ENCOLADO
            ids = [r.id for r in registros]
            self.db.execute(
                update(RegistroFacturacion)
                .where(RegistroFacturacion.id.in_(ids))
                .values(
                    estado=EstadoRegistroFacturacion.ENCOLADO,
                    ultimo_intento_at=datetime.utcnow(),
                )
            )

            self.db.commit()
            return lote

        except Exception:
            self.db.rollback()
            raise

        finally:
            # Liberar candado si sigue siendo nuestro
            if redis_client.get(lock_key) == lock_token:
                redis_client.delete(lock_key)
