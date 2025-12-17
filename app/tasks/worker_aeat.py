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
    5. Actualizar estados de registros según respuesta
    6. Marcar evento outbox como 'procesado'
    7. COMMIT

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

        # Actualizar estado a ENVIANDO
        lote.estado = EstadoLoteEnvio.ENVIANDO
        db.flush()

        logger.info(
            f"Lote {lote_id}: instalación {lote.instalacion_sif_id}, "
            f"{lote.num_registros} registros"
        )

        # PASO 2-5: Procesar lote completo
        # ProcessLoteService se encarga de:
        # - Generar XML
        # - Enviar a AEAT
        # - Parsear respuesta
        # - Actualizar BD (lote, registros, instalación)
        from app.domain.services.process_lote import procesar_lote

        resultado = procesar_lote(lote, db)

        # Verificar si fue exitoso
        if not resultado.exitoso:
            # Construir mensaje de error descriptivo
            error_msg = resultado.error_parseo or "Error desconocido"

            if resultado.mensaje_resumen:
                error_msg = f"{resultado.mensaje_resumen}: {error_msg}"

            # Si hay registros con error, incluir algunos ejemplos
            if resultado.registros_error:
                ejemplos = []
                for reg_err in resultado.registros_error[:3]:  # Primeros 3
                    if reg_err.es_duplicado:
                        ejemplos.append(f"Registro {reg_err.ref_externa}: DUPLICADO")
                    else:
                        ejemplos.append(
                            f"Registro {reg_err.ref_externa}: "
                            f"{reg_err.codigo_error} - {reg_err.descripcion_error}"
                        )

                if ejemplos:
                    error_msg += f". Ejemplos: {'; '.join(ejemplos)}"

            # Actualizar estado del lote según el tipo de error
            # Si es error de parseo/comunicación, es ERROR
            lote.estado = EstadoLoteEnvio.ERROR
            db.flush()

            raise Exception(f"Error en procesamiento AEAT: {error_msg}")

        # Éxito: actualizar estado del lote según respuesta AEAT
        from app.infrastructure.aeat.models.respuesta_suministro import EstadoEnvioType

        if resultado.estado_envio == EstadoEnvioType.CORRECTO:
            lote.estado = EstadoLoteEnvio.CORRECTO
        elif resultado.estado_envio == EstadoEnvioType.PARCIALMENTE_CORRECTO:
            lote.estado = EstadoLoteEnvio.PARCIALMENTE_CORRECTO
        elif resultado.estado_envio == EstadoEnvioType.INCORRECTO:
            lote.estado = EstadoLoteEnvio.INCORRECTO
        else:
            # Fallback por si AEAT devuelve algo inesperado
            lote.estado = EstadoLoteEnvio.ERROR

        db.flush()

        logger.info(
            f"✅ Lote {lote_id} procesado exitosamente: {resultado.mensaje_resumen}"
        )

        # PASO 6: Marcar evento como procesado
        servicio_outbox = OutboxService(db)
        servicio_outbox.marcar_procesado(evento_id)

        # COMMIT final
        db.commit()

        logger.info(
            f"✅ Lote {lote_id} completado exitosamente "
            f"(evento {evento_id} marcado como procesado)"
        )

        # Log de estadísticas
        logger.info(
            f"📊 Estadísticas del lote {lote_id}: "
            f"{resultado.registros_correctos} correctos, "
            f"{resultado.registros_con_errores_aceptados} con warnings, "
            f"{resultado.registros_incorrectos} rechazados"
        )

        if resultado.tiene_duplicados:
            logger.warning(
                f"⚠️ Lote {lote_id} tiene {len(resultado.registros_duplicados)} "
                f"registros duplicados"
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

        # Distinguir entre errores retryables y no retryables
        error_str = str(e).lower()

        # Errores NO retryables (problemas de validación o negocio)
        errores_no_retryables = [
            "lote sin registros",
            "xml inválido",
            "validación rechazada",
        ]

        es_no_retryable = any(err in error_str for err in errores_no_retryables)

        # Errores retryables: timeout, conexión, 5xx de AEAT
        errores_retryables = [
            "timeout",
            "connection",
            "502",
            "503",
            "504",
        ]

        es_retryable = any(err in error_str for err in errores_retryables)

        if es_no_retryable:
            # No reintentar, marcar como error permanente
            logger.warning(f"⚠️ Error no retryable en lote {lote_id}: {e}")

            # Actualizar estado del lote
            lote = db.get(LoteEnvio, lote_id)
            if lote:
                lote.estado = EstadoLoteEnvio.ERROR
                db.flush()

            servicio_outbox = OutboxService(db)
            servicio_outbox.marcar_error(
                evento_id, f"Error no retryable: {str(e)[:500]}"
            )
            db.commit()
            return  # No propagar excepción (no reintentar)

        # Errores retryables (timeout, conexión, 5xx, etc.)
        if self.request.retries < self.max_retries:
            logger.warning(
                f"🔄 Reintentando lote {lote_id} "
                f"(intento {self.request.retries + 1}/{self.max_retries})"
            )

            # Actualizar estado del lote si es 5xx de AEAT
            if es_retryable:
                lote = db.get(LoteEnvio, lote_id)
                if lote:
                    lote.estado = EstadoLoteEnvio.ERROR_REINTENTABLE
                    db.flush()
                    db.commit()

            raise self.retry(exc=e)
        else:
            # Máximo de reintentos alcanzado: marcar como error permanente
            lote = db.get(LoteEnvio, lote_id)
            if lote:
                lote.estado = EstadoLoteEnvio.ERROR
                db.flush()

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
