#!/usr/bin/env bash
# Django for e2e: a separate database, fresh demo data, fake payments, login codes written to a file.
# Playwright starts it (webServer); by hand: E2E_DATABASE_URL=... ./e2e/backend.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT/backend"

export DJANGO_SETTINGS_MODULE=config.settings.dev
export DEBUG=true
export DATABASE_URL="${E2E_DATABASE_URL:-postgres://keramike:keramike@127.0.0.1:5432/keramike_e2e}"
export REDIS_URL=""
export SECRET_KEY="e2e-only-secret-key-not-for-production-use-0123456789"
export ALLOWED_HOSTS="127.0.0.1,localhost"
export SITE_URL="${E2E_SITE_URL:-http://localhost:3100}"
export PAYMENT_PROVIDER=fake
export PAYMENT_PRIVATE_KEY="${E2E_PAYMENT_KEY:-e2e-payment-key}"
export TELEGRAM_LOGIN_BOT_USERNAME=keramike_e2e_bot
export TELEGRAM_LOGIN_BOT_TOKEN=""
export TELEGRAM_WEBHOOK_SECRET="${E2E_TELEGRAM_SECRET:-e2e-telegram-secret}"
export TELEGRAM_BOT_TOKEN=""
export NOVA_POSHTA_API_KEY=""
export TURNSTILE_SECRET_KEY=""
export AUTH_CODE_CHANNELS=console
export AUTH_CONSOLE_OUTBOX_FILE="${E2E_OUTBOX:-$ROOT/web/test-results/auth-outbox.txt}"
export THROTTLE_FORMS=10000/hour THROTTLE_ESTIMATES=10000/hour THROTTLE_AUTH=10000/hour
export LOG_JSON=false

PY="${PYTHON:-$ROOT/backend/.venv/bin/python}"
mkdir -p "$(dirname "$AUTH_CONSOLE_OUTBOX_FILE")"
: > "$AUTH_CONSOLE_OUTBOX_FILE"

"$PY" - <<'PY'
# The e2e database is created if missing (the user needs the CREATEDB privilege).
import os, urllib.parse, psycopg
url = urllib.parse.urlparse(os.environ["DATABASE_URL"])
name = url.path.lstrip("/")
admin = url._replace(path="/postgres").geturl()
with psycopg.connect(admin, autocommit=True) as conn:
    if not conn.execute("select 1 from pg_database where datname = %s", (name,)).fetchone():
        conn.execute(f'create database "{name}"')
PY

"$PY" manage.py migrate --noinput -v 0
"$PY" manage.py flush --noinput
"$PY" manage.py seed_demo --owner-password "e2e-owner-pass-123" --extra-products 30
exec "$PY" manage.py runserver 127.0.0.1:${E2E_API_PORT:-8010} --noreload
