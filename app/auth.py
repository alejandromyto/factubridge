import hashlib
import secrets
from datetime import UTC, datetime
from uuid import UUID

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database import get_db
from app.models import InstalacionSIF, ObligadoTributario

security = HTTPBearer()


def hash_api_key(key: str) -> str:
    """Hash SHA256 de la API key."""
    return hashlib.sha256(key.encode()).hexdigest()


def generar_api_key() -> str:
    """Genera una API key segura."""
    return secrets.token_urlsafe(48)


async def verificar_api_key(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: AsyncSession = Depends(get_db),
) -> InstalacionSIF:
    """Verifica la API key y devuelve la instalación SIF asociada."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="API key requerida"
        )

    key_hash = hash_api_key(credentials.credentials)

    # Buscar instalación SIF con joinedload para cargar el obligado
    stmt = (
        select(InstalacionSIF)
        .options(joinedload(InstalacionSIF.obligado))
        .where(
            and_(
                InstalacionSIF.key_hash == key_hash,
                InstalacionSIF.enabled,
            )
        )
    )
    result = await db.execute(stmt)
    instalacion = result.scalar_one_or_none()

    if not instalacion:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key inválida o instalación deshabilitada",
        )

    # Verificar obligado activo
    if not instalacion.obligado.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Obligado tributario inactivo"
        )

    # Actualizar last_used_at
    stmt_update = (
        update(InstalacionSIF)
        .where(InstalacionSIF.id == instalacion.id)
        .values(last_used_at=datetime.now(UTC))
    )
    await db.execute(stmt_update)

    return instalacion


# ===== Funciones de utilidad =====


async def crear_instalacion_sif(
    db: AsyncSession,
    obligado_id: UUID,
    nombre: str = "Instalación SIF",
) -> tuple[str, InstalacionSIF]:
    """
    Crea una nueva instalación SIF para un obligado tributario.

    Devuelve (api_key_plaintext, instalacion_sif_object)
    """
    # Verificar que existe el obligado tributario
    stmt = select(ObligadoTributario).where(ObligadoTributario.id == obligado_id)
    result = await db.execute(stmt)
    obligado = result.scalar_one_or_none()

    if not obligado:
        raise ValueError(f"No existe obligado tributario con ID {obligado_id}")

    # Generar API key
    key_plaintext = generar_api_key()
    key_hash = hash_api_key(key_plaintext)

    # Crear instalación
    instalacion = InstalacionSIF(
        obligado_id=obligado_id,
        key_hash=key_hash,  # o api_key_hash según tu columna
        enabled=True,
    )

    db.add(instalacion)
    await db.commit()
    await db.refresh(instalacion)

    return key_plaintext, instalacion
