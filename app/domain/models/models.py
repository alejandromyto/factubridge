from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    text,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.domain.models.aeat_models import RegistroFacturacion


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

    __tablename__ = "obligado_tributario"

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
        back_populates="obligado"
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

    __tablename__ = "instalacion_sif"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    nombre_sistema_informatico: Mapped[str] = mapped_column(String(255), nullable=False)
    version_sistema_informatico: Mapped[str] = mapped_column(String(50), nullable=False)
    id_sistema_informatico: Mapped[str] = mapped_column(String(100), nullable=False)
    numero_instalacion: Mapped[str] = mapped_column(String(50), nullable=False)
    # Una panadería de Xespropan puede tener varios obligados tributarios (OT) usando un
    # solo despliegue Xespropan. Con este campo se identifica el cliente común
    cliente_id: Mapped[Optional[str]] = mapped_column(
        String(50), index=True, nullable=True
    )
    # indicador_multiples_ot: si cliente tiene más de un obligado tributario en su SIF
    indicador_multiples_ot: Mapped[bool] = mapped_column(nullable=False, default=False)

    obligado_id: Mapped[UUID] = mapped_column(
        ForeignKey("obligado_tributario.id"), nullable=False, index=True
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
    registros: Mapped[List[RegistroFacturacion]] = relationship(
        back_populates="instalacion_sif",
    )
    __table_args__ = (Index("idx_key_hash", "key_hash"),)

    def __repr__(self) -> str:
        return f"<InstalacionSIF obligado_nif={self.obligado.nif}>"
