import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: { proxy: { '/api': 'http://localhost:8000' } },
  test: { include: ['tests/**/*.test.{ts,tsx}'], environment: 'jsdom', setupFiles: ['./tests/setup.ts'], restoreMocks: true },
});
