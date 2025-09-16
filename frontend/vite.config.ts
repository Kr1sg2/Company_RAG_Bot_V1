import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 8080,
    proxy: {
      // Dev proxy: forward /api to backend
      '/api': {
        target: 'http://localhost:8601',
        changeOrigin: true,
        secure: false
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
});

