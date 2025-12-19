"""
app/tasks/scheduler.py

CAPA 1: Planificador ligero (Celery Beat: cada 5 min)

Responsabilidad ÚNICA:
- Evaluar condiciones de control de flujo por instalación
- Encolar tareas de orquestación (NO crea lotes aquí)

Garantías:
- Sin locks (lectura rápida)
- Sin transacciones pesadas
- Delegación a orquestador por instalación
"""

import logging
from typing import cast
from uuid import uuid4

from celery import Task
from sqlalchemy import select

from app.core.logging.logging_context import set_correlation_id
from app.domain.models.models import InstalacionSIF
from app.domain.services.lote_service import LoteService
from app.infrastructure.database import get_sync_db
from app.tasks.decorators import typed_task

logger = logging.getLogger(__name__)


@typed_task
def scheduler_envios_ligero() -> None:
    """
    Scheduler ligero: evalúa condiciones y delega a orquestador.

    Responsabilidad:
    - Leer instalaciones activas
    - Evaluar condiciones de control de flujo (rápido, sin locks)
    - Encolar tarea de orquestación por cada instalación que califique

    NO hace:
    - Crear lotes (responsabilidad del orquestador)
    - Adquirir locks (responsabilidad del orquestador)
    - Crear eventos outbox (responsabilidad del orquestador)

    Ejecutar: Cada 5 minutos vía Celery Beat
    """
    correlation_id = str(uuid4())
    set_correlation_id(correlation_id)
    logger.info("Scheduler ligero iniciado")

    stats = {
        "total": 0,
        "encoladas": 0,
        "sin_condiciones": 0,
    }

    with get_sync_db() as db:
        # Obtener todas las instalaciones activas
        instalaciones = db.scalars(select(InstalacionSIF)).all()
        stats["total"] = len(instalaciones)

        logger.info(
            "Evaluando instalaciones activas",
            extra={"total_instalaciones": stats["total"]},
        )

        # Servicio para evaluación de control de flujo (solo lectura)
        servicio = LoteService(db)

        for ins in instalaciones:
            try:
                # Evaluación rápida: ¿cumple condiciones?
                cumple_condiciones = servicio.control_flujo(ins.id, max_registros=1000)

                if cumple_condiciones:
                    # Encolar tarea de orquestación (procesamiento pesado)
                    from app.tasks.orquestador import orquestar_instalacion

                    cast(Task, orquestar_instalacion).apply_async(
                        args=[ins.id],
                        kwargs={"correlation_id": correlation_id},
                    )
                    stats["encoladas"] += 1

                    logger.info(
                        "Instalación encolada para orquestación",
                        extra={"instalacion_id": ins.id},
                    )
                else:
                    stats["sin_condiciones"] += 1
                    logger.debug(
                        "Instalación no cumple condiciones, omitida",
                        extra={"instalacion_id": ins.id},
                    )

            except Exception as e:
                # Error en evaluación: log y continuar
                logger.error(
                    "Error evaluando instalación",
                    extra={
                        "instalacion_id": ins.id,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                    exc_info=True,
                )
                continue

    logger.info(
        "Scheduler ligero completado",
        extra={
            "total_instalaciones": stats["total"],
            "encoladas": stats["encoladas"],
            "sin_condiciones": stats["sin_condiciones"],
        },
    )
