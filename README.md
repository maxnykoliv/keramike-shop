# Keramike

Магазин кераміки з калькулятором ремонту: клієнт обирає плитку, вводить розміри приміщення
й одразу бачить кількість упаковок, супутні матеріали, вартість роботи та суму.

Технічне завдання й архітектура: https://claude.ai/artifact/LRKvdTRZpfyVPkyLnohQF1

## Структура

```
backend/      Django 5.2 + DRF, Celery, PostgreSQL — модульний моноліт з 12 застосунків
web/          сайт на Next.js 16: каталог, калькулятор, кошик, кабінет; сервер Next — BFF до API
calc-cases/   еталонні випадки калькулятора для обох реалізацій
```

Застосунки бекенду лежать у `backend/apps` і розкладені за шарами. Імпортувати можна лише нижчі шари,
це перевіряє import-linter:

| Шар | Застосунки |
| --- | --- |
| Вхід і реакції | checkout, notifications, backoffice |
| Процеси | payments, delivery, leads |
| Продаж | cart, orders |
| Розрахунок | calc (рушій `calc/engine` — чистий Python без Django) |
| Довідники | catalog, accounts |
| Клієнти | customers: вхід, сесії, кабінет, статус майстра |
| Основа | core |

Бізнес-логіка живе лише в `services.py`, читання — у `selectors.py`. API, адмінка й задачі Celery
тонкі й викликають сервіси. Нижчі шари повідомляють вищі через події `core.events`.

## Локальний запуск без Docker

Потрібні Python 3.12+ і PostgreSQL 16+. Redis не обов'язковий: без нього кеш живе в пам'яті,
а задачі Celery виконуються одразу.

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r <(.venv/bin/python -c "import tomllib; d = tomllib.load(open('pyproject.toml','rb')); print('\n'.join(d['project']['dependencies'] + d['dependency-groups']['dev']))")
cp .env.example .env            # вкажіть DATABASE_URL, REDIS_URL залиште порожнім
.venv/bin/python manage.py migrate
.venv/bin/python manage.py seed_demo --owner-password 'свій-пароль'
.venv/bin/python manage.py runserver
```

- Адмінка: http://localhost:8000/admin/ (власник `owner@example.com`)
- Документація API: http://localhost:8000/api/v1/docs/
- Стан сервісу: http://localhost:8000/health

### Вхід клієнтів локально

Клієнти входять через Telegram-бота або одноразовим кодом. Для розробки задайте в `.env`
`AUTH_CODE_CHANNELS=console`: код для входу з'явиться в логах `runserver`.

```bash
curl -X POST localhost:8000/api/v1/auth/code/request -H 'Content-Type: application/json' \
  -d '{"phone": "0670000001", "channel": "console"}'
curl -X POST localhost:8000/api/v1/auth/code/verify -H 'Content-Type: application/json' \
  -d '{"phone": "0670000001", "code": "<код з логів>"}'
```

Відповідь містить токен для заголовка `Authorization: Bearer <токен>`. Номер `0670000001`
у демо-даних належить майстру, тож для нього кошик і калькулятор рахують ціни майстра.

## Локальний запуск з Docker

```bash
cp backend/.env.example backend/.env
docker compose up --build
docker compose exec api python manage.py seed_demo --owner-password 'свій-пароль'
```

## Перевірки

```bash
cd backend
.venv/bin/ruff check .
.venv/bin/mypy apps config conftest.py
.venv/bin/lint-imports
.venv/bin/pytest
```

Тестам потрібен PostgreSQL. За замовчуванням вони йдуть до `postgres://keramike@127.0.0.1:5433/keramike`,
інший сервер задається змінною `DATABASE_URL`.

```bash
cd web && npm install && npm test && npm run typecheck
```

Калькулятор існує у двох реалізаціях: Python на сервері рахує остаточні суми, TypeScript у браузері
показує результат миттєво. Обидві проганяють `calc-cases`, і розбіжність навіть на копійку валить CI.
Новий випадок додається JSON-файлом у `calc-cases/cases`.

Після змін в API оновіть схему, бо CI звіряє її з кодом:

```bash
cd backend && DJANGO_SETTINGS_MODULE=config.settings.dev .venv/bin/python manage.py spectacular --file openapi.yml
```

## Розгортання

API з адмінкою працює на Railway, сайт — на Vercel. Браузер не звертається до API напряму:
усі запити йдуть через сервер Next.js, а токени живуть лише в httpOnly cookie сайту.

### 1. Бекенд на Railway

Один образ із `backend/Dockerfile`, три сервіси з коренем `backend`:

| Сервіс | Команда запуску |
| --- | --- |
| api | за замовчуванням з Dockerfile; міграції йдуть перед стартом через `railway.toml` |
| worker | `celery -A config worker -Q default,heavy -l info` |
| beat | `celery -A config beat -l info`, рівно один екземпляр |

Плюс PostgreSQL і Redis від Railway. Диск контейнера тимчасовий, тому фото товарів і PDF мають
лежати в Cloudflare R2 (`AWS_*`). Без R2 вони зникатимуть після кожного деплою.

Змінні середовища перелічені в `backend/.env.example`. Для продакшену обов'язкові:

| Змінна | Значення |
| --- | --- |
| `DJANGO_SETTINGS_MODULE` | `config.settings.prod` |
| `SECRET_KEY` | випадковий рядок, `openssl rand -hex 50` |
| `DATABASE_URL`, `REDIS_URL` | посилання на сервіси Railway: `${{Postgres.DATABASE_URL}}`, `${{Redis.REDIS_URL}}` |
| `ALLOWED_HOSTS` | домен API, наприклад `api.keramike.ua` |
| `CSRF_TRUSTED_ORIGINS` | `https://` + домен API, для адмінки |
| `API_URL`, `SITE_URL` | повні адреси API й сайту з `https://` |
| `BFF_SHARED_SECRET`, `REVALIDATE_SECRET` | випадкові рядки; ті самі значення задаються на Vercel |
| `AWS_*` | бакет Cloudflare R2 і його публічний домен |
| `PAYMENT_PROVIDER` | `liqpay` і ключі `PAYMENT_PUBLIC_KEY`, `PAYMENT_PRIVATE_KEY` |
| `NOVA_POSHTA_API_KEY`, `TELEGRAM_*`, `EMAIL_URL`, `SENTRY_DSN` | ключі відповідних сервісів |

`CORS_ALLOWED_ORIGINS` залишайте порожнім: браузер API не викликає. `TRUSTED_PROXY_COUNT` у
продакшені дорівнює 1, бо перед Django стоїть рівно один проксі Railway. Саме з його запису
бекенд бере IP клієнта, коли запит прийшов не із сайту.

Після першого деплою:

```bash
python manage.py setup_roles
python manage.py createsuperuser
python manage.py telegram_set_webhook
```

Бот входу створюється в @BotFather окремо від бота сповіщень менеджеру. Його токен і username
задаються в `TELEGRAM_LOGIN_BOT_TOKEN` і `TELEGRAM_LOGIN_BOT_USERNAME`. Секрет вебхука
`TELEGRAM_WEBHOOK_SECRET` — будь-який випадковий рядок, наприклад з `openssl rand -hex 32`.
Вхід за кодом у Viber або SMS вмикається пізніше: новий клас у `apps/customers/channels`
і назва каналу в `AUTH_CODE_CHANNELS`.

Далі в адмінці: налаштування доставки (дані відправника Нової пошти), тарифи робіт, налаштування
калькулятора з матеріалами за замовчуванням, кнопка «Опублікувати версію».

### 2. Сайт на Vercel

Імпортуйте репозиторій у Vercel і вкажіть **Root Directory** `web`. Фреймворк Next.js Vercel
визначить сам. Змінні середовища перелічені в `web/.env.example`:

| Змінна | Значення |
| --- | --- |
| `API_URL` | адреса API на Railway з `https://` |
| `SITE_URL` | адреса сайту з `https://` |
| `BFF_SECRET` | те саме, що `BFF_SHARED_SECRET` на Railway |
| `REVALIDATE_SECRET` | те саме, що на Railway |
| `NEXT_PUBLIC_MEDIA_URL` | публічний домен R2 з `https://` |
| `NEXT_PUBLIC_SHOP_*`, `NEXT_PUBLIC_TURNSTILE_SITE_KEY`, `NEXT_PUBLIC_GA_ID` | контакти магазину, капча, аналітика |

Під час збірки сайт до API не звертається, тож Vercel можна налаштовувати паралельно з Railway.
Змінні `NEXT_PUBLIC_*` вбудовуються в збірку, тому після їхньої зміни потрібен новий деплой.

### 3. Зв'язати обидва боки

1. Коли з'явиться домен сайту, впишіть його в `SITE_URL` на Railway. Звідти беруться посилання
   в листах і повернення після оплати.
2. Перевірте, що `BFF_SHARED_SECRET` і `BFF_SECRET`, а також обидва `REVALIDATE_SECRET` збігаються.
   Без першої пари ліміти на вхід і форми рахуватимуться для всіх клієнтів разом. Без другої
   зміни в каталозі з'являтимуться на сайті з затримкою до 5 хвилин.
3. Відкрийте `https://<API>/health` і головну сторінку сайту, увійдіть через Telegram, оформіть
   тестове замовлення з `PAYMENT_PROVIDER=fake` до того, як вмикати LiqPay.
