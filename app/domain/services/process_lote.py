"""
app/services/process_lote.py

Servicio para procesamiento completo de lotes de envío a AEAT.

Responsabilidades:
- Generar XML de envío Veri*factu
- Enviar a AEAT (POST con certificado)
- Procesar respuesta (aplicar lógica de negocio)
- Actualizar instalación (control de flujo)
- Actualizar estados de registros
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.domain.models.models import (
    EstadoRegistroFacturacion,
    InstalacionSIF,
    LoteEnvio,
    RegistroFacturacion,
)
from app.infrastructure.aeat.models.respuesta_suministro import EstadoEnvioType
from app.infrastructure.aeat.response_parser import (
    ResultadoProcesamiento,
    ResultadoRegistroError,
    ResultadoRegistroOK,
)

logger = logging.getLogger(__name__)

TIEMPO_ESPERA_DEFAULT: int = 60


class ProcessLoteService:
    """
    Servicio para procesamiento de lotes a AEAT.

    RESPONSABILIDAD: Lógica de negocio y persistencia
    - Generar XML
    - Enviar a AEAT
    - Aplicar resultados a la BD
    - Actualizar control de flujo

    NO interpreta XML (eso lo hace AEATResponseParser)
    """

    def __init__(self, db: Session):
        self.db = db

    def procesar_lote(self, lote: LoteEnvio) -> ResultadoProcesamiento:
        """
        Procesa un lote completo: XML → AEAT → Actualizar BD.

        Args:
            lote: Lote a procesar (debe tener registros asociados)

        Returns:
            ResultadoProcesamiento con resultado del envío

        Raises:
            Exception: Errores críticos que deben reintentarse

        IMPORTANTE:
        - NO hace commit (el caller debe hacerlo)
        - Actualiza estado del lote y registros
        - CRÍTICO: Actualiza instalacion.ultimo_envio_at y ultimo_tiempo_espera
        """
        logger.info(f"=== Procesando lote {lote.id} ===")

        try:
            # PASO 1: Obtener registros del lote
            registros = self._obtener_registros_lote(lote)

            if not registros:
                return ResultadoProcesamiento(
                    exitoso=False,
                    tiempo_espera_segundos=TIEMPO_ESPERA_DEFAULT,
                    estado_envio=EstadoEnvioType.INCORRECTO,
                    error_parseo="Lote sin registros asociados",
                )

            logger.info(f"Lote {lote.id}: {len(registros)} registros para procesar")

            # PASO 2: Generar XML de envío
            xml_envio = self._generar_xml_envio(lote, registros)

            # Guardar XML en el lote (para auditoría)
            lote.xml_enviado = xml_envio
            self.db.flush()

            logger.info(f"XML generado para lote {lote.id}")

            # PASO 3: Enviar a AEAT y parsear respuesta
            resultado = self._enviar_a_aeat(lote, xml_envio)

            if not resultado.exitoso:
                # Error en envío o parseo: marcar registros como ERROR
                error = resultado.error_parseo or "Error desconocido"
                self._marcar_todos_registros_error(lote, error)
                return resultado

            # PASO 4: Aplicar resultados a la BD
            self._aplicar_resultados_a_bd(lote, resultado)

            # PASO 5: ✅ CRÍTICO - Actualizar instalación (control de flujo)
            self._actualizar_instalacion_control_flujo(
                lote, resultado.tiempo_espera_segundos or TIEMPO_ESPERA_DEFAULT
            )

            logger.info(
                f"✅ Lote {lote.id} procesado exitosamente. "
                f"Tiempo espera AEAT: {resultado.tiempo_espera_segundos}s"
            )

            return resultado

        except Exception as e:
            logger.error(f"❌ Error procesando lote {lote.id}: {e}", exc_info=True)
            # Propagar para que Celery reintente
            raise

    def _obtener_registros_lote(self, lote: LoteEnvio) -> list[RegistroFacturacion]:
        """Obtiene los registros asociados al lote."""
        registros = (
            self.db.execute(
                select(RegistroFacturacion)
                .where(RegistroFacturacion.lote_envio_id == lote.id)
                .order_by(RegistroFacturacion.created_at.asc())
            )
            .scalars()
            .all()
        )
        return list(registros)

    def _generar_xml_envio(
        self, lote: LoteEnvio, registros: list[RegistroFacturacion]
    ) -> str:
        """Genera el XML de envío según especificación Veri*factu."""
        from app.infrastructure.aeat.xml.builder_lote import (
            construir_xml_lote_desde_entidades,
        )

        obligado = lote.instalacion_sif.obligado
        xml = construir_xml_lote_desde_entidades(
            registros=registros,
            emisor_nif=obligado.nif,
            emisor_nombre=obligado.nombre_razon_social,
        )
        return xml

    def _enviar_a_aeat(self, lote: LoteEnvio, xml_envio: str) -> ResultadoProcesamiento:
        """
        Envía el XML a AEAT y devuelve el resultado parseado.

        Usa AEATClient para HTTP y AEATResponseParser para parsear.
        """
        try:
            from app.infrastructure.aeat.client import AEATClient
            from app.infrastructure.aeat.response_parser import (
                parsear_respuesta_verifactu,
            )

            instalacion = lote.instalacion_sif

            # Crear cliente
            client = AEATClient(instalacion)

            logger.info(f"Enviando lote {lote.id} a AEAT")

            # Enviar XML
            respuesta_http = client.enviar_xml(xml_envio)

            if not respuesta_http.exitoso:
                # Error HTTP (4xx, 5xx)
                return ResultadoProcesamiento(
                    exitoso=False,
                    tiempo_espera_segundos=TIEMPO_ESPERA_DEFAULT,
                    estado_envio=EstadoEnvioType.INCORRECTO,
                    error_parseo=respuesta_http.error,
                )

            if not respuesta_http.xml_respuesta:
                return ResultadoProcesamiento(
                    exitoso=False,
                    tiempo_espera_segundos=TIEMPO_ESPERA_DEFAULT,
                    estado_envio=EstadoEnvioType.INCORRECTO,
                    error_parseo="Respuesta HTTP vacía: no se recibió XML de AEAT",
                )

            # ✅ Parsear respuesta XML (el parser hace TODA la interpretación)
            resultado = parsear_respuesta_verifactu(respuesta_http.xml_respuesta)

            logger.info(
                f"Respuesta AEAT para lote {lote.id}: "
                f"tiempo_espera={resultado.tiempo_espera_segundos}s, "
                f"estado={resultado.estado_envio}"
            )

            return resultado

        except Exception as e:
            # Error de conexión/timeout: propagar para retry
            error_msg = f"Error al enviar a AEAT: {e}"
            logger.error(error_msg, exc_info=True)
            raise

    def _aplicar_resultados_a_bd(
        self, lote: LoteEnvio, resultado: ResultadoProcesamiento
    ) -> None:
        """
        Aplica los resultados del parseo a la base de datos.

        RESPONSABILIDAD: Lógica de negocio
        - Actualizar estado del lote
        - Actualizar estados de registros según resultado
        - Guardar metadata (CSV, tiempo de espera)
        """
        ahora = datetime.now(timezone.utc)

        # Actualizar lote
        lote.tiempo_espera_recibido = resultado.tiempo_espera_segundos
        lote.proximo_envio_permitido_at = ahora + timedelta(
            seconds=resultado.tiempo_espera_segundos or TIEMPO_ESPERA_DEFAULT
        )
        lote.csv_aeat = resultado.csv
        self.db.flush()

        # ✅ Aplicar resultados a registros OK
        for reg_ok in resultado.registros_ok:
            self._aplicar_registro_ok(reg_ok)

        # ✅ Aplicar resultados a registros ERROR
        for reg_error in resultado.registros_error:
            self._aplicar_registro_error(reg_error)

        logger.info(
            f"Lote {lote.id}: "
            f"{resultado.registros_correctos}/{resultado.total_registros} correctos, "
            f"{resultado.registros_incorrectos} rechazados"
        )

    def _aplicar_registro_ok(self, reg_ok: ResultadoRegistroOK) -> None:
        """
        Aplica resultado OK a un registro.

        LÓGICA DE NEGOCIO: Define qué estado asignar según la respuesta.
        """
        from app.infrastructure.aeat.models.respuesta_suministro import (
            EstadoRegistroType,
        )

        try:
            registro_id = uuid.UUID(reg_ok.ref_externa)

            # Determinar nuevo estado según tipo
            if reg_ok.estado == EstadoRegistroType.CORRECTO:
                nuevo_estado = EstadoRegistroFacturacion.CORRECTO
            elif reg_ok.estado == EstadoRegistroType.ACEPTADO_CON_ERRORES:
                nuevo_estado = EstadoRegistroFacturacion.ACEPTADO_CON_ERRORES
            else:
                # No debería pasar (el parser ya filtró)
                logger.warning(f"Estado inesperado en registro OK: {reg_ok.estado}")
                nuevo_estado = EstadoRegistroFacturacion.CORRECTO

            # Serializar respuesta XML (si está disponible)
            xml_respuesta_aeat = None
            if reg_ok.xml_linea_respuesta:
                xml_respuesta_aeat = reg_ok.xml_linea_respuesta

            # Actualizar registro
            self.db.execute(
                update(RegistroFacturacion)
                .where(RegistroFacturacion.id == registro_id)
                .values(estado=nuevo_estado, xml_respuesta_aeat=xml_respuesta_aeat)
            )

            logger.debug(f"Registro {registro_id} → {nuevo_estado.value}")

        except (ValueError, TypeError) as e:
            logger.error(f"Error procesando registro OK '{reg_ok.ref_externa}': {e}")

    def _aplicar_registro_error(self, reg_error: ResultadoRegistroError) -> None:
        """
        Aplica resultado ERROR a un registro.

        LÓGICA DE NEGOCIO: Marcar como INCORRECTO y loguear detalles.
        """
        try:
            registro_id = uuid.UUID(reg_error.ref_externa)

            # Siempre INCORRECTO (fue rechazado por AEAT)
            nuevo_estado = EstadoRegistroFacturacion.INCORRECTO

            # Serializar respuesta XML (si está disponible)
            xml_respuesta_aeat = None
            if reg_error.xml_linea_respuesta:
                xml_respuesta_aeat = reg_error.xml_linea_respuesta

            # Actualizar registro
            self.db.execute(
                update(RegistroFacturacion)
                .where(RegistroFacturacion.id == registro_id)
                .values(estado=nuevo_estado, xml_respuesta_aeat=xml_respuesta_aeat)
            )

            # Log detallado
            if reg_error.es_duplicado:
                logger.warning(
                    f"Registro {registro_id} RECHAZADO por DUPLICADO: "
                    f"id_original={reg_error.id_duplicado}"
                )
            else:
                logger.warning(
                    f"Registro {registro_id} RECHAZADO: "
                    f"código={reg_error.codigo_error}, "
                    f"error={reg_error.descripcion_error}"
                )

        except (ValueError, TypeError) as e:
            logger.error(
                f"Error procesando registro ERROR '{reg_error.ref_externa}': {e}"
            )

    def _marcar_todos_registros_error(self, lote: LoteEnvio, error: str) -> None:
        """
        Marca todos los registros del lote como ERROR.

        Usar cuando falla el envío completo (antes de tener respuesta de AEAT).
        """
        self.db.execute(
            update(RegistroFacturacion)
            .where(RegistroFacturacion.lote_envio_id == lote.id)
            .values(estado=EstadoRegistroFacturacion.ERROR_SERVIDOR_AEAT)
        )

        logger.warning(
            f"Todos los registros del lote {lote.id} marcados como ERROR: {error}"
        )

    def _actualizar_instalacion_control_flujo(
        self, lote: LoteEnvio, tiempo_espera: int
    ) -> None:
        """
        ✅ CRÍTICO: Actualiza instalación para control de flujo.

        Estos campos controlan el próximo envío:
        - ultimo_envio_at: timestamp del envío
        - ultimo_tiempo_espera: tiempo 't' recibido de AEAT

        El scheduler usa estos valores para decidir cuándo enviar de nuevo.
        """
        ahora = datetime.now(timezone.utc)

        self.db.execute(
            update(InstalacionSIF)
            .where(InstalacionSIF.id == lote.instalacion_sif_id)
            .values(
                ultimo_envio_at=ahora,
                ultimo_tiempo_espera=tiempo_espera,
            )
        )

        logger.info(
            f"✅ Instalación {lote.instalacion_sif_id} actualizada: "
            f"ultimo_envio_at={ahora.isoformat()}, "
            f"ultimo_tiempo_espera={tiempo_espera}s"
        )


def procesar_lote(lote: LoteEnvio, db: Session) -> ResultadoProcesamiento:
    """
    Función helper para procesar un lote.

    Args:
        lote: Lote a procesar
        db: Sesión de BD (NO hace commit)

    Returns:
        ResultadoProcesamiento
    """
    servicio = ProcessLoteService(db)
    return servicio.procesar_lote(lote)
