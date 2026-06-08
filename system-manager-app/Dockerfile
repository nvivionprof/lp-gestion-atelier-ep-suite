FROM python:3.12-slim
ENV PIP_ROOT_USER_ACTION=ignore
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential libreoffice-writer libreoffice-calc libreoffice-impress fonts-dejavu && rm -rf /var/lib/apt/lists/*
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY . /app
RUN chmod +x /app/docker-entrypoint.sh
RUN mkdir -p /data/system-manager
EXPOSE 8000
ENV DJANGO_WSGI_MODULE=system_project.wsgi:application
CMD ["/app/docker-entrypoint.sh"]
