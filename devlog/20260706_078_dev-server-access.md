# 20260706_078 — 개발/테스트 서버(m710q) 외부 접근 + HANDOFF

> tailnet/LAN 에서 개발서버 docker 컨테이너에 접근. 배포는 사용자.

## 개발서버 접근 (`deploy/host/docker-compose.yml`)
- m710q 의 dev 컨테이너(포트 8011, `/srv/cdGTS/db.sqlite3`)를 tailscale 호스트명/IP·ethernet 주소로 접근 가능하게 bind·ALLOWED_HOSTS 반영.
- m710q 는 빌드 호스트 겸 dev 호스트. WIP 이미지는 `honestjung/cdgts:0.1.19-wip` 로 로컬 빌드 후 compose 로 직접 실행(Hub push·git commit 없이), `seed --mode=replace` 로 재시드.

## HANDOFF (`HANDOFF.md`)
- boundary/span 모델 작업 상태 및 배포 절차(운영 dolfinid ↔ 개발 m710q) 갱신.

## 참고
- dev DB(`/srv/cdGTS/db.sqlite3`)는 운영 미러로 야간 cron 이 덮어씀 — WIP 재시드는 일시적.
