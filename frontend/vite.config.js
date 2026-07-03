import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// dev: /api 를 Django(:8000) 로 프록시 → CORS 불필요.
// prod: `npm run build` → dist/ 를 Django 가 서빙(추후).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
  build: {
    outDir: 'dist',
  },
})
