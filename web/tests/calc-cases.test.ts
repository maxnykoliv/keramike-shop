// Ті самі еталони, що й backend/apps/calc/tests/test_engine_cases.py.
import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

import { CalcValidationError, calculate } from "../src/calc";
import type { CalcResult, CalcSettings } from "../src/calc";

const ROOT = join(__dirname, "..", "..", "calc-cases");
const settings: CalcSettings = JSON.parse(readFileSync(join(ROOT, "settings.json"), "utf8"));
const files = readdirSync(join(ROOT, "cases")).filter((f) => f.endsWith(".json")).sort();

const summarize = (r: CalcResult) => ({
  surfaces: r.surfaces.map(({ area_m2, area_with_waste_m2, packs }) =>
    ({ area_m2, area_with_waste_m2, packs })),
  lines: r.lines.map(({ kind, quantity, quantity_base, total_kop, weight_kg }) =>
    ({ kind, quantity, quantity_base, total_kop, weight_kg })),
  total_kop: r.total_kop,
  weight_kg: r.weight_kg,
  warnings: r.warnings.map((w) => w.code),
});

describe("calc-cases", () => {
  it("has cases", () => expect(files.length).toBeGreaterThanOrEqual(5));

  for (const file of files) {
    it(file, () => {
      const testCase = JSON.parse(readFileSync(join(ROOT, "cases", file), "utf8"));
      if (testCase.expected_error) {
        try {
          calculate(testCase.input, settings);
          throw new Error("expected CalcValidationError");
        } catch (error) {
          expect(error).toBeInstanceOf(CalcValidationError);
          const { code, field } = error as CalcValidationError;
          expect({ code, field }).toEqual(testCase.expected_error);
        }
        return;
      }
      expect(summarize(calculate(testCase.input, settings))).toEqual(testCase.expected);
    });
  }
});
