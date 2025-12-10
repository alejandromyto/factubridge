from contextlib import contextmanager
from typing import AsyncGenerator, Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from app.config.settings import settings

# Engine asíncrono
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Base para los modelos
Base = declarative_base()


# Dependency para obtener sesión de BD
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ===== SYNC (para Celery tasks, schedulers, scripts) =====
# Convierte la URL async a sync (postgresql+asyncpg -> postgresql)
sync_database_url = settings.database_url.replace("+asyncpg", "")
sync_engine = create_engine(
    sync_database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def session_factory_sync() -> Session:
    """Helper para usarlo fuera del estilo dependency-injection

    Manejar manualmente commit(), rollback() y close()
    """
    return SyncSessionLocal()


@contextmanager
def get_sync_db() -> Generator[Session, None, None]:
    """Dependency para obtener sesión síncrona (Celery, schedulers)

    Hace commit(), rollback() (en exception) y close() automáticamente.
    """
    db = SyncSessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
