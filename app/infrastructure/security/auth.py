import hashlib
import secrets
from datetime import UTC, datetime
from uuid import UUID

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.domain.models.models import InstalacionSIF, ObligadoTributario
from app.infrastructure.database import get_db

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
async def _recalcular_indicador_multiples_ot(db: AsyncSession, cliente_id: str) -> None:
    """Recalcula el indicador para TODAS las instalaciones de un cliente.

    Se llama cuando se crea/borra una instalación. Por ejemplo un cliente en Xespropan
    puede tener varios obligados tributarios (OT) usando un solo despliegue Xespropan.
    """
    # Cuenta cuántos obligados tiene este cliente
    stmt = select(func.count()).where(InstalacionSIF.cliente_id == cliente_id)
    result = await db.execute(stmt)
    total_ot = result.scalar() or 0

    # Determina el valor (True si >1, False si solo 1)
    nuevo_valor = True if total_ot > 1 else False

    # Actualiza TODAS las instalaciones del cliente
    stmt_update = (
        update(InstalacionSIF)
        .where(InstalacionSIF.cliente_id == cliente_id)
        .values(indicador_multiples_ot=nuevo_valor)
    )
    await db.execute(stmt_update)


async def crear_instalacion_sif(
    db: AsyncSession,
    obligado_id: UUID,
    nombre_sistema_informatico: str = "Instalación SIF",
    version_sistema_informatico: str = "1.0",
    id_sistema_informatico: str = "SIF001",
    cliente_id: str | None = None,
) -> tuple[str, InstalacionSIF]:
    """
    Crea una nueva instalación SIF para un obligado tributario.

    Devuelve (api_key_plaintext, instalacion_sif_object)
    Parámetros Xespropan:
    - nombre_sistema_informatico = "Xespropan"
    - version_sistema_informatico = "YYMMDD"
    - id_sistema_informatico ="XPPAN" (valor en src/ServerProductCode.java en Xespropan)
    - numero_instalacion autoincremental por obligado
    - cliente_id (opcional) 1 Xespropan con varios obligados tributarios, por ej.'acuña'
    - indicador_multiples_ot se calcula automáticamente
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

    # Calcular numero_instalacion que toca según contexto bloqueando todos los registros
    # que cumplan el where
    if cliente_id:
        # Modo multi-OT: secuencial por cliente (para acuña = N obligados)
        stmt_max = (
            select(InstalacionSIF.numero_instalacion)
            .where(
                InstalacionSIF.cliente_id == cliente_id,
                InstalacionSIF.id_sistema_informatico == id_sistema_informatico,
            )
            .with_for_update()
        )
    else:
        # Modo single-OT: secuencial por obligado (para 1 obligado = 1 instalación)
        stmt_max = (
            select(InstalacionSIF.numero_instalacion)
            .where(InstalacionSIF.obligado_id == obligado_id)
            .with_for_update()
        )

    result_max = await db.execute(stmt_max)
    numeros = result_max.scalars().all()

    if not numeros:
        siguiente = "0001"
    else:
        ultimo_num = max(map(int, numeros))
        siguiente = f"{ultimo_num + 1:04d}"

    # Crear instalación
    instalacion = InstalacionSIF(
        obligado_id=obligado_id,
        key_hash=key_hash,
        enabled=True,
        nombre_sistema_informatico=nombre_sistema_informatico,
        version_sistema_informatico=version_sistema_informatico,
        id_sistema_informatico=id_sistema_informatico,
        numero_instalacion=siguiente,
        cliente_id=cliente_id,
    )

    db.add(instalacion)
    # 🎯 FLUSH para volcar a db la instalacion creada
    await db.flush()

    # 🎯 ACTUALIZAR DESPUÉS DEL flush para que tenga en cuenta la nueva instalación
    if cliente_id:
        await _recalcular_indicador_multiples_ot(db, cliente_id)

    # 🎯 SOLO UN COMMIT AL FINAL
    await db.commit()
    await db.refresh(instalacion)

    return key_plaintext, instalacion


# async def eliminar_instalacion_sif(
#     db: AsyncSession,
#     instalacion_id: UUID,
# ) -> InstalacionSIF:
#     """
#     Elimina una instalación SIF y recalcula el indicador para el cliente.

#     ATENCIÓN: Esta operación puede tener implicaciones fiscales/regulatorias.
#     Usar solo en casos excepcionales y con auditoría completa.

#     Args:
#         db: Sesión de base de datos
#         instalacion_id: UUID de la instalación a eliminar

#     Returns:
#         InstalacionSIF: La instalación eliminada (para auditoría)

#     Raises:
#         ValueError: Si la instalación no existe
#     """
#     # Bloquear la fila para evitar carreras
#     stmt = (
#         select(InstalacionSIF)
#         .where(InstalacionSIF.id == instalacion_id)
#         .with_for_update()
#     )
#     result = await db.execute(stmt)
#     instalacion = result.scalar_one_or_none()

#     if not instalacion:
#         raise ValueError(f"Instalación {instalacion_id} no encontrada")

#     cliente_id = instalacion.cliente_id

#     # Eliminar la instalación
#     await db.delete(instalacion)
#     await db.flush()  # Para que la COUNT vea el DELETE

#     # Recalcular indicador si pertenecía a un cliente
#     if cliente_id:
#         await _recalcular_indicador_multiples_ot(db, cliente_id)

#     # Commit final de la transacción
#     await db.commit()

#     return instalacion  # Devuelve para auditoría (puedes registrar qué se eliminó)
