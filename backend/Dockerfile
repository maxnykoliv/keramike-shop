FROM python:3.13-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# pg_dump 17 з репозиторію PGDG знімає дампи з PostgreSQL 16 на Railway.
# Pango і шрифти потрібні WeasyPrint для PDF кошторисів.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && install -d /usr/share/postgresql-common/pgdg \
    && curl -fsSL -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.asc \
       https://www.postgresql.org/media/keys/ACCC4CF8.asc \
    && echo "deb [signed-by=/usr/share/postgresql-common/pgdg/apt.postgresql.org.asc] https://apt.postgresql.org/pub/repos/apt bookworm-pgdg main" \
       > /etc/apt/sources.list.d/pgdg.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends postgresql-client-17 \
       libpango-1.0-0 libpangoft2-1.0-0 fonts-dejavu-core \
    && apt-get purge -y curl && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml ./
RUN python -c "import tomllib; d = tomllib.load(open('pyproject.toml', 'rb')); \
print('\n'.join(d['project']['dependencies'] + d['project']['optional-dependencies']['pdf']))" \
    > /tmp/requirements.txt \
    && pip install -r /tmp/requirements.txt

COPY . .

RUN SECRET_KEY=build DATABASE_URL=sqlite:////tmp/build.db \
    DJANGO_SETTINGS_MODULE=config.settings.prod \
    python manage.py collectstatic --noinput

RUN useradd --create-home app && chown -R app /app
USER app

ENV DJANGO_SETTINGS_MODULE=config.settings.prod
EXPOSE 8000
CMD ["sh", "-c", "gunicorn config.wsgi --bind 0.0.0.0:${PORT:-8000} --workers ${WEB_CONCURRENCY:-3} --access-logfile -"]
