"""
app/tasks/worker_aeat.py

CAPA 4: Worker de envío a AEAT (Worker: envios, rate_limit='10/m')

Responsabilidad:
- Procesar cada lote individualmente
- Generar XML de envío
- Enviar a AEAT (con timeout y retry)
- Procesar respuesta (tiempo 't', estados)
- Actualizar instalación (ultimo_envio_at, ultimo_tiempo_espera)
- Marcar evento outbox como 'procesado'

CRÍTICO para control de flujo:
- Actualizar instalacion.ultimo_envio_at = now()
- Actualizar instalacion.ultimo_tiempo_espera = tiempo_recibido_aeat
- Estos valores controlan el siguiente envío
"""

import logging

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.domain.models.models import EstadoLoteEnvio, LoteEnvio
from app.domain.services.outbox_service import OutboxService
from app.infrastructure.database import session_factory_sync
from app.tasks.decorators import BindTask, typed_task

logger = logging.getLogger(__name__)


@typed_task(
    bind=True,
    max_retries=10,
    default_retry_delay=30,
    rate_limit="10/m",  # CRÍTICO: máximo 10 envíos por minuto (AEAT)
)
def enviar_lote_aeat(self: BindTask, lote_id: int, evento_id: int) -> None:
    """
    Worker AEAT: procesa un lote y lo envía a AEAT.

    Args:
        lote_id: ID del lote a procesar
        evento_id: ID del evento outbox asociado

    Flujo:
    1. Obtener lote de BD
    2. Generar XML de envío
    3. Enviar a AEAT (POST con timeout 60s)
    4. Procesar respuesta:
       - lote.tiempo_espera_recibido
       - lote.proximo_envio_permitido_at
       - instalacion.ultimo_envio_at = now()
       - instalacion.ultimo_tiempo_espera = tiempo_t
    5. Marcar evento outbox como 'procesado'
    6. COMMIT

    CRÍTICO: Los campos de instalación controlan el próximo envío.

    Reintentos:
    - Máximo 10 intentos
    - 30 segundos entre reintentos (escalonado)
    - Rate limit: 10/minuto (respeta límites AEAT)
    """
    logger.info(f"=== Procesando lote {lote_id} (evento {evento_id}) ===")

    db: Session = session_factory_sync()

    try:
        # PASO 1: Obtener lote
        lote = db.get(LoteEnvio, lote_id)

        if not lote:
            logger.error(f"❌ Lote {lote_id} no encontrado en BD")
            # Marcar evento como error
            servicio_outbox = OutboxService(db)
            servicio_outbox.marcar_error(evento_id, "Lote no encontrado")
            db.commit()
            return  # No reintentar si no existe

        lote.estado = EstadoLoteEnvio.ENVIANDO

        logger.info(
            f"Lote {lote_id}: instalación {lote.instalacion_sif_id}, "
            f"{lote.num_registros} registros"
        )

        # PASO 2-5: Procesar lote completo
        from app.domain.services.process_lote import procesar_lote

        resultado = procesar_lote(lote, db)

        # procesar_lote debe:
        # 1. Generar XML (lote.xml_enviado)
        # 2. Enviar a AEAT
        # 3. Procesar respuesta:
        #    - lote.tiempo_espera_recibido = tiempo_t_recibido
        #    - lote.proximo_envio_permitido_at = now() + tiempo_t
        # 4. Actualizar estados de registros
        # 5. ✅ CRÍTICO: Actualizar instalación

        if not resultado.exitoso:
            raise Exception(f"Error en procesamiento AEAT: {resultado.error}")

        # PLACEHOLDER: Simulación por ahora
        logger.info(f"🔄 Lote {lote_id} listo para envío a AEAT")

        # TODO: Cuando implementes process_lote, descomentar esto:
        # from app.services.process_lote import procesar_lote
        # resultado = procesar_lote(lote, db)

        # PASO CRÍTICO: Actualizar instalación (controla próximo envío)
        # TODO: Esto debería estar dentro de process_lote.procesar_lote()
        """
        tiempo_espera_recibido = resultado.tiempo_espera  # De respuesta AEAT

        db.execute(
            update(InstalacionSIF)
            .where(InstalacionSIF.id == lote.instalacion_sif_id)
            .values(
                ultimo_envio_at=datetime.now(timezone.utc),
                ultimo_tiempo_espera=tiempo_espera_recibido,
            )
        )

        logger.info(
            f"✅ Instalación {lote.instalacion_sif_id} actualizada: "
            f"ultimo_envio_at={datetime.now(timezone.utc)}, "
            f"ultimo_tiempo_espera={tiempo_espera_recibido}s"
        )
        """

        # PASO 6: Marcar evento como procesado
        servicio_outbox = OutboxService(db)
        servicio_outbox.marcar_procesado(evento_id)

        # COMMIT final
        db.commit()

        logger.info(
            f"✅ Lote {lote_id} completado exitosamente "
            f"(evento {evento_id} marcado como procesado)"
        )

    except SQLAlchemyError as e:
        # Error de BD: rollback y reintentar
        db.rollback()
        logger.error(
            f"❌ Error de BD al procesar lote {lote_id}: {e}",
            exc_info=True,
        )

        # Reintentar (Celery lo hará automáticamente)
        raise self.retry(exc=e)

    except Exception as e:
        # Error inesperado: decidir si reintentar
        db.rollback()
        logger.error(
            f"❌ Error al procesar lote {lote_id}: {e}",
            exc_info=True,
        )

        # TODO: Distinguir entre errores retryables y no retryables
        # Retryables: timeout, conexión, Redis caído, 5xx AEAT
        # NO retryables: XML inválido, 4xx AEAT, validación rechazada

        # Por ahora, reintentar todos
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)
        else:
            # Máximo de reintentos alcanzado: marcar como error
            servicio_outbox = OutboxService(db)
            servicio_outbox.marcar_error(
                evento_id, f"Máximo de reintentos alcanzado: {str(e)[:500]}"
            )
            db.commit()
            logger.critical(
                f"⚠️ ALERTA: Lote {lote_id} falló después de {self.max_retries} "
                f"intentos. Evento {evento_id} marcado como ERROR."
            )

    finally:
        db.close()
        logger.debug(f"Sesión cerrada para lote {lote_id}")


# Tarea auxiliar para debugging/testing
@typed_task
def test_worker_aeat() -> str:
    """
    Tarea de prueba para verificar que el worker AEAT funciona.

    Returns:
        Mensaje de confirmación
    """
    logger.info("Worker AEAT de prueba ejecutado correctamente")
    return "Worker AEAT funcionando OK"
