from celery import Celery
from celery.schedules import crontab

celery_app = Celery(
    "app",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/1",
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Madrid",
    enable_utc=True,
)

# ============================================================================
# CONFIGURACIÓN DE COLAS (Routing)
# ============================================================================

celery_app.conf.task_routes = {
    # CAPA 1: Scheduler ligero
    "app.tasks.scheduler.scheduler_envios_ligero": {"queue": "scheduler"},
    # CAPA 2: Orquestador (procesamiento pesado)
    "app.tasks.orquestador.orquestar_instalacion": {"queue": "orquestador"},
    # CAPA 3: Dispatcher outbox
    "app.tasks.dispatcher.dispatch_outbox_event": {"queue": "dispatcher"},
    # CAPA 4: Workers AEAT (rate-limited)
    "app.tasks.worker_aeat.enviar_lote_aeat": {"queue": "envios"},
    # MONITOREO
    "app.tasks.monitoring.*": {"queue": "monitoring"},
}

# ============================================================================
# TAREAS PERIÓDICAS (Celery Beat Schedule)
# ============================================================================

celery_app.conf.beat_schedule = {
    # ========================================================================
    # CAPA 1: PLANIFICADOR LIGERO
    # ========================================================================
    "scheduler-envios-ligero": {
        "task": "app.tasks.scheduler.scheduler_envios_ligero",
        "schedule": 60.0,  # Cada 60 segundos (1 minuto) ⚡ CRÍTICO: 240s límite
        "options": {
            "expires": 50,  # Expirar si no se ejecuta en 50 segundos
        },
    },
    # ========================================================================
    # CAPA 3: DISPATCHER OUTBOX (CRÍTICO - FRECUENCIA ALTA)
    # ========================================================================
    "dispatcher-outbox": {
        "task": "app.tasks.dispatcher.dispatch_outbox_event",
        "schedule": 5.0,  # Cada 5 segundos (latencia ultra-baja) ⚡
        "options": {
            "expires": 4,  # Expirar si no se ejecuta en 4 segundos
        },
    },
    # ========================================================================
    # MONITOREO Y ALERTAS
    # ========================================================================
    "detector-atasco-dispatcher": {
        "task": "app.tasks.monitoring.detector_atasco_dispatcher",
        "schedule": crontab(minute="*/1"),  # Cada 1 minuto (alerta rápida)
        "options": {
            "expires": 50,
        },
    },
    "alertar-eventos-error": {
        "task": "app.tasks.monitoring.alertar_eventos_error",
        "schedule": crontab(minute="*/10"),  # Cada 10 minutos
        "options": {
            "expires": 540,
        },
    },
    "estadisticas-salud-outbox": {
        "task": "app.tasks.monitoring.estadisticas_salud_outbox",
        "schedule": crontab(minute="*/5"),  # Cada 5 minutos (opcional)
        "options": {
            "expires": 240,
        },
    },
}

# ============================================================================
# CONFIGURACIÓN GENERAL
# ============================================================================

# Opciones de optimización
celery_app.conf.task_acks_late = True  # ACK después de ejecutar (seguridad)
celery_app.conf.worker_prefetch_multiplier = 1  # Sin prefetch (distribución justa)
celery_app.conf.task_reject_on_worker_lost = True  # Re-encolar si worker muere

# Serialización (JSON más seguro que pickle)
celery_app.conf.task_serializer = "json"
celery_app.conf.accept_content = ["json"]
celery_app.conf.result_serializer = "json"

# Límites de tiempo (evitar tareas zombies)
celery_app.conf.task_time_limit = 600  # 10 minutos máximo
celery_app.conf.task_soft_time_limit = 540  # Aviso a 9 minutos

# ============================================================================
# COMANDOS PARA EJECUTAR
# ============================================================================

"""
# Worker para SCHEDULER (CAPA 1)
celery -A app.celery.celery_app worker -Q scheduler -n scheduler@%h -l info

# Worker para ORQUESTADOR (CAPA 2) - Múltiples workers recomendado
celery -A app.celery.celery_app worker \
    -Q orquestador -n orquestador@%h -l info --concurrency=4

# Worker para DISPATCHER (CAPA 3) - Un solo worker suficiente
celery -A app.celery.celery_app worker \
    -Q dispatcher -n dispatcher@%h -l info --concurrency=2

# Worker para ENVIOS AEAT (CAPA 4) - Rate limited
celery -A app.celery.celery_app worker \
    -Q envios -n envios@%h -l info --concurrency=10

# Worker para MONITOREO
celery -A app.celery.celery_app worker \
    -Q monitoring -n monitoring@%h -l info

# Celery Beat (scheduler de tareas periódicas)
celery -A app.celery.celery_app beat -l info

# ============================================================================
# DESARROLLO: Todo en uno (NO usar en producción)
# ============================================================================
celery -A app.celery.celery_app worker --beat -l info --concurrency=8


# 1 solo scheduler
docker run -d --name scheduler \
  mi-app celery -A app.celery.celery_app beat -l info

# 4 cocineros
docker run -d --name orquestador \
  mi-app celery -A app.celery.celery_app worker -Q orquestador -c 4 -l info

# 2 despachadores ultra-rápidos
docker run -d --name dispatcher \
  mi-app celery -A app.celery.celery_app worker -Q dispatcher -c 2 -l info

# 10 transportistas (rate-limit 10/m en conjunto)
docker run -d --name envios \
  mi-app celery -A app.celery.celery_app worker -Q envios -c 10 -l info
"""
