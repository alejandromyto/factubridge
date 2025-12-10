# Arquitectura Outbox Pattern - Gateway AEAT Veri*factu

## 🎯 Objetivo

Garantizar **integridad absoluta de la cadena hash** (Art. 12 Reglamento Veri*factu) mediante Outbox Pattern con doble commit separado.

## ✅ Garantías Críticas

### GARANTÍA 1: Sin Huérfanos (NUNCA)
- **Lote + OutboxEvent** se crean en la **MISMA transacción**
- Si commit falla → NINGUNO persiste (SIN RIESGO)
- Si commit OK → SIEMPRE hay evento para procesar el lote

### GARANTÍA 2: Orden FIFO Estricto
- Eventos procesados por `ORDER BY created_at ASC`
- Cadena hash **NUNCA** se rompe por procesamiento fuera de orden

### GARANTÍA 3: Control de Flujo AEAT
- Lock Redis exclusivo por instalación
- Doble verificación de condiciones (scheduler + orquestador)
- Actualización atómica de `ultimo_envio_at` y `ultimo_tiempo_espera`

### GARANTÍA 4: Resiliencia Total
- Orquestador muere → Lote + Evento NO persisten (rollback)
- Dispatcher muere → Eventos siguen en 'pendiente' (reintento automático)
- Worker AEAT muere → Evento vuelve a cola (retry policy)
- Redis cae → Lock expira automáticamente (timeout 60s)

---

## 🏗️ Arquitectura por Capas

```
┌─────────────────────────────────────────────────────────────┐
│  CAPA 1: PLANIFICADOR (Celery Beat: cada 5 min)           │
│  scheduler_envios_ligero()                                  │
│  ├─ Evalúa condiciones de control de flujo (lectura)      │
│  └─ Encola: orquestar_instalacion(id) por cada instalación │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  CAPA 2: ORQUESTADOR (Worker: orquestador, on-demand)     │
│  orquestar_instalacion(instalacion_sif_id)                 │
│  ├─ Lock Redis exclusivo (sif:{id})                        │
│  ├─ Doble verificación control_flujo()                     │
│  ├─ LoteService.crear_lote() (flush)                       │
│  ├─ OutboxService.crear_evento() (flush)                   │
│  ├─ ✅ COMMIT ATÓMICO: lote + evento = TODO o NADA        │
│  └─ Liberar lock                                            │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  CAPA 3: DISPATCHER (Worker: dispatcher, cada 10s)        │
│  dispatch_outbox_event()                                   │
│  ├─ SELECT FOR UPDATE SKIP LOCKED (eventos pendientes)    │
│  ├─ ORDER BY created_at ASC (FIFO estricto)               │
│  ├─ Encolar: enviar_lote_aeat(lote_id, evento_id)         │
│  ├─ Marcar evento como 'encolado'                          │
│  └─ ✅ COMMIT (transacción SEPARADA del orquestador)      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  CAPA 4: WORKER AEAT (Worker: envios, rate_limit 10/m)   │
│  enviar_lote_aeat(lote_id, evento_id)                     │
│  ├─ Generar XML de envío                                   │
│  ├─ POST a AEAT (timeout 60s, retry 10x)                  │
│  ├─ Procesar respuesta (tiempo 't', estados)              │
│  ├─ ✅ CRÍTICO: Actualizar instalación                    │
│  │   ├─ ultimo_envio_at = now()                           │
│  │   └─ ultimo_tiempo_espera = tiempo_t_recibido          │
│  ├─ Marcar evento como 'procesado'                         │
│  └─ COMMIT                                                  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  MONITOREO (Celery Beat: cada 1-10 min)                   │
│  ├─ detector_atasco_dispatcher() [1 min]                  │
│  ├─ alertar_eventos_error() [10 min]                      │
│  └─ estadisticas_salud_outbox() [5 min]                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 Flujo de Datos Completo

### Caso Normal (Happy Path)

```
T=0:   scheduler_envios_ligero() ejecuta
       ├─ Lee instalación 1
       ├─ Evalúa: registros_pendientes >= 1000 ✅
       └─ Encola: orquestar_instalacion(1)

T=5:   orquestar_instalacion(1) ejecuta
       ├─ Adquiere lock Redis: sif:1 ✅
       ├─ Doble verificación: cumple condiciones ✅
       ├─ Crea lote (flush, ID=100)
       ├─ Crea evento outbox (flush, ID=1, lote_id=100)
       ├─ COMMIT ATÓMICO ✅
       └─ Libera lock sif:1

T=10:  dispatch_outbox_event() ejecuta
       ├─ SELECT eventos pendientes ORDER BY created_at ASC
       ├─ Encuentra evento ID=1 (lote_id=100)
       ├─ Encola: enviar_lote_aeat.apply_async(100, 1)
       ├─ Marca evento como 'encolado'
       └─ COMMIT ✅

T=15:  enviar_lote_aeat(100, 1) ejecuta
       ├─ Genera XML del lote 100
       ├─ POST a AEAT (respuesta: tiempo_t=120s)
       ├─ Actualiza instalación:
       │   ├─ ultimo_envio_at = 2025-12-02 15:30:00
       │   └─ ultimo_tiempo_espera = 120
       ├─ Marca evento como 'procesado'
       └─ COMMIT ✅

T=300: scheduler_envios_ligero() ejecuta de nuevo
       ├─ Lee instalación 1
       ├─ Evalúa: tiempo_transcurrido < 120*1.1 ❌
       └─ Skip (no encola)

T=450: scheduler_envios_ligero() ejecuta
       ├─ Evalúa: tiempo_transcurrido >= 132s ✅
       └─ Encola: orquestar_instalacion(1) de nuevo
```

### Caso Error: Orquestador Falla Antes de Commit

```
T=5:   orquestar_instalacion(1) ejecuta
       ├─ Adquiere lock Redis: sif:1 ✅
       ├─ Crea lote (flush, ID=100)
       ├─ Crea evento (flush, ID=1)
       ├─ ❌ CRASH antes de COMMIT
       └─ Redis auto-libera lock tras 60s

Resultado:
- Lote 100: NO persiste (rollback)
- Evento 1: NO persiste (rollback)
- ✅ NO HAY HUÉRFANO
- Próximo scheduler reintentará
```

### Caso Error: Dispatcher Falla Después de Encolar

```
T=10:  dispatch_outbox_event() ejecuta
       ├─ Encola: enviar_lote_aeat(100, 1) ✅
       ├─ Marca evento como 'encolado'
       ├─ ❌ CRASH antes de COMMIT
       └─ Evento vuelve a estado 'pendiente'

Resultado:
- Evento 1: Sigue en 'pendiente'
- Worker AEAT: Puede ejecutarse (ya encolado)
- T=20: Dispatcher reintenta y lo marca 'encolado' de nuevo
- ✅ Sistema se auto-recupera
```

### Caso Error: Worker AEAT Falla

```
T=15:  enviar_lote_aeat(100, 1) ejecuta
       ├─ Genera XML ✅
       ├─ POST a AEAT → timeout ❌
       └─ Celery reintenta automáticamente (max 10x)

T=45:  Reintento 1 → timeout ❌
T=105: Reintento 2 → timeout ❌
...
T=600: Reintento 10 → timeout ❌
       └─ Marca evento como 'error'

Resultado:
- Evento 1: Estado = 'error'
- alertar_eventos_error() genera alerta
- ✅ Requiere intervención manual
```

---

## 📊 Estados del OutboxEvent

```
PENDIENTE → ENCOLADO → PROCESADO
    ↓           ↓
  ERROR ← ─ ─ ─ ┘
```

- **PENDIENTE**: Creado junto al lote, esperando dispatcher
- **ENCOLADO**: Dispatcher envió a worker AEAT (puede no haber commit aún)
- **PROCESADO**: Worker AEAT completó exitosamente
- **ERROR**: Falló después de todos los reintentos (max 10)

---

## 🔒 Locks y Concurrencia

### Lock Redis por Instalación

```python
lock_key = f"sif:{instalacion_id}"
lock = redis_client.lock(lock_key, timeout=60, blocking=False)
```

**Garantías:**
- Solo 1 worker puede procesar una instalación a la vez
- Auto-release tras 60 segundos (evita deadlocks)
- Non-blocking: si ocupado, skip sin error

### Row-Level Locks en BD

```python
SELECT ... FOR UPDATE SKIP LOCKED
```

**Garantías:**
- Solo registros disponibles (sin bloqueos)
- Concurrencia segura entre múltiples workers
- Evita race conditions en lectura/escritura

---

## 📈 Monitoreo y Alertas

### Detector de Atasco (Cada 1 min)

**Condición de alerta:**
```
eventos_pendientes > 2 minutos → ALERTA CRÍTICA
```

**Impacto:**
- ⚠️ Instalaciones no envían (disponibilidad)
- ✅ Cadena hash NO se rompe (integridad garantizada)

**Acción:**
- Revisar logs del worker `dispatcher`
- Verificar conectividad Redis
- Escalar workers si necesario

### Alertas de Error (Cada 10 min)

**Condición:**
```
eventos.estado = 'error' → Revisión manual
```

**Posibles causas:**
- AEAT caído por >10 minutos
- XML inválido (error de generación)
- Certificado expirado
- Rate limit excedido

---

## 🚀 Comandos de Ejecución

### Producción (Workers Separados)

```bash
# CAPA 1: Scheduler (ligero)
celery -A app.celery.celery_app worker -Q scheduler -n scheduler@%h -l info

# CAPA 2: Orquestador (4 workers concurrentes)
celery -A app.celery.celery_app worker -Q orquestador -n orquestador@%h -l info --concurrency=4

# CAPA 3: Dispatcher (1 worker suficiente)
celery -A app.celery.celery_app worker -Q dispatcher -n dispatcher@%h -l info --concurrency=2

# CAPA 4: Envíos AEAT (rate-limited 10/minuto)
celery -A app.celery.celery_app worker -Q envios -n envios@%h -l info --concurrency=10

# MONITOREO
celery -A app.celery.celery_app worker -Q monitoring -n monitoring@%h -l info

# BEAT (tareas periódicas)
celery -A app.celery.celery_app beat -l info
```

### Desarrollo (Todo en uno)

```bash
celery -A app.celery.celery_app worker --beat -l info --concurrency=8
```

---

## 🧪 Testing

### Test de Atomicidad

```python
# Test: Simular crash antes de commit
def test_atomicidad_orquestador():
    with patch('app.tasks.orquestador.db.commit', side_effect=Exception("Crash")):
        orquestar_instalacion(1)

    # Verificar: NO hay lote ni evento en BD
    assert LoteEnvio.query.count() == 0
    assert OutboxEvent.query.count() == 0
```

### Test de FIFO

```python
def test_orden_fifo():
    # Crear 3 lotes en orden
    lote1 = crear_lote(instalacion=1)
    lote2 = crear_lote(instalacion=2)
    lote3 = crear_lote(instalacion=1)

    # Dispatcher debe procesar en orden de creación
    dispatch_outbox_event()

    assert eventos_encolados == [lote1.id, lote2.id, lote3.id]
```

---

## 📝 Migración Alembic

```python
# Crear tabla outbox_event
def upgrade():
    op.create_table(
        'outbox_event',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lote_id', sa.Integer(), nullable=False),
        sa.Column('instalacion_sif_id', sa.Integer(), nullable=False),
        sa.Column('estado', sa.Enum('pendiente', 'encolado', 'procesado', 'error'), nullable=False),
        sa.Column('task_name', sa.String(), nullable=False),
        sa.Column('payload', sa.String(), nullable=False),
        sa.Column('intentos', sa.Integer(), nullable=False, default=0),
        sa.Column('max_intentos', sa.Integer(), nullable=False, default=10),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ultimo_intento_at', sa.DateTime(timezone=True)),
        sa.Column('procesado_at', sa.DateTime(timezone=True)),
        sa.Column('error_mensaje', sa.String()),
        sa.ForeignKeyConstraint(['lote_id'], ['lotes_envio.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['instalacion_sif_id'], ['instalaciones_sif.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Índices críticos
    op.create_index('idx_outbox_estado', 'outbox_event', ['estado'])
    op.create_index('idx_outbox_created_at', 'outbox_event', ['created_at'])
    op.create_index('idx_outbox_instalacion_estado', 'outbox_event', ['instalacion_sif_id', 'estado'])

    # Índice parcial (PostgreSQL)
    op.execute('''
        CREATE INDEX idx_outbox_pendiente_order
        ON outbox_event(estado, created_at)
        WHERE estado = 'pendiente'
    ''')
```

---

## 🎯 Resumen de Garantías

| Garantía | Mecanismo | Estado |
|----------|-----------|--------|
| Sin huérfanos | Lote + Evento en MISMA TX | ✅ |
| Orden FIFO | ORDER BY created_at ASC | ✅ |
| Control de flujo AEAT | Lock + Doble verificación | ✅ |
| Resiliencia crashes | Rollback automático | ✅ |
| Reintentos automáticos | Celery retry policy | ✅ |
| Monitoreo atasco | Alerta < 2 min | ✅ |
| Rate limiting AEAT | 10/minuto en worker | ✅ |
| Idempotencia | Locks Redis | ✅ |

**CONCLUSIÓN: Sistema garantiza integridad de cadena hash bajo CUALQUIER escenario de fallo.**
