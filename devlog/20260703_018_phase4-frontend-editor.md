# 20260703_018 — Phase 4: 프론트엔드 노드 에디터 (React Flow + Vite)

> 계획 [P01](20260703_P01_app-build-plan.md) Phase 4 완료 기록. 설계 [app-architecture §3](../docs/app-architecture.md).
> 스택이 Django 순수 서버렌더에서 벗어나 **Node/React 툴체인**으로 확장된 지점.

## 한 일

### 백엔드: 팔레트 소스 API (`nodes`)
- `GET /api/node-types/` (ReadOnlyModelViewSet) — slug/name/category/params_schema + 중첩 ports.
  프론트 팔레트를 **데이터로** 구동. serializers/views/urls + `/api/` 마운트. 테스트 1개 추가.

### 프론트엔드 (`frontend/`, Vite + React 18 + @xyflow/react 12)
- `vite.config.js` — dev `/api` → Django(:8000) **프록시**(CORS 불필요). prod 는 `npm run build` → `dist/`.
- `src/api.js` — REST 왕복(listNodeTypes/listGraphs/get/create/save/evaluate).
- `src/CdgtsNode.jsx` — 커스텀 노드. **포트별 Handle**(입력=좌·출력=우, id=포트명) → 연결이
  `source_port`/`target_port` 로 매핑. category 색(data 녹/process 청/clamp 보).
- `src/Editor.jsx` — 팔레트(카테고리별, **드래그**) + 캔버스(onDrop 으로 배치) + onConnect(엣지) +
  저장(PUT)·평가 버튼 + 검증오류 표시 + Background/Controls/MiniMap. API↔RF 변환(apiToRF/rfToApi).
- `src/App.jsx` — ReactFlowProvider 래핑. `index.css` — 팔레트/툴바/노드 스타일.

## 검증
- `npm install`(85 pkg, 0 vuln) · `npm run build` **성공**(191 modules, ~108 kB gzip).
- Django(:8000)+Vite(:5173) 동시 기동 → vite 가 index(root div+main.jsx) 서빙, **/api 프록시로
  node-types 12개(+ports) 수신**, `/src/main.jsx` 200. 백엔드 pytest 29 passed(node-types API 포함).
- **한계(정직)**: 헤드리스 환경이라 실제 브라우저 클릭(드래그 배치·엣지 연결·새로고침 복원)은 육안
  검증 못 함. 대신 (a) 빌드 통과 (b) 서빙+프록시 동작 (c) 저장/복원 왕복은 Phase 3 API 가 pytest+curl 로
  검증됨 — 즉 배관은 확인, 픽셀은 미확인. React Flow 표준 패턴 사용.
- **DoD**: 배관 기준 충족(웹페이지 위 노드 그래프 편집 + API 저장/복원). 브라우저 육안 확인은 사용자 몫.

## 스택
- 추가: `frontend/`(package.json — react/react-dom/@xyflow/react + vite/@vitejs/plugin-react).
  node_modules·dist 는 gitignore, package-lock.json 은 커밋.
- 백엔드 추가 없음(DRF 는 Phase 3).

## 알려진 소소한 것
- React StrictMode dev 이중호출 → 그래프 0개일 때 createGraph 가 2번 시도돼 중복 slug 400 가능
  (dev DB 엔 이미 그래프 존재해 미발생). prod 빌드엔 무관. 후속 정리 대상.

## 다음
- **Phase 5 `engine`** — pass-through 평가(값+출처 전파), EvalRun/NodeResult(콘텐츠 해시 증분),
  CoherenceCertificate 스텁. `/evaluate` 스텁 → 실동작, 에디터에 결과 뱃지.
