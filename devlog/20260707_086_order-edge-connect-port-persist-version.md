# 20260707_086 — order edge 연결/포트 영속화 · 헤더 버전 표시

085 배포(0.1.23) 이후 발견한 order edge 관련 버그 2건 + 버전 표시. 0.1.23 재빌드로 반영.

## 1. 새 order edge 가 실선으로 생성되던 문제 — Editor.jsx
`onConnect` 이 항상 `kind:'data'` 로 만들고 order 스타일도 안 붙였다.
- `isOrderConn(srcH,tgtH)` 추가 — `younger`(source·상단)→`older`(target·하단) 연결이면 order 로 판정.
- order 면 `kind:'order'` + 점선/보라(`ORDER_EDGE_STYLE`, apiToRF 와 공유). 저장 시 `rfToApi` 가 kind 직렬화 → 왕복.

## 2. 그룹 order edge 삭제 시 포트가 사라져 재연결 불가 — Editor.jsx
collapsed 그룹 포트는 경계 넘는 edge 에서 파생 → edge 삭제 시 포트 소실, 재연결 앵커 없음.
- `buildView` 에 unit 그룹 order 인터페이스 영속화. 내부 order 체인에서 youngest(내부 order target-only)/
  oldest(source-only)를 앵커로 계산 — 외부 경계 edge 를 지워도 유지되는 내부 체인 기반.
- **양쪽 포트 항상 노출**(younger 상단·older 하단). upper 경계가 없는 Quaternary 도 younger 포트 존재
  (앵커=`pub-meghalayan`). 포트 핸들 id 가 edge-파생과 동일(`out:<y>:younger`/`in:<o>:older`)이라 edge 있을 땐
  중복 없이, 지우면 유지 → 거기서 경계로 드래그하면 #1 로 점선 order edge 로 복구.

## 3. 헤더에 버전 표시 — App.jsx · vite.config.js · Dockerfile · index.css
`cdGTS` 브랜드 옆에 작게 `v0.1.23`.
- 단일 출처 = `config/version.py`. `vite.config.js` 가 빌드 타임에 읽어 `__APP_VERSION__` 주입(regex 파싱, 실패 시 'dev').
- Docker frontend 스테이지에 `COPY config/version.py /config/version.py` — 빌드 시 `../config/version.py` 동일 경로 해석.
- `.brand-ver` 작고 흐린 스타일.
