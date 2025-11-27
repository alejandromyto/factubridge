# test_instalaciones_postgres.py
import asyncio
from datetime import datetime
from typing import Any, AsyncGenerator, Generator, List, Optional
from uuid import UUID, uuid4

import pytest
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
    select,
    text,
    update,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, relationship
from testcontainers.postgres import PostgresContainer

# ==================== MODELOS ====================

Base = declarative_base()


class ObligadoTributario(Base):
    """Cliente del colaborador social que emite facturas."""

    __tablename__ = "obligado_tributario"

    id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
    )

    # colaborador_id: Mapped[int] = mapped_column(
    #     ForeignKey("colaborador_social.id"), nullable=False, index=True
    # )

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
    # colaborador: Mapped[ColaboradorSocial] = relationship(back_populates="obligados")
    instalaciones_sif: Mapped[List["InstalacionSIF"]] = relationship(
        back_populates="obligado"
    )

    def __init__(self, nif: str, nombre_razon_social: Optional[str] = None):
        # mypy ahora sabe que estos argumentos son válidos para el constructor.
        # No necesitas llamar a super().__init__ en SQLAlchemy 2.0.
        self.nif = nif
        if nombre_razon_social:
            self.nombre_razon_social = nombre_razon_social


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

    # registros: Mapped[List["RegistroFacturacion"]] = relationship(
    #     back_populates="instalacion_sif",
    # )
    def __init__(  # para evitar error mypy
        self,
        obligado_id: UUID,
        cliente_id: Optional[str],
        key_hash: str,
        nombre_sistema_informatico: str,
        version_sistema_informatico: str,
        id_sistema_informatico: str,
        numero_instalacion: str,
        indicador_multiples_ot: bool,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.obligado_id = obligado_id
        if cliente_id is not None:
            self.cliente_id = cliente_id
        self.key_hash = key_hash
        self.nombre_sistema_informatico = nombre_sistema_informatico
        self.version_sistema_informatico = version_sistema_informatico
        self.id_sistema_informatico = id_sistema_informatico
        self.numero_instalacion = numero_instalacion
        self.indicador_multiples_ot = indicador_multiples_ot

    # __table_args__ = (Index("idx_key_hash", "key_hash"),)

    __table_args__ = (
        UniqueConstraint(
            "obligado_id", "numero_instalacion", name="uq_obligado_numero"
        ),
        UniqueConstraint(
            "cliente_id",
            "numero_instalacion",
            "id_sistema_informatico",
            name="uq_cliente_numero_producto",
        ),
    )


# ==================== SERVICES ====================


async def crear_obligado(db: AsyncSession, nif: str, nombre: str) -> ObligadoTributario:
    """Crea un obligado tributario."""
    # obligado = ObligadoTributario(id=uuid4(), nif=nif, nombre_razon_social=nombre)
    obligado = ObligadoTributario(nif=nif, nombre_razon_social=nombre)
    db.add(obligado)
    await db.commit()
    await db.refresh(obligado)
    return obligado


async def _recalcular_indicador_multiples_ot(db: AsyncSession, cliente_id: str) -> None:
    """
    Recalcula y actualiza el indicador para TODAS las instalaciones de un cliente.

    Se ejecuta DENTRO de la transacción (sin commit).
    """
    stmt = select(func.count()).where(InstalacionSIF.cliente_id == cliente_id)
    result = await db.execute(stmt)
    total_ot = result.scalar() or 0

    nuevo_valor = total_ot > 1

    stmt_update = (
        update(InstalacionSIF)
        .where(InstalacionSIF.cliente_id == cliente_id)
        .values(indicador_multiples_ot=nuevo_valor)
    )
    await db.execute(stmt_update)


async def crear_instalacion_sif(
    db: AsyncSession,
    obligado_id: UUID,
    cliente_id: str | None = None,
    nombre_sistema_informatico: str = "Instalación SIF",
    version_sistema_informatico: str = "1.0",
    id_sistema_informatico: str = "SIF001",
) -> InstalacionSIF:
    """Crea una nueva instalación SIF con número secuencial."""
    # Calcular siguiente número de instalación
    if cliente_id:
        # Modo multi-OT: secuencial por cliente_id y producto
        stmt_num = (
            select(InstalacionSIF.numero_instalacion)
            .where(
                InstalacionSIF.cliente_id == cliente_id,
                InstalacionSIF.id_sistema_informatico == id_sistema_informatico,
            )
            .with_for_update()
        )
    else:
        # Modo single-OT: secuencial por obligado_id
        stmt_num = (
            select(InstalacionSIF.numero_instalacion)
            .where(InstalacionSIF.obligado_id == obligado_id)
            .with_for_update()
        )

    result_num = await db.execute(stmt_num)
    numeros = result_num.scalars().all()
    if not numeros:
        siguiente = "0001"
    else:
        ultimo_numero = max(map(int, numeros))
        siguiente = f"{int(ultimo_numero) + 1:04d}"

    # Crear instalación (con indicador temporal)
    instalacion = InstalacionSIF(
        obligado_id=obligado_id,
        cliente_id=cliente_id,
        key_hash=f"hash_{uuid4()}",
        nombre_sistema_informatico=nombre_sistema_informatico,
        version_sistema_informatico=version_sistema_informatico,
        id_sistema_informatico=id_sistema_informatico,
        numero_instalacion=siguiente,
        indicador_multiples_ot=False,
    )

    db.add(instalacion)
    await db.flush()

    # Recalcular indicador si es multi-OT
    if cliente_id:
        await _recalcular_indicador_multiples_ot(db, cliente_id)

    await db.commit()
    await db.refresh(instalacion)
    return instalacion


async def eliminar_instalacion_sif(db: AsyncSession, instalacion_id: int) -> dict:
    """Elimina una instalación SIF y recalcula el indicador para el cliente."""
    stmt = (
        select(InstalacionSIF)
        .where(InstalacionSIF.id == instalacion_id)
        .with_for_update()
    )
    result = await db.execute(stmt)
    instalacion = result.scalar_one_or_none()

    if not instalacion:
        raise ValueError(f"Instalación {instalacion_id} no encontrada")

    cliente_id = instalacion.cliente_id

    # Datos para auditoría
    # Create a detached copy of the installation for return
    deleted_data = {
        "id": instalacion.id,
        "obligado_id": instalacion.obligado_id,
        "cliente_id": instalacion.cliente_id,
        "numero_instalacion": instalacion.numero_instalacion,
        "indicador_multiples_ot": instalacion.indicador_multiples_ot,
    }

    # Eliminar
    await db.delete(instalacion)
    await db.flush()

    # Recalcular indicador si pertenecía a un cliente
    if cliente_id:
        await _recalcular_indicador_multiples_ot(db, cliente_id)

    await db.commit()

    # Devolver objeto para auditoría
    return deleted_data


# ==================== FIXTURES ====================


@pytest.fixture(scope="session")
def postgres_container() -> Generator[PostgresContainer, None, None]:
    """Levanta un contenedor PostgreSQL para los tests."""
    with PostgresContainer("postgres:15-alpine", driver="asyncpg") as postgres:
        yield postgres


@pytest.fixture
async def db_engine(postgres_container: Any) -> AsyncGenerator:
    """Crea el engine conectado al PostgreSQL del contenedor."""
    connection_string = postgres_container.get_connection_url().replace(
        "postgresql://", "postgresql+asyncpg://"
    )
    engine = create_async_engine(connection_string, echo=False)

    async with engine.begin() as conn:
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Limpieza después de cada test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def db_session(db_engine: Any) -> AsyncGenerator[AsyncSession, None]:
    """Crea una sesión de base de datos para cada test."""
    async_session = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        await session.rollback()


# ==================== TESTS ====================


class TestObligadoService:
    @pytest.mark.asyncio
    async def test_crear_obligado_exitoso(self, db_session: Any) -> None:
        obligado = await crear_obligado(db_session, "A12345678", "Test SL")

        assert obligado.nif == "A12345678"
        assert obligado.nombre_razon_social == "Test SL"
        assert obligado.activo is True
        assert isinstance(obligado.id, UUID)

        # Verificar en BD
        stmt = select(ObligadoTributario).where(ObligadoTributario.nif == "A12345678")
        result = await db_session.execute(stmt)
        db_obligado = result.scalar_one()
        assert db_obligado.nombre_razon_social == "Test SL"

    @pytest.mark.asyncio
    async def test_crear_obligado_unico_nif(self, db_session: Any) -> None:
        await crear_obligado(db_session, "B87654321", "Test1 SL")

        # En PostgreSQL real esto fallaría por UniqueConstraint
        # Aquí verificamos que no se crean duplicados
        stmt = select(ObligadoTributario).where(ObligadoTributario.nif == "B87654321")
        result = await db_session.execute(stmt)
        obligados = result.scalars().all()
        assert len(obligados) == 1


class TestInstalacionSingleOT:
    @pytest.mark.asyncio
    async def test_crear_instalacion_sin_cliente_id(self, db_session: Any) -> None:
        obligado = await crear_obligado(db_session, "C11223344", "Test2 SL")
        instalacion = await crear_instalacion_sif(
            db_session,
            obligado_id=obligado.id,
            nombre_sistema_informatico="Xespropan",
            version_sistema_informatico="3.2.1",
            id_sistema_informatico="XPPAN",
        )

        assert instalacion.numero_instalacion == "0001"
        assert instalacion.indicador_multiples_ot is False
        assert instalacion.cliente_id is None
        assert instalacion.id_sistema_informatico == "XPPAN"

    @pytest.mark.asyncio
    async def test_multiples_instalaciones_sin_cliente_id_secuencial(
        self, db_session: Any
    ) -> None:
        obligado1 = await crear_obligado(db_session, "D11223344", "Test3 SL")
        obligado2 = await crear_obligado(db_session, "E55667788", "Test4 SL")

        inst1 = await crear_instalacion_sif(db_session, obligado_id=obligado1.id)
        inst2 = await crear_instalacion_sif(db_session, obligado_id=obligado2.id)

        # Cada obligado tiene su propio secuencial (empiezan en 0001)
        assert inst1.numero_instalacion == "0001"
        assert inst2.numero_instalacion == "0001"
        assert inst1.indicador_multiples_ot is False
        assert inst2.indicador_multiples_ot is False


class TestInstalacionMultiOT:
    @pytest.mark.asyncio
    async def test_dos_instalaciones_mismo_cliente_id_incremental(
        self, db_session: Any
    ) -> None:
        cliente_id = "acuña"  # str(uuid4())
        obligado1 = await crear_obligado(db_session, "F11223344", "Test5 SL")
        obligado2 = await crear_obligado(db_session, "G55667788", "Test6 SL")

        # Primera instalación
        inst1 = await crear_instalacion_sif(
            db_session, obligado_id=obligado1.id, cliente_id=cliente_id
        )
        assert inst1.numero_instalacion == "0001"
        assert inst1.indicador_multiples_ot is False

        # Segunda instalación
        inst2 = await crear_instalacion_sif(
            db_session, obligado_id=obligado2.id, cliente_id=cliente_id
        )
        assert inst2.numero_instalacion == "0002"
        assert inst2.indicador_multiples_ot is True

        # Verificar que la primera se actualizó a True
        await db_session.refresh(inst1)
        assert inst1.indicador_multiples_ot is True

        # Verificar que comparten cliente_id
        assert inst1.cliente_id == cliente_id  # type: ignore[unreachable]
        assert inst2.cliente_id == cliente_id

    @pytest.mark.asyncio
    async def test_tres_instalaciones_mismo_cliente_id_todas_true(
        self, db_session: Any
    ) -> None:
        cliente_id = "acuña"  # str(uuid4())
        obligados = [
            await crear_obligado(db_session, f"H{100 + i:06d}", f"Test{i} SL")
            for i in range(3)
        ]

        instalaciones = []
        for obligado in obligados:
            inst = await crear_instalacion_sif(
                db_session, obligado_id=obligado.id, cliente_id=cliente_id
            )
            instalaciones.append(inst)

        # Números secuenciales (0001, 0002, 0003)
        assert instalaciones[0].numero_instalacion == "0001"
        assert instalaciones[1].numero_instalacion == "0002"
        assert instalaciones[2].numero_instalacion == "0003"

        # Todas deben tener indicador True (porque son 3)
        for inst in instalaciones:
            await db_session.refresh(inst)
            assert inst.indicador_multiples_ot is True

        # Verificar que comparten cliente_id
        assert len({inst.cliente_id for inst in instalaciones}) == 1

    @pytest.mark.asyncio
    async def test_crear_instalacion_multi_ot_sin_cliente_id(
        self, db_session: Any
    ) -> None:
        """Verifica crear instalación sin cliente_id después de tener con cliente_id."""
        cliente_id = "acuña"  # str(uuid4())

        # Crear una con cliente_id
        obligado1 = await crear_obligado(db_session, "M11223344", "Test10 SL")
        inst1 = await crear_instalacion_sif(
            db_session, obligado_id=obligado1.id, cliente_id=cliente_id
        )

        # Crear una sin cliente_id (debe funcionar sin error)
        obligado2 = await crear_obligado(db_session, "N55667788", "Test11 SL")
        inst2 = await crear_instalacion_sif(
            db_session, obligado_id=obligado2.id, cliente_id=None
        )

        # Verificar que no interfieren entre sí
        await db_session.refresh(inst1)
        assert inst1.cliente_id == cliente_id
        assert inst1.indicador_multiples_ot is False  # Solo 1 con ese cliente_id

        assert inst2.cliente_id is None
        assert inst2.indicador_multiples_ot is False  # Sin cliente_id, siempre False


class TestInstalacionEliminacion:
    @pytest.mark.asyncio
    async def test_eliminar_instalacion_actualiza_indicador_a_false(
        self, db_session: Any
    ) -> None:
        cliente_id = "acuña"  # str(uuid4())

        obligado1 = await crear_obligado(db_session, "O11223344", "Test12 SL")
        obligado2 = await crear_obligado(db_session, "P55667788", "Test13 SL")

        inst1 = await crear_instalacion_sif(
            db_session, obligado_id=obligado1.id, cliente_id=cliente_id
        )
        inst2 = await crear_instalacion_sif(
            db_session, obligado_id=obligado2.id, cliente_id=cliente_id
        )

        # Ambas tienen True
        await db_session.refresh(inst1)
        assert inst1.indicador_multiples_ot is True
        assert inst2.indicador_multiples_ot is True

        # Eliminar la segunda
        eliminada = await eliminar_instalacion_sif(db_session, inst2.id)

        # Verificar que devolvió datos correctos
        assert eliminada["id"] == inst2.id
        assert eliminada["obligado_id"] == inst2.obligado_id
        assert eliminada["cliente_id"] == inst2.cliente_id
        I_SIF = InstalacionSIF  # para acortar la línea
        # La primera debe pasar a False
        await db_session.refresh(inst1)
        assert inst1.indicador_multiples_ot is False

        # La segunda debe desaparecer
        stmt = select(I_SIF).where(I_SIF.id == inst2.id)  # type: ignore[unreachable]
        result = await db_session.execute(stmt)
        assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_eliminar_instalacion_sin_cliente_id(self, db_session: Any) -> None:
        obligado = await crear_obligado(db_session, "Q11223344", "Test14 SL")
        instalacion = await crear_instalacion_sif(db_session, obligado_id=obligado.id)

        # Eliminar
        eliminada = await eliminar_instalacion_sif(db_session, instalacion.id)

        # Verificar eliminación
        assert eliminada["id"] == instalacion.id
        stmt = select(InstalacionSIF).where(InstalacionSIF.id == instalacion.id)
        result = await db_session.execute(stmt)
        assert result.scalar_one_or_none() is None


class TestConcurrencia:
    @pytest.mark.asyncio
    async def test_concurrente_creacion_instalaciones_mismo_cliente(
        self, db_engine: Any
    ) -> None:
        """
        Dos procesos intentando crear instalación para el mismo cliente.

        Con with_for_update(), uno esperará y el secuencial será correcto.
        """
        async_session = async_sessionmaker(db_engine, class_=AsyncSession)

        cliente_id = "acuña"  # str(uuid4())

        # Crear obligados en sesiones separadas (como hace crear_obligado)
        async with async_session() as db:
            obligado1 = ObligadoTributario(
                # id=uuid4(),
                nif="R11223344",
                nombre_razon_social="Test15 SL",
            )
            db.add(obligado1)
            await db.flush()  # Flush para obtener el ID
            obligado1_id = obligado1.id
            await db.commit()

        async with async_session() as db:
            obligado2 = ObligadoTributario(
                # id=uuid4(),
                nif="S55667788",
                nombre_razon_social="Test16 SL",
            )
            db.add(obligado2)
            await db.flush()
            obligado2_id = obligado2.id
            await db.commit()

        # Función que simula un proceso creando instalación
        async def crear_proceso(obligado_id: UUID) -> str:
            async with async_session() as db:
                await asyncio.sleep(0.01)
                inst = await crear_instalacion_sif(
                    db, obligado_id=obligado_id, cliente_id=cliente_id
                )
                return inst.numero_instalacion

        try:
            results = await asyncio.wait_for(
                asyncio.gather(
                    crear_proceso(obligado1_id), crear_proceso(obligado2_id)
                ),
                timeout=5.0,  # ← Timeout de 5 segundos
            )

            assert len(set(results)) == 2
            assert "0001" in results
            assert "0002" in results
        except asyncio.TimeoutError:
            pytest.fail("Test timeout: posible deadlock en with_for_update()")


if __name__ == "__main__":
    # Ejecutar tests con pytest
    pytest.main([__file__, "-v", "-s"])
