"""Line items for invoices (LineaFactura)

The AEAT API limits a maximum of 12 lines per invoice; each line groups items with the
same VAT rate. Fields use string/decimal formats in the API; here we map to Decimal but
accept strings.
"""

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.infrastructure.aeat.models.suministro_informacion import (
    CalificacionOperacionType,
    IdOperacionesTrascendenciaTributariaType,
    ImpuestoType,
    OperacionExentaType,
)


class LineaFactura(BaseModel):
    """A single invoice line.

    Fields
    - base_imponible: base taxable amount (required)
    - tipo_impositivo: VAT rate or amount applied (optional)
    - cuota_repercutida: VAT amount (optional)
    - impuesto
    - calificacion_operacion
    - clave_regimen IdOperacionesTranscendenciaTributariaType
    - operacion_exenta: when the operation is exempt (then no tipos/cuotas allowed)
    - base_imponible_a_coste
    - tipo_recargo_equivalencia: recargo equivalencia VAT rate (optional)
    - cuota_recargo_equivalencia: recargo equivalencia amount (optional)
    """

    base_imponible: Decimal = Field(
        ..., description=r"Base imponible. Pattern: (+|-)d{1,12}(\.d{0,2})?"
    )

    tipo_impositivo: Optional[Decimal] = Field(
        default=None,
        description=(
            "Tipo impositivo de la línea. Obligatorio si calificacion_operacion es S1 "
            "y base_imponible_a_coste no está cumplimentado. Si impuesto = 01 (IVA) "
            "valores permitidos: 0, 2, 4, 5, 7.5, 10, 21."
        ),
        max_digits=5,
        decimal_places=2,
    )
    cuota_repercutida: Optional[Decimal] = Field(
        None, description="Cuota repercutida (si aplica)."
    )
    impuesto: Optional[ImpuestoType] = Field(
        default=ImpuestoType.VALUE_01,
        description=(
            "Default: '01' Enum: '01' '02' '03' '05'"
            "Tipo de impuesto. Los valores permitidos son:"
            "01: Impuesto sobre el Valor Añadido (IVA)"
            "02: Impuesto sobre la Producción, los Servicios y la Importación (IPSI) de"
            " Ceuta y Melilla"
            "03: Impuesto General Indirecto Canario (IGIC)"
            "05: Otros"
        ),
    )
    calificacion_operacion: Optional[CalificacionOperacionType] = Field(
        default=CalificacionOperacionType.N1,
        description=(
            "Enum: 'S1' 'S2' 'N1' 'N2'. Calificación de la operación. Solo se"
            " puede informar si el campo operacion_exenta no se cumplimenta. En ese"
            " caso, por defecto se usará el valor S1."
            "S1: Operación sujeta y no exenta - sin inversión del sujeto pasivo."
            "S2: Operación sujeta y no exenta - con inversión del sujeto pasivo."
            "N1: Operación no sujeta (art. 7, 14, otros)."
            "N2: Operación no sujeta por reglas de localización."
        ),
    )
    clave_regimen: Optional[IdOperacionesTrascendenciaTributariaType] = Field(
        default=IdOperacionesTrascendenciaTributariaType.VALUE_01,
        description=(
            "Enum: '01' '02' '03' '04' '05' '06' '07' '08' '09' '10' '11' '14'"
            " '15' '17' '18' '19' '20'"
            "Clave que identifica el tipo de régimen del IVA/IGIC. Permitido únicamente"
            " cuando impuesto = 01 (IVA) o impuesto = 03 (IGIC). En estos casos el"
            " valor por defecto es 01."
            "01: Operación de régimen general."
            "02: Exportación."
            "03: Operaciones a las que se aplique el régimen especial de bienes usados,"
            " objetos de arte, antigüedades y objetos de colección."
            "04: Régimen especial del oro de inversión."
            "05: Régimen especial de las agencias de viajes."
            "06: Régimen especial grupo de entidades en IVA o IGIC (Nivel Avanzado)"
            "07: Régimen especial del criterio de caja."
            "08: Operaciones sujetas al IPSI/IVA o IGIC."
            "09: Facturación de las prestaciones de servicios de agencias de viaje que"
            " actúan como mediadoras en nombre y por cuenta ajena(D.A.4ª RD1619/ 2012)"
            "10: Cobros por cuenta de terceros de honorarios profesionales o de"
            " derechos derivados de la propiedad industrial, de autor u otros por"
            " cuenta de sus socios, asociados o colegiados efectuados por sociedades,"
            " asociaciones, colegios profesionales u otras entidades que realicen estas"
            " funciones de cobro."
            "11: Operaciones de arrendamiento de local de negocio."
            "14: Factura con IVA o IGIC pendiente de devengo en certificaciones de obra"
            " cuyo destinatario sea una Administración Pública."
            "15: Factura con IVA o IGIC pendiente de devengo en operaciones de tracto"
            " sucesivo."
            "17: Operación acogida a alguno de los regímenes previstos en el Capítulo"
            " XI del Título IX(OSS e IOSS) o régimen especial de comerciante minorista"
            "18: Recargo de equivalencia o régimen especial del pequeño empresario o"
            " profesional."
            "19: Operaciones de actividades incluidas en el Régimen Especial de"
            " Agricultura, Ganadería y Pesca(REAGYP) u operaciones interiores exentas"
            " por aplicación artículo 25 Ley 19 / 1994"
            "20: Régimen simplificado"
        ),
    )
    operacion_exenta: Optional[OperacionExentaType] = Field(
        None,
        description=(
            "Enum: 'E1' 'E2' 'E3' 'E4' 'E5' 'E6'. Tipo de operación"
            " exenta. En caso de estar cumplimentado, no podrá informarse de los campos"
            " tipo_impositivo, cuota_repercutida, tipo_recargo_equivalencia y"
            " cuota_recargo_equivalencia. Valores permitidos son (BOE-A-1992-28740):"
            "                E1: Exenta por artículo 20"
            "                E2: Exenta por artículo 21"
            "                E3: Exenta por artículo 22"
            "                E4: Exenta por artículo 24"
            "                E5: Exenta por artículo 25"
            "                E6: Otros"
        ),
    )
    base_imponible_a_coste: Optional[Decimal] = Field(
        default=None,
        description=(
            "Base imponible a coste de la linea. Este campo solo puede estar"
            " cumplimentado si la clave_regimen es = 06 o impuesto = 02 (IPSI) o"
            " impuesto = 05 (Otros)."
        ),
    )
    tipo_recargo_equivalencia: Optional[Decimal] = Field(
        default=None,
        max_digits=5,
        decimal_places=2,
        description=(
            "- Si Impuesto = '01' (IVA) o no se cumplimenta"
            " (considerándose '01' - IVA) y CalificacionOperacion = 'S1':"
            "   - Solo se permiten TipoRecargoEquivalencia = 0; 0,26; 0,5; 0,62; 1;"
            "   1,4; 1,75; 5,2 (valores que indican el tanto por ciento)."
            "- Si TipoImpositivo es 21 sólo se admitirán TipoRecargoEquivalencia = 5,2"
            " ó 1,75."
            "- Si TipoImpositivo es 10 sólo se admitirá TipoRecargoEquivalencia = 1,4."
            "- Si TipoImpositivo es 7,5 sólo se admitirá TipoRecargoEquivalencia = 1."
            "   ✓ Si FechaOperacion (FechaExpedicionFactura de la agrupación IDFactura"
            "   si no se informa FechaOperacion) es mayor o igual que 1 de octubre de"
            "   2024 y menor o igual que 31 de diciembre de 2024 se admitirá el"
            "   TipoRecargoEquivalencia = 1."
            "- Si tipo impositivo es 5:"
            "   ✓ Si FechaOperacion (FechaExpedicionFactura de la agrupación IDFactura"
            "   si no se informa FechaOperacion) es igual o inferior al 31 de diciembre"
            "   de 2022, solo se admitirá TipoRecargoEquivalencia = 0,5."
            "   ✓ Si FechaOperacion (FechaExpedicionFactura de la agrupación IDFactura"
            "   si no se informa FechaOperacion) es mayor o igual que 1 de enero de"
            "   2023 y menor o igual que 30 de septiembre de 2024, solo se admitirá"
            "   TipoRecargoEquivalencia = 0,62."
            "- Si TipoImpositivo es 4 sólo se admitirá TipoRecargoEquivalencia = 0,5."
            "- Si TipoImpositivo es 2 sólo se admitirá TipoRecargoEquivalencia = 0,26."
            "   ✓ Si FechaOperacion (FechaExpedicionFactura de la agrupación IDFactura"
            "   si no se informa FechaOperacion) es mayor o igual que 1 de octubre de"
            "   2024 y menor o igual que 31 de diciembre de 2024 se admitirá el"
            "   TipoRecargoEquivalencia = 0,26."
            "- Si tipo impositivo es 0:"
            "   ✓ Si FechaOperacion (FechaExpedicionFactura de la agrupación IDFactura"
            "   si no se informa FechaOperacion) es mayor o igual que 1 de enero de"
            "   2023 y menor o igual que 30 de septiembre de 2024, solo se admitirá"
            "   TipoRecargoEquivalencia = 0."
        ),
    )
    cuota_recargo_equivalencia: Optional[Decimal] = Field(
        None, description="Cuota recargo equivalencia."
    )

    @field_validator("cuota_repercutida", "cuota_recargo_equivalencia", mode="before")
    def ensure_decimal(cls, v: Decimal | None) -> Decimal | None:
        if v is None:
            return None
        return Decimal(v)

    @model_validator(mode="after")
    def _valida_base_imponible_a_coste(self) -> "LineaFactura":
        if self.base_imponible_a_coste is None:
            return self  # nada que validar

        # Regla: sólo puede informarse si se cumple alguna de estas tres condiciones
        if not (
            self.clave_regimen == IdOperacionesTrascendenciaTributariaType.VALUE_06
            or self.impuesto == ImpuestoType.VALUE_02
            or self.impuesto == ImpuestoType.VALUE_05
        ):
            raise ValueError(
                "base_imponible_a_coste solo puede informarse si "
                "clave_regimen='06' o impuesto='02' (IPSI) o impuesto='05' (Otros)."
            )
        return self
