# 20260703_015 — Phase 1: chrono 앱 (정본 registry)

> 계획 [P01](20260703_P01_app-build-plan.md) Phase 1 완료 기록. 설계 [app-architecture §2.1](../docs/app-architecture.md).

## 한 일

첫 Django 앱 `chrono` — Layer 0 정본 registry. 값이 아니라 **이름·계보**.

### 모델 (`chrono/models.py`)
- `Unit` — 이중 명명(연대층서 ↔ 지질연대) 한 엔티티 양면. `rank`(Eon~Age 5단) + self-FK 위계.
  `chronostratigraphic_name`/`geochronologic_name` 프로퍼티(예: "Induan Stage" == "Induan Age").
- `Boundary` — 안정 슬러그 + `below`/`above`(→Unit) + `definition_type`(GSSP|GSSA, *현재* 분류).
  값·정의 스냅샷은 두지 않음(→ 후속 releases.BoundaryRecord).
- `BoundaryLineage` — `op(created|renamed|split|merged|retyped|deprecated)` + `sources` M2M. 토폴로지 diff 전제.
- `Authority` — ICS·subcommission·sandbox·fork, self-FK.
- `Ratification` — 경계 비준(year, authority).
- `Locality` — GSSP 노두(OneToOne Boundary). lat/lon 스칼라 → **PostGIS 착수 시 PointField 승격**.

### admin (`chrono/admin.py`)
- 6개 모델 등록. Boundary 에 Locality/Ratification/Lineage 인라인, autocomplete(below/above/parent),
  slug prepopulate. → "DB 관리" 1차 UI.

### fixture (`chrono/fixtures/initial_boundaries.json`)
- 스키마 §3 세 사례 시드: base-triassic(GSSP·국소보간) / base-proterozoic(GSSA·결정) /
  base-cambrian(GSSP·섹션간상관) + 단위 12개(위계 포함) + ICS + 노두 2 + 비준 3 + lineage 3. **24 객체.**
- 좌표는 날조 않고 null(스키마도 공란).

### 테스트 (`chrono/tests.py`, `pytest.ini`)
- fixture 로드·이중명명·separates+위계·GSSA 무노두·GSSP 노두/비준. **5 passed.**

## 검증
- `check` 0 이슈 · `migrate` OK · `loaddata` 24객체 · shell 조회(세 경계·이중명명·위계 체인) · `pytest` 5 passed.
- **DoD 충족**: 세 경계가 DB에 존재, definition_type·lineage·authority·노두 연결, 위계 조회 동작.

## 스택
- 추가 없음(Django + SQLite 그대로). pytest.ini 로 pytest-django 활성.
- `chrono.apps.ChronoConfig` → INSTALLED_APPS.

## 다음
- **Phase 2 `nodes`** — NodeType(타입 시스템) + Distribution(충실도 L0–L5) + 기본 타입 fixture.
