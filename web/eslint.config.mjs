import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

// Module boundaries (like import-linter on the backend): shared knows nothing about features,
// features import each other only through index.ts, calc knows nothing about React.
const boundaries = {
  files: ["src/shared/**", "src/calc/**"],
  rules: {
    "no-restricted-imports": ["error", { patterns: [
      { group: ["@/features/*", "@/app/*"], message: "shared and calc must not depend on features or app" },
    ] }],
  },
};
const featureBoundaries = {
  files: ["src/features/**"],
  rules: {
    "no-restricted-imports": ["error", { patterns: [
      { group: ["@/features/*/*"], message: "Import another module only through its index.ts" },
      { group: ["@/app/*"], message: "features must not depend on app" },
    ] }],
  },
};
const noRawColors = {
  files: ["src/**/*.tsx"],
  rules: {
    "no-restricted-syntax": ["error", {
      selector: "Literal[value=/#[0-9a-fA-F]{6}\\b/]",
      message: "Use colors only through tokens from tokens.css",
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
