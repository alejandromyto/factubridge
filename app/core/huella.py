"""
Generador de hash para VeriFactu según especificaciones AEAT
Portado desde Java - mantiene la misma lógica exacta
https://www.agenciatributaria.es/static_files/AEAT_Desarrolladores/EEDD/IVA/VERI-FACTU/Veri-Factu_especificaciones_huella_hash_registros.pdf
"""
import hashlib
import logging
from typing import Optional
from datetime import datetime
from decimal import Decimal

logger = logging.getLogger(__name__)


def get_hash_verifactu(msg: str) -> str:
    """
    Calcula el hash SHA-256 en formato hexadecimal (mayúsculas) según VeriFactu
    
    Args:
        msg: Cadena de texto a hashear
        
    Returns:
        Hash SHA-256 en formato hexadecimal con mayúsculas (64 caracteres)
    """
    try:
        # DEBUG: Imprimir la cadena exacta y sus bytes (igual que en Java)
        logger.debug("=== DEBUG HASH ===")
        logger.debug(f"Cadena a hashear: [{msg}]")
        logger.debug(f"Longitud: {len(msg)}")
        
        # Primeros 50 caracteres
        logger.debug("Primeros 50 caracteres:")
        logger.debug(msg[:min(50, len(msg))])
        
        # Últimos 50 caracteres
        logger.debug("Últimos 50 caracteres:")
        logger.debug(msg[max(0, len(msg) - 50):])
        
        # Convertir a bytes UTF-8
        input_bytes = msg.encode('utf-8')
        logger.debug(f"Bytes UTF-8: {len(input_bytes)}")
        
        # Primeros 20 bytes en hex
        hex_bytes = ' '.join(f'{b:02X}' for b in input_bytes[:min(20, len(input_bytes))])
        logger.debug(f"Primeros 20 bytes (hex): {hex_bytes}")
        
        # Calcular SHA-256
        hash_bytes = hashlib.sha256(input_bytes).digest()
        
        # Convertir a hexadecimal en mayúsculas
        result = ''.join(f'{b:02x}' for b in hash_bytes).upper()
        
        logger.debug(f"Hash resultado: {result}")
        logger.debug("==================")
        
        return result
        
    except Exception as e:
        logger.error(f"Error al generar la huella SHA: {e}")
        return ""


def get_valor_campo(nombre: str, valor: Optional[str], separador: bool) -> str:
    """
    Formatea un campo para la cadena de hash
    Formato: nombre=valor& (con separador) o nombre=valor (sin separador)
    
    Args:
        nombre: Nombre del campo
        valor: Valor del campo (puede ser None)
        separador: Si se debe añadir '&' al final
        
    Returns:
        Campo formateado
    """
    valor_limpio = "" if valor is None else valor.strip()
    campo = f"{nombre}={valor_limpio}"
    
    if separador:
        return campo + "&"
    else:
        return campo


def format_date(date: datetime, pattern: str) -> str:
    """
    Formatea una fecha según el patrón especificado
    Para fechas con hora usa la zona horaria local con offset
    
    Args:
        date: Fecha a formatear
        pattern: Patrón de formato (ej: "dd-MM-yyyy" o "yyyy-MM-dd'T'HH:mm:ssXXX")
        
    Returns:
        Fecha formateada
    """
    if date is None:
        return ""
    
    # Para fechas simples (sin hora)
    if "HH:mm:ss" not in pattern:
        # dd-MM-yyyy
        return date.strftime("%d-%m-%Y")
    
    # Para fechas con hora (timestamp ISO 8601 con zona horaria)
    # Python: strftime("%Y-%m-%dT%H:%M:%S%z") genera formato +0100
    # Necesitamos +01:00 (con dos puntos)
    iso_str = date.astimezone().isoformat()
    
    # CRÍTICO: Asegurar formato correcto de zona horaria
    # Python genera: 2024-11-14T10:30:00+01:00 ✓
    # Java puede generar 'Z' que hay que convertir a +00:00
    
    return iso_str


def get_referencia_registro_alta(
    nif_emisor: str,
    num_factura_serie: str,
    fecha_expedicion: str,
    tipo_factura: str,
    cuota_total: str,
    importe_total: str,
    huella_anterior: Optional[str],
    fecha_hora_huso_registro: str
) -> str:
    """
    Genera la cadena de referencia para el registro de alta
    Formato AEAT con campos separados por &
    
    Returns:
        Cadena completa para hashear
    """
    return (
        get_valor_campo("IDEmisorFactura", nif_emisor, True) +
        get_valor_campo("NumSerieFactura", num_factura_serie, True) +
        get_valor_campo("FechaExpedicionFactura", fecha_expedicion, True) +
        get_valor_campo("TipoFactura", tipo_factura, True) +
        get_valor_campo("CuotaTotal", cuota_total, True) +
        get_valor_campo("ImporteTotal", importe_total, True) +
        get_valor_campo("Huella", huella_anterior, True) +
        get_valor_campo("FechaHoraHusoGenRegistro", fecha_hora_huso_registro, False)
    )


def calcular_huella_alta(
    nif_emisor: str,
    num_factura_serie: str,
    fecha_expedicion: datetime,
    tipo_factura: str,
    cuota_total: str,
    importe_total: str,
    huella_anterior: Optional[str],
    fecha_hora_huso_gen_registro: datetime
) -> str:
    """
    Calcula la huella para un registro de alta (operación normal)
    
    Args:
        nif_emisor: NIF del emisor
        num_factura_serie: Serie + Número concatenados
        fecha_expedicion: Fecha de expedición de la factura
        tipo_factura: Tipo (F1, F2, R1, etc.)
        cuota_total: Cuota total formateada
        importe_total: Importe total formateado
        huella_anterior: Huella del registro anterior (puede ser None)
        fecha_hora_huso_gen_registro: Timestamp de generación del registro
        
    Returns:
        Hash SHA-256 en mayúsculas (64 caracteres)
    """
    # Formatear fechas
    fecha_exp = format_date(fecha_expedicion, "dd-MM-yyyy")
    fecha_hora_reg = format_date(fecha_hora_huso_gen_registro, "yyyy-MM-dd'T'HH:mm:ssXXX")
    
    # Generar cadena de referencia
    ref = get_referencia_registro_alta(
        nif_emisor,
        num_factura_serie,
        fecha_exp,
        tipo_factura,
        cuota_total,
        importe_total,
        huella_anterior,
        fecha_hora_reg
    )
    
    logger.debug(f"Calculando Huella Alta de: {ref}")
    print("Cadena completa para hash:")
    print(ref)
    
    return get_hash_verifactu(ref)


# Función de conveniencia para usar desde el endpoint
def calcular_huella(
    nif_emisor: str,
    numero_serie: str,
    fecha_expedicion: str,
    tipo_factura: str,
    cuota_total: Decimal,
    importe_total: Decimal,
    huella_anterior: Optional[str] = None
) -> str:
    """
    Función de alto nivel para calcular huella desde el endpoint
    
    Args:
        nif_emisor: NIF del emisor
        numero_serie: Serie + Número concatenados
        fecha_expedicion: Fecha en formato dd-mm-yyyy
        tipo_factura: Tipo (F1, F2, R1, etc.)
        cuota_total: Cuota total como Decimal
        importe_total: Importe total como Decimal
        huella_anterior: Huella del registro anterior (opcional)
        
    Returns:
        Hash SHA-256 en mayúsculas
    """
    # Parsear fecha de expedición desde dd-mm-yyyy
    fecha_exp_dt = datetime.strptime(fecha_expedicion, "%d-%m-%Y")
    
    # Timestamp actual de generación del registro
    fecha_hora_gen = datetime.now().astimezone()
    
    # Formatear importes como strings (sin formato especial aquí, 
    # AEAT los espera como números normales con hasta 2 decimales)
    cuota_str = f"{cuota_total:.2f}"
    importe_str = f"{importe_total:.2f}"
    
    return calcular_huella_alta(
        nif_emisor=nif_emisor,
        num_factura_serie=numero_serie,
        fecha_expedicion=fecha_exp_dt,
        tipo_factura=tipo_factura,
        cuota_total=cuota_str,
        importe_total=importe_str,
        huella_anterior=huella_anterior,
        fecha_hora_huso_gen_registro=fecha_hora_gen
    )


# Ejemplo de uso:
"""
from decimal import Decimal
from datetime import datetime

huella = calcular_huella(
    nif_emisor="B12345678",
    numero_serie="A001",
    fecha_expedicion="14-11-2024",
    tipo_factura="F1",
    cuota_total=Decimal("42.00"),
    importe_total=Decimal("242.00"),
    huella_anterior="ABCD1234..." if existe_anterior else None
)

# Resultado esperado:
# Cadena: IDEmisorFactura=B12345678&NumSerieFactura=A001&FechaExpedicionFactura=14-11-2024&
#         TipoFactura=F1&CuotaTotal=42.00&ImporteTotal=242.00&Huella=ABCD...&
#         FechaHoraHusoGenRegistro=2024-11-14T10:30:00+01:00
# Hash: [64 caracteres hexadecimales en mayúsculas]
"""