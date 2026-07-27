FROM python:3.12-slim

# Thiet lap bien moi truong Python de container chay on dinh va log hien ra ngay.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=config.settings.development
ENV SECRET_KEY=docker-local-build-only-secret
ENV DEBUG=False
ENV ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,web
ENV DATABASE_URL=sqlite:////app/django_backend/db.sqlite3
ENV LEGACY_DATABASE_URL=file:/app/backend/database/mecprecision.sqlite?mode=ro

WORKDIR /app

# Cai cac goi he thong toi thieu can cho psycopg va health check bang Python.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements truoc de Docker cache dependency layer tot hon.
COPY django_backend/requirements.txt /tmp/django-requirements.txt
COPY backend/requirements.txt /tmp/legacy-requirements.txt

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /tmp/django-requirements.txt -r /tmp/legacy-requirements.txt

# Copy source sau khi cai dependencies de build lap lai nhanh hon.
COPY . .

# Tao user khong phai root de giam rui ro khi container bi khai thac.
RUN adduser --disabled-password --gecos "" appuser \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Healthcheck goi endpoint Django local. Day la kiem tra trong container, khong dung production.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health/', timeout=3).read()"

CMD ["python", "django_backend/manage.py", "runserver", "0.0.0.0:8000"]
