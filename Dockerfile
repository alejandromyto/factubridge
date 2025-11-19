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

# Crear usuario de desarrollo (UID/GID pueden pasarse en build-args si se desea)
ARG USERNAME=devuser
ARG USER_UID=1000
ARG USER_GID=1000

RUN groupadd --gid ${USER_GID} ${USERNAME} || true && \
    useradd --uid ${USER_UID} --gid ${USER_GID} -m -s /bin/bash ${USERNAME} && \
    adduser ${USERNAME} sudo || true && \
    echo "${USERNAME} ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers && \
    mkdir -p /home/${USERNAME}/.cache && \
    chown -R ${USERNAME}:${USERNAME} /home/${USERNAME} /app || true

# Copiar código; en dev normalmente se monta el volumen y sobrescribe
COPY . .
# Ejecutar como usuario no-root en dev (coincidir con user: "1000:1000" en compose)
USER ${USERNAME}
# Exponer puerto para conveniencia en dev; no fijamos CMD para que el devcontainer pueda sobrescribir
EXPOSE 8000

################
# Stage: prod
################
FROM deps-prod AS prod
# Copiar código para la imagen de producción (no bind-mount)
COPY . .
# En producción no instalamos git/sudo ni creamos el usuario dev
EXPOSE 8000
# CMD por defecto para producción
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
