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
    # Logger con contexto (en JSON aparecerán lote_id y evento_id)
    logger.info(
        "Iniciando procesamiento de lote",
        extra={"lote_id": str(lote_id), "evento_id": evento_id},
    )

    db: Session = session_factory_sync()

    try:
        # PASO 1: Obtener lote
        lote = db.get(LoteEnvio, lote_id)

        if not lote:
            logger.error("Lote no encontrado en BD", extra={"lote_id": str(lote_id)})
            # Marcar evento como error
            servicio_outbox = OutboxService(db)
            servicio_outbox.marcar_error(evento_id, "Lote no encontrado")
            db.commit()
            return  # No reintentar si no existe

        # Añadir instalacion_id al contexto para todos los logs siguientes
        log_context = {
            "lote_id": str(lote_id),
            "evento_id": evento_id,
            "instalacion_id": lote.instalacion_sif_id,
        }

        # Actualizar estado a ENVIANDO
        lote.estado = EstadoLoteEnvio.ENVIANDO
        db.flush()

        logger.info(
            f"Lote preparado para envío: {lote.num_registros} registros",
            extra=log_context,
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

            # Log estructurado del error
            logger.error(
                "Error en procesamiento AEAT",
                extra={
                    **log_context,
                    "error": error_msg,
                    "estado_envio": (
                        resultado.estado_envio.value if resultado.estado_envio else None
                    ),
                },
            )

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
            "Lote procesado exitosamente",
            extra={
                **log_context,
                "estado_final": lote.estado.value,
                "mensaje_resumen": resultado.mensaje_resumen,
                "csv": resultado.csv,
            },
        )

        # PASO 6: Marcar evento como procesado
        servicio_outbox = OutboxService(db)
        servicio_outbox.marcar_procesado(evento_id)

        # COMMIT final
        db.commit()

        # Log de estadísticas (JSON estructurado para métricas)
        logger.info(
            "Estadísticas del lote",
            extra={
                **log_context,
                "total_registros": resultado.total_registros,
                "registros_correctos": resultado.registros_correctos,
                "registros_con_errores": resultado.registros_con_errores_aceptados,
                "registros_incorrectos": resultado.registros_incorrectos,
                "tiene_duplicados": resultado.tiene_duplicados,
                "num_duplicados": (
                    len(resultado.registros_duplicados)
                    if resultado.tiene_duplicados
                    else 0
                ),
                "tiempo_espera_segundos": resultado.tiempo_espera_segundos,
            },
        )

        if resultado.tiene_duplicados:
            logger.warning(
                f"Lote con {len(resultado.registros_duplicados)} registros duplicados",
                extra={
                    **log_context,
                    "duplicados": [
                        {
                            "ref_externa": d.ref_externa,
                            "id_original": d.id_duplicado,
                            "estado_original": d.estado_duplicado,
                        }
                        for d in resultado.registros_duplicados[:5]  # Primeros 5
                    ],
                },
            )

    except SQLAlchemyError as e:
        # Error de BD: rollback y reintentar
        db.rollback()
        logger.error(
            "Error de BD al procesar lote",
            extra={
                "lote_id": str(lote_id),
                "evento_id": evento_id,
                "error_type": type(e).__name__,
                "error": str(e),
            },
            exc_info=True,
        )

        # Reintentar (Celery lo hará automáticamente)
        raise self.retry(exc=e)

    except Exception as e:
        # Error inesperado: decidir si reintentar
        db.rollback()

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
            logger.warning(
                "Error no retryable en lote",
                extra={
                    "lote_id": str(lote_id),
                    "evento_id": evento_id,
                    "error": str(e),
                    "es_no_retryable": True,
                },
            )

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
                "Reintentando lote",
                extra={
                    "lote_id": str(lote_id),
                    "evento_id": evento_id,
                    "intento": self.request.retries + 1,
                    "max_intentos": self.max_retries,
                    "error": str(e),
                    "es_retryable": es_retryable,
                },
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
            logger.critical(
                "Máximo de reintentos alcanzado",
                extra={
                    "lote_id": str(lote_id),
                    "evento_id": evento_id,
                    "intentos": self.max_retries,
                    "error": str(e),
                },
            )

            lote = db.get(LoteEnvio, lote_id)
            if lote:
                lote.estado = EstadoLoteEnvio.ERROR
                db.flush()

            servicio_outbox = OutboxService(db)
            servicio_outbox.marcar_error(
                evento_id, f"Máximo de reintentos alcanzado: {str(e)[:500]}"
            )
            db.commit()

    finally:
        db.close()
        logger.debug("Sesión cerrada", extra={"lote_id": str(lote_id)})


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
