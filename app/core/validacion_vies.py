"""
Validación de IVA intracomunitario en el censo VIES

Documentación: https://ec.europa.eu/taxation_customs/vies/
"""

import logging

from zeep import Client
from zeep.exceptions import Fault, TransportError

logger = logging.getLogger(__name__)

VIES_WSDL = "https://ec.europa.eu/taxation_customs/vies/checkVatService.wsdl"


class VIESValidationError(Exception):
    """Error al validar IVA en VIES"""


def validar_iva_vies(codigo_pais: str, numero_iva: str) -> dict:
    """
    Valida un número de IVA intracomunitario en el censo VIES.

    Args:
        codigo_pais: Código ISO 3166-1 alpha-2 del país (ej: "DE", "FR", "IT")
        numero_iva: Número de IVA sin el prefijo del país (ej: "123456789")

    Returns:
        dict con:
            - valido (bool): Si el IVA es válido
            - pais (str): Código del país
            - numero_iva (str): Número de IVA consultado
            - nombre (str | None): Nombre o razón social (si disponible)
            - direccion (str | None): Dirección (si disponible)

    Raises:
        VIESValidationError: Si hay error en la consulta

    Ejemplo:
        >>> validar_iva_vies("DE", "123456789")
        {
            "valido": True,
            "pais": "DE",
            "numero_iva": "123456789",
            "nombre": "ACME GmbH",
            "direccion": "Hauptstrasse 1, 10115 Berlin"
        }
    """
    # Limpiar número de IVA (quitar espacios, guiones) - FUERA del try
    numero_iva_limpio = numero_iva.strip().replace(" ", "").replace("-", "")
    codigo_pais = codigo_pais.upper().strip()

    try:
        logger.info(f"Validando IVA en VIES: {codigo_pais}{numero_iva_limpio}")

        # Crear cliente SOAP
        client = Client(VIES_WSDL)

        # Llamar al servicio checkVat
        result = client.service.checkVat(
            countryCode=codigo_pais, vatNumber=numero_iva_limpio
        )

        # Procesar respuesta
        response = {
            "valido": result.valid,
            "pais": result.countryCode,
            "numero_iva": result.vatNumber,
            "nombre": result.name if hasattr(result, "name") else None,
            "direccion": result.address if hasattr(result, "address") else None,
        }

        logger.info(
            f"Resultado VIES: válido={response['valido']},nombre={response['nombre']}"
        )

        return response

    except Fault as e:
        # Errores SOAP específicos de VIES
        error_msg = str(e)

        if "INVALID_INPUT" in error_msg:
            logger.warning(f"IVA formato inválido: {codigo_pais}{numero_iva}")
            return {
                "valido": False,
                "pais": codigo_pais,
                "numero_iva": numero_iva_limpio,
                "nombre": None,
                "direccion": None,
            }
        elif "SERVICE_UNAVAILABLE" in error_msg:
            logger.error(f"VIES no disponible temporalmente: {e}")
            raise VIESValidationError("Servicio VIES temporalmente no disponible")
        else:
            logger.error(f"Error SOAP en VIES: {e}")
            raise VIESValidationError(f"Error validando IVA: {error_msg}")

    except TransportError as e:
        logger.error(f"Error de red conectando a VIES: {e}")
        raise VIESValidationError("Error de conexión con VIES")

    except Exception as e:
        logger.error(f"Error inesperado validando VIES: {e}", exc_info=True)
        raise VIESValidationError(f"Error validando IVA: {str(e)}")


def extraer_pais_e_iva(nif_iva: str) -> tuple[str, str]:
    """
    Extrae el código de país y número de IVA de un NIF-IVA completo.

    Args:
        nif_iva: NIF-IVA completo (ej: "DE123456789", "FR12345678901")

    Returns:
        Tupla (codigo_pais, numero_iva)

    Ejemplo:
        >>> extraer_pais_e_iva("DE123456789")
        ("DE", "123456789")
    """
    # Los primeros 2 caracteres son el código del país
    if len(nif_iva) < 3:
        raise ValueError(f"NIF-IVA demasiado corto: {nif_iva}")

    codigo_pais = nif_iva[:2].upper()
    numero_iva = nif_iva[2:].strip()

    return codigo_pais, numero_iva


def validar_iva_vies_completo(nif_iva: str) -> dict:
    """
    Valida un NIF-IVA completo (con código de país incluido).

    Args:
        nif_iva: NIF-IVA completo (ej: "DE123456789")

    Returns:
        dict con resultado de validación

    Ejemplo:
        >>> validar_iva_vies_completo("DE123456789")
        {"valido": True, "pais": "DE", ...}
    """
    codigo_pais, numero_iva = extraer_pais_e_iva(nif_iva)
    return validar_iva_vies(codigo_pais, numero_iva)


# Países de la UE válidos para VIES
PAISES_UE = {
    "AT",
    "BE",
    "BG",
    "HR",
    "CY",
    "CZ",
    "DK",
    "EE",
    "FI",
    "FR",
    "DE",
    "GR",
    "HU",
    "IE",
    "IT",
    "LV",
    "LT",
    "LU",
    "MT",
    "NL",
    "PL",
    "PT",
    "RO",
    "SK",
    "SI",
    "ES",
    "SE",
}


def es_pais_intracomunitario(codigo_pais: str) -> bool:
    """
    Verifica si un código de país es de la UE (intracomunitario).

    Args:
        codigo_pais: Código ISO 3166-1 alpha-2 (ej: "DE", "FR")

    Returns:
        True si es país UE, False en caso contrario
    """
    return codigo_pais.upper() in PAISES_UE


# Ejemplo de uso en el endpoint:
"""
from app.core.validacion_vies import validar_iva_vies, es_pais_intracomunitario

# En el endpoint /v1/create:
if factura_input.id_otro and factura_input.id_otro.id_type == "02":
    # Es un NIF-IVA
    codigo_pais = factura_input.id_otro.codigo_pais
    numero_iva = factura_input.id_otro.id

    if es_pais_intracomunitario(codigo_pais):
        try:
            resultado = validar_iva_vies(codigo_pais, numero_iva)
            if not resultado["valido"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"IVA {codigo_pais}{numero_iva} no encontrado en censo VIES"
                )
        except VIESValidationError as e:
            # Decidir si fallas o permites (AEAT puede validar después)
            logger.warning(f"No se pudo validar IVA en VIES: {e}")
"""
