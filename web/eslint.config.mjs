import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

// Межі модулів (як import-linter на бекенді): shared не знає про features,
// features імпортують один одного лише через index.ts, calc не знає про React.
const boundaries = {
  files: ["src/shared/**", "src/calc/**"],
  rules: {
    "no-restricted-imports": ["error", { patterns: [
      { group: ["@/features/*", "@/app/*"], message: "shared і calc не залежать від features чи app" },
    ] }],
  },
};
const featureBoundaries = {
  files: ["src/features/**"],
  rules: {
    "no-restricted-imports": ["error", { patterns: [
      { group: ["@/features/*/*"], message: "Імпортуйте інший модуль лише через його index.ts" },
      { group: ["@/app/*"], message: "features не залежать від app" },
    ] }],
  },
};
const noRawColors = {
  files: ["src/**/*.tsx"],
  rules: {
    "no-restricted-syntax": ["error", {
      selector: "Literal[value=/#[0-9a-fA-F]{6}\\b/]",
      message: "Кольори лише через токени з tokens.css",
    }],
  },
};

const config = [
  ...nextVitals,
  ...nextTs,
  boundaries,
  featureBoundaries,
  noRawColors,
  { ignores: [".next/**", "node_modules/**", "playwright-report/**", "test-results/**", "src/shared/api/schema.ts", "next-env.d.ts"] },
];

export default config;
