import hashlib
import secrets
from datetime import UTC, datetime

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import APIKey, ObligadoTributario

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
) -> tuple[str, APIKey]:
    """Verifica la API key y devuelve el NIF asociado."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="API key requerida"
        )

    key_hash = hash_api_key(credentials.credentials)

    # Buscar API key
    stmt = select(APIKey).where(and_(APIKey.key_hash == key_hash, APIKey.activa))
    result = await db.execute(stmt)
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key inválida o inactiva",
        )

    # Verificar que el obligado tributario esté activo
    stmt_obligado = select(ObligadoTributario).where(
        and_(ObligadoTributario.nif == api_key.nif, ObligadoTributario.activo)
    )
    result_obligado = await db.execute(stmt_obligado)
    obligado = result_obligado.scalar_one_or_none()

    if not obligado:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Obligado tributario inactivo"
        )

    # Actualizar last_used_at (sin bloquear la request)
    stmt_update = (
        update(APIKey)
        .where(APIKey.id == api_key.id)
        .values(last_used_at=datetime.now(UTC))
    )
    await db.execute(stmt_update)

    return api_key.nif, api_key


async def get_current_nif(
    auth_data: tuple[str, APIKey] = Depends(verificar_api_key),
) -> str:
    """Dependency que devuelve solo el NIF actual"""
    return auth_data[0]


# ===== Funciones de utilidad =====


async def crear_api_key(
    db: AsyncSession, nif: str, nombre: str = "SIF"
) -> tuple[str, APIKey]:
    """
    Crea una nueva API key para un NIF.

    Devuelve (key_plaintext, api_key_object)
    """
    # Verificar que existe el obligado tributario
    stmt = select(ObligadoTributario).where(ObligadoTributario.nif == nif)
    result = await db.execute(stmt)
    obligado = result.scalar_one_or_none()

    if not obligado:
        raise ValueError(f"No existe obligado tributario con NIF {nif}")

    # Generar key
    key_plaintext = generar_api_key()
    key_hash = hash_api_key(key_plaintext)

    # Guardar en BD
    api_key = APIKey(key_hash=key_hash, nif=nif, nombre=nombre, activa=True)

    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)

    return key_plaintext, api_key
