# 20260707_084 — 그룹 내부 열 인터리브 · exit-to-parent 버튼 · 그래프 목록 정렬

세 가지 작은 개선. 평가/차트 로직 영향 없음(좌표·정렬·UI).

## 1. 시대 그룹 내부: boundary + time-period 단일 열 인터리브 (seed/03_graphs.json)
각 age 그룹에 드릴인하면 boundary(`published-age`)와 time-period(`unit`)가
`x=2380` / `x=2570` 두 개의 나란한 열로 갈라져 있었다. 최상위 그래프(선캄브리아 열,
x=2350에서 unit·pub 교대)처럼 **하나의 열(x=2570)에 세로 교대 배치**하도록 좌표만 수정.

- 간격 리듬은 최상위 그래프와 동일: `unit` 뒤 +68, `boundary` 뒤 +42
  (unit 노드가 더 커서 겹치지 않고 균일하게 끼어든다). 예) Cambrian:
  `unit-cambrianstage10`(954) → `pub-cambrianstage10`(1022) → `unit-jiangshanian`(1064) …
- merge 노드는 열 오른쪽(x=2830)에서 세로 중앙에 재배치.
- 적용: boundary·unit 두 열이 모두 있는 11개 그룹(cambrian, ordovician, silurian,
  devonian, permian, triassic, jurassic, cretaceous, paleogene, neogene, quaternary).
- 제외: Carboniferous 는 boundary 가 한 단계 아래 하위 그룹(Mississippian·Pennsylvanian)에
  들어 있어 이 레벨엔 boundary 열이 없다 → 손대지 않음.
- 좌표(x/y)만 변경, 엣지·노드 수·구조 그대로. 새 DB fixture 로드 검증 완료.

## 2. exit-to-parent 버튼 (Editor.jsx · index.css)
그룹에 드릴인했을 때 캔버스 **좌상단**에 상위로 나가는 버튼 추가.
- React Flow `<Panel position="top-left">` 오버레이 (Controls 좌하단·MiniMap 우하단과 안 겹침).
- 핸들러는 우클릭 메뉴의 *Exit to parent* 와 동일(`setActiveGroup(activeGroupObj?.parent || null)`).
- 라벨: 상위가 그룹이면 `↰ Parent`, 최상위로 나가면 `↰ Top level`.
- 기존 상단 breadcrumb 네비게이션은 유지, 캔버스 코너 버튼을 별도로 얹음.

## 3. 그래프 드롭다운 정렬: slug → name (graph/models.py · migration 0007)
드롭다운이 `Graph.Meta.ordering = ["slug"]` 라 slug 알파벳순(`example-cambrian-base`,
`example-gssa-precambrian`, `example-icc-partial`, `example-permian-triassic`)으로 ③①④② 로 보였다.
- `ordering = ["name"]` 로 변경. name 이 "Example ①②③④" 원문자로 시작 → 보이는 문자열순 = 1,2,3,4.
- 마이그레이션 `0007_alter_graph_options`(메타 옵션만, 스키마 무변경).
- 부수효과: 첫 로드 기본 그래프가 Example ①(선캄브리아 GSSA)로 바뀜.

## 비고
- boundary 프레임 제목 출처 확인: 그룹의 `upper`/`lower` FK 가 가리키는 **바깥 바운더리 노드의
  label 을 렌더 시점에 조회**(제목을 그룹이 복사 저장하지 않음). 참조 제거(토폴로지 유도)는
  논의했으나 경계 공유·`upper=None` 처리 이유로 **현행 유지** 결정.
