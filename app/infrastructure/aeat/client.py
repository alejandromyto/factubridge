"""
app/infrastructure/aeat/client.py

Cliente HTTP para comunicación con AEAT Veri*factu.
"""

import logging
from dataclasses import dataclass
from typing import Optional, Tuple

import requests
from requests.exceptions import RequestException, Timeout

from app.domain.models.models import InstalacionSIF

logger = logging.getLogger(__name__)


@dataclass
class RespuestaAeatHTTP:
    """Respuesta HTTP de AEAT (antes de parsear XML)."""

    exitoso: bool
    status_code: int
    xml_respuesta: Optional[str] = None
    error: Optional[str] = None


class AEATClient:
    """
    Cliente HTTP para envío a AEAT.

    Responsabilidades:
    - Configurar URLs según entorno
    - Gestionar certificados
    - Hacer POST con timeouts
    - Manejar errores HTTP
    """

    # URLs oficiales AEAT
    URLS = {
        "produccion": (
            "https://www2.agenciatributaria.gob.es/static_files/common/"
            "internet/dep/aplicaciones/es/aeat/verifactu/ws/SuministroInformacion.svc"
        ),
        "pruebas": "https://prewww1.aeat.es/wlpl/TIKE-CONT/ws/SuministroInformacion",
    }

    def __init__(self, instalacion: InstalacionSIF):
        self.instalacion = instalacion
        self.url = self._get_url()
        self.cert = self._get_certificado()

    def enviar_xml(self, xml_envio: str) -> RespuestaAeatHTTP:
        """
        Envía XML a AEAT y retorna respuesta HTTP.

        Args:
            xml_envio: XML del lote a enviar

        Returns:
            RespuestaAeatHTTP con status y contenido

        Raises:
            RequestException: Errores de red/timeout (retryables)
        """
        try:
            data = xml_envio.encode("utf-8")
            logger.info(
                f"Enviando XML ({len(data)} bytes) a AEAT"
                f" (instalación {self.instalacion.id}): {self.url}"
            )
            response = requests.post(
                self.url,
                data=data,
                headers={
                    "Content-Type": "application/xml; charset=utf-8",
                    "Accept": "application/xml",
                    "SOAPAction": "SuministroLR",  # Según especificación AEAT
                },
                cert=self.cert,
                timeout=60,  # 60 segundos máximo
                verify=True,  # Verificar SSL de AEAT
            )

            # Log de respuesta
            logger.info(
                f"Respuesta AEAT: HTTP {response.status_code} "
                f"({len(response.text)} bytes)"
            )

            # Verificar código HTTP
            if response.status_code != 200:
                error_msg = f"HTTP {response.status_code}: {response.text[:500]}"

                # 4xx = error de negocio (NO reintentar)
                if 400 <= response.status_code < 500:
                    return RespuestaAeatHTTP(
                        exitoso=False, status_code=response.status_code, error=error_msg
                    )

                # 5xx = error de servidor (reintentar)
                logger.error(f"Error 5xx de AEAT: {error_msg}")
                raise RequestException(error_msg)

            # Respuesta exitosa
            return RespuestaAeatHTTP(
                exitoso=True, status_code=200, xml_respuesta=response.text
            )

        except Timeout as e:
            error_msg = f"Timeout al enviar a AEAT: {e}"
            logger.error(error_msg)
            raise RequestException(error_msg) from e

        except RequestException as e:
            error_msg = f"Error de conexión con AEAT: {e}"
            logger.error(error_msg)
            raise

        except Exception as e:
            error_msg = f"Error inesperado al enviar a AEAT: {e}"
            logger.error(error_msg, exc_info=True)
            raise RequestException(error_msg) from e

    def _get_url(self) -> str:
        """Obtiene URL según entorno de la instalación."""
        # TODO: Añadir campo 'entorno' a InstalacionSIF
        # entorno = self.instalacion.entorno or "pruebas"
        entorno = "pruebas"  # Por defecto pruebas

        url = self.URLS.get(entorno)
        if not url:
            raise ValueError(f"Entorno desconocido: {entorno}")

        return url

    def _get_certificado(self) -> Tuple[str, str]:
        """
        Obtiene certificado del obligado.

        TODO: Implementar gestión de certificados
        - Opción 1: Sistema de archivos (/certs/{instalacion_id}/)
        - Opción 2: AWS Secrets Manager
        - Opción 3: Azure Key Vault
        - Opción 4: HashiCorp Vault

        Returns:
            (cert_path, key_path)
        """
        # TODO: Implementar
        # cert_dir = f"/certs/{self.instalacion.id}"
        # return (f"{cert_dir}/cert.pem", f"{cert_dir}/key.pem")

        # PLACEHOLDER
        logger.warning(
            f"⚠️ Usando certificado placeholder para instalación {self.instalacion.id}"
        )
        return ("/path/to/cert.pem", "/path/to/key.pem")
