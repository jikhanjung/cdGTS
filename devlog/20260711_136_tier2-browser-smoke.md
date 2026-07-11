# 20260711_136 — Tier-2 브라우저 스모크 스캐폴딩 (Playwright)

[devlog 134 §Tier 2](20260711_134_ci-flow-scenario-test.md) · [R02 검토 노트](20260711_R02_source-code-review.md)
후속. Tier 1(백엔드 `test_ci_flow.py`)이 login→fork→edit→bake→diff→propose→ratify 를 세션+CSRF 로 이미
고정했으니, Tier 2 는 **브라우저만 검증할 수 있는 seam**(SPA 부팅·React Flow 마운트·real JS 의 CSRF 로그인)만
얇게 덮는다. **비블로킹·opt-in** — `npm run build`/`deploy/build.sh` 에 안 엮이고, 릴리스 전 수동 실행.

## 구성 (`frontend/`)

- **`playwright.config.js`** — `testDir=e2e`, chromium 1개, `baseURL=E2E_BASE_URL`(기본 `http://127.0.0.1:8011`
  = 테스트 서버). 이미 떠 있는 배포본을 대상으로 도는 모델(별도 webServer 오케스트레이션 없음).
- **`e2e/smoke.spec.js`** — 해피패스 3개:
  1. `app boots` — brand·nav(Editor/Vault/Proposals/Bibliography)·Login 버튼 렌더 + uncaught pageerror 0.
  2. `editor mounts a graph (read-only, anon)` — 익명이 첫 시스템 그래프 자동 로드 → `.react-flow` +
     `.react-flow__node` 마운트 확인(React Flow + API fetch 가 브라우저에서 실동작).
  3. `login CSRF round-trip` — `E2E_USER`/`E2E_PASS` 있을 때만(없으면 skip). 로그인 → `.login-user`(username)
     + Logout 확인 → 로그아웃. **real JS 의 csrftoken→X-CSRFToken 왕복** 검증. 데이터 변경 없음(login/out 만).
- **`e2e/README.md`** — 실행법·env·왜 비블로킹인지·Tier 1 과의 역할 분담.
- **`package.json`** — `@playwright/test` devDep + `e2e`·`e2e:ui`·`e2e:install` 스크립트. `.gitignore` 에
  `playwright-report/`·`test-results/`.

## 검증

- `npm i` → `npm run e2e:install`(chromium) → **3 테스트 실측**: 익명 2개 pass + login(폐기 테스트 DB 에
  `e2e-smoke` 계정 임시 세팅) pass → **CSRF 로그인 seam 브라우저에서 실동작 확인**, 이후 임시 계정 삭제.
- 데이터 mutation 없음(fork/edit/propose 는 Tier 1 담당). 앱 코드/배포 변경 없음 — 테스트 툴링만 추가.

## 메모 / 다음

- 실행 대상은 "갓 배포된 인스턴스"(예: 테스트 서버) — 배포 후 스모크 → 승격 흐름에 맞춤. CI 자동화 시
  `webServer`(migrate+seed+테스트유저)로 self-host 하는 옵션은 후속.
- R02 우선순위 재정렬대로, 이 안전망을 확보했으니 다음은 **`Editor.jsx` 분해**가 낮은 위험으로 가능해짐.
