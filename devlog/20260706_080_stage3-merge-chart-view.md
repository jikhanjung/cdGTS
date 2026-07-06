# 20260706_080 — Stage 3: merge 출력을 ICC Chart 뷰로

P03 Stage 3. merge 노드의 산출(geometry)을 프론트에서 직접 볼 수 있게 하고, 낡은 "bake" 프레이밍 정리.

## 변경 (frontend only)
- **`IccChart.jsx` — "Merge" 선택기**: graph 소스에서 graph detail의 merge 노드(`node_type=merge`, `group==null`)를 모아 종단 `icc-chart`(전 차트, 기본) + 컬럼 merge 5개를 드롭다운으로. 선택 시 `?node=`로 그 merge의 부분 차트를 렌더.
- **`api.js`**: `iccChart(id, node)` — `node` 있으면 `?node=<key>` 부착.
- **라벨/설명 갱신**: "Graph bake" → "Graph (merge)". 그래프 차트는 bake가 아니라 종단 merge의 **라이브 산출**(evaluate → tile)임을 명시. 낡은 "3 columns (network, period+)" 문구 제거(이제 Eon~Age 전 rank).

## bake 은퇴 범위
- 그래프 차트(`IccChartView`)는 원래 BoundaryRecord bake가 아니라 evaluate 로 뽑고 있었음 → 백엔드에서 뗄 chart-bake 없음.
- bake 는 계획대로 **릴리스 차트 + narrate + diff** 에만 유지(P03 결정 ②).
- 따라서 Stage 3 실질 = merge 산출을 UI 노출 + bake 프레이밍 정리.

## 검증 (dev, live)
- 종단 `icc-chart` = 22 period(전 차트). `merge-cenozoic`=3, `merge-mesozoic`=3, `merge-paleozoic`=6 — 컬럼 부분 차트 정확.

## 다음 (선택)
- Editor 에서 merge 노드 클릭 시 인스펙터 미니 차트.
- age unit 채우기 + unit→group 재귀, narrate/diff 의 geometry 수렴(별도 라운드).
