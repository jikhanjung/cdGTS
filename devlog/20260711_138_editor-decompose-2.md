# 20260711_138 — Editor.jsx 분해 2차 (상호작용 스모크 + 인스펙터 핸들러 훅)

[분해 1차](20260711_137_editor-decompose.md) 후속. 기록한 순서대로 **상호작용 스모크로 안전망을 먼저 두껍게 한
뒤** 깨끗한 seam만 추출한다.

## 1. 상호작용 e2e 스모크 (`frontend/e2e/smoke.spec.js`)

Tier2 스모크가 boot/render/login 만 덮던 것을 확장(익명·무변경):
- **auto-evaluate 렌더** — 기본 그래프(Example ① Precambrian GSSA) 로드 시 **2500 Ma** 노드가 표시되는지.
  `runEvaluation`(평가+결과부착) 전 경로를 브라우저에서 실동작 검증(Tier1 이 백엔드에서 덮는 것의 프론트 짝).
- **그룹 노드 렌더** — Example ④(그룹 15개) 선택 → collapsed 그룹 노드가 뜨는지. 1차에서 추출한 `buildView` 의
  최상위 출력을 브라우저에서 커버.
- ⚠️ **드릴인(더블클릭) 자동화는 보류** — React Flow 의 `onNodeDoubleClick` 이 Playwright 합성 이벤트
  (dblclick/force/dispatchEvent)로 깨어나지 않아 신뢰성 있게 자동화 못 함(기능은 실제 마우스로 동작). activeGroup
  전환 경로는 수동 검증으로 남기고, buildView 최상위 출력만 스모크로 커버.

## 2. 인스펙터 핸들러 훅 (`useNodeInspectorHandlers.js`)

`patchNodeData` + `onLabel`·`onDescription`·`onParam`·`onDist`·`onReplaceParams`(setNodes) + `onGroupName`
(setGroups)를 훅으로 추출. **의존이 setNodes/setGroups 뿐인 깨끗한 seam** — view/selection 상태와 무관.

## 의도적으로 남긴 것 — graph-actions / selection 훅은 추출 안 함

R02 가 지목한 나머지 seam 은 조사해보니 **core state(nodes/edges/groups/selection/activeGroup)에 깊게 얽혀**
있어, 훅으로 빼면 **인자 10~18개·반환 15개짜리 leaky 추상**이 된다(예: `runEvaluation`/`onSave`/`bake`/`propose`
는 graphId·nodes·edges·groups·gateways·dirty·getViewport·graphSig + 8개 setter 에 의존; outputs·runMeta·
showResults·verifyData·bakeDialog 는 렌더·hydrate 리셋에도 얽힘). 이건 **분해가 아니라 재배치**라 코드가 오히려
나빠진다 → 추출하지 않음. **Editor 의 남은 ~966줄은 대체로 응집된 컴포넌트 로직**이라, 여기서 큰 분해는 마무리.

## 결과·검증

- `Editor.jsx` **990 → 966줄**. 누적 1차+2차로 1252→966(−23%), + `graphView.js`·`EditorMenu.jsx`·
  `useNodeInspectorHandlers.js` 로 관심사 분리.
- `npm run build` 정상. 배포 **0.1.53** 후 브라우저 스모크 **5/5**(app boots·editor 마운트·auto-eval 2500·
  그룹 노드 렌더·login CSRF) 통과.

## 다음 (선택)

- 더 쪼갤 여지는 프레젠테이션(bake/graph-info 다이얼로그 → 컴포넌트) 정도. 저위험·저이득. 훅 분해는 위 이유로 종결 권장.
