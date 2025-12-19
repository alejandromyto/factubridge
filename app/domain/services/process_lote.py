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
        logger.info(
            "Procesando lote",
            extra={"lote_id": str(lote.id)},
        )

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

            logger.info(
                "Registros obtenidos para procesamiento",
                extra={
                    "lote_id": str(lote.id),
                    "num_registros": len(registros),
                },
            )

            # PASO 2: Generar XML de envío
            xml_envio = self._generar_xml_envio(lote, registros)

            # Guardar XML en el lote (para auditoría)
            lote.xml_enviado = xml_envio
            self.db.flush()

            logger.info(
                "XML de envío generado",
                extra={"lote_id": str(lote.id)},
            )

            # PASO 3: Enviar a AEAT y parsear respuesta
            resultado = self._enviar_a_aeat(lote, xml_envio)

            if not resultado.exitoso:
                # Error en envío o parseo: marcar registros como ERROR
                error = resultado.error_parseo or "Error desconocido"
                self._marcar_todos_registros_error(lote, error)
                return resultado

            # PASO 4: Aplicar resultados a la BD
            self._aplicar_resultados_a_bd(lote, resultado)

            # PASO 5: CRÍTICO - Actualizar instalación (control de flujo)
            self._actualizar_instalacion_control_flujo(
                lote, resultado.tiempo_espera_segundos or TIEMPO_ESPERA_DEFAULT
            )

            logger.info(
                "Lote procesado exitosamente",
                extra={
                    "lote_id": str(lote.id),
                    "tiempo_espera_segundos": resultado.tiempo_espera_segundos,
                },
            )

            return resultado

        except Exception as e:
            logger.error(
                "Error procesando lote",
                extra={
                    "lote_id": str(lote.id),
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )
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

            logger.info(
                "Enviando lote a AEAT",
                extra={"lote_id": str(lote.id)},
            )

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

            # Parsear respuesta XML (el parser hace TODA la interpretación)
            resultado = parsear_respuesta_verifactu(respuesta_http.xml_respuesta)

            logger.info(
                "Respuesta AEAT recibida y parseada",
                extra={
                    "lote_id": str(lote.id),
                    "tiempo_espera_segundos": resultado.tiempo_espera_segundos,
                    "estado_envio": (
                        resultado.estado_envio.value if resultado.estado_envio else None
                    ),
                },
            )

            return resultado

        except Exception as e:
            # Error de conexión/timeout: propagar para retry
            logger.error(
                "Error al enviar lote a AEAT",
                extra={
                    "lote_id": str(lote.id),
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )
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

        # Aplicar resultados a registros OK
        for reg_ok in resultado.registros_ok:
            self._aplicar_registro_ok(reg_ok)

        # Aplicar resultados a registros ERROR
        for reg_error in resultado.registros_error:
            self._aplicar_registro_error(reg_error)

        logger.info(
            "Resultados aplicados a base de datos",
            extra={
                "lote_id": str(lote.id),
                "registros_correctos": resultado.registros_correctos,
                "total_registros": resultado.total_registros,
                "registros_incorrectos": resultado.registros_incorrectos,
            },
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
                logger.warning(
                    "Estado inesperado en registro OK",
                    extra={
                        "registro_id": str(registro_id),
                        "estado": reg_ok.estado.value if reg_ok.estado else None,
                    },
                )
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

            logger.debug(
                "Registro actualizado a estado OK",
                extra={
                    "registro_id": str(registro_id),
                    "nuevo_estado": nuevo_estado.value,
                },
            )

        except (ValueError, TypeError) as e:
            logger.error(
                "Error procesando registro OK",
                extra={
                    "ref_externa": reg_ok.ref_externa,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )

    def _aplicar_registro_error(self, reg_error: ResultadoRegistroError) -> None:
        """
        Aplica resultado ERROR a un registro.

        LÓGICA DE NEGOCIO: Marcar como INCORRECTO y guardar detalles del error.
        Si es duplicado, guardar también información del registro original.
        """
        try:
            registro_id = uuid.UUID(reg_error.ref_externa)

            # Siempre INCORRECTO (fue rechazado por AEAT)
            nuevo_estado = EstadoRegistroFacturacion.INCORRECTO

            # Serializar respuesta XML (si está disponible)
            xml_respuesta_aeat = None
            if reg_error.xml_linea_respuesta:
                xml_respuesta_aeat = reg_error.xml_linea_respuesta

            # Preparar datos a actualizar
            valores = {
                "estado": nuevo_estado,
                "xml_respuesta_aeat": xml_respuesta_aeat,
                "aeat_codigo_error": (
                    int(reg_error.codigo_error) if reg_error.codigo_error else None
                ),
                "aeat_descripcion_error": reg_error.descripcion_error,
            }

            # Si es duplicado, guardar información del registro original
            if reg_error.es_duplicado:
                from app.domain.models.models import EstadoDuplicadoAEAT

                valores["aeat_duplicado_id_peticion"] = reg_error.id_duplicado

                # Mapear estado del duplicado al enum
                if reg_error.estado_duplicado:
                    estado_map = {
                        "Correcta": EstadoDuplicadoAEAT.CORRECTA,
                        "AceptadaConErrores": EstadoDuplicadoAEAT.ACEPTADA_CON_ERRORES,
                        "Anulada": EstadoDuplicadoAEAT.ANULADA,
                    }
                    valores["aeat_duplicado_estado"] = estado_map.get(
                        reg_error.estado_duplicado
                    )

                # Guardar errores del duplicado (si los hay)
                if reg_error.codigo_error_duplicado:
                    valores["aeat_duplicado_codigo_error"] = int(
                        reg_error.codigo_error_duplicado
                    )

                valores["aeat_duplicado_descripcion"] = (
                    reg_error.descripcion_error_duplicado
                )

                logger.warning(
                    "Registro rechazado por duplicado",
                    extra={
                        "registro_id": str(registro_id),
                        "id_original": reg_error.id_duplicado,
                        "estado_original": reg_error.estado_duplicado,
                    },
                )
            else:
                logger.warning(
                    "Registro rechazado por AEAT",
                    extra={
                        "registro_id": str(registro_id),
                        "codigo_error": reg_error.codigo_error,
                        "descripcion_error": reg_error.descripcion_error,
                    },
                )

            # Actualizar registro
            self.db.execute(
                update(RegistroFacturacion)
                .where(RegistroFacturacion.id == registro_id)
                .values(**valores)
            )

        except (ValueError, TypeError) as e:
            logger.error(
                "Error procesando registro ERROR",
                extra={
                    "ref_externa": reg_error.ref_externa,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
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
            "Todos los registros del lote marcados como ERROR",
            extra={
                "lote_id": str(lote.id),
                "error": error,
            },
        )

    def _actualizar_instalacion_control_flujo(
        self, lote: LoteEnvio, tiempo_espera: int
    ) -> None:
        """
        CRÍTICO: Actualiza instalación para control de flujo.

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
            "Instalación actualizada con control de flujo",
            extra={
                "instalacion_id": lote.instalacion_sif_id,
                "ultimo_envio_at": ahora.isoformat(),
                "ultimo_tiempo_espera": tiempo_espera,
            },
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
