# 20260705_062 — 중첩 노드그룹

> 단일 계층이던 노드그룹을 **N단 중첩**으로. Period⊃Subperiod⊃… 같은 시각 계층을 드릴인으로.
> 엔진은 여전히 평탄(그룹은 표현/편집용) — parent 는 뷰 계층만.

## 한 일

### 백엔드 (`graph` · 마이그레이션 0004)
- `NodeGroup.parent` self-FK(null=최상위, on_delete CASCADE). 직렬화 read/write(`parent` = 그룹 key).
- `_replace_topology` 2패스(그룹 생성 → parent 링크). validate: parent 존재·자기참조·**순환** 거부.
- 왕복·중첩·순환 거부 테스트(graph 12 passed).

### 프론트 (`Editor.jsx`)
- **buildView 통합 재작성** — `repOf(그룹키)` 로 노드를 현재 레벨 대표로 환원:
  `node`(직속) / `group`(하위그룹 = 자기 서브트리 대표, 접힌 노드) / `external`(현재 서브트리 밖 → 스텁).
  최상위·드릴인을 하나의 규칙으로. 서브트리 경계 넘는 엣지 → 그룹 포트 또는 좌우 스텁. 뱃지 = 서브트리 전체 노드 수.
- **중첩 편집** — 그룹 안에서 "하위그룹 만들기"(새 그룹 parent=현재 레벨), 병합은 사라진 그룹의 하위그룹을 대상으로 승격.
  "상위 레벨로 빼기", 해제 시 내용물·하위그룹을 상위로 승격.
- **내비게이션** — breadcrumb 전체 경로(각 조상 클릭 이동), "상위로" = parent. 저장/로드에 parent 왕복.

### 시드 데모 (`03_graphs`)
- `ages-carboniferous`(order 노드 유지)에 **Mississippian·Age / Pennsylvanian·Age** 두 하위그룹 중첩.
  Carboniferous age pub 6개를 아계별로 재배정 → 2단 중첩 시연(하위그룹 크로싱 포트 포함).

## 검증
- reseed: 그룹 14(top 12 + 중첩 2), cert L1·L2 pass, bake **177**(불변), parent 직렬화 왕복.
- `pytest` **84 passed**(중첩 왕복·순환거부·그룹수). 프론트 빌드 클린. **육안 확인 권장**(드릴인·하위그룹 포트).

## 한계
- 중첩은 표현 계층만 — 엔진 평탄 불변. UI 로 임의 N단 생성/편집 가능.
