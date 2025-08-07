module.exports = {
  env: {
    browser: true,
    es2021: true,
    node: true
  },
  extends: [
    'eslint:recommended',
    'prettier'
  ],
  plugins: [
    'prettier'
  ],
  parserOptions: {
    ecmaVersion: 2021,
    sourceType: 'script'
  },
  rules: {
    'prettier/prettier': 'error',
    'no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
    'no-console': 'off',
    'prefer-const': 'error',
    'no-var': 'error',
    'indent': ['error', 4],
    'quotes': ['error', 'single'],
    'semi': ['error', 'always']
  },
  globals: {
    // Global variables for the frontend
    'USE_MOCK_DATA': 'readonly',
    'API_BASE_URL': 'readonly',
    'currentUser': 'writable',
    'assignments': 'writable',
    'events': 'writable',
    'streams': 'writable',
    'selectedStream': 'writable',
    'currentStreamAnnouncements': 'writable',
    'authToken': 'writable'
  }
};
