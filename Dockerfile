FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*


# Argumento para instalar git solo en dev
ARG INSTALL_GIT=false
RUN if [ "$INSTALL_GIT" = "true" ]; then \
    apt-get update && \
    apt-get install -y \
    git \
    sudo \
    locales \
    && echo "en_US.UTF-8 UTF-8" > /etc/locale.gen && \
    locale-gen en_US.UTF-8 && \
    rm -rf /var/lib/apt/lists/*; \
    fi

# Copiar requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Variables de entorno por defecto
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Crear usuario de desarrollo (solo si existe .devcontainer)
# Esto no afectará producción porque solo se ejecuta si el argumento se pasa
ARG USERNAME=devuser
ARG USER_UID=1000
ARG USER_GID=1000
RUN if [ "$INSTALL_GIT" = "true" ]; then \
    groupadd --gid $USER_GID $USERNAME && \
    useradd --uid $USER_UID --gid $USER_GID -m $USERNAME && \
    # Añadir usuario al grupo sudo
    adduser $USERNAME sudo && \
    # Permitir sudo sin password (formato correcto)
    echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers && \
    chown -R $USERNAME:$USERNAME /app && \
    mkdir -p /home/$USERNAME/.cache && \
    chown -R $USERNAME:$USERNAME /home/$USERNAME/.cache; \
    fi

USER $USERNAME

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
