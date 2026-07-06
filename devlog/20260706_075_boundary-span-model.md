# 20260706_075 — boundary/span 이중성 모델 + 그래프 재구성 (예제 4)

> 지질컬럼을 **셀 복합체**로 재구성: 경계(0-셀, 점)와 시대(1-셀, span)가 교호하고, 경계는 인접 시대들이 공유.
> 스키마·엔진·시드·문서·테스트. 프론트는 [076](20260706_076_frontend-boundary-editor.md), 배포는 사용자.

## 모델 (`graph/models.py`, 마이그레이션 0005/0006)
- `NodeInstance.nature` = generic | **boundary** — 경계 점(독립 시민, 그룹에 담기지 않고 lower/upper 로 참조). node_type 과 직교.
- `NodeGroup.kind` = container | **unit**(span) + `unit`(정본 chrono 단위 FK) + `lower`/`upper`(bounding 경계 노드 FK).
- `Edge.kind` = data | **order** — 경계의 세로(시간축) 연결. 데이터 DAG 사이클 판정·평가 토폴로지에서 제외, L1 정합성만 읽음.
- order 노드 제거 → **order 엣지**로 대체 (younger=source/older=target 규약).

## 노드 타입·커널 (`seed/02_nodes.json`, `engine/kernels.py`)
- **boundary** 타입 — `age` 입력을 받아 통과, `out`·세로(older/younger) 포트. 상류 계산의 연대를 표시. 입력 없으면 자기 공표값.
- **unit** 타입 — 세분 없는 시대 span(older/younger 포트만, 값 없음).
- 커널: `boundary` = 입력 우선 pass-through.

## 그래프 재구성 (`seed/03_graphs.json`, 예제 4)
- 동일 GSSP 경계 **통합**(하나의 boundary 노드가 여러 게이트웨이 담당):
  - base-Cambrian·Paleozoic·Phanerozoic → `bnd-base-cambrian` (global δ13C model 이 연대 산출).
  - base-Triassic·Mesozoic → `bnd-base-triassic` (age-depth 모델).
  - base-Siderian·Paleoproterozoic·Proterozoic → `bnd-base-siderian` (GSSA 2500).
  - Cenozoic/Paleogene(66)·Neoproterozoic/Tonian(1000)·Mesoproterozoic/Calymmian(1600)·Archean/Eoarchean(4031) 흡수.
  - 동일점이 이제 같은 값(예: base-Phanerozoic 538.8→계산값 538.795 로 정합).
- 선캄브리아 **unit 노드 15개**(Ediacaran…Hadean) 생성 → boundary 사이 교호 삽입.
- boundary↔boundary 직접 order 엣지 제거(그룹/unit 이 매개) — boundary 는 항상 time-period 와만 order.
- **5-컬럼 레이아웃**: 왼쪽부터 Cenozoic·Mesozoic·Paleozoic·Proterozoic·Hadean/Archean. 컬럼 내 group/unit↔boundary 교호, 균일 세로 간격(16px). feeder(계산 노드)+데이터 leaf 는 해당 경계 왼쪽.

## 시드 로더 (`releases/management/commands/seed.py`)
- 순환 FK(NodeGroup.lower/upper ↔ NodeInstance.group) 대응: `handle_forward_references=True` + deferred 2-pass 저장.

## 직렬화·엔진 (`graph/serializers.py`, `engine/evaluate.py`)
- 직렬화: nature/kind/unit/lower/upper 왕복, order 엣지는 포트·사이클 검증 제외, 3-pass 토폴로지 재구성.
- 평가: order 엣지를 데이터 토폴로지에서 제외, L1 인증이 order 체인으로 선후 판정.

## 문서 (`docs/`)
- `boundary-span-duality.md`(+`_en`) 신설, `concept-map`(+`_en`) 에 링크.

## 검증
- pytest 90 passed(카운트·order 엣지·narration 테스트 갱신), evaluate·bake·certify 정상, 시드 재적용 OK.
