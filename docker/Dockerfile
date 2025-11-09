FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
 && apt-get install -y --no-install-recommends gcc libpq-dev \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt \
 && python -c "import psycopg2, redis; print('deps ok')"

COPY . .

RUN chmod +x docker/entrypoint.sh

EXPOSE 8000

CMD ["bash", "docker/entrypoint.sh", "python", "manage.py", "runserver", "0.0.0.0:8000"]
