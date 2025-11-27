FROM python:3.11-slim AS base
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

############################
# deps-dev: dependencias dev
############################
FROM base AS deps-dev
# Usamos requirements.lock (no requirements.txt) para alinear dev con producción
COPY requirements.lock .
COPY dev-requirements.txt .
RUN pip install --no-cache-dir \
    -r requirements.lock \
    -r dev-requirements.txt && \
    rm -rf /root/.cache/pip

#############################
# deps-prod: dependencias prod
#############################
FROM base AS deps-prod
# Copy only requirements.lock to maximize cache for prod builds
COPY requirements.lock .
RUN pip install --no-cache-dir -r requirements.lock && \
    rm -rf /root/.cache/pip

################
# Stage: dev
################
FROM deps-dev AS dev

# Herramientas y locales solo en dev
RUN apt-get update && apt-get install -y \
    git \
    sudo \
    locales \
    bash bash-completion \
    && echo "en_US.UTF-8 UTF-8" > /etc/locale.gen \
    && locale-gen en_US.UTF-8 \
    && rm -rf /var/lib/apt/lists/*

# Valores por defecto (solo para fallback). Indicar valores en docker-compose.dev.yml
ARG USER_UID=1000
ARG USER_GID=1000
ARG DOCKER_GROUP_ID=999

# Crear grupo docker con GID del host (para poder usar testcontainers)
RUN groupadd --gid ${DOCKER_GROUP_ID} docker

# Crear usuario y su grupo primario
RUN groupadd --gid ${USER_GID} factubridge && \
    useradd --uid ${USER_UID} --gid ${USER_GID} -m -s /bin/bash factubridge

# Añadir a grupos secundarios y dar permisos sudo
RUN usermod -aG docker factubridge && \
    usermod -aG sudo factubridge && \
    echo "factubridge ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Descomentar si la imagen de dev se usa en CI o sin volumen montado,
#RUN chown -R factubridge:factubridge /app
#COPY --chown=factubridge:factubridge . .

# Ejecutar como usuario no-root en dev
USER factubridge

# Exponer puerto para conveniencia en dev; no fijamos CMD para que el devcontainer pueda sobrescribir
EXPOSE 8000

################
# Stage: prod
################
FROM deps-prod AS prod

# Crear usuario no-root para producción
RUN useradd -m -s /bin/bash factubridge

# Copiar código con permisos correctos
RUN chown factubridge:factubridge /app
COPY --chown=factubridge:factubridge . .

# Cambiar a usuario no-root
USER factubridge

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
