FROM python:3.12-slim

# Thiet lap bien moi truong Python de container chay on dinh va log hien ra ngay.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=config.settings.production

WORKDIR /app

# Cai cac goi he thong toi thieu can cho psycopg va health check bang Python.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements truoc de Docker cache dependency layer tot hon.
COPY django_backend/requirements-prod.txt /tmp/django-requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /tmp/django-requirements.txt

# Copy source sau khi cai dependencies de build lap lai nhanh hon.
COPY django_backend /app/django_backend

# Static assets are built without production credentials or a database connection.
RUN DJANGO_SETTINGS_MODULE=config.settings.test \
    SECRET_KEY=container-build-only \
    python django_backend/manage.py collectstatic --noinput \
    && rm -rf /app/django_backend/logs

# Tao user khong phai root de giam rui ro khi container bi khai thac.
RUN adduser --disabled-password --gecos "" appuser \
    && mkdir -p /app/django_backend/media /app/django_backend/logs \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Healthcheck mô phỏng header HTTPS do reverse proxy tin cậy cung cấp.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; r=urllib.request.Request('http://127.0.0.1:8000/api/v1/health/', headers={'X-Forwarded-Proto':'https'}); urllib.request.urlopen(r, timeout=3).read()"

WORKDIR /app/django_backend

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "60", "--access-logfile", "-", "--error-logfile", "-", "config.wsgi:application"]
