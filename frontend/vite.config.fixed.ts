import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 8082, // Updated to match your actual dev port
    host: '0.0.0.0', // Allow external connections
    proxy: {
      // Dev-only: proxy /api requests to backend
      '/api': {
        target: 'http://127.0.0.1:8601', // Backend dev server
        changeOrigin: true,
        secure: false,
        timeout: 30000, // 30 second timeout for long requests
        configure: (proxy) => {
          proxy.on('error', (err, req, res) => {
            console.error('Proxy error:', err);
          });
          proxy.on('proxyReq', (proxyReq, req, res) => {
            console.log(`Proxying ${req.method} ${req.url} -> ${proxyReq.path}`);
          });
        }
      },
      // Proxy file requests for document viewing
      '/files': {
        target: 'http://127.0.0.1:8601',
        changeOrigin: true,
        secure: false
      }
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom'],
        },
      },
    },
  },
  define: {
    // Expose environment variables to the app
    __APP_VERSION__: JSON.stringify(process.env.npm_package_version),
  },
  optimizeDeps: {
    include: ['react', 'react-dom', 'react-router-dom'],
  },
});