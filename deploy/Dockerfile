# cdGTS 이미지 (honestjung/cdgts).
# fsis2026 패턴 + 프론트(Vite SPA) 멀티스테이지 빌드.
# 빌드 컨텍스트 = 저장소 루트. build.sh / docker-compose.dev.yml 참조.

# --- stage 1: 프론트엔드 빌드 (Vite → frontend/dist, base=/static/) ---
FROM node:22-slim AS frontend
WORKDIR /fe
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
# version single-source: vite.config.js reads ../config/version.py at build → __APP_VERSION__
COPY config/version.py /config/version.py
RUN npm run build

# --- stage 2: Django ---
FROM python:3.12-slim
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
# 빌드된 SPA 를 이미지에 포함 (settings.FRONTEND_DIST / SPA 라우트 / collectstatic 이 소비).
COPY --from=frontend /fe/dist ./frontend/dist

RUN chmod +x deploy/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./deploy/entrypoint.sh"]
