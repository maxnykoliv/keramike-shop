# web

The Keramike site on Next.js 16: catalog, renovation calculator, cart, checkout and customer
account. The Next.js server works as a BFF. The browser talks only to the site, and the site calls
Django (`API_URL`) and keeps tokens in httpOnly cookies.

```bash
cp .env.example .env.local
npm install
npm run dev          # http://localhost:3000; the backend must be running at API_URL
npm run typecheck
npm run lint
npm test             # calculator golden cases from ../calc-cases
npm run build
```

The calculator computes results instantly in the browser using a port of the engine in
`src/calc`. The backend computes the final totals. The port is checked against the Python engine
with the shared golden cases in `../calc-cases`. The site loads the calculation settings from
`GET /api/v1/calc/config`.

TypeScript API types are generated from `backend/openapi.yml` with `npm run gen:api`.

Deployment to Vercel is described in the root README.
