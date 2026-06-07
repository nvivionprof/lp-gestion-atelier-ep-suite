FROM python:3.12-slim

# Les paquets système sont volontairement limités : l’application doit rester légère,
# portable et facile à auditer sur un serveur d’établissement.
ENV PYTHONDONTWRITEBYTECODE=1     PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app/
RUN chmod +x /app/docker-entrypoint.sh

# collectstatic est lancé au démarrage pour que WhiteNoise puisse servir CSS/JS/images
# même quand Django tourne derrière Gunicorn.
ENV DJANGO_WSGI_MODULE=pedashop_project.wsgi:application
CMD ["/app/docker-entrypoint.sh"]