"""
app/infrastructure/aeat/response_parser.py

Parser de respuestas XML de AEAT usando modelos Pydantic generados del XSD.
Sin DTOs intermedios: usa directamente los modelos xsdata.
"""

import logging
from dataclasses import dataclass, field
from typing import List, Optional

from xsdata.exceptions import ParserError
from xsdata.formats.dataclass.parsers import XmlParser

from app.infrastructure.aeat.models.respuesta_suministro import (
    EstadoEnvioType,
    EstadoRegistroType,
    RespuestaExpedidaType,
    RespuestaRegFactuSistemaFacturacion,
)

logger = logging.getLogger(__name__)


@dataclass
class ResultadoProcesamiento:
    """
    Resultado del procesamiento de un lote completo.

    Usa directamente los modelos Pydantic de xsdata (sin DTOs intermedios).
    """

    exitoso: bool
    tiempo_espera: int  # Segundos para próximo envío (TiempoEsperaEnvio)
    estado_envio: Optional[EstadoEnvioType]
    csv: Optional[str] = None  # Código Seguro de Verificación

    # ✅ Lista de respuestas por registro (modelos Pydantic directos)
    lineas: List[RespuestaExpedidaType] = field(default_factory=list)

    # Metadata
    codigo_respuesta: Optional[str] = None  # Para errores HTTP
    mensaje: Optional[str] = None
    error: Optional[str] = None
    respuesta_raw: Optional[str] = None

    # ========================================================================
    # PROPERTIES DERIVADAS (sin duplicar datos)
    # ========================================================================

    @property
    def total_registros(self) -> int:
        """Total de registros procesados."""
        return len(self.lineas)

    @property
    def registros_correctos(self) -> int:
        """Registros con estado CORRECTO."""
        return sum(
            1
            for linea in self.lineas
            if linea.estado_registro == EstadoRegistroType.CORRECTO
        )

    @property
    def registros_con_errores(self) -> int:
        """Registros con estado ACEPTADO_CON_ERRORES."""
        return sum(
            1
            for linea in self.lineas
            if linea.estado_registro == EstadoRegistroType.ACEPTADO_CON_ERRORES
        )

    @property
    def registros_incorrectos(self) -> int:
        """Registros con estado INCORRECTO."""
        return sum(
            1
            for linea in self.lineas
            if linea.estado_registro == EstadoRegistroType.INCORRECTO
        )

    @property
    def tiene_duplicados(self) -> bool:
        """Indica si hay algún registro rechazado por duplicado."""
        return any(linea.registro_duplicado is not None for linea in self.lineas)

    @property
    def registros_duplicados(self) -> List[RespuestaExpedidaType]:
        """Lista de registros rechazados por duplicado."""
        return [linea for linea in self.lineas if linea.registro_duplicado is not None]

    def resumen(self) -> str:
        """Genera resumen legible del procesamiento."""
        msg = (
            f"Envío {self.estado_envio.value if self.estado_envio else None}: "
            f"{self.registros_correctos}/{self.total_registros} correctos"
        )

        if self.registros_con_errores > 0:
            msg += f", {self.registros_con_errores} con errores"

        if self.registros_incorrectos > 0:
            msg += f", {self.registros_incorrectos} incorrectos"

        if self.tiene_duplicados:
            msg += f" ({len(self.registros_duplicados)} duplicados)"

        return msg


class AEATResponseParser:
    """
    Parser de respuestas AEAT usando xsdata.

    Convierte XML → Modelo Pydantic → ResultadoProcesamiento (sin DTOs intermedios)
    """

    def __init__(self) -> None:
        self.parser: XmlParser = XmlParser()

    def parsear_respuesta(self, xml_respuesta: str) -> ResultadoProcesamiento:
        """
        Parsea XML de respuesta de AEAT.

        Args:
            xml_respuesta: XML completo de AEAT (puede incluir SOAP envelope)

        Returns:
            ResultadoProcesamiento con modelos Pydantic directos

        Raises:
            Exception: Si el XML es inválido o no se puede parsear
        """
        try:
            logger.debug(f"Parseando respuesta AEAT ({len(xml_respuesta)} bytes)")

            # PASO 1: Extraer XML limpio (quitar SOAP envelope si existe)
            xml_limpio = self._extraer_body_xml(xml_respuesta)

            # PASO 2: Parsear con xsdata
            try:
                respuesta: RespuestaRegFactuSistemaFacturacion = (
                    self.parser.from_string(
                        xml_limpio, RespuestaRegFactuSistemaFacturacion
                    )
                )
            except ParserError as e:
                logger.error(f"Error parseando XML con xsdata: {e}")
                # Fallback: parseo manual
                return self._parsear_sin_validacion(xml_respuesta)

            # PASO 3: Convertir a ResultadoProcesamiento
            return self._convertir_a_resultado(respuesta, xml_respuesta)

        except Exception as e:
            error_msg = f"Error inesperado parseando respuesta: {e}"
            logger.error(error_msg, exc_info=True)
            return ResultadoProcesamiento(
                exitoso=False,
                tiempo_espera=120,  # Default safe
                estado_envio=EstadoEnvioType.INCORRECTO,
                error=error_msg,
                respuesta_raw=xml_respuesta,
            )

    def _extraer_body_xml(self, xml_respuesta: str) -> str:
        """
        Extrae el body del SOAP envelope si existe.

        Si no es SOAP, devuelve el XML tal cual.
        """
        import xml.etree.ElementTree as ET

        try:
            root = ET.fromstring(xml_respuesta)

            # Buscar SOAP Body
            namespaces = {
                "soapenv": "http://schemas.xmlsoap.org/soap/envelope/",
                "soap": "http://www.w3.org/2003/05/soap-envelope",
            }

            for ns_uri in namespaces:
                body = root.find(f".//{{{ns_uri}}}Body")
                if body is not None:
                    # Obtener primer hijo del Body
                    for child in body:
                        return ET.tostring(child, encoding="unicode")

            # No es SOAP, devolver tal cual
            return xml_respuesta

        except ET.ParseError:
            # XML inválido, devolver tal cual y dejar que xsdata falle
            return xml_respuesta

    def _convertir_a_resultado(
        self, respuesta: RespuestaRegFactuSistemaFacturacion, xml_raw: str
    ) -> ResultadoProcesamiento:
        """
        Convierte modelo xsdata a ResultadoProcesamiento.

        Args:
            respuesta: Modelo Pydantic parseado por xsdata
            xml_raw: XML original para auditoría

        Returns:
            ResultadoProcesamiento con modelos Pydantic directos
        """
        # Extraer campos de la respuesta base
        tiempo_espera_str = respuesta.tiempo_espera_envio or "120"
        tiempo_espera = int(tiempo_espera_str)

        estado_envio = respuesta.estado_envio
        csv = respuesta.csv

        # ✅ Usar directamente las líneas (RespuestaExpedidaType)
        lineas = respuesta.respuesta_linea or []

        # Determinar éxito global
        exitoso = (
            estado_envio == EstadoEnvioType.CORRECTO
            or estado_envio == EstadoEnvioType.PARCIALMENTE_CORRECTO
        )

        # Crear resultado
        resultado = ResultadoProcesamiento(
            exitoso=exitoso,
            tiempo_espera=tiempo_espera,
            estado_envio=estado_envio,
            csv=csv,
            lineas=lineas,  # ✅ Modelos Pydantic directos, sin mapeo
            respuesta_raw=xml_raw,
        )

        # Generar mensaje resumen
        resultado.mensaje = resultado.resumen()

        # Log de resultados
        logger.info(resultado.mensaje)

        # Log detallado de errores
        for linea in lineas:
            if linea.estado_registro == EstadoRegistroType.INCORRECTO:
                logger.warning(
                    f"Registro {linea.ref_externa} RECHAZADO: "
                    f"código={linea.codigo_error_registro}, "
                    f"error={linea.descripcion_error_registro}"
                )

            # Log de duplicados
            if linea.registro_duplicado:
                dup = linea.registro_duplicado
                logger.warning(
                    f"Registro {linea.ref_externa} DUPLICADO en AEAT: "
                    f"id_original={dup.id_peticion_registro_duplicado}, "
                    f"estado_original={dup.estado_registro_duplicado}"
                )

        return resultado

    def _parsear_sin_validacion(self, xml_respuesta: str) -> ResultadoProcesamiento:
        """
        Parseo de emergencia sin xsdata.

        Extrae campos críticos directamente del XML con regex.
        Usar como fallback si la validación falla.
        """
        logger.warning("⚠️ Usando parseo sin validación (fallback)")

        try:
            import re

            # Extraer campos básicos con regex
            tiempo_match = re.search(
                r"<TiempoEsperaEnvio>(\d+)</TiempoEsperaEnvio>", xml_respuesta
            )
            tiempo_espera = int(tiempo_match.group(1)) if tiempo_match else 120

            csv_match = re.search(r"<CSV>([^<]+)</CSV>", xml_respuesta)
            csv = csv_match.group(1) if csv_match else None
            ESTADO_REGEX = (
                r"<EstadoEnvio>"
                r"(Correcto|ParcialmenteCorrecto|Incorrecto)"
                r"</EstadoEnvio>"
            )
            estado_match = re.search(ESTADO_REGEX, xml_respuesta)
            estado_str = estado_match.group(1) if estado_match else "Incorrecto"

            # Mapear a enum
            estado_map = {
                "Correcto": EstadoEnvioType.CORRECTO,
                "ParcialmenteCorrecto": EstadoEnvioType.PARCIALMENTE_CORRECTO,
                "Incorrecto": EstadoEnvioType.INCORRECTO,
            }
            estado_envio = estado_map.get(estado_str, EstadoEnvioType.INCORRECTO)

            exitoso = estado_envio != EstadoEnvioType.INCORRECTO

            return ResultadoProcesamiento(
                exitoso=exitoso,
                tiempo_espera=tiempo_espera,
                estado_envio=estado_envio,
                csv=csv,
                lineas=[],  # Sin detalle por registro en fallback
                mensaje="Parseado con fallback (sin validación completa)",
                respuesta_raw=xml_respuesta,
            )

        except Exception as e:
            logger.error(f"Error en parseo de emergencia: {e}")
            return ResultadoProcesamiento(
                exitoso=False,
                tiempo_espera=120,
                estado_envio=EstadoEnvioType.INCORRECTO,
                error=f"No se pudo parsear respuesta: {e}",
                respuesta_raw=xml_respuesta,
            )


def parsear_respuesta_verifactu(xml_respuesta: str) -> ResultadoProcesamiento:
    """
    Función helper para parsear respuesta AEAT.

    Args:
        xml_respuesta: XML de respuesta de AEAT

    Returns:
        ResultadoProcesamiento con modelos Pydantic directos
    """
    parser = AEATResponseParser()
    return parser.parsear_respuesta(xml_respuesta)
