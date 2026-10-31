# Calculator golden cases

Shared by the Python engine (`backend/apps/calc/engine`) and the TypeScript port (`web/src/calc`).
Both implementations run every file in `cases/` with the settings from `settings.json` and must
produce the same numbers down to the kopiyka. Any difference fails CI.

Each case has an `input` in the same shape as the body of POST /api/v1/calc/estimate, except that
the tile is described in full instead of by product id. A valid case then lists the areas, lines,
total, weight and warning codes it expects under `expected`. An invalid one has `expected_error`
with the `code` and `field` the engine must report.

Decimals are written as strings with a fixed number of digits, money as integer kopiykas.
New cases are added after checking them with the client.
