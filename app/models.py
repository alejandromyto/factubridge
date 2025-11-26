from __future__ import annotations

import enum
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy import (
    DECIMAL,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class ColaboradorSocial(Base):
    """
    Entidad desarrolladora que actúa como colaborador social ante AEAT.

    Normalmente habrá un único registro.
    """

    __tablename__ = "colaborador_social"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    nif: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)

    software_name: Mapped[str] = mapped_column(String(255), nullable=False)
    software_version: Mapped[str] = mapped_column(String(50), nullable=False)

    certificate_path: Mapped[Optional[str]] = mapped_column(String(500))
    certificate_password: Mapped[Optional[str]] = mapped_column(String(255))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )

    # Relaciones
    obligados: Mapped[List["ObligadoTributario"]] = relationship(
        back_populates="colaborador"
    )


class ObligadoTributario(Base):
    """Cliente del colaborador social que emite facturas."""

    __tablename__ = "obligados_tributarios"

    id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
    )

    colaborador_id: Mapped[int] = mapped_column(
        ForeignKey("colaborador_social.id"), nullable=False, index=True
    )

    nif: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True
    )
    nombre_razon_social: Mapped[str] = mapped_column(String(255), nullable=False)
    activo: Mapped[bool] = mapped_column(default=True, nullable=False)

    # Certificado del obligado para firmar facturas
    cert_subject: Mapped[str | None] = mapped_column(String(500))
    cert_serial: Mapped[str | None] = mapped_column(String(100))
    cert_valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )

    # Relaciones
    colaborador: Mapped[ColaboradorSocial] = relationship(back_populates="obligados")
    instalaciones_sif: Mapped[List["InstalacionSIF"]] = relationship(
        back_populates="obligado", cascade="all, delete-orphan"
    )


class InstalacionSIF(Base):
    """
    Instalación específica de un Sist. Inf. de Facturación para un Obligado Tributario.

    Ojo: si un cliente tiene varios obligados tributarios (OT) usando un solo
    despliegue (por ejemplo en un Xespropan), cada OT tendrá su propia instalación SIF
    pero compartirán el mismo cliente_id.
    - Control de secuencias de numeración de instalación. Aunque en la realidad sea el
     mismo despliegue para varios OT, cada OT tendrá su propia secuencia de facturación.
    """

    __tablename__ = "instalaciones_sif"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    nombre_sistema_informatico: Mapped[str] = mapped_column(String(255), nullable=False)
    version_sistema_informatico: Mapped[str] = mapped_column(String(50), nullable=False)
    id_sistema_informatico: Mapped[str] = mapped_column(String(100), nullable=False)
    numero_instalacion: Mapped[str] = mapped_column(String(50), nullable=False)
    # Una panadería de Xespropan puede tener varios obligados tributarios (OT) usando un
    # solo despliegue Xespropan. Con este campo se identifica el cliente común
    cliente_id = mapped_column(String(50), index=True, nullable=True)
    # indicador_multiples_ot: si cliente tiene más de un obligado tributario en su SIF
    indicador_multiples_ot: Mapped[bool] = mapped_column(nullable=False, default=False)

    obligado_id: Mapped[UUID] = mapped_column(
        ForeignKey("obligados_tributarios.id"), nullable=False, index=True
    )

    # API Key única para que el SIF se autentique con este backend
    key_hash: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )

    # Certificado específico de esta instalación (opcional)
    certificate_path: Mapped[Optional[str]] = mapped_column(String(500))
    certificate_password: Mapped[Optional[str]] = mapped_column(String(255))

    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relaciones
    obligado: Mapped[ObligadoTributario] = relationship(
        "ObligadoTributario",
        back_populates="instalaciones_sif",
        lazy="selectin",  # ← Carga en batch al acceder a obligado
    )
    __table_args__ = (Index("idx_key_hash", "key_hash"),)

    def __repr__(self) -> str:
        return f"<InstalacionSIF obligado_nif={self.obligado.nif}>"


class EstadoRegistroFacturacion(str, enum.Enum):
    PENDIENTE = "pendiente"
    CORRECTO = "correcto"
    ACEPTADO_CON_ERRORES = "aceptado_con_errores"
    INCORRECTO = "incorrecto"
    DUPLICADO = "duplicado"
    ANULADO = "anulado"
    FACTURA_INEXISTENTE = "factura_inexistente"
    NO_REGISTRADO = "no_registrado"
    ERROR_SERVIDOR_AEAT = "error_servidor_aeat"


class RegistroFacturacion(Base):
    """
    Registros de facturación recibidos desde los SIFs y enviados a AEAT.

    Cada registro representa una factura que:
    1. Llega desde el SIF del obligado tributario
    2. Se valida y procesa
    3. Se envía a AEAT (con posibles reintentos)
    """

    __tablename__ = "registros_facturacion"

    id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
    )

    # ===== para nif del obligado: instalacion_sif.obligado.nif =====
    instalacion_sif_id: Mapped[int] = mapped_column(
        ForeignKey("instalaciones_sif.id"), nullable=False, index=True
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
            EstadoRegistroFacturacion, name="chk_estado_registro_type", create_type=True
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
    instalacion_sif: Mapped["InstalacionSIF"] = relationship(
        "InstalacionSIF",
        back_populates="registros",
        lazy="selectin",  # ← Carga en batch cuando accedas a instalacion_sif
    )
    envios_aeat: Mapped[List["EnvioAEAT"]] = relationship(
        back_populates="reg_facturacion",
        cascade="all, delete-orphan",
        order_by="EnvioAEAT.created_at.desc()",
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
    """
    Histórico de intentos de envío a la AEAT.

    Permite tracking completo de todos los intentos, útil para:
    - Debugging de errores
    - Auditoría
    - Análisis de problemas recurrentes
    """

    __tablename__ = "envios_aeat"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    registro_facturacion_id: Mapped[UUID] = mapped_column(
        ForeignKey("registros_facturacion.id"), nullable=False, index=True
    )

    # Número de intento (1, 2, 3...)
    intento_numero: Mapped[int] = mapped_column(Integer, nullable=False)

    # Request/Response completos
    xml_enviado: Mapped[str] = mapped_column(Text, nullable=False)
    xml_respuesta: Mapped[str | None] = mapped_column(Text)
    respuesta_json: Mapped[dict | None] = mapped_column(postgresql.JSONB)

    # Resultado
    exitoso: Mapped[bool] = mapped_column(Boolean, nullable=False)
    codigo_respuesta: Mapped[str | None] = mapped_column(String(50))
    mensaje_respuesta: Mapped[str | None] = mapped_column(Text)

    # Datos técnicos
    tiempo_respuesta_ms: Mapped[int | None] = mapped_column(Integer)
    endpoint_usado: Mapped[str] = mapped_column(String(500), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relación
    reg_facturacion: Mapped["RegistroFacturacion"] = relationship(
        back_populates="envios_aeat"
    )

    __table_args__ = (
        Index(
            "idx_envio_registro_intento", "registro_facturacion_id", "intento_numero"
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<EnvioAEAT intento={self.intento_numero} "
            f"exitoso={self.exitoso} at={self.created_at}>"
        )
