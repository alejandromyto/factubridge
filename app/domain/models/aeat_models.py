from __future__ import annotations

import enum
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    DECIMAL,
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.domain.models.models import Base, InstalacionSIF


class EstadoRegistroFacturacion(str, enum.Enum):
    PENDIENTE = "pendiente"  # registrado y persistido
    ENCOLADO = "encolado"  # en espera de envío
    CORRECTO = "correcto"
    ACEPTADO_CON_ERRORES = "aceptado_con_errores"
    INCORRECTO = "incorrecto"
    DUPLICADO = "duplicado"
    ANULADO = "anulado"
    FACTURA_INEXISTENTE = "factura_inexistente"
    NO_REGISTRADO = "no_registrado"
    ERROR_SERVIDOR_AEAT = "error_servidor_aeat"


class EstadoLoteEnvio(str, enum.Enum):
    PENDIENTE = "pendiente"
    PROCESADO = "procesando"
    ENVIADO = "enviado"
    ERROR_PARCIAL = "error_parcial"
    ERROR_TOTAL = "error_total"
    COMPLETADO = "completado"


class RegistroFacturacion(Base):
    """
    Registros de facturación recibidos desde los SIFs y enviados a AEAT.

    Cada registro representa una factura que:
    1. Llega desde el SIF del obligado tributario
    2. Se valida y procesa
    3. Se envía a AEAT (con posibles reintentos)
    """

    __tablename__ = "registro_facturacion"

    id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
    )

    # ===== para nif del obligado: instalacion_sif.obligado.nif =====
    instalacion_sif_id: Mapped[int] = mapped_column(
        ForeignKey("instalacion_sif.id"), nullable=False, index=True
    )
    emisor_nif: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    # Razón social en el momento de la emisión (por si cambia en el futuro)
    emisor_nombre: Mapped[str | None] = mapped_column(String(120))
    # ===== IDENTIFICACIÓN DE LA FACTURA =====
    serie: Mapped[str] = mapped_column(String(50), nullable=False)
    numero: Mapped[str] = mapped_column(String(50), nullable=False)
    fecha_expedicion: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_operacion: Mapped[date | None] = mapped_column(Date)
    destinatario_nif: Mapped[str | None] = mapped_column(String(20))
    destinatario_nombre: Mapped[str | None] = mapped_column(String(255))

    # F1, F2, etc.
    tipo_factura: Mapped[str] = mapped_column(String(10), nullable=False)
    tipo_rectificativa: Mapped[str | None] = mapped_column(String(1))
    operacion: Mapped[str] = mapped_column(String(255), nullable=False)
    # <element name="DescripcionOperacion" type="sf:TextMax500Type"/>
    descripcion: Mapped[str | None] = mapped_column(String(500))

    importe_total: Mapped[Decimal] = mapped_column(DECIMAL(precision=15, scale=2))
    cuota_total: Mapped[Decimal] = mapped_column(DECIMAL(precision=15, scale=2))

    # ===== CONTENIDO COMPLETO =====
    factura_json: Mapped[dict] = mapped_column(postgresql.JSONB, nullable=False)

    # ===== ENCADENAMIENTO Y SEGURIDAD =====
    huella: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True
    )
    anterior_huella: Mapped[str | None] = mapped_column(
        String(64), index=True, unique=True, nullable=True
    )
    anterior_emisor_nif: Mapped[str | None] = mapped_column(String(20))
    anterior_serie: Mapped[str | None] = mapped_column(String(50))
    anterior_numero: Mapped[str | None] = mapped_column(String(50))
    anterior_fecha_expedicion: Mapped[date | None] = mapped_column(Date)
    # ===== QR =====
    qr_data: Mapped[str | None] = mapped_column(Text)

    # ===== ESTADO Y CONTROL =====
    estado: Mapped[EstadoRegistroFacturacion] = mapped_column(
        Enum(
            EstadoRegistroFacturacion,
            name="chk_estado_registro_type",
            create_type=False,
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        nullable=False,
        server_default=EstadoRegistroFacturacion.PENDIENTE.value,
        index=True,
    )

    # ===== COMUNICACIÓN CON AEAT =====
    xml_generado: Mapped[str | None] = mapped_column(Text)
    xml_respuesta: Mapped[str | None] = mapped_column(Text)
    respuesta_aeat: Mapped[dict | None] = mapped_column(postgresql.JSONB)

    codigo_error: Mapped[str | None] = mapped_column(String(50))
    mensaje_error: Mapped[str | None] = mapped_column(Text)

    intentos_envio: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ultimo_intento_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    enviado_aeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # ===== FLAGS DE PROCESO (CRÍTICOS PARA LA API) =====
    # NEW: Necesario para endpoint /modify y /cancel
    # rechazo_previo: Mapped[str] = mapped_column(String(1),
    # server_default="N", nullable=False) # 'N', 'S', 'X'
    # NEW: Necesario para endpoint /cancel
    # sin_registro_previo: Mapped[str] = mapped_column(String(1),
    # server_default="N", nullable=False) # 'N', 'S'
    # NEW: Marca de incidencia (flag "S")
    # incidencia: Mapped[str] = mapped_column(String(1),
    # server_default="N", nullable=False)

    # ===== TIMESTAMPS =====
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )

    # ===== RELACIONES =====
    instalacion_sif: Mapped[InstalacionSIF] = relationship(
        "InstalacionSIF",
        back_populates="registros",
        lazy="selectin",  # ← Carga en batch cuando accedas a instalacion_sif
    )
    # No como relación directa 1-N mapeada, sino como relación lógica consultable para
    # evitar cargas innecesarias
    # envios_aeat: Mapped[List["EnvioAEAT"]] = relationship(
    #     back_populates="registro_facturacion",
    #     order_by="EnvioAEAT.created_at.desc()",
    # )
    lotes_envio: Mapped[list["LoteEnvio"]] = relationship(
        secondary="lote_envio_registro", back_populates="registros"
    )

    __table_args__ = (
        # Índice compuesto para búsquedas frecuentes
        Index(
            "idx_registro_instalacion_fecha", "instalacion_sif_id", "fecha_expedicion"
        ),
        Index("idx_registro_estado_created", "estado", "created_at"),
        # Unicidad: misma factura no puede existir dos veces en la misma instalación
        UniqueConstraint(
            "instalacion_sif_id",
            "serie",
            "numero",
            "fecha_expedicion",
            name="uq_factura_instalacion",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<RegistroFacturacion {self.serie}-{self.numero} "
            f"estado={self.estado} huella={self.huella[:8]}...>"
        )


class EnvioAEAT(Base):
    """Intento de envío técnico a AEAT. (puede haber reintentos del mismo lote)"""

    __tablename__ = "envio_aeat"

    id: Mapped[int] = mapped_column(primary_key=True)
    lote_envio_id: Mapped[UUID] = mapped_column(ForeignKey("lote_envio.id"), index=True)

    # Mantiene el historial pero evita acoplarlo al modelo principal
    registro_facturacion_id: Mapped[UUID] = mapped_column(
        ForeignKey("registro_facturacion.id"), index=True
    )
    intento: Mapped[int] = mapped_column(Integer, nullable=False)

    exitoso: Mapped[bool] = mapped_column(Boolean, nullable=False)
    codigo_respuesta: Mapped[str | None] = mapped_column(String(50))
    mensaje_respuesta: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relaciones
    # registro_facturacion: Mapped["RegistroFacturacion"] = relationship(
    #     back_populates="envios_aeat"
    # )
    def __repr__(self) -> str:
        return (
            f"<EnvioAEAT intento={self.intento} "
            f"exitoso={self.exitoso} at={self.created_at}>"
        )


class LoteEnvio(Base):
    __tablename__ = "lote_envio"

    id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
    )

    instalacion_sif_id: Mapped[int] = mapped_column(
        ForeignKey("instalacion_sif.id"), index=True
    )
    num_registros: Mapped[int] = mapped_column(Integer, nullable=False)

    xml_enviado: Mapped[str] = mapped_column(Text, nullable=False)
    xml_respuesta: Mapped[str | None] = mapped_column(Text)
    respuesta_json: Mapped[dict | None] = mapped_column(postgresql.JSONB)

    codigo_respuesta: Mapped[str | None] = mapped_column(String(50))
    mensaje_respuesta: Mapped[str | None] = mapped_column(Text)

    tiempo_respuesta_ms: Mapped[int | None] = mapped_column(Integer)
    endpoint_usado: Mapped[str] = mapped_column(String(500), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relaciones
    registros: Mapped[list["RegistroFacturacion"]] = relationship(
        secondary="lote_envio_registro",  # tabla puente
        back_populates="lotes_envio",
        lazy="selectin",
    )


lote_envio_registro = Table(
    "lote_envio_registro",
    Base.metadata,
    Column("lote_envio_id", ForeignKey("lote_envio.id"), primary_key=True),
    Column(
        "registro_facturacion_id",
        ForeignKey("registro_facturacion.id"),
        primary_key=True,
    ),
)
