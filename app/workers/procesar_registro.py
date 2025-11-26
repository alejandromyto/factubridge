import asyncio
from typing import Callable, cast

from celery import Task
from celery.exceptions import Retry
from redis import Redis

from app.aeat.models.suministro_informacion import (
    ClaveTipoFacturaType,
)

# Importamos tu lógica de XML
from app.aeat.xml.builder import build_registro_factura_from_json
from app.aeat.xml.serializer import default_serializer
from app.database import AsyncSessionLocal
from app.models import RegistroFacturacion
from app.sif.models.factura_create import (
    FacturasRectificadasInput,
    FacturasSustituidasInput,
    ImporteRectificativaInput,
)
from app.sif.models.ids import IdOtro
from app.sif.models.lineas import LineaFactura

# Importamos la app centralizada de Celery
from . import celery_app

# Configuración de Redis para el Candado (ajustar host/port si hay Docker network)
redis_client = Redis(host="redis", port=6379, db=0, decode_responses=True)

# Tipado concreto del decorador: recibe una función Task -> devuelve una función Task
TaskDecorator = Callable[[Callable[[Task, str], None]], Callable[[Task, str], None]]
task_decorator_celery_app = cast(
    TaskDecorator, celery_app.task(bind=True, max_retries=10)
)


@task_decorator_celery_app
def procesar_registro_task(self: Task, registro_id: str) -> None:
    """Worker que procesa el registro.

    Flujo:
        1. Leer DB para obtener SIF.
        2. Adquirir LOCK por SIF en Redis.
        3. Generar XML y Validar.
        4. (Futuro) Enviar a AEAT.
        5. Actualizar estado y liberar LOCK.
    """

    async def inner() -> None:
        async with AsyncSessionLocal() as session:
            # 1. RECUPERAR DATOS
            # Usamos session.get para obtener el objeto por PK
            r: RegistroFacturacion | None = await session.get(
                RegistroFacturacion, registro_id
            )

            if not r:
                print(f"Registro {registro_id} no encontrado. Abortando.")
                return

            instalacion_sif = r.instalacion_sif
            obligado = instalacion_sif.obligado

            # 2. GESTIÓN DEL CANDADO (LOCK)
            # Definimos la clave única para este SIF
            lock_key = f"nif_lock:{instalacion_sif.id}"
            # Token único para asegurar que solo quien puso el candado lo pueda quitar
            lock_token = self.request.id

            # Intentamos adquirir el candado:
            # nx=True (Solo si No Existe), ex=300 (Expira en 300s por seguridad)
            lock_acquired = redis_client.set(lock_key, lock_token, nx=True, ex=300)

            if not lock_acquired:
                # Si está ocupado, lanzamos reintento a Celery (vuelve a la cola)
                # countdown=2: Espera 2 segundos antes de reintentar
                print(
                    f"SIF {instalacion_sif.id} bloqueado."
                    f"Reintentando tarea {registro_id}..."
                )
                raise self.retry(countdown=2)

            try:
                # --- ZONA CRÍTICA (Solo un worker por SIF entra aquí a la vez) ---
                print(
                    f"Procesando registro {r.serie}-{r.numero}"
                    f" para SIF {instalacion_sif.id}"
                )
                # 3. Extracción de dato para la composición del XML
                # ✅ Revalida SOLO los objetos compuestos
                factura_data = r.factura_json

                # Parsea lineas con seguridad de tipos List[LineaFactura]
                lineas = [
                    LineaFactura(**linea) for linea in factura_data.get("lineas", [])
                ]
                id_otro_data = factura_data.get("id_otro")
                id_otro: IdOtro | None = (
                    IdOtro(**id_otro_data) if id_otro_data else None
                )
                importe_rect_data = factura_data.get("importe_rectificativa")
                importe_rectificativa = None
                if importe_rect_data:
                    importe_rectificativa = ImporteRectificativaInput(
                        **importe_rect_data
                    )
                sustituidas_data = factura_data.get("facturas_sustituidas")
                facturas_sustituidas = None
                if sustituidas_data:
                    facturas_sustituidas = FacturasSustituidasInput(**sustituidas_data)
                rectificadas_data = factura_data.get("facturas_rectificadas")
                facturas_rectificadas = None
                if rectificadas_data:
                    facturas_rectificadas = FacturasRectificadasInput(
                        **rectificadas_data
                    )
                # 3. CONSTRUCCIÓN DEL XML
                root = build_registro_factura_from_json(
                    r.id,
                    instalacion_sif,
                    nombre_emisor=obligado.nombre_razon_social,
                    nif_emisor=obligado.nif,
                    serie=r.serie,
                    numero=r.numero,
                    fecha_expedicion=r.fecha_expedicion,
                    fecha_operacion=r.fecha_operacion,
                    fecha_hora_huso_=r.created_at,
                    destinatario_nif=r.destinatario_nif,
                    destinatario_nombre=r.destinatario_nombre,
                    id_otro=id_otro,
                    tipo_factura=ClaveTipoFacturaType(r.tipo_factura),
                    tipo_rectificativa=r.tipo_rectificativa,
                    importe_rectificativa=importe_rectificativa,
                    facturas_rectificadas=facturas_rectificadas,
                    facturas_sustituidas=facturas_sustituidas,
                    operacion=r.operacion,
                    descripcion=r.descripcion,
                    importe_total=r.importe_total,
                    cuota_total=r.cuota_total,
                    huella=r.huella,
                    anterior_huella=r.anterior_huella,
                    anterior_emisor_nif=r.anterior_emisor_nif,
                    anterior_serie=r.anterior_serie,
                    anterior_numero=r.anterior_numero,
                    anterior_fecha_expedicion=r.anterior_fecha_expedicion,
                    lineas=lineas,
                )

                xml_content = default_serializer.to_valid_xml(root)

                # 5. ACTUALIZAR ESTADO (Pre-envío AEAT)
                r.xml_generado = xml_content
                # xml_generado is not None es lo que marca si está generado
                # r.estado = "xml_generado"

                # TODO: AQUÍ IRÁ EL ENVÍO REAL A LA AEAT
                # await enviar_aeat(xml_content...)

                await session.commit()
                print(f"Registro {r.serie}-{r.numero} procesado correctamente.")

            except Exception as e:
                # Si ocurre un error no controlado, hacemos rollback DB
                await session.rollback()
                # relanzamos para que Celery lo intente again (o falle definitivamente)
                raise e

            finally:
                # 6. LIBERAR EL CANDADO (CRÍTICO)
                # Verificamos que el candado sigue siendo nuestro antes de borrarlo
                if redis_client.get(lock_key) == lock_token:
                    redis_client.delete(lock_key)
                    print(f"Candado liberado para SIF {instalacion_sif.id}")

    # Puente para ejecutar código async en Celery (que es síncrono por defecto)
    try:
        asyncio.run(inner())
    except Retry:
        # Celery Retry Exception debe subir para que funcione el mecanismo de reintento
        raise
    except Exception as e:
        # Loguear error grave
        print(f"Error fatal en tarea: {e}")
        raise
