from celery import Celery

# Inicializar Celery App
celery_app = Celery(
    "app.workers",
    broker="redis://redis:6379/0",
    include=["app.workers.procesar_registro"],
)
