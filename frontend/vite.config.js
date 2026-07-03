import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// dev(serve): base '/' + /api 를 Django(:8000) 로 프록시 → CORS 불필요.
// prod(build): base '/static/' — Django/WhiteNoise 가 /static/ 에서 자산 서빙,
//              index.html 은 SPA 라우트(TemplateView)로 루트에서 서빙.
export default defineConfig(({ command }) => ({
  base: command === 'build' ? '/static/' : '/',
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
}))
