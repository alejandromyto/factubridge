"""
app/tasks/monitoring.py

Tareas de monitoreo y alertas para Outbox Pattern.

Responsabilidad:
- Detectar atasco del dispatcher (eventos pendientes > 2 min)
- Alertar eventos en error final
- Estadísticas de salud del sistema
"""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from app.domain.models.models import EstadoOutboxEvent, OutboxEvent
from app.infrastructure.database import get_sync_db
from app.tasks.decorators import typed_task

logger = logging.getLogger(__name__)


@typed_task()
def detector_atasco_dispatcher() -> None:
    """
    Detecta si el dispatcher está atascado.

    ALERTA CRÍTICA:
    - Si hay eventos pendientes > 2 minutos → dispatcher detenido
    - Impacto: Instalaciones no envían (disponibilidad)
    - NO impacta: Integridad de cadena hash (garantizada por diseño)

    Ejecutar: Cada 1 minuto vía Celery Beat
    """
    logger.info("=== Detector de atasco iniciado ===")

    umbral_tiempo = datetime.now(timezone.utc) - timedelta(minutes=2)

    with get_sync_db() as db:
        # Contar eventos pendientes antiguos (> 2 minutos)
        count_atascados = db.scalar(
            select(func.count()).where(
                OutboxEvent.estado == EstadoOutboxEvent.PENDIENTE,
                OutboxEvent.created_at < umbral_tiempo,
            )
        )

        if count_atascados and count_atascados > 0:
            # ⚠️ ALERTA CRÍTICA: Dispatcher atascado
            logger.critical(
                f"⚠️⚠️⚠️ ALERTA CRÍTICA: {count_atascados} eventos pendientes "
                f"desde hace más de 2 minutos. "
                f"El dispatcher puede estar detenido. "
                f"ACCIÓN REQUERIDA: Revisar worker 'dispatcher' y logs."
            )

            # TODO: Integrar con sistema de alertas
            # - Sentry: sentry_sdk.capture_message(...)
            # - PagerDuty: incident API
            # - Email: enviar a equipo de ops
            # - Slack: webhook de alerta

            # Obtener detalle de eventos atascados (para debugging)
            eventos_atascados = db.scalars(
                select(OutboxEvent)
                .where(
                    OutboxEvent.estado == EstadoOutboxEvent.PENDIENTE,
                    OutboxEvent.created_at < umbral_tiempo,
                )
                .order_by(OutboxEvent.created_at.asc())
                .limit(10)
            ).all()

            logger.critical(
                f"Primeros eventos atascados: "
                f"{[(e.id, e.lote_id, e.created_at) for e in eventos_atascados]}"
            )
        else:
            logger.debug("✅ Dispatcher funcionando correctamente (sin atasco)")


@typed_task()
def alertar_eventos_error() -> None:
    """
    Revisa eventos en estado ERROR y genera alertas.

    Estos eventos fallaron después de todos los reintentos.
    Requieren intervención manual.

    Ejecutar: Cada 10 minutos vía Celery Beat
    """
    logger.info("=== Revisor de eventos en error ===")

    with get_sync_db() as db:
        # Contar eventos en error
        count_errores = db.scalar(
            select(func.count()).where(OutboxEvent.estado == EstadoOutboxEvent.ERROR)
        )

        if count_errores and count_errores > 0:
            logger.warning(
                f"⚠️ {count_errores} eventos en estado ERROR "
                f"(fallaron después de reintentos)"
            )

            # Obtener eventos en error
            eventos_error = db.scalars(
                select(OutboxEvent)
                .where(OutboxEvent.estado == EstadoOutboxEvent.ERROR)
                .order_by(OutboxEvent.ultimo_intento_at.desc())
                .limit(10)
            ).all()

            for evento in eventos_error:
                logger.error(
                    f"Evento {evento.id} en ERROR: lote={evento.lote_id}, "
                    f"instalacion={evento.instalacion_sif_id}, "
                    f"intentos={evento.intentos}/{evento.max_intentos}, "
                    f"error={evento.error_mensaje}"
                )

            # TODO: Integrar con sistema de alertas
            # - Crear ticket en sistema de tracking
            # - Enviar resumen diario al equipo
        else:
            logger.debug("✅ No hay eventos en estado ERROR")


@typed_task
def estadisticas_salud_outbox() -> dict:
    """
    Genera estadísticas de salud del sistema outbox.

    Útil para dashboards y monitoreo.

    Returns:
        Dict con métricas del sistema

    Ejecutar: Cada 5 minutos vía Celery Beat (opcional)
    """
    logger.info("=== Generando estadísticas de salud ===")

    with get_sync_db() as db:
        # Contar por estado
        stats = {}

        for estado in EstadoOutboxEvent:
            count = db.scalar(select(func.count()).where(OutboxEvent.estado == estado))
            stats[estado.value] = count or 0

        # Evento más antiguo pendiente
        evento_mas_antiguo = db.scalar(
            select(OutboxEvent.created_at)
            .where(OutboxEvent.estado == EstadoOutboxEvent.PENDIENTE)
            .order_by(OutboxEvent.created_at.asc())
            .limit(1)
        )

        if evento_mas_antiguo:
            edad_segundos = (
                datetime.now(timezone.utc) - evento_mas_antiguo
            ).total_seconds()
            stats["evento_pendiente_mas_antiguo_segundos"] = int(edad_segundos)
        else:
            stats["evento_pendiente_mas_antiguo_segundos"] = 0

        # Total de eventos (histórico)
        stats["total_eventos"] = sum(stats.values())

        logger.info(f"Estadísticas outbox: {stats}")

        # TODO: Enviar a sistema de métricas
        # - Prometheus: push_gateway
        # - Datadog: statsd
        # - CloudWatch: put_metric_data

        return stats
