set -e

echo "Waiting for database..."
python - <<'PY'
import os, time, sys
import psycopg2
host = os.environ.get("POSTGRES_HOST","db")
port = int(os.environ.get("POSTGRES_PORT","5432"))
user = os.environ.get("POSTGRES_USER","electronics")
password = os.environ.get("POSTGRES_PASSWORD","electronics")
dbname = os.environ.get("POSTGRES_DB","electronics")
for _ in range(30):
    try:
        psycopg2.connect(host=host, port=port, user=user, password=password, dbname=dbname).close()
        sys.exit(0)
    except Exception:
        time.sleep(1)
print("DB not ready after 30s", file=sys.stderr); sys.exit(1)
PY

echo "Apply migrations..."
python manage.py migrate --noinput

if [ "${CREATE_SUPERUSER:-1}" = "1" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]; then
  echo "Ensuring superuser exists..."
  python manage.py ensure_superuser \
    ${DJANGO_SUPERUSER_USERNAME:+--username "$DJANGO_SUPERUSER_USERNAME"} \
    ${DJANGO_SUPERUSER_EMAIL:+--email "$DJANGO_SUPERUSER_EMAIL"} \
    --password "$DJANGO_SUPERUSER_PASSWORD" || true
else
  echo "Skip ensure_superuser (flag CREATE_SUPERUSER=0 or no password)."
fi

if [ "${SEED_DEMO:-0}" = "1" ]; then
  echo "Seeding demo data..."
  if [ "${SEED_RESET:-0}" = "1" ]; then
    python manage.py seed_demo --reset || true
  else
    python manage.py seed_demo || true
  fi
else
  echo "Skip seed_demo (flag SEED_DEMO=0)."
fi

echo "Start: $@"
exec "$@"
