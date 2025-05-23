import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  test: {
    globals: true, // Use Vitest global APIs (describe, it, expect)
    environment: 'happy-dom', // Or 'jsdom'
    setupFiles: ['./vitest.setup.js'], // Optional setup file
    coverage: { // Optional: configure code coverage
      provider: 'v8', // or 'istanbul'
      reporter: ['text', 'json', 'html'],
    },
  },
});
