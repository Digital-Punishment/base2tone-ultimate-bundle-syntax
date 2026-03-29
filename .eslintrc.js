module.exports = {
  env: {
    browser: true,
    es2024: true,
    node: true
  },
  extends: "eslint:recommended",
  globals: { atom: "readonly" },
  ignorePatterns: [
    "tools/schemes/*"
  ],
  parserOptions: {
    ecmaVersion: "latest",
    sourceType: "module"
  },
  rules: {},
};
