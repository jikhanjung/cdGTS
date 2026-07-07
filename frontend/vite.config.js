import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { readFileSync } from 'node:fs'

// Single source of truth for the version = config/version.py (used by deploy/build.sh). Read at build time and inject as
// __APP_VERSION__. In Docker the frontend stage copies config/version.py to ../config so this same path resolves.
function appVersion() {
  try {
    const txt = readFileSync(new URL('../config/version.py', import.meta.url), 'utf8')
    const m = txt.match(/VERSION\s*=\s*['"]([^'"]+)['"]/)
    return m ? m[1] : 'dev'
  } catch { return 'dev' }
}

// dev(serve): base '/' + /api 를 Django(:8000) 로 프록시 → CORS 불필요.
// prod(build): base '/static/' — Django/WhiteNoise 가 /static/ 에서 자산 서빙,
//              index.html 은 SPA 라우트(TemplateView)로 루트에서 서빙.
export default defineConfig(({ command }) => ({
  base: command === 'build' ? '/static/' : '/',
  plugins: [react()],
  define: { __APP_VERSION__: JSON.stringify(appVersion()) },
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
