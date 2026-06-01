module.exports = {
  env: {
    browser: true,
    es2022: true,
    node: true,
  },
  extends: 'eslint:recommended',
  globals: { atom: 'readonly' },
  ignorePatterns: ['tools/schemes/*'],
  parserOptions: {
    ecmaVersion: 2022,
    sourceType: 'module',
  },
  rules: {},
};
