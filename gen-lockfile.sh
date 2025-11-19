#!/bin/bash
set -e

# Genera requirements.lock en entorno limpio, para tener versiones de producción fijadas
# y probarlas bien en desarrollo. Despliegue prod con requirements.lock
docker run --rm -v "$PWD:/src" -w /src python:3.11-slim bash -c "
  pip install --upgrade pip &&
  pip install --only-binary=all -r requirements.txt &&
  pip freeze > requirements.lock
"
