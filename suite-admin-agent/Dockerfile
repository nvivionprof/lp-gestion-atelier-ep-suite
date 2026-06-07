FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DOCKER_CLI_VERSION=27.5.1 \
    DOCKER_COMPOSE_VERSION=2.32.4 \
    LEGO_VERSION=4.23.1
RUN apt-get update \
    && apt-get install -y --no-install-recommends bash ca-certificates curl unzip rsync openssl zip tar gzip \
    && rm -rf /var/lib/apt/lists/* \
    && ARCH="$(dpkg --print-architecture)" \
    && case "$ARCH" in \
         amd64) DOCKER_ARCH="x86_64"; COMPOSE_ARCH="x86_64"; LEGO_ARCH="amd64" ;; \
         arm64) DOCKER_ARCH="aarch64"; COMPOSE_ARCH="aarch64"; LEGO_ARCH="arm64" ;; \
         *) echo "Architecture non supportée pour Docker/Compose/lego: $ARCH" >&2; exit 1 ;; \
       esac \
    && curl -fsSL "https://download.docker.com/linux/static/stable/${DOCKER_ARCH}/docker-${DOCKER_CLI_VERSION}.tgz" -o /tmp/docker.tgz \
    && tar -xzf /tmp/docker.tgz -C /tmp \
    && install -m 0755 /tmp/docker/docker /usr/local/bin/docker \
    && mkdir -p /usr/local/lib/docker/cli-plugins \
    && curl -fsSL "https://github.com/docker/compose/releases/download/v${DOCKER_COMPOSE_VERSION}/docker-compose-linux-${COMPOSE_ARCH}" -o /usr/local/lib/docker/cli-plugins/docker-compose \
    && chmod +x /usr/local/lib/docker/cli-plugins/docker-compose \
    && curl -fsSL "https://github.com/go-acme/lego/releases/download/v${LEGO_VERSION}/lego_v${LEGO_VERSION}_linux_${LEGO_ARCH}.tar.gz" -o /tmp/lego.tgz \
    && tar -xzf /tmp/lego.tgz -C /tmp lego \
    && install -m 0755 /tmp/lego /usr/local/bin/lego \
    && rm -rf /tmp/docker /tmp/docker.tgz /tmp/lego /tmp/lego.tgz \
    && docker --version \
    && docker compose version \
    && lego --version
WORKDIR /agent
COPY agent.py /agent/agent.py
EXPOSE 8079
CMD ["python", "/agent/agent.py"]
