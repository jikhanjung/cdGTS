# 20260703_020 — Phase 6: releases 앱 (버전·bake·diff)

> 계획 [P01](20260703_P01_app-build-plan.md) **Phase 6(마지막)** 완료 기록. 설계 [app-architecture §2.5](../docs/app-architecture.md).

## 한 일

여섯 번째 앱 `releases` — 최상위 조립자. 릴리스를 얼리고(bake) 두 릴리스를 diff.

### 모델 (`releases/models.py`)
- `ModelCandidate` + `CandidateOutput` — 네트워크 공존 경쟁 후보(독립 주소), 경계별 출력 분포.
- `Release` — 매니페스트: `Selection{boundary→candidate}` + `clamps`(M2M). **릴리스가 selection 소유**.
- `Clamp` — authored 거버넌스 clamp(owner·target·kind·value·ratified). graph 의 clamp 노드와 구분.
- `BoundaryRecord` — 한 릴리스에서 얼린 BoundaryGateway 스냅샷 = ICC bake(definition_type·value·uncertainty·
  method·candidate·narrative).

### 서비스 (`releases/services.py`)
- `bake_release` — selection 을 돌며 후보 출력 + 경계 현재 definition_type 을 BoundaryRecord 로 스냅샷.
- `diff_releases` — **값 diff**(같은 경계 value_ma 변화 +Δ)와 **토폴로지 diff**(retype·added·removed)를 **분리**.
  topology-diff.md 의 "값 diff 와 직교하는 축" 구현.

### API
- `GET /api/releases/`·`/{id}/`(레코드 포함) · `POST /{id}/bake/` · `GET /diff/?a=&b=`.
- admin: Release(Selection·Record 인라인) / ModelCandidate(Output 인라인) / Clamp / BoundaryRecord.

## 검증
- check 0 · migrate OK · **pytest 40 passed**(releases 5: bake 스냅샷·값diff·retype토폴로지·added·API).
- **live curl**: ICC-2023/09 → ICC-2024/12 diff — 값(base-cambrian 538.8→536.0, Δ−2.8) **vs**
  토폴로지(base-proterozoic **retype GSSA→GSSP**) 한 응답에서 분리 표기.
- **DoD 충족**: 릴리스를 얼리고 두 릴리스를 diff, 값/토폴로지 직교.

## 스택
- 추가 없음. `releases.apps.ReleasesConfig` → INSTALLED_APPS, `/api/` 마운트.

## P01 계획 완주
- Phase 0(환경)~6(releases) **전부 완료**. 5개 앱(chrono/nodes/graph/engine/releases) + React Flow 에디터.
  미션 재정의("사람이 clamp, 기계가 전파·정합·diff")의 **전파(engine)·정합(certificate)·diff(releases)** 골격 완성.
- 남은 것(후속): 무거운 계산 커널(MC/베이지안/joint), 브라우저 육안 검증, 인증·소유권, PostGIS(공간),
  narrate(GTS) 충실화, clamp 노드↔releases.Clamp 통합, 프론트에 releases/diff UI.

## 다음 후보
- HANDOFF/TODOs 를 "코드 착수 반영본"으로 갱신 / 위 후속 항목 중 선택 / 리뷰(R01).
