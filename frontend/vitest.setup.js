import { config } from '@vue/test-utils';
import { createPinia } from 'pinia';

// Example: Make Pinia available to all tests if needed globally
// This can also be done per test suite by installing pinia in the test file.
// const pinia = createPinia();
// config.global.plugins.push(pinia);

// Mock global objects or functions if necessary
// For example, if using i18n:
// import { createI18n } from 'vue-i18n';
// const i18n = createI18n({ legacy: false, locale: 'en', messages: { en: {} } });
// config.global.plugins.push(i18n);

// Clean up after each test (e.g., clear mocks)
import { afterEach } from 'vitest';
// import { vi } from 'vitest'; // if using vi.mock for extensive mocking

afterEach(() => {
  // vi.clearAllMocks(); // if using vi.mock
  // vi.resetAllMocks();
  // Clear localStorage or other global states if tests modify them
  // localStorage.clear();
});

console.log('Vitest global setup file loaded.');
