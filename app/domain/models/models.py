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
    registros: Mapped[List["RegistroFacturacion"]] = relationship(
        back_populates="instalacion_sif",
    )
    lotes_envio: Mapped[list["LoteEnvio"]] = relationship(
        "LoteEnvio",
        back_populates="instalacion_sif",
        lazy="dynamic",  # Para no cargar todos los lotes automáticamente
    )
    # ===== CONTROL DE FLUJO AEAT =====
    ultimo_tiempo_espera: Mapped[int] = mapped_column(
        Integer,
        default=60,  # Valor inicial según documentación AEAT
        nullable=False,
        comment="Último valor 't' recibido de AEAT (en segundos)",
    )
    ultimo_envio_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="Fecha/hora del último envío exitoso a AEAT"
    )
    registros_pendientes: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Contador de registros PENDIENTES/ENCOLADOS para esta instalación",
    )

    __table_args__ = (
        # Índice para workers de envío
        Index(
            "idx_instalacion_para_worker",
            "ultimo_envio_at",
            "ultimo_tiempo_espera",
            "registros_pendientes",
            postgresql_where=text("registros_pendientes > 0"),
        ),
    )

    def __repr__(self) -> str:
        return f"<InstalacionSIF obligado_nif={self.obligado.nif}>"


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
    """
    Estados del lote de envío a AEAT.

    Ciclo de vida:
    1. CREADO: Lote creado, OutboxEvent pendiente
    2. ENCOLADO: OutboxEvent enviado a worker AEAT
    3. ENVIANDO: Worker procesando (opcional, para observabilidad)
    4. CORRECTO: AEAT aceptó todos los registros
    5. PARCIALMENTE_CORRECTO: AEAT aceptó algunos, rechazó otros
    6. INCORRECTO: AEAT rechazó todos los registros
    7. ERROR: Error técnico (timeout, conexión, etc.)
    8. ERROR_REINTENTABLE: Error 5xx, se reintentará.
    """

    # ========================================================================
    # ESTADOS PRE-ENVÍO (internos)
    # ========================================================================
    CREADO = "Creado"  # Lote creado, esperando dispatcher
    ENCOLADO = "Encolado"  # Dispatcher envió a worker AEAT
    ENVIANDO = "Enviando"  # Worker procesando (opcional)

    # ========================================================================
    # ESTADOS POST-ENVÍO (de AEAT, alineados con EstadoEnvioType del XSD)
    # ========================================================================
    # Todos los registros de facturación de la remisión tienen estado “Correcto”
    CORRECTO = "Correcto"
    # Algunos registros de la remisión tienen estado “Incorrecto” o “AceptadoConErrores”
    PARCIALMENTE_CORRECTO = "ParcialmenteCorrecto"
    # Todos los registros de la remisión tienen estado “Incorrecto”
    INCORRECTO = "Incorrecto"

    # ========================================================================
    # ESTADOS DE ERROR (técnicos, no de negocio)
    # ========================================================================
    ERROR = "Error"  # Error técnico (timeout, conexión, XML inválido, etc.)
    ERROR_REINTENTABLE = "ErrorReintentable"  # Error 5xx, se reintentará


class EstadoOutboxEvent(str, enum.Enum):
    """Estados del evento en el outbox"""

    PENDIENTE = "pendiente"  # Creado, esperando dispatch
    ENCOLADO = "encolado"  # Enviado a cola Celery
    PROCESADO = "procesado"  # Worker AEAT completó exitosamente
    ERROR = "error"  # Falló después de reintentos


class EstadoDuplicadoAEAT(str, enum.Enum):
    """
    Estados posibles de un registro duplicado en AEAT.

    Según L21 de especificación Veri*factu:
    - Correcta: Registro duplicado es correcto
    - AceptadaConErrores: Registro duplicado tiene errores
    - Anulada: Registro duplicado fue anulado
    """

    CORRECTA = "Correcta"
    ACEPTADA_CON_ERRORES = "AceptadaConErrores"
    ANULADA = "Anulada"


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
            create_type=True,
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        nullable=False,
        server_default=EstadoRegistroFacturacion.PENDIENTE.value,
        index=True,
    )

    # ===== COMUNICACIÓN CON AEAT =====
    xml_generado: Mapped[str | None] = mapped_column(Text)
    xml_respuesta_aeat: Mapped[str | None] = mapped_column(
        Text, comment="XML de RespuestaLinea de AEAT para este registro específico"
    )
    respuesta_aeat: Mapped[dict | None] = mapped_column(postgresql.JSONB)

    intentos_envio: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ultimo_intento_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    enviado_aeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # ========================================================================
    # METADATA DE RESPUESTA AEAT
    # ========================================================================

    # Error general del registro
    aeat_codigo_error: Mapped[int | None] = mapped_column(Integer, nullable=True)
    aeat_descripcion_error: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )

    # ✅ Información de duplicado (si el registro fue rechazado por duplicado)
    aeat_duplicado_id_peticion: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="IdPeticion del registro ya existente en AEAT",
    )
    aeat_duplicado_estado: Mapped[EstadoDuplicadoAEAT | None] = mapped_column(
        Enum(
            EstadoDuplicadoAEAT,
            name="chk_estado_duplicado_aeat_type",
            create_type=True,
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
            comment="Estado del duplicado: Correcta, AceptadaConErrores, Anulada",
        ),
        nullable=True,
    )
    aeat_duplicado_codigo_error: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    aeat_duplicado_descripcion: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )

    lote_envio_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("lote_envio.id"),
        index=True,
        nullable=True,  # Puede ser NULL si aún no se ha enviado
    )
    # Relación 1:N con LoteEnvio
    lote_envio: Mapped["LoteEnvio | None"] = relationship(
        back_populates="registros", lazy="selectin"
    )

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
    registros: Mapped[list["RegistroFacturacion"]] = relationship(
        back_populates="lote_envio",
        lazy="selectin",
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
    estado: Mapped[EstadoLoteEnvio] = mapped_column(
        Enum(
            EstadoLoteEnvio,
            name="chk_estado_lote_envio_type",
            create_type=True,
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        nullable=False,
        server_default=EstadoLoteEnvio.CREADO,
        index=True,
    )
    csv_aeat: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment=(
            "Código Seguro de Verificación devuelto por AEAT (NULL si todos rechazados)"
        ),
    )
    # ========== RELACIONES ==========
    instalacion_sif: Mapped["InstalacionSIF"] = relationship(
        "InstalacionSIF",
        back_populates="lotes_envio",  # Opcional: si quieres acceso bidireccional
        lazy="joined",  # Carga automáticamente con el lote
    )
    # ===== CONTROL DE FLUJO =====
    tiempo_espera_recibido: Mapped[int | None] = mapped_column(
        Integer, comment="Valor 't' devuelto por AEAT en esta respuesta (en segundos)"
    )
    proximo_envio_permitido_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        comment="Fecha/hora calculada: created_at + tiempo_espera_recibido",
    )
    # ===== LÍMITES =====
    num_registros_enviados: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Número real de registros incluidos en este lote (máx 1000)",
    )


class OutboxEvent(Base):
    """
    Patrón Outbox: garantiza atomicidad lote ↔ evento.

    GARANTÍA CRÍTICA (Art. 12 Reglamento Veri*factu):
    - Lote + OutboxEvent se crean en la MISMA transacción
    - Si commit falla → NINGUNO persiste (SIN HUÉRFANOS)
    - Si commit OK → SIEMPRE hay evento para procesar el lote
    - Respeta orden FIFO por created_at (cadena hash inviolable)

    Ciclo de vida:
    1. PENDIENTE: Creado junto al lote (orquestador)
    2. ENCOLADO: Dispatcher envió a worker AEAT
    3. PROCESADO: Worker AEAT completó exitosamente
    4. ERROR: Falló después de todos los reintentos
    """

    __tablename__ = "outbox_event"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, autoincrement=True
    )

    # Relación con lote (FK)
    lote_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        ForeignKey("lote_envio.id"),
        nullable=False,
        index=True,
    )

    # Instalación (para filtrado rápido)
    instalacion_sif_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("instalacion_sif.id"),
        nullable=False,
        index=True,
    )

    # Estado del evento
    estado: Mapped[EstadoOutboxEvent] = mapped_column(
        Enum(
            EstadoOutboxEvent,
            name="chk_estado_outbox_event_type",
            create_type=True,
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        nullable=False,
        server_default=EstadoOutboxEvent.PENDIENTE,
        index=True,  # Índice crítico para SELECT WHERE estado='pendiente'
    )

    # Task name de Celery (para dispatch)
    task_name: Mapped[str] = mapped_column(
        String, nullable=False, default="app.tasks.worker_aeat.enviar_lote_aeat"
    )

    # Payload (normalmente solo lote_id)
    payload: Mapped[str] = mapped_column(
        String, nullable=False
    )  # JSON string: {"lote_id": 123}

    # Contadores de reintentos
    intentos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_intentos: Mapped[int] = mapped_column(Integer, nullable=False, default=10)

    # Timestamps (CRÍTICO: created_at define orden FIFO)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,  # Índice crítico para ORDER BY created_at
    )

    # Último intento (para debugging)
    ultimo_intento_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Procesado exitosamente
    procesado_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Error final (si estado=ERROR)
    error_mensaje: Mapped[str] = mapped_column(String(500), nullable=True)

    __table_args__ = (
        # ÍNDICE OPTIMIZADO PARA POLLING FIFO
        Index(
            "idx_outbox_polling_fifo",
            "created_at",  # 1. Primer criterio de ordenamiento
            "id",  # 2. Segundo criterio (desempate determinista)
            postgresql_where=text("estado = 'pendiente'"),  # Filtro parcial
        ),
        # Índice para ver historial por instalación (útil para UI/Debug)
        Index("idx_outbox_instalacion_estado", "instalacion_sif_id", "estado"),
    )

    def __repr__(self) -> str:
        return (
            f"<OutboxEvent(id={self.id}, lote_id={self.lote_id}, "
            f"estado={self.estado}, created_at={self.created_at})>"
        )
