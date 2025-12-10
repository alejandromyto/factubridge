"""Factura create model (FacturaInput) with business validations mirroring Verifacti.

The model implements:
- parsing of DD-MM-YYYY date strings
- business rules: destinatario presence/absence per tipo_factura
- F2 amount maximum check
- rectificativa rules (tipo_rectificativa, facturas_rectificadas)
- operation exenta checks per line
- importe_total vs sum of lines check (±10.00€)
- fecha_expedicion must not be future date
"""

from datetime import date
from decimal import Decimal
from typing import Dict, FrozenSet, List, Optional, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.infrastructure.aeat.models.suministro_informacion import (
    CalificacionOperacionType,
    ClaveTipoFacturaType,
    ClaveTipoRectificativaType,
    ImpuestoType,
)

from .especiales import Especial
from .ids import IdOtro
from .lineas import LineaFactura
from .validators import (
    importe_matches_total,
    parse_dd_mm_yyyy,
)


class IdFacturaArInput(BaseModel):
    nif_emisor: Optional[str] = Field(
        None,
        min_length=9,
        max_length=9,
        description="NIF del emisor. Si no se envía, se usará el NIF del emisor de la"
        " factura actual.",
    )
    serie: str = Field(..., max_length=20)
    numero: str = Field(..., max_length=20)
    fecha_expedicion: date


class FacturasRectificadasInput(BaseModel):
    """Lista de facturas rectificadas."""

    facturas: List[IdFacturaArInput] = Field(..., min_length=1, max_length=1000)


class FacturasSustituidasInput(BaseModel):
    """Lista de facturas sustituidas."""

    facturas: List[IdFacturaArInput] = Field(..., min_length=1, max_length=1000)


class ImporteRectificativaInput(BaseModel):
    """Validación de entrada para datos de rectificación.

    - base_rectificada: base imponible rectificada
    - cuota_rectificada: cuota repercutida rectificada
    - cuota_recargo_rectificado: cuota recargo equivalencia rectificada (opcional)
    """

    base_rectificada: Decimal = Field(..., max_digits=14, decimal_places=2)
    cuota_rectificada: Decimal = Field(..., max_digits=14, decimal_places=2)
    cuota_recargo_rectificado: Optional[Decimal] = Field(
        None, max_digits=14, decimal_places=2
    )


class FacturaInput(BaseModel):
    """Schema de entrada EXACTO para creación de facturas.

    Docstrings and comments intentionally verbose for auditability. For cross-checking,
    see the original Verifactu OpenAPI spec.
    """

    serie: str = Field(..., max_length=60)
    numero: str = Field(..., max_length=60)
    fecha_expedicion: date
    fecha_operacion: Optional[date] = None

    tipo_factura: ClaveTipoFacturaType = Field(...)
    descripcion: str = Field(..., min_length=1, max_length=500)

    lineas: List[LineaFactura] = Field(..., min_length=1, max_length=12)
    importe_total: Decimal = Field(...)

    nif: Optional[str] = Field(None)
    id_otro: Optional[IdOtro] = None
    nombre: Optional[str] = Field(None, max_length=120)

    validar_destinatario: bool = True
    tipo_rectificativa: Optional[ClaveTipoRectificativaType] = Field(None)
    importe_rectificativa: Optional[ImporteRectificativaInput] = None
    facturas_rectificadas: Optional[List[dict]] = None
    facturas_sustituidas: Optional[List[dict]] = None
    incidencia: Optional[str] = None
    especial: Optional[Especial] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "serie": "A",
                "numero": "234634",
                "fecha_expedicion": "15-11-2024",
                "tipo_factura": "F1",
                "descripcion": "Prestación de servicios",
                "nif": "A15022510",
                "nombre": "Cliente SL",
                "lineas": [
                    {
                        "base_imponible": "200.00",
                        "tipo_impositivo": "21",
                        "cuota_repercutida": "42.00",
                    }
                ],
                "importe_total": "242.00",
            }
        }
    )

    @field_validator("fecha_expedicion", "fecha_operacion", mode="before")
    def parse_date(cls, v: str | date | None) -> date | None:
        if isinstance(v, str):
            return parse_dd_mm_yyyy(v)
        return v

    @model_validator(mode="after")
    def business_validations(self) -> Self:
        """Apply business rules described in OpenAPI.

        Important rules:
        - F2/R5: no destinatario (nif/nombre/id_otro)
        - F2: importe_total must be <= 3010.00 (3.000 + 10 margin)
        - Rectificativas (R*): require tipo_rectificativa and related fields
        - For each line, if operacion_exenta == 'S' then no tipos/cuotas may be provided
        - importe_total must equal sum of lines +/- 10.00 (unless special regimes)
        - fecha_expedicion cannot be future date
        """
        SIN_DESTINATARIO = {
            ClaveTipoFacturaType.F2,
            ClaveTipoFacturaType.R5,
        }
        RECTIFICATIVAS = {
            ClaveTipoFacturaType.R1,
            ClaveTipoFacturaType.R2,
            ClaveTipoFacturaType.R3,
            ClaveTipoFacturaType.R4,
            ClaveTipoFacturaType.R5,
        }
        tipo = self.tipo_factura
        # 1) destinatarios según tipo
        if tipo in SIN_DESTINATARIO and (self.nif or self.nombre or self.id_otro):
            raise ValueError(f"Tipo {tipo.value}, no se permite informar destinatario")

        # 2) F2 importe máximo (3.000 + 10 margen)
        if tipo == ClaveTipoFacturaType.F2:
            importe = Decimal(str(self.importe_total))
            if importe > Decimal("3010"):
                raise ValueError(
                    "Factura simplificada (F2) supera importe permitido (3.000€ + 10€)"
                )

        # 3) Rx: require tipo_rectificativa and facturas_rectificadas when needed
        if tipo in RECTIFICATIVAS:
            if not self.tipo_rectificativa:
                raise ValueError(
                    f"Para {tipo.value} es obligatorio especificar tipo_rectificativa"
                )
            if (
                self.tipo_rectificativa == ClaveTipoRectificativaType.S
                and not self.facturas_rectificadas
            ):
                raise ValueError(
                    "Para rectificativa por sustitución se requieren facturas"
                    " rectificadas"
                )
            if not self.facturas_rectificadas:
                # Although optional in OpenAPI for some R types, keep conservative:
                # require at least empty list for traceability
                raise ValueError("Se requiere información de facturas rectificadas")

        # 4) impuestos/recargo validaciones por linea
        for ln in self.lineas:
            if ln.operacion_exenta is not None:
                if (
                    getattr(ln, "tipo_impositivo", None)
                    or getattr(ln, "cuota_repercutida", None)
                    or getattr(ln, "tipo_recargo_equivalencia", None)
                    or getattr(ln, "cuota_recargo_equivalencia", None)
                ):
                    raise ValueError(
                        "Cuando existe operación exenta no pueden informarse tipos"
                        " impositivo/recargos/cuotas"
                    )

        # 5) importe_total consistency (±10.00€)
        if not importe_matches_total(
            self.importe_total, self.lineas, allowed_margin=Decimal("10.00")
        ):
            raise ValueError(
                "Importe total no coincide con suma de líneas dentro del margen"
                " permitido (±10.00€)"
            )

        # 6) fecha_expedicion not future
        if self.fecha_expedicion > date.today():
            raise ValueError("FechaExpedicion no puede ser futura")

        # 7) fecha_expedicion >= 28/10/2024
        min_fecha = date(2024, 10, 28)
        if self.fecha_expedicion < min_fecha:
            raise ValueError(
                f"FechaExpedicion no puede ser anterior a {min_fecha.isoformat()}"
            )
        # 8) serie: ASCII 32..126 and forbidden chars
        forbidden = {'"', "'", "<", ">", "="}
        if any(ord(ch) < 32 or ord(ch) > 126 for ch in self.serie):
            raise ValueError(
                "Serie contiene caracteres no imprimibles (ASCII fuera 32-126)"
            )
        if any(ch in forbidden for ch in self.serie):
            raise ValueError("Serie no puede contener los caracteres: \" ' < > =")

        # 9) fecha_expedicion vs fecha_operacion según impuesto/clave_regimen
        # derive impuesto_effectivo and claves_regimen_presentes from lineas
        impuestos = {getattr(ln, "impuesto", None) for ln in self.lineas}
        claves = {getattr(ln, "clave_regimen", None) for ln in self.lineas}
        # treat missing impuesto as IVA ("01")
        impuesto_is_iva_igic = any(i in (None, "01", "03") for i in impuestos)
        clave_excepcion = any(k in ("14", "15") for k in claves)

        if self.fecha_operacion:
            if impuesto_is_iva_igic and not clave_excepcion:
                if self.fecha_expedicion < self.fecha_operacion:
                    raise ValueError(
                        "Para IVA/IGIC (o sin indicación) FechaExpedicion no puede"
                        " ser anterior a FechaOperacion salvo ClaveRegimen 14/15"
                    )
        return self

    @model_validator(mode="after")
    def _valida_tipos_impositivo_y_recargo_equivalencia(self) -> Self:
        from datetime import date

        # --- constantes de negocio ---
        FECHA_31_DIC_2022 = date(2022, 12, 31)
        FECHA_30_SEP_2024 = date(2024, 9, 30)

        # ---------- única fuente de valores ----------
        _RAW_TI = ("0", "2", "4", "5", "7.5", "10", "21")  # tipo impositivo
        _RAW_R5 = ("0.5", "0.62")  # recargos 5 según fecha
        _RAW_RECARGOS = _RAW_R5 + (
            "0",
            "0.26",
            "1",
            "1.4",
            "1.75",
            "5.2",
        )  # todos los recargos

        # conjuntos reutilizables
        TIPOS_IMPOSITIVOS_OK: FrozenSet[Decimal] = frozenset(map(Decimal, _RAW_TI))
        RECARGOS_S1: FrozenSet[Decimal] = frozenset(map(Decimal, _RAW_RECARGOS))

        # recargos fijos por tipo (sin ventana)
        RECARGO_FIJO: Dict[Decimal, FrozenSet[Decimal]] = {
            Decimal("21"): frozenset(map(Decimal, ("5.2", "1.75"))),
            Decimal("10"): frozenset(map(Decimal, ("1.4",))),
            Decimal("7.5"): frozenset(map(Decimal, ("1",))),
            Decimal("4"): frozenset(map(Decimal, ("0.5",))),
            Decimal("2"): frozenset(map(Decimal, ("0.26",))),
            Decimal("0"): frozenset(map(Decimal, ("0",))),
        }

        # recargos para tipo 5 según fecha
        def recargos_tipo5(fecha: date) -> frozenset[Decimal]:
            if fecha <= FECHA_31_DIC_2022:
                return frozenset((Decimal("0.5"),))
            if fecha <= FECHA_30_SEP_2024:
                return frozenset((Decimal("0.62"),))
            return frozenset((Decimal("0.62"),))  # post 30-09-2024

        # --- lógica ---
        fecha_efectiva = self.fecha_operacion or self.fecha_expedicion

        for ln in self.lineas:
            ti = ln.tipo_impositivo
            tr = ln.tipo_recargo_equivalencia
            imp = ln.impuesto or "01"  # si no viene se considera IVA
            calif = ln.calificacion_operacion
            bcoste = ln.base_imponible_a_coste

            # 1. tipo_impositivo obligatorio si S1 y sin base_imponible_a_coste
            if calif == CalificacionOperacionType.S1 and bcoste is None and ti is None:
                raise ValueError(
                    "tipo_impositivo es obligatorio cuando calificacion_operacion='S1' "
                    "y base_imponible_a_coste no está cumplimentado."
                )

            # 2. valores permitidos si impuesto = 01 (IVA)
            if (
                imp == ImpuestoType.VALUE_01
                and ti is not None
                and ti not in TIPOS_IMPOSITIVOS_OK
            ):
                raise ValueError(
                    f"tipo_impositivo no permitido para IVA: {ti}. "
                    f"Válidos: {sorted(map(str, TIPOS_IMPOSITIVOS_OK))}"
                )

            # 3. validar recargo
            if tr is None:
                continue

            # 3.a regla general S1 + IVA/IGIC
            if (
                imp in {ImpuestoType.VALUE_01, ImpuestoType.VALUE_03}
                and calif == CalificacionOperacionType.S1
                and tr not in RECARGOS_S1
            ):
                raise ValueError(
                    f"TipoRecargoEquivalencia {tr} no permitido para IVA/IGIC S1. "
                    f"Válidos: {sorted(map(str, RECARGOS_S1))}"
                )

            # 3.b por tipo_impositivo
            if ti is None:
                continue

            # elegir lista permitida
            if ti == Decimal("5"):
                if fecha_efectiva is None:
                    raise ValueError(
                        "Se requiere fecha_operacion/fecha_expedicion para validar "
                        "recargo con tipo_impositivo 5"
                    )
                permitidos = recargos_tipo5(fecha_efectiva)
            else:
                permitidos = RECARGO_FIJO.get(ti, frozenset())

            if tr not in permitidos:
                raise ValueError(
                    f"Para tipo_impositivo {ti} solo se permiten "
                    f"{', '.join(map(str, permitidos))} en TipoRecargoEquivalencia"
                )

        return self
