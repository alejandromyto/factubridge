"""
Script para inicializar la BD con datos de prueba.

Uso:
    python scripts/init_db.py
"""

import asyncio
import sys
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth import crear_api_key
from app.config import settings
from app.models import Base, ObligadoTributario

# Añadir el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))


async def init_database() -> None:
    """Inicializa la base de datos con datos de prueba"""
    print("🔧 Conectando a la base de datos...")
    engine = create_async_engine(settings.database_url, echo=True)

    print("📋 Creando tablas...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("✅ Tablas creadas correctamente")

    # Crear sesión
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as _session:
        session: AsyncSession = _session
        # Crear un obligado tributario de prueba
        print("\n👤 Creando obligado tributario de prueba...")

        obligado = ObligadoTributario(
            nif="B12345678", nombre_razon_social="EMPRESA PRUEBA SL", activo=True
        )

        session.add(obligado)
        await session.commit()
        print(f"✅ Obligado creado: {obligado.nif} - {obligado.nombre_razon_social}")

        # Crear API key para el obligado
        print("\n🔑 Generando API key...")

        key_plaintext, api_key_obj = await crear_api_key(
            db=session, nif="B12345678", nombre="SIF_PRUEBA"
        )

        print("✅ API Key generada:")
        print(f"   ID: {api_key_obj.id}")
        print(f"   Nombre: {api_key_obj.nombre}")
        print("\n   🔐 API KEY (guárdala, no se mostrará de nuevo):")
        print(f"   {key_plaintext}\n")

        print("=" * 70)
        print("Ejemplo de uso con curl:")
        print("=" * 70)
        print(
            f"""
curl -X POST http://localhost:8000/v1/facturas \\
  -H "Authorization: Bearer {key_plaintext}" \\
  -H "Content-Type: application/json" \\
  -d '{{
    "nif_emisor": "B12345678",
    "sistema_informatico": "SIF001",
    "factura": {{
      "IDFactura": {{
        "NumSerieFactura": "FAC2024-001",
        "FechaExpedicionFactura": "15-01-2024"
      }},
      "TipoFactura": "F1",
      "ImporteTotal": 121.00
    }}
  }}'
        """
        )

    await engine.dispose()
    print("\n✅ Inicialización completada")


if __name__ == "__main__":
    asyncio.run(init_database())
