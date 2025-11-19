"""
Validación de NIF, CIF y NIE españoles

Basado en algoritmos oficiales del Ministerio de Hacienda
"""

import re
from typing import Literal

# Letras válidas para NIF (DNI)
LETRAS_NIF = "TRWAGMYFPDXBNJZSQVHLCKE"

# Letras válidas para CIF según tipo de organización
LETRAS_CIF_ORGANIZACION = "ABCDEFGHJNPQRSUVW"

# Dígitos de control para CIF
DIGITOS_CONTROL_CIF = "JABCDEFGHI"


class NIFValidationError(Exception):
    """Error de validación de NIF/CIF/NIE"""


def limpiar_nif(nif: str) -> str:
    """
    Limpia y normaliza un NIF/CIF/NIE.

    Args:
        nif: NIF a limpiar

    Returns:
        NIF limpio en mayúsculas
    """
    return nif.strip().upper().replace(" ", "").replace("-", "")


def validar_formato_nif(nif: str) -> bool:
    """
    Valida el formato básico de un NIF/CIF/NIE.

    Args:
        nif: NIF a validar

    Returns:
        True si el formato es válido
    """
    nif = limpiar_nif(nif)

    # Debe tener entre 9 y 10 caracteres
    if len(nif) < 9 or len(nif) > 10:
        return False

    # Patrones válidos:
    # - NIF: 8 dígitos + letra (12345678Z)
    # - NIE: X/Y/Z + 7 dígitos + letra (X1234567L)
    # - CIF: Letra + 7-8 dígitos + letra/dígito (A12345678)

    patrones = [
        r"^\d{8}[A-Z]$",  # NIF: 8 dígitos + letra
        r"^[XYZ]\d{7}[A-Z]$",  # NIE: X/Y/Z + 7 dígitos + letra
        r"^[A-W]\d{7}[A-Z0-9]$",  # CIF: Letra org + 7 dígitos + control
        r"^[A-W]\d{8}$",  # CIF alternativo
    ]

    return any(re.match(patron, nif) for patron in patrones)


def calcular_letra_nif(numero: int) -> str:
    """
    Calcula la letra de control de un NIF (DNI).

    Args:
        numero: Número del DNI (8 dígitos)

    Returns:
        Letra de control
    """
    return LETRAS_NIF[numero % 23]


def validar_nif_dni(nif: str) -> bool:
    """
    Valida un NIF (DNI español).

    Args:
        nif: NIF a validar (formato: 12345678Z)

    Returns:
        True si el NIF es válido

    Ejemplo:
        >>> validar_nif_dni("12345678Z")
        True
    """
    nif = limpiar_nif(nif)

    if not re.match(r"^\d{8}[A-Z]$", nif):
        return False

    numero = int(nif[:8])
    letra = nif[8]

    return letra == calcular_letra_nif(numero)


def validar_nie(nie: str) -> bool:
    """
    Valida un NIE (Número de Identificación de Extranjero).

    Args:
        nie: NIE a validar (formato: X1234567L)

    Returns:
        True si el NIE es válido

    Ejemplo:
        >>> validar_nie("X1234567L")
        True
    """
    nie = limpiar_nif(nie)

    if not re.match(r"^[XYZ]\d{7}[A-Z]$", nie):
        return False

    # Convertir primera letra a número
    # X=0, Y=1, Z=2
    conversion = {"X": "0", "Y": "1", "Z": "2"}
    numero_str = conversion[nie[0]] + nie[1:8]
    numero = int(numero_str)
    letra = nie[8]

    return letra == calcular_letra_nif(numero)


def calcular_digito_control_cif(cif_sin_control: str) -> str:
    """
    Calcula el dígito/letra de control de un CIF.

    Args:
        cif_sin_control: CIF sin el dígito de control (8 caracteres)

    Returns:
        Dígito o letra de control
    """
    # Algoritmo de cálculo del dígito de control CIF
    letra_org = cif_sin_control[0]
    numeros = cif_sin_control[1:]

    # Suma de dígitos en posiciones impares multiplicados por 2
    suma_impares = 0
    for i in range(0, len(numeros), 2):
        doble = int(numeros[i]) * 2
        suma_impares += doble // 10 + doble % 10

    # Suma de dígitos en posiciones pares
    suma_pares = sum(int(numeros[i]) for i in range(1, len(numeros), 2))

    # Suma total
    suma_total = suma_impares + suma_pares

    # Dígito de control
    unidad = suma_total % 10
    digito_control = (10 - unidad) % 10

    # Algunas organizaciones usan letra en lugar de dígito
    # A, B, E, H → letra
    # Resto → dígito o letra
    if letra_org in "NPQRSW":
        return DIGITOS_CONTROL_CIF[digito_control]
    else:
        return str(digito_control)


def validar_cif(cif: str) -> bool:
    """
    Valida un CIF (Código de Identificación Fiscal).

    Args:
        cif: CIF a validar (formato: A12345678 o A1234567B)

    Returns:
        True si el CIF es válido

    Ejemplo:
        >>> validar_cif("A12345678")
        True
    """
    cif = limpiar_nif(cif)

    # Debe empezar con letra de organización
    if len(cif) != 9 or cif[0] not in LETRAS_CIF_ORGANIZACION:
        return False

    # Extraer parte numérica y control
    cif_sin_control = cif[:8]
    control_esperado = cif[8]

    # Verificar que los 7 caracteres intermedios son dígitos
    if not cif[1:8].isdigit():
        return False

    # Calcular control
    control_calculado = calcular_digito_control_cif(cif_sin_control)

    # El control puede ser dígito o letra según el tipo de organización
    letra_org = cif[0]

    if letra_org in "NPQRSW":
        # Debe ser letra
        return control_esperado == control_calculado
    elif letra_org in "ABEH":
        # Debe ser dígito
        return control_esperado.isdigit() and control_esperado == control_calculado
    else:
        # Puede ser dígito o letra
        if control_esperado.isdigit():
            return control_esperado == control_calculado
        else:
            return control_esperado == DIGITOS_CONTROL_CIF[int(control_calculado)]


def detectar_tipo_documento(doc: str) -> Literal["NIF", "NIE", "CIF", "DESCONOCIDO"]:
    """
    Detecta el tipo de documento español.

    Args:
        doc: Documento a analizar

    Returns:
        Tipo de documento: "NIF", "NIE", "CIF" o "DESCONOCIDO"
    """
    doc = limpiar_nif(doc)

    if re.match(r"^\d{8}[A-Z]$", doc):
        return "NIF"
    elif re.match(r"^[XYZ]\d{7}[A-Z]$", doc):
        return "NIE"
    elif re.match(r"^[A-W]\d{7}[A-Z0-9]$", doc):
        return "CIF"
    else:
        return "DESCONOCIDO"


def validar_documento_espanol(doc: str) -> dict:
    """
    Valida cualquier tipo de documento español (NIF, NIE o CIF).

    Args:
        doc: Documento a validar

    Returns:
        dict con:
            - valido (bool): Si el documento es válido
            - tipo (str): Tipo de documento (NIF, NIE, CIF)
            - documento (str): Documento limpio

    Ejemplo:
        >>> validar_documento_espanol("12345678Z")
        {"valido": True, "tipo": "NIF", "documento": "12345678Z"}
    """
    doc_limpio = limpiar_nif(doc)
    tipo = detectar_tipo_documento(doc_limpio)

    if tipo == "NIF":
        valido = validar_nif_dni(doc_limpio)
    elif tipo == "NIE":
        valido = validar_nie(doc_limpio)
    elif tipo == "CIF":
        valido = validar_cif(doc_limpio)
    else:
        valido = False

    return {"valido": valido, "tipo": tipo, "documento": doc_limpio}


# Ejemplo de uso en endpoint:
"""
from app.core.validacion_nif import validar_documento_espanol

# En el endpoint /v1/create:
if factura_input.nif:
    resultado = validar_documento_espanol(factura_input.nif)
    if not resultado["valido"]:
        raise HTTPException(
            status_code=400,
            detail=f"NIF/CIF/NIE inválido: {factura_input.nif}"
        )
"""
