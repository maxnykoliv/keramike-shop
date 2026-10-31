# Keramike

An online ceramic tile shop with a renovation cost calculator. A customer picks a tile and enters
the room dimensions. The site shows right away how many packs to buy, which materials go with them,
what the labour costs and the total. The site's interface is in Ukrainian.

## Features

The calculator handles floors and walls with door and window openings, four laying patterns and a
waste allowance for each. Besides tiles it counts glue, grout, primer, waterproofing and labour.
An estimate can be saved, shared by link, downloaded as a PDF or moved into the cart.

The catalog has categories, faceted filters and trigram search. Staff import and export products
as CSV from the admin.

Checkout reserves stock, quotes Nova Poshta delivery and takes payment through LiqPay. Guests can
order without an account. Customers who log in (through a Telegram bot or a one-time code) keep
their addresses, orders and estimates. Tradespeople, called "masters" in the code, see their own
prices.

Staff work in the Django admin (Unfold theme), which has roles, change history and a dashboard.
Managers hear about new orders, payments and leads in Telegram, and customers get order updates
by email.

## Tech stack

| Part | Stack |
| --- | --- |
| Backend | Python, Django 5.2 LTS, Django REST Framework, Celery, PostgreSQL, Redis |
| Frontend | Next.js 16 (App Router), React 19, TypeScript, TanStack Query, Tailwind CSS |
| Infrastructure | Railway (API, workers), Vercel (site), Cloudflare R2 (media), Sentry |
| Quality | pytest, Vitest, Playwright, ruff, mypy, import-linter, GitHub Actions |

## Project layout

```text
backend/      Django + DRF, Celery, PostgreSQL: a modular monolith of 12 apps
web/          Next.js site: catalog, calculator, cart, account; the Next server is a BFF for the API
calc-cases/   golden test cases shared by both calculator implementations
```

Backend apps live in `backend/apps` and are arranged in layers. An app may import only from the
layers below it, and import-linter enforces this:

| Layer | Apps |
| --- | --- |
| Entry points and reactions | checkout, notifications, backoffice |
| Processes | payments, delivery, leads |
| Sales | cart, orders |
| Calculation | calc (the `calc/engine` engine is plain Python with no Django) |
| Reference data | catalog, accounts |
| Customers | customers: login, sessions, account, master status |
| Foundation | core |

Business logic lives only in `services.py`, and reads go through `selectors.py`. The API, the admin
and Celery tasks stay thin and call services. Lower layers notify higher ones through
`core.events`.

The calculator has two implementations. Python on the server computes the final totals, and
TypeScript in the browser shows the result instantly. Both run the `calc-cases` suite, and CI fails
on a difference of even one kopiyka. To add a case, add a JSON file to `calc-cases/cases`.

## Running locally without Docker

You need Python 3.12+ and PostgreSQL 16+. Redis is optional: without it the cache lives in memory
and Celery tasks run synchronously.

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r <(.venv/bin/python -c "import tomllib; d = tomllib.load(open('pyproject.toml','rb')); print('\n'.join(d['project']['dependencies'] + d['dependency-groups']['dev']))")
cp .env.example .env            # set DATABASE_URL, leave REDIS_URL empty
.venv/bin/python manage.py migrate
.venv/bin/python manage.py seed_demo --owner-password 'your-password'
.venv/bin/python manage.py runserver
```

- Admin: <http://localhost:8000/admin/> (owner `owner@example.com`)
- API docs: <http://localhost:8000/api/v1/docs/>
- Health check: <http://localhost:8000/health>

Then start the site in another terminal:

```bash
cd web
cp .env.example .env.local
npm install
npm run dev                     # http://localhost:3000
```

### Customer login locally

Customers log in through a Telegram bot or with a one-time code. For development, set
`AUTH_CODE_CHANNELS=console` in `.env`, and the login code will appear in the `runserver` logs.

```bash
curl -X POST localhost:8000/api/v1/auth/code/request -H 'Content-Type: application/json' \
  -d '{"phone": "0670000001", "channel": "console"}'
curl -X POST localhost:8000/api/v1/auth/code/verify -H 'Content-Type: application/json' \
  -d '{"phone": "0670000001", "code": "<code from the logs>"}'
```

The response contains a token for the `Authorization: Bearer <token>` header. In the demo data,
`0670000001` belongs to a master, so the cart and calculator use master prices for this number.

## Running locally with Docker

```bash
cp backend/.env.example backend/.env
docker compose up --build
docker compose exec api python manage.py seed_demo --owner-password 'your-password'
```

## Checks

```bash
cd backend
.venv/bin/ruff check .
.venv/bin/mypy apps config conftest.py
.venv/bin/lint-imports
.venv/bin/pytest
```

The tests need PostgreSQL. By default they connect to `postgres://keramike@127.0.0.1:5433/keramike`.
Set `DATABASE_URL` to use another server.

```bash
cd web && npm install && npm run typecheck && npm run lint && npm test
```

After changing the API, regenerate the schema, because CI compares it with the code:

```bash
cd backend && DJANGO_SETTINGS_MODULE=config.settings.dev .venv/bin/python manage.py spectacular --file openapi.yml
cd ../web && npm run gen:api
```

## Deployment

The API and admin run on Railway, and the site runs on Vercel. The browser never calls the API
directly: every request goes through the Next.js server, and tokens live only in the site's
httpOnly cookies.

### 1. Backend on Railway

One image from `backend/Dockerfile` runs as three services, each with `backend` as its root directory:

| Service | Start command |
| --- | --- |
| api | the Dockerfile default; `railway.toml` runs migrations before start |
| worker | `celery -A config worker -Q default,heavy -l info` |
| beat | `celery -A config beat -l info`, exactly one instance |

Add PostgreSQL and Redis from Railway as well. The container disk is ephemeral, so product photos
and PDFs must be stored in Cloudflare R2 (`AWS_*`). Without R2 they disappear on every deploy.

All environment variables are listed in `backend/.env.example`. These are required in production:

| Variable | Value |
| --- | --- |
| `DJANGO_SETTINGS_MODULE` | `config.settings.prod` |
| `SECRET_KEY` | a random string, e.g. `openssl rand -hex 50` |
| `DATABASE_URL`, `REDIS_URL` | references to the Railway services: `${{Postgres.DATABASE_URL}}`, `${{Redis.REDIS_URL}}` |
| `ALLOWED_HOSTS` | the API domain, e.g. `api.keramike.ua` |
| `CSRF_TRUSTED_ORIGINS` | `https://` plus the API domain, for the admin |
| `API_URL`, `SITE_URL` | full API and site URLs with `https://` |
| `BFF_SHARED_SECRET`, `REVALIDATE_SECRET` | random strings; the same values are set on Vercel |
| `AWS_*` | the Cloudflare R2 bucket and its public domain |
| `PAYMENT_PROVIDER` | `liqpay`, plus `PAYMENT_PUBLIC_KEY` and `PAYMENT_PRIVATE_KEY` |
| `NOVA_POSHTA_API_KEY`, `TELEGRAM_*`, `EMAIL_URL`, `SENTRY_DSN` | keys for the corresponding services |

Leave `CORS_ALLOWED_ORIGINS` empty, because the browser never calls the API. In production
`TRUSTED_PROXY_COUNT` is 1, since exactly one Railway proxy sits in front of Django. When a
request does not come from the site, the backend takes the client IP from that proxy's entry.

After the first deploy:

```bash
python manage.py setup_roles
python manage.py createsuperuser
python manage.py telegram_set_webhook
```

Create the login bot in @BotFather separately from the manager notification bot. Its token and
username go into `TELEGRAM_LOGIN_BOT_TOKEN` and `TELEGRAM_LOGIN_BOT_USERNAME`. The webhook secret
`TELEGRAM_WEBHOOK_SECRET` can be any random string, e.g. from `openssl rand -hex 32`. Login with a
code over Viber or SMS can be added later: write a new class in `apps/customers/channels` and add
the channel name to `AUTH_CODE_CHANNELS`.

Then, in the admin, set up delivery (the Nova Poshta sender details), labour rates and the
calculator settings with default materials, and press "Publish version".

### 2. Site on Vercel

Import the repository into Vercel and set Root Directory to `web`. Vercel detects Next.js on
its own. The environment variables are listed in `web/.env.example`:

| Variable | Value |
| --- | --- |
| `API_URL` | the Railway API URL with `https://` |
| `SITE_URL` | the site URL with `https://` |
| `BFF_SECRET` | the same value as `BFF_SHARED_SECRET` on Railway |
| `REVALIDATE_SECRET` | the same value as on Railway |
| `NEXT_PUBLIC_MEDIA_URL` | the public R2 domain with `https://` |
| `NEXT_PUBLIC_SHOP_*`, `NEXT_PUBLIC_TURNSTILE_SITE_KEY`, `NEXT_PUBLIC_GA_ID` | shop contacts, captcha, analytics |

The build does not call the API, so you can set up Vercel in parallel with Railway.
`NEXT_PUBLIC_*` variables are baked into the build, so changing them requires a new deploy.

### 3. Connect the two sides

1. Once the site has a domain, set it as `SITE_URL` on Railway. Links in emails and the return
   page after payment use it.
2. Make sure `BFF_SHARED_SECRET` matches `BFF_SECRET`, and that both `REVALIDATE_SECRET` values
   match. If the first pair differs, login and form rate limits are shared by all customers. If
   the second differs, catalog changes reach the site with up to a 5-minute delay.
3. Open `https://<API>/health` and the site's home page, log in via Telegram, and place a test
   order with `PAYMENT_PROVIDER=fake` before switching on LiqPay.
