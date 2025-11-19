from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class ObligadoTributario(Base):
    __tablename__ = "obligados_tributarios"

    id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
    )
    nif: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True
    )
    nombre_razon_social: Mapped[str] = mapped_column(String(255), nullable=False)
    activo: Mapped[bool] = mapped_column(default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )

    cert_subject: Mapped[str | None] = mapped_column(String(500))
    cert_serial: Mapped[str | None] = mapped_column(String(100))
    cert_valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class APIKey(Base):
    """API Keys para autenticación de SIFs"""

    __tablename__ = "api_keys"

    id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
    )
    key_hash: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )  # SHA256 del key
    nif: Mapped[str] = mapped_column(
        ForeignKey("obligados_tributarios.nif"), nullable=False
    )
    nombre: Mapped[str | None] = mapped_column(
        String(100)
    )  # Identificador amigable del SIF
    activa: Mapped[bool] = mapped_column(default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (Index("idx_api_keys_nif_activa", "nif", "activa"),)


class RegistroFacturacion(Base):
    """Registros de facturación enviados por los SIFs

    Attributes:
        id (uuid.UUID): Identificador único del registro.
        nif_emisor (str): NIF del emisor de la factura.
        sistema_informatico (str | None): Nombre del SIF que generó la factura.
        serie (str): Serie de la factura.
        numero (str): Número de la factura.
        fecha_expedicion (datetime.date): Fecha de expedición de la factura.
        fecha_operacion (datetime.date | None): Fecha de la operación (si aplica).
        operacion (str): Tipo de operación.
        tipo_factura (str): Código del tipo de factura (p. ej., "F1").
        factura_json (dict): Contenido de la factura en formato JSON.
        importe_total (decimal.Decimal | None): Importe total de la factura.
        cuota_total (decimal.Decimal | None): Cuota total del IVA.
        descripcion (str | None): Descripción de la factura.
        huella (str): Huella única de la factura.
        huella_anterior (str | None): Huella de la factura anterior (en cadenas).
        xml_generado (str | None): XML enviado a la AEAT.
        xml_respuesta (str | None): XML de respuesta de la AEAT.
        qr_data (str | None): Datos codificados en el QR.
        estado (str): Estado actual del registro (p. ej., "pendiente", "enviado").
        csv (str | None): Referencia al archivo CSV asociado.
        respuesta_aeat (dict | None): Respuesta estructurada de la AEAT.
        codigo_error (str | None): Código de error devuelto por la AEAT.
        mensaje_error (str | None): Mensaje descriptivo del error.
        intentos_envio (int): Número de intentos de envío a la AEAT.
        ultimo_intento_at (datetime.datetime | None): Fecha y hora del último intento.
        created_at (datetime.datetime): Fecha y hora de creación del registro.
        updated_at (datetime.datetime | None): Fecha hora de la última actualización.
        enviado_aeat_at (datetime.datetime | None): Fecha hora de envío OK a la AEAT.
    """

    __tablename__ = "registros_facturacion"

    id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
    )

    nif_emisor: Mapped[str] = mapped_column(
        ForeignKey("obligados_tributarios.nif"), nullable=False, index=True
    )
    sistema_informatico: Mapped[str | None] = mapped_column(
        String(50)
    )  # Identificador del SIF (opcional)

    # Identificación de la factura (clave compuesta)
    serie: Mapped[str] = mapped_column(String(60), nullable=False)
    numero: Mapped[str] = mapped_column(String(60), nullable=False)
    fecha_expedicion: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_operacion: Mapped[date | None] = mapped_column(Date)

    # Tipo de operación y factura
    operacion: Mapped[str] = mapped_column(String(50), default="Alta", nullable=False)
    # Valores: Alta, Subsanacion, Anulacion, Alta (rechazo previo), etc.
    tipo_factura: Mapped[str] = mapped_column(
        String(2), nullable=False
    )  # F1, F2, R1, R2, R3, R4, R5, F3

    # Datos JSON completos
    factura_json: Mapped[dict] = mapped_column(
        postgresql.JSONB, nullable=False
    )  # JSON original del SIF

    # Datos económicos (desnormalizados para consultas rápidas)
    importe_total: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    cuota_total: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    descripcion: Mapped[str | None] = mapped_column(Text)

    # Huella y firma
    huella: Mapped[str] = mapped_column(
        String(128), index=True, nullable=False
    )  # SHA-256 hex
    huella_anterior: Mapped[str | None] = mapped_column(
        String(128)
    )  # Para encadenamiento
    xml_generado: Mapped[str | None] = mapped_column(Text)  # XML firmado enviado a AEAT
    xml_respuesta: Mapped[str | None] = mapped_column(Text)  # XML de respuesta de AEAT
    qr_data: Mapped[str | None] = mapped_column(Text)  # URL del QR

    # Estado de envío a AEAT
    estado: Mapped[str] = mapped_column(
        String(50), default="pendiente_envio", nullable=False, index=True
    )
    # Estados: pendiente_envio, enviando, correcto, aceptado_con_errores,
    #          incorrecto, duplicado, anulado, factura_inexistente,
    #          no_registrado, error_servidor_aeat

    csv: Mapped[str | None] = mapped_column(
        String(100)
    )  # CSV devuelto por AEAT cuando aceptado
    respuesta_aeat: Mapped[dict | None] = mapped_column(
        postgresql.JSONB
    )  # Respuesta completa parseada de AEAT

    # Códigos de error
    codigo_error: Mapped[str | None] = mapped_column(String(20))
    mensaje_error: Mapped[str | None] = mapped_column(Text)

    # Control de envíos
    intentos_envio: Mapped[int] = mapped_column(default=0)
    ultimo_intento_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )
    enviado_aeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        Index("idx_registros_nif_fecha", "nif_emisor", "fecha_expedicion"),
        Index("idx_registros_estado", "estado"),
        Index(
            "idx_registros_factura_unica",
            "nif_emisor",
            "serie",
            "numero",
            "fecha_expedicion",
        ),
        Index("idx_registros_operacion", "operacion"),
    )


class Webhook(Base):
    """Webhooks configurados por los obligados tributarios"""

    __tablename__ = "webhooks"

    id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
    )
    nif: Mapped[str] = mapped_column(
        ForeignKey("obligados_tributarios.nif"), nullable=False
    )
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    # Lista de eventos soportados ["registro.correcto", "registro.incorrecto"]
    eventos: Mapped[list[str]] = mapped_column(postgresql.JSONB, nullable=False)
    activo: Mapped[bool] = mapped_column(default=True, nullable=False)
    secret: Mapped[Optional[str]] = mapped_column(
        String(64)
    )  # Para firmar payload HMAC
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (Index("idx_webhooks_nif_activo", "nif", "activo"),)


class EventoWebhook(Base):
    """Log de eventos de webhook enviados"""

    __tablename__ = "eventos_webhook"

    id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
    )
    webhook_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), ForeignKey("webhooks.id"), nullable=False
    )
    registro_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        ForeignKey("registros_facturacion.id"),
        nullable=False,
    )

    evento: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # "registro.correcto"
    # Payload enviado a webhooks
    payload: Mapped[dict | list] = mapped_column(postgresql.JSONB, nullable=False)

    # Estado del envío
    estado: Mapped[str] = mapped_column(String(50), default="pendiente", nullable=False)
    # Estados: pendiente, enviado, error
    intentos: Mapped[int] = mapped_column(Integer, default=0)
    http_status: Mapped[Optional[int]] = mapped_column(Integer)
    respuesta: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    enviado_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        Index("idx_eventos_estado", "estado"),
        Index("idx_eventos_webhook", "webhook_id"),
    )
