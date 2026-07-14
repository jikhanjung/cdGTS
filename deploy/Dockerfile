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

# gosu: entrypoint 가 root 로 시작해 마운트 디렉터리 소유 uid 로 권한을 드롭할 때 사용(비-root 실행).
RUN apt-get update && apt-get install -y --no-install-recommends gosu \
    && rm -rf /var/lib/apt/lists/* && gosu nobody true

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
# `COPY . .` 로 deploy/host/* (compose·deploy.sh·smoke·rollback·maintenance)도 /app/deploy/host/ 에 실린다.
# 운영 서버가 git 없이 이미지에서 이 파일들을 추출해 배포한다(git-free, deploy/host/_extract_and_deploy.sh · P08.6).
# 빌드된 SPA 를 이미지에 포함 (settings.FRONTEND_DIST / SPA 라우트 / collectstatic 이 소비).
COPY --from=frontend /fe/dist ./frontend/dist

RUN chmod +x deploy/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./deploy/entrypoint.sh"]
