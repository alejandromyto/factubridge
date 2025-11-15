# 📖 Alembic – Guía rápida de migraciones

Este directorio contiene la configuración y el historial de migraciones de la base de datos.

---

## 🚀 Comandos básicos

### Inicializar (solo una vez)
```bash
alembic init alembic
```

## 🔄 Migraciones (cuando cambiamos models.py y hay que actualizar la estructura de la db)

### Crear una nueva migración autogenerada:

```bash
alembic revision --autogenerate -m "descripción del cambio"
```

Ejemplo:

```bash
alembic revision --autogenerate -m "hacer huella not null"
```

### Aplicar migraciones a la base de datos:

```bash
alembic upgrade head
```

Esto lleva la DB al último estado.

### Generar SQL en lugar de aplicarlo directamente (útil para revisar o entornos con permisos restringidos):

```bash
alembic upgrade head --sql
```

### Retroceder una migración:

```bash
alembic downgrade -1
```
(o a una versión concreta con el revision id).

## 📂 Estructura

- alembic.ini → configuración global (se versiona en git, pero parametrizado con variables de entorno para credenciales).

- alembic/env.py → lógica de conexión y autogeneración.

- alembic/versions/ → scripts de migración (se versionan en git, forman parte del historial de la DB).

## ✅ Buenas prácticas

- Revisar siempre el archivo generado en versions/ antes de hacer commit. El autogenerate puede meter cambios inesperados.

- Versionar todo: alembic.ini, env.py, y versions/.

- No hardcodear credenciales en alembic.ini. Usa variables de entorno:

    ```ini
    sqlalchemy.url = ${DB_URL}
    ```

- Convenciones de mensajes: usa descripciones claras en -m, ej.
    - "add users table"
    - "alter invoices precision"

### Verifica que Alembic lee la URL correcta

```bash
alembic current
```

Esto te mostrará la versión actual de la base de datos.

Si se conecta bien, significa que Alembic está usando la URL síncrona de tu .env.
