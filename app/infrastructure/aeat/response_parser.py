"""
app/infrastructure/aeat/response_parser.py

Parser de respuestas XML de AEAT.
RESPONSABILIDAD: Interpretar XML y devolver estructuras de datos simples.
NO conoce la BD, NO actualiza estados, NO hace lógica de negocio.
"""

import logging
from dataclasses import dataclass, field
from typing import Optional

from xsdata.exceptions import ParserError
from xsdata.formats.dataclass.parsers import XmlParser

from app.infrastructure.aeat.models.respuesta_suministro import (
    EstadoEnvioType,
    EstadoRegistroType,
    RespuestaRegFactuSistemaFacturacion,
)

logger = logging.getLogger(__name__)


# ============================================================================
# MODELOS DE SALIDA DEL PARSER (sin dependencias de BD)
# ============================================================================


@dataclass(frozen=True)
class ResultadoRegistroOK:
    """Registro procesado correctamente por AEAT."""

    ref_externa: str
    """Referencia externa (típicamente el ID del RegistroFacturacion)."""

    estado: EstadoRegistroType
    """Estado específico: CORRECTO o ACEPTADO_CON_ERRORES."""

    xml_linea_respuesta: Optional[str] = None
    """XML completo de la línea de respuesta de AEAT (para auditoría)."""


@dataclass(frozen=True)
class ResultadoRegistroError:
    """Registro rechazado por AEAT."""

    ref_externa: str
    """Referencia externa (típicamente el ID del RegistroFacturacion)."""

    codigo_error: Optional[int] = None
    """Código de error de AEAT."""

    descripcion_error: Optional[str] = None
    """Descripción del error de AEAT."""

    es_duplicado: bool = False
    """Indica si el rechazo fue por registro duplicado."""

    id_duplicado: Optional[str] = None
    """ID de la petición original (si es duplicado)."""

    estado_duplicado: Optional[str] = None
    """Estado del registro duplicado en AEAT: Correcta, AceptadaConErrores, Anulada."""

    codigo_error_duplicado: Optional[int] = None
    """Código de error del registro duplicado (si aplica)."""

    descripcion_error_duplicado: Optional[str] = None
    """Descripción del error del registro duplicado (si aplica)."""

    xml_linea_respuesta: Optional[str] = None
    """XML completo de la línea de respuesta de AEAT (para auditoría)."""


@dataclass(frozen=True)
class ResultadoProcesamiento:
    """
    Resultado del parseo de una respuesta AEAT.

    IMPORTANTE: Este modelo solo contiene datos parseados del XML.
    NO contiene lógica de negocio ni referencias a la BD.
    """

    exitoso: bool
    """Indica si el envío fue exitoso (CORRECTO o PARCIALMENTE_CORRECTO)."""

    tiempo_espera_segundos: Optional[int]
    """Segundos que AEAT indica esperar antes del próximo envío."""

    estado_envio: Optional[EstadoEnvioType]
    """Estado global del envío según AEAT."""

    csv: Optional[str] = None
    """Código Seguro de Verificación de AEAT."""

    registros_ok: list[ResultadoRegistroOK] = field(default_factory=list)
    """Registros procesados correctamente (CORRECTO o ACEPTADO_CON_ERRORES)."""

    registros_error: list[ResultadoRegistroError] = field(default_factory=list)
    """Registros rechazados (INCORRECTO)."""

    # Metadata
    mensaje_resumen: Optional[str] = None
    """Resumen legible del procesamiento."""

    error_parseo: Optional[str] = None
    """Error durante el parseo (si exitoso=False por error de parseo)."""

    xml_raw: Optional[str] = None
    """XML original para auditoría."""

    # ========================================================================
    # PROPERTIES DERIVADAS (solo cálculos sobre datos ya existentes)
    # ========================================================================

    @property
    def total_registros(self) -> int:
        """Total de registros procesados."""
        return len(self.registros_ok) + len(self.registros_error)

    @property
    def registros_correctos(self) -> int:
        """Registros con estado CORRECTO."""
        return sum(
            1 for r in self.registros_ok if r.estado == EstadoRegistroType.CORRECTO
        )

    @property
    def registros_con_errores_aceptados(self) -> int:
        """Registros con estado ACEPTADO_CON_ERRORES."""
        return sum(
            1
            for r in self.registros_ok
            if r.estado == EstadoRegistroType.ACEPTADO_CON_ERRORES
        )

    @property
    def registros_incorrectos(self) -> int:
        """Registros rechazados."""
        return len(self.registros_error)

    @property
    def tiene_duplicados(self) -> bool:
        """Indica si hay registros rechazados por duplicado."""
        return any(r.es_duplicado for r in self.registros_error)

    @property
    def registros_duplicados(self) -> list[ResultadoRegistroError]:
        """Lista de registros rechazados por duplicado."""
        return [r for r in self.registros_error if r.es_duplicado]


# ============================================================================
# PARSER
# ============================================================================


class AEATResponseParser:
    """
    Parser de respuestas AEAT usando xsdata.

    RESPONSABILIDAD: XML → ResultadoProcesamiento
    NO conoce: BD, estados, lógica de negocio
    """

    def __init__(self) -> None:
        self.parser: XmlParser = XmlParser()

    def parsear_respuesta(self, xml_respuesta: str) -> ResultadoProcesamiento:
        """
        Parsea XML de respuesta de AEAT.

        Args:
            xml_respuesta: XML completo de AEAT (puede incluir SOAP envelope)

        Returns:
            ResultadoProcesamiento con datos parseados

        Raises:
            Exception: Si el XML es inválido o no se puede parsear
        """
        try:
            logger.debug(f"Parseando respuesta AEAT ({len(xml_respuesta)} caracteres)")

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
                tiempo_espera_segundos=120,  # Default safe
                estado_envio=EstadoEnvioType.INCORRECTO,
                error_parseo=error_msg,
                xml_raw=xml_respuesta,
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

            for _ns_prefix, ns_uri in namespaces.items():
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
            ResultadoProcesamiento con datos estructurados
        """
        from xsdata.formats.dataclass.serializers import XmlSerializer
        from xsdata.formats.dataclass.serializers.config import SerializerConfig

        # Extraer campos básicos
        tiempo_espera_str = respuesta.tiempo_espera_envio or "120"
        tiempo_espera = int(tiempo_espera_str)

        estado_envio = respuesta.estado_envio
        csv = respuesta.csv

        # Configurar serializador para XML limpio
        config = SerializerConfig(pretty_print=True)
        serializer = XmlSerializer(config=config)

        # Clasificar registros según su estado
        registros_ok: list[ResultadoRegistroOK] = []
        registros_error: list[ResultadoRegistroError] = []

        lineas = respuesta.respuesta_linea or []

        for linea in lineas:
            ref_externa = linea.ref_externa or ""

            # Serializar la línea completa a XML
            try:
                xml_linea = serializer.render(linea)
            except Exception as e:
                logger.warning(f"No se pudo serializar línea {ref_externa}: {e}")
                xml_linea = None

            if linea.estado_registro in (
                EstadoRegistroType.CORRECTO,
                EstadoRegistroType.ACEPTADO_CON_ERRORES,
            ):
                # Registro OK (puede tener warnings pero fue aceptado)
                registros_ok.append(
                    ResultadoRegistroOK(
                        ref_externa=ref_externa,
                        estado=linea.estado_registro,
                        xml_linea_respuesta=xml_linea,
                    )
                )

            elif linea.estado_registro == EstadoRegistroType.INCORRECTO:
                # Registro rechazado
                es_duplicado = linea.registro_duplicado is not None
                id_duplicado = None
                estado_duplicado = None
                codigo_error_duplicado = None
                descripcion_error_duplicado = None

                if es_duplicado and linea.registro_duplicado:
                    dup = linea.registro_duplicado
                    id_duplicado = dup.id_peticion_registro_duplicado

                    # Estado del duplicado (Correcta, AceptadaConErrores, Anulada)
                    if dup.estado_registro_duplicado:
                        estado_duplicado = dup.estado_registro_duplicado.value

                    # Errores del duplicado (si los hay)
                    if dup.codigo_error_registro is not None:
                        codigo_error_duplicado = dup.codigo_error_registro

                    descripcion_error_duplicado = dup.descripcion_error_registro

                # Convertir código de error a string (puede ser int en el modelo xsdata)
                codigo_error = None
                if linea.codigo_error_registro is not None:
                    codigo_error = linea.codigo_error_registro

                registros_error.append(
                    ResultadoRegistroError(
                        ref_externa=ref_externa,
                        codigo_error=codigo_error,
                        descripcion_error=linea.descripcion_error_registro,
                        es_duplicado=es_duplicado,
                        id_duplicado=id_duplicado,
                        estado_duplicado=estado_duplicado,
                        codigo_error_duplicado=codigo_error_duplicado,
                        descripcion_error_duplicado=descripcion_error_duplicado,
                        xml_linea_respuesta=xml_linea,
                    )
                )

        # Determinar éxito global
        exitoso = (
            estado_envio == EstadoEnvioType.CORRECTO
            or estado_envio == EstadoEnvioType.PARCIALMENTE_CORRECTO
        )

        # Crear resultado
        resultado = ResultadoProcesamiento(
            exitoso=exitoso,
            tiempo_espera_segundos=tiempo_espera,
            estado_envio=estado_envio,
            csv=csv,
            registros_ok=registros_ok,
            registros_error=registros_error,
            xml_raw=xml_raw,
        )

        # Generar mensaje resumen
        resultado = self._agregar_resumen(resultado)

        # Log de resultados
        logger.info(resultado.mensaje_resumen)
        self._log_detalles(resultado)

        return resultado

    def _agregar_resumen(
        self, resultado: ResultadoProcesamiento
    ) -> ResultadoProcesamiento:
        """Genera un mensaje resumen del resultado."""
        estado_str = (
            resultado.estado_envio.value if resultado.estado_envio else "DESCONOCIDO"
        )

        msg = (
            f"Envío {estado_str}: "
            f"{resultado.registros_correctos}/{resultado.total_registros} correctos"
        )

        if resultado.registros_con_errores_aceptados > 0:
            msg += f", {resultado.registros_con_errores_aceptados} con warnings"

        if resultado.registros_incorrectos > 0:
            msg += f", {resultado.registros_incorrectos} rechazados"

        if resultado.tiene_duplicados:
            msg += f" ({len(resultado.registros_duplicados)} duplicados)"

        # Crear nuevo objeto con el resumen (dataclass frozen)
        return ResultadoProcesamiento(
            exitoso=resultado.exitoso,
            tiempo_espera_segundos=resultado.tiempo_espera_segundos,
            estado_envio=resultado.estado_envio,
            csv=resultado.csv,
            registros_ok=resultado.registros_ok,
            registros_error=resultado.registros_error,
            mensaje_resumen=msg,
            error_parseo=resultado.error_parseo,
            xml_raw=resultado.xml_raw,
        )

    def _log_detalles(self, resultado: ResultadoProcesamiento) -> None:
        """Log detallado de errores y duplicados."""
        for reg_error in resultado.registros_error:
            if reg_error.es_duplicado:
                logger.warning(
                    f"Registro {reg_error.ref_externa} DUPLICADO en AEAT: "
                    f"id_original={reg_error.id_duplicado}"
                )
            else:
                logger.warning(
                    f"Registro {reg_error.ref_externa} RECHAZADO: "
                    f"código={reg_error.codigo_error}, "
                    f"error={reg_error.descripcion_error}"
                )

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

            estado_match = re.search(
                r"<EstadoEnvio>"
                r"(Correcto|ParcialmenteCorrecto|Incorrecto)</EstadoEnvio>",
                xml_respuesta,
            )
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
                tiempo_espera_segundos=tiempo_espera,
                estado_envio=estado_envio,
                csv=csv,
                registros_ok=[],  # Sin detalle por registro en fallback
                registros_error=[],
                mensaje_resumen="Parseado con fallback (sin validación completa)",
                xml_raw=xml_respuesta,
            )

        except Exception as e:
            logger.error(f"Error en parseo de emergencia: {e}")
            return ResultadoProcesamiento(
                exitoso=False,
                tiempo_espera_segundos=120,
                estado_envio=EstadoEnvioType.INCORRECTO,
                error_parseo=f"No se pudo parsear respuesta: {e}",
                xml_raw=xml_respuesta,
            )


# ============================================================================
# FUNCIÓN HELPER
# ============================================================================


def parsear_respuesta_verifactu(xml_respuesta: str) -> ResultadoProcesamiento:
    """
    Función helper para parsear respuesta AEAT.

    Args:
        xml_respuesta: XML de respuesta de AEAT

    Returns:
        ResultadoProcesamiento con datos parseados (sin lógica de BD)
    """
    parser = AEATResponseParser()
    return parser.parsear_respuesta(xml_respuesta)
