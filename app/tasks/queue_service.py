# app/workers/queue_service.py
from uuid import UUID

from app.tasks import celery_app


# Llama al método de Celery para enviar la tarea a Redis de forma asíncrona.
def enqueue_registro(registro_id: UUID) -> None:
    """
    Despacha la tarea de procesamiento de registro al worker de Celery.

    Función síncrona para enviar una tarea de procesamiento de registro a Celery
    utilizando send_task por nombre (más robusto).
    """
    # Usar send_task con el nombre completo de la tarea
    celery_app.send_task(
        "app.workers.procesar_registro.procesar_registro_task", args=[str(registro_id)]
    )
    # Aquí puedes añadir cualquier lógica de logging/monitoreo del encolado.
