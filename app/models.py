from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class ObligadoTributario(Base):
    """Emisores autorizados (empresas/autónomos)"""

    __tablename__ = "obligados_tributarios"

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()")
    )
    nif = Column(String(20), unique=True, nullable=False, index=True)
    nombre_razon_social = Column(String(255), nullable=False)
    activo = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Certificado asociado (cuando lo tengamos)
    cert_subject = Column(String(500))
    cert_serial = Column(String(100))
    cert_valid_until = Column(DateTime(timezone=True))


class APIKey(Base):
    """API Keys para autenticación de SIFs"""

    __tablename__ = "api_keys"

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()")
    )
    key_hash = Column(
        String(64), unique=True, nullable=False, index=True
    )  # SHA256 del key
    nif = Column(String(20), ForeignKey("obligados_tributarios.nif"), nullable=False)
    nombre = Column(String(100))  # Identificador amigable del SIF
    activa = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used_at = Column(DateTime(timezone=True))

    __table_args__ = (Index("idx_api_keys_nif_activa", "nif", "activa"),)


class RegistroFacturacion(Base):
    """Registros de facturación enviados por los SIFs"""

    __tablename__ = "registros_facturacion"

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()")
    )
    nif_emisor = Column(
        String(20), ForeignKey("obligados_tributarios.nif"), nullable=False, index=True
    )
    sistema_informatico = Column(String(50))  # Identificador del SIF (opcional)

    # Identificación de la factura (clave compuesta)
    serie = Column(String(60), nullable=False)
    numero = Column(String(60), nullable=False)
    fecha_expedicion = Column(DateTime(timezone=True), nullable=False)
    fecha_operacion = Column(DateTime(timezone=True))

    # Tipo de operación y factura
    operacion = Column(String(50), default="Alta", nullable=False)
    # Valores: Alta, Subsanacion, Anulacion, Alta (rechazo previo), etc.
    tipo_factura = Column(String(2), nullable=False)  # F1, F2, R1, R2, R3, R4, R5, F3

    # Datos JSON completos
    factura_json = Column(JSONB, nullable=False)  # JSON original del SIF

    # Datos económicos (desnormalizados para consultas rápidas)
    importe_total = Column(Numeric(14, 2))
    cuota_total = Column(Numeric(14, 2))
    descripcion = Column(Text)

    # Huella y firma
    huella = Column(String(128), index=True)  # SHA-256 hex
    huella_anterior = Column(String(128))  # Para encadenamiento
    xml_generado = Column(Text)  # XML firmado enviado a AEAT
    xml_respuesta = Column(Text)  # XML de respuesta de AEAT
    qr_data = Column(Text)  # URL del QR

    # Estado de envío a AEAT
    estado = Column(String(50), default="pendiente_envio", nullable=False, index=True)
    # Estados: pendiente_envio, enviando, correcto, aceptado_con_errores,
    #          incorrecto, duplicado, anulado, factura_inexistente, no_registrado, error_servidor_aeat

    csv = Column(String(100))  # CSV devuelto por AEAT cuando aceptado
    respuesta_aeat = Column(JSONB)  # Respuesta completa parseada de AEAT

    # Códigos de error
    codigo_error = Column(String(20))
    mensaje_error = Column(Text)

    # Control de envíos
    intentos_envio = Column(Integer, default=0)
    ultimo_intento_at = Column(DateTime(timezone=True))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    enviado_aeat_at = Column(DateTime(timezone=True))

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

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()")
    )
    nif = Column(String(20), ForeignKey("obligados_tributarios.nif"), nullable=False)
    url = Column(String(500), nullable=False)
    eventos = Column(
        JSONB, nullable=False
    )  # ["registro.correcto", "registro.incorrecto"]
    activo = Column(Boolean, default=True, nullable=False)
    secret = Column(String(64))  # Para firmar payload HMAC
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (Index("idx_webhooks_nif_activo", "nif", "activo"),)


class EventoWebhook(Base):
    """Log de eventos de webhook enviados"""

    __tablename__ = "eventos_webhook"

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()")
    )
    webhook_id = Column(UUID(as_uuid=True), ForeignKey("webhooks.id"), nullable=False)
    registro_id = Column(
        UUID(as_uuid=True), ForeignKey("registros_facturacion.id"), nullable=False
    )

    evento = Column(String(50), nullable=False)  # "registro.correcto"
    payload = Column(JSONB, nullable=False)

    # Estado del envío
    estado = Column(String(50), default="pendiente", nullable=False)
    # Estados: pendiente, enviado, error

    intentos = Column(Integer, default=0)
    http_status = Column(Integer)
    respuesta = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    enviado_at = Column(DateTime(timezone=True))

    __table_args__ = (
        Index("idx_eventos_estado", "estado"),
        Index("idx_eventos_webhook", "webhook_id"),
    )
