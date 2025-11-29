"""
Script para inicializar la BD con datos de prueba.

Uso:
    python scripts/init_db.py
"""

import asyncio
import sys
from pathlib import Path

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

# Añadir el directorio raíz al path. Sin esto falla python scripts/init_db.py
sys.path.insert(0, str(Path(__file__).parent.parent))
# isort: off
from app.infrastructure.security.auth import crear_instalacion_sif  # noqa: E402
from app.config.settings import settings  # noqa: E402
from app.domain.models.models import ColaboradorSocial, ObligadoTributario  # noqa: E402

# isort: on


async def init_database() -> None:
    """Inicializa la base de datos con datos de prueba"""
    print("🔧 Conectando a la base de datos...")
    engine = create_async_engine(settings.database_url, echo=True)

    # Crear sesión
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        # 1. Crear colaborador social
        print("\n🏢 Creando colaborador social...")
        colaborador = ColaboradorSocial(
            name="Intergal Soc.Coop.Galega",
            nif="F36856276",
            software_name="Factubridge",
            software_version="0.0.1",
        )
        session.add(colaborador)
        await session.commit()
        await session.refresh(colaborador)
        print(f"✅ Colaborador creado: {colaborador.name}")

        # 2. Crear obligado tributario de prueba
        print("\n👤 Creando obligado tributario de prueba...")
        obligado = ObligadoTributario(
            nif="00000001R",
            nombre_razon_social="EMPRESA PRUEBAS SL",
            activo=True,
            colaborador_id=colaborador.id,
        )
        session.add(obligado)
        await session.commit()
        await session.refresh(obligado)
        print(f"✅ Obligado creado: {obligado.nif} - {obligado.nombre_razon_social}")

        # 3. Crear instalación SIF con API key
        print("\n🔑 Generando instalación SIF y API key...")
        key_plaintext, instalacion = await crear_instalacion_sif(
            db=session,
            obligado_id=obligado.id,
            nombre_sistema_informatico="SIF PRUEBAS",
        )

        print(f"✅ Instalación SIF creada (ID: {instalacion.id})")
        print("🔐 API Key (guardar en lugar seguro, no se mostrará más):")
        print(f"   {key_plaintext}\n")
        print(f"   Nombre: {obligado.nombre_razon_social}")

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
