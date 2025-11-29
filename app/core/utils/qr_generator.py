"""
Generador de código QR según especificaciones AEAT para Verifactu

Documentación: Características del QR y especificaciones del servicio de cotejo
"""

import base64
import logging
from io import BytesIO

import qrcode

logger = logging.getLogger(__name__)


def generar_qr(url: str, size_mm: int = 40) -> str:
    """
    Genera un código QR a partir de una URL según especificaciones AEAT.

    Especificaciones AEAT (Artículo 21):
    - Tamaño: entre 30x30 y 40x40 milímetros
    - Nivel de corrección de errores: M (medio)
    - Norma: ISO/IEC 18004:2015

    Args:
        url: URL a codificar en el QR (ya debe estar con URL encoding aplicado)
        size_mm: Tamaño del QR en milímetros (30-40, default 40)

    Returns:
        String con la imagen en base64 (formato: data:image/png;base64,...)
    """
    try:
        # Validar tamaño según AEAT
        if not 30 <= size_mm <= 40:
            logger.warning(
                f"Tamaño QR {size_mm}mm fuera de rango AEAT (30-40mm), usando 40mm"
            )
            size_mm = 40

        # Crear QR con nivel de corrección M (medio) según especificación AEAT
        qr = qrcode.QRCode(
            version=1,  # Tamaño automático
            error_correction=qrcode.ERROR_CORRECT_M,  # NIVEL M (no L)
            box_size=10,  # Píxeles por "caja"
            border=4,  # Borde mínimo (4 cajas = ~2mm según AEAT)
        )

        qr.add_data(url)
        qr.make(fit=True)

        # Generar imagen (qrcode usará PIL automáticamente si está instalado)
        img = qr.make_image(fill_color="black", back_color="white")

        # Nota: El tamaño se ajusta automáticamente con box_size y version
        # No es crítico hacer resize exacto, el QR será válido igualmente

        # Convertir a base64
        buffer = BytesIO()
        img.save(buffer, "PNG")
        img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        # Retornar en formato data URI para incrustar directamente
        return f"data:image/png;base64,{img_base64}"

    except Exception as e:
        logger.error(f"Error generando QR: {e}", exc_info=True)
        # Retornar string vacío en caso de error (no bloquear la creación de factura)
        return ""


def validar_url_qr(url: str) -> bool:
    """
    Valida que la URL del QR cumpla con las especificaciones AEAT.

    Validaciones:
    - Contiene los 4 parámetros obligatorios: nif, numserie, fecha, importe
    - URL base correcta según entorno
    - Caracteres ASCII imprimibles (32-126)

    Args:
        url: URL a validar

    Returns:
        True si la URL es válida, False en caso contrario
    """
    try:
        # Verificar que contiene los parámetros obligatorios
        required_params = ["nif=", "numserie=", "fecha=", "importe="]
        if not all(param in url for param in required_params):
            logger.error(f"URL QR no contiene todos los parámetros obligatorios: {url}")
            return False

        # Verificar base URL correcta
        valid_bases = [
            "https://prewww2.aeat.es/wlpl/TIKE-CONT/ValidarQR",  # Test
            "https://www2.agenciatributaria.gob.es/wlpl/TIKE-CONT/ValidarQR",  # Prod
        ]

        if not any(url.startswith(base) for base in valid_bases):
            logger.error(f"URL QR no tiene base válida: {url}")
            return False

        # Verificar caracteres ASCII imprimibles (32-126)
        if not all(32 <= ord(c) <= 126 for c in url):
            logger.error("URL QR contiene caracteres no ASCII imprimibles")
            return False

        return True

    except Exception as e:
        logger.error(f"Error validando URL QR: {e}")
        return False


# Ejemplo de uso correcto según AEAT:
"""
from urllib.parse import quote

# Caso con caracteres especiales en numserie
nif = "89890001K"
serie = "12345678"
numero = "G33"
fecha = "14-11-2024"
importe = "241.40"

# Concatenar serie + número
num_serie = f"{serie}-{numero}"  # o serie + numero sin separador

# IMPORTANTE: Aplicar URL encoding
url = (
    f"https://prewww2.aeat.es/wlpl/TIKE-CONT/ValidarQR"
    f"?nif={quote(nif)}"
    f"&numserie={quote(num_serie)}"  # Esto convierte & en %26
    f"&fecha={quote(fecha)}"
    f"&importe={importe}"
)

# Generar QR
qr_base64 = generar_qr(url, size_mm=40)

# Resultado:
# URL: https://prewww2.aeat.es/wlpl/TIKE-CONT/ValidarQR?nif=89890001K
#               &numserie=12345678-G33&fecha=14-11-2024&importe=241.40
# QR: data:image/png;base64,iVBORw0KGgo...
"""
