"""
app/services/process_lote.py

Servicio para procesamiento completo de lotes de envío a AEAT.

Responsabilidades:
- Generar XML de envío Veri*factu
- Enviar a AEAT (POST con certificado)
- Procesar respuesta (tiempo 't', estados)
- Actualizar instalación (control de flujo)
- Actualizar estados de registros
"""

import logging
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
from app.infrastructure.aeat.response_parser import ResultadoProcesamiento

logger = logging.getLogger(__name__)

TIEMPO_ESPERA_DEFAULT: int = 60


class ProcessLoteService:
    """
    Servicio para procesamiento de lotes a AEAT.

    CRÍTICO para control de flujo:
    - Actualizar instalacion.ultimo_envio_at
    - Actualizar instalacion.ultimo_tiempo_espera
    """

    def __init__(self, db: Session):
        self.db = db

    def procesar_lote(self, lote: LoteEnvio) -> ResultadoProcesamiento:
        """
        Procesa un lote completo: XML → AEAT → Actualizar.

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
                    tiempo_espera=TIEMPO_ESPERA_DEFAULT,  # Espera antes de reintentar
                    estado_envio=EstadoEnvioType.INCORRECTO,
                    error="Lote sin registros asociados",
                )
            logger.info(f"Lote {lote.id}: {len(registros)} registros para procesar")

            # PASO 2: Generar XML de envío
            xml_envio = self._generar_xml_envio(lote, registros)

            # Guardar XML en el lote (para auditoría)
            lote.xml_enviado = xml_envio
            self.db.flush()

            logger.info(f"XML generado para lote {lote.id} ")

            # PASO 3: Enviar a AEAT
            respuesta_aeat = self._enviar_a_aeat(lote, xml_envio)

            if not respuesta_aeat.exitoso:
                # Error en envío: marcar registros como ERROR
                self._marcar_registros_error(
                    lote, respuesta_aeat.error or "Error desconocido"
                )
                return respuesta_aeat

            # PASO 4: Procesar respuesta exitosa
            self._procesar_respuesta_exitosa(lote, respuesta_aeat)

            # PASO 5: ✅ CRÍTICO - Actualizar instalación (control de flujo)
            self._actualizar_instalacion_control_flujo(
                lote, respuesta_aeat.tiempo_espera or TIEMPO_ESPERA_DEFAULT
            )

            logger.info(
                f"✅ Lote {lote.id} procesado exitosamente. "
                f"Tiempo espera AEAT: {respuesta_aeat.tiempo_espera}s"
            )

            return respuesta_aeat

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
        Envía el XML a AEAT y procesa la respuesta.

        Usa AEATClient para HTTP y AEATResponseParser para XML.
        """
        try:
            # ✅ Usar cliente AEAT de infraestructura
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
                # Error HTTP (4xx)
                return ResultadoProcesamiento(
                    exitoso=False,
                    tiempo_espera=TIEMPO_ESPERA_DEFAULT,
                    estado_envio=EstadoEnvioType.INCORRECTO,
                    # codigo_respuesta=str(respuesta_http.status_code),
                    error=respuesta_http.error,
                )
            if not respuesta_http.xml_respuesta:
                return ResultadoProcesamiento(
                    exitoso=False,
                    tiempo_espera=TIEMPO_ESPERA_DEFAULT,
                    estado_envio=EstadoEnvioType.INCORRECTO,
                    error="Respuesta HTTP vacía: no se recibió XML de AEAT",
                )
            # Parsear respuesta XML
            resultado = parsear_respuesta_verifactu(respuesta_http.xml_respuesta)

            logger.info(
                f"Respuesta AEAT para lote {lote.id}: "
                # f"código={resultado.codigo_respuesta}, "
                f"tiempo_espera={resultado.tiempo_espera}s"
            )

            return resultado

        except Exception as e:
            # Error de conexión/timeout: propagar para retry
            error_msg = f"Error al enviar a AEAT: {e}"
            logger.error(error_msg, exc_info=True)
            raise

    def _parsear_respuesta_aeat(self, xml_respuesta: str) -> ResultadoProcesamiento:
        """
        Parsea la respuesta XML de AEAT.

        Delegado a response_parser.py (ya no se usa aquí directamente).
        """
        # Este método ya no se llama, pero lo dejamos por compatibilidad
        from app.infrastructure.aeat.response_parser import parsear_respuesta_verifactu

        return parsear_respuesta_verifactu(xml_respuesta)

    def _procesar_respuesta_exitosa(
        self, lote: LoteEnvio, respuesta: ResultadoProcesamiento
    ) -> None:
        """
        Procesa una respuesta exitosa de AEAT.

        - Actualiza estado del lote
        - Actualiza tiempo de espera recibido
        - Actualiza estados de CADA registro según respuesta AEAT
        """
        from app.infrastructure.aeat.models.respuesta_suministro import (
            EstadoRegistroType,
        )

        ahora = datetime.now(timezone.utc)

        # Actualizar lote
        lote.tiempo_espera_recibido = respuesta.tiempo_espera
        lote.proximo_envio_permitido_at = ahora + timedelta(
            seconds=respuesta.tiempo_espera or TIEMPO_ESPERA_DEFAULT
        )
        lote.csv_aeat = respuesta.csv
        self.db.flush()

        # ✅ CRÍTICO: Actualizar estado de CADA registro según respuesta
        if respuesta.lineas:
            for resultado_reg in respuesta.lineas:
                # RefExterna debería ser el ID del RegistroFacturacion
                # Si no usas RefExterna, necesitas otro mecanismo de matching
                if resultado_reg.ref_externa:
                    try:
                        registro_id = int(resultado_reg.ref_externa)

                        # Determinar nuevo estado
                        if resultado_reg.estado_registro == EstadoRegistroType.CORRECTO:
                            nuevo_estado = EstadoRegistroFacturacion.CORRECTO
                        elif (
                            resultado_reg.estado_registro
                            == EstadoRegistroType.ACEPTADO_CON_ERRORES
                        ):
                            nuevo_estado = (
                                EstadoRegistroFacturacion.ACEPTADO_CON_ERRORES
                            )
                        elif (
                            resultado_reg.estado_registro
                            == EstadoRegistroType.INCORRECTO
                        ):
                            nuevo_estado = EstadoRegistroFacturacion.INCORRECTO
                        else:
                            nuevo_estado = EstadoRegistroFacturacion.ERROR_SERVIDOR_AEAT
                        # Actualizar registro
                        self.db.execute(
                            update(RegistroFacturacion)
                            .where(RegistroFacturacion.id == registro_id)
                            .values(estado=nuevo_estado)
                        )

                        if (
                            nuevo_estado
                            == EstadoRegistroFacturacion.ERROR_SERVIDOR_AEAT
                        ):
                            logger.warning(
                                f"Registro {registro_id} marcado como ERROR: "
                                f"{resultado_reg.descripcion_error_registro}"
                            )
                    except (ValueError, TypeError) as e:
                        logger.error(
                            f"Error en RefExterna '{resultado_reg.ref_externa}': {e}"
                        )
        # else:
        #     # Fallback: sin detalle por registro, marcar todos según estado global
        #     logger.warning(
        #         f"Respuesta AEAT sin detalle por registro. "
        #         f"Marca todos con ENVIADO por estado global: {respuesta.estado_envio}"
        #     )
        #     self.db.execute(
        #         update(RegistroFacturacion)
        #         .where(RegistroFacturacion.lote_envio_id == lote.id)
        #         .values(estado=EstadoRegistroFacturacion.ENVIADO)
        #     )

        # logger.info(
        #     f"Lote {lote.id}: "
        #     f"{respuesta.registros_correctos}/{respuesta.total_registros} "
        #     f"registros correctos, {respuesta.registros_incorrectos} rechazados"
        # )

    def _marcar_registros_error(self, lote: LoteEnvio, error: str) -> None:
        """Marca los registros del lote como ERROR."""
        self.db.execute(
            update(RegistroFacturacion)
            .where(RegistroFacturacion.lote_envio_id == lote.id)
            .values(estado=EstadoRegistroFacturacion.ERROR_SERVIDOR_AEAT)
        )

        logger.warning(f"Registros del lote {lote.id} marcados como ERROR: {error}")

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

    def _get_url_aeat(self, instalacion: InstalacionSIF) -> str | None:
        """DEPRECATED: Movido a AEATClient.Mantener por compatibilidad."""
        from app.infrastructure.aeat.client import AEATClient

        return AEATClient.URLS.get("pruebas")

    def _get_certificado_path(self, instalacion: InstalacionSIF) -> tuple[str, str]:
        """DEPRECATED: Movido a AEATClient.        Mantener por compatibilidad."""
        return ("/path/to/cert.pem", "/path/to/key.pem")


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
