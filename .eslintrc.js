module.exports = {
  env: {
    browser: true,
    es2024: true,
    node: true
  },
  extends: "eslint:recommended",
  globals: { atom: "readonly" },
  parserOptions: {
    ecmaVersion: "latest",
    sourceType: "commonjs"
  },
  rules: {},
};
