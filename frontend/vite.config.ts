import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 8080,
    proxy: {
      '/api': {
        target: 'http://localhost:8600',
        changeOrigin: true,
      },
      '/admin': {
        target: 'http://localhost:8600',
        changeOrigin: true,
      },
      '/auth': {
        target: 'http://localhost:8600',
        changeOrigin: true,
      },
      '/query': {
        target: 'http://localhost:8600',
        changeOrigin: true,
      },
      '/chat': {
        target: 'http://localhost:8600',
        changeOrigin: true,
      },
      '/files': {
        target: 'http://localhost:8600',
        changeOrigin: true,
      },
    }
  }
})
