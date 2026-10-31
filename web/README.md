# web

Сайт Keramike на Next.js 16: каталог, калькулятор ремонту, кошик, оформлення замовлення
й кабінет клієнта. Сервер Next.js працює як BFF: браузер говорить лише із сайтом, а той
звертається до Django (`API_URL`) і тримає токени в httpOnly cookie.

```bash
cp .env.example .env.local
npm install
npm run dev          # http://localhost:3000, бекенд має працювати на API_URL
npm run typecheck
npm run lint
npm test             # еталони калькулятора з ../calc-cases
npm run build
```

Калькулятор рахує в браузері миттєво (порт рушія в `src/calc`), остаточні суми рахує бекенд.
Порт звіряється з Python-рушієм через спільні еталони `../calc-cases`. Налаштування для
розрахунку сайт бере з `GET /api/v1/calc/config`.

TypeScript-типи API генеруються з `backend/openapi.yml`: `npm run gen:api`.

Розгортання на Vercel описане в кореневому README.
