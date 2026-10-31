# Calculator golden cases

Shared by the Python engine (`backend/apps/calc/engine`) and the TypeScript port (`web/src/calc`).
Both implementations run every file in `cases/` with the settings from `settings.json` and must
produce the same numbers down to the kopiyka. Any difference fails CI.

Case format:

- `input`: calculator input, as in POST /api/v1/calc/estimate, but with the tile fully described;
- `expected`: the expected result: areas, lines, total, weight, warning codes;
- `expected_error`: used instead of `expected` when the input is invalid: `code` and `field`.

Decimals are written as strings with a fixed number of digits, money as integer kopiykas.
New cases are added after checking them with the client.
