# 20260705_044 — ICC stage 까지 완성 (공표 릴리스 + 5 컬럼 차트)

> [042](20260704_042_icc-chart.md) 차트가 Period 에서 멈춰 있던 걸 **Epoch/Age 까지** 확장.
> finer 유닛(색·계보) + **공표 ICC 릴리스(ICS-2024/12)** 로 값을 정식화 → 실제 국제표처럼 5 컬럼.

## 한 일

### 1) finer 유닛 시드 (Epoch/Age)
- chart.ttl 에서 Epoch/Age 유닛 **134개** 추가(rank 4:35 · 5:99), 전부 공식 ICS 색 + broader 계보(parent).
- slug = 기존 이름매칭 재사용 or kebab(prefLabel). 기존 finer 경계 `base-<kebab>` 가 그대로 정렬되어
  **경계는 손 안 댐**. 예제 유닛 early-triassic 은 base 경계가 없어 차트에 안 뜸(중복 방지).
- units 42 → **176**(Eon4/Era10/Period22/Epoch38/Age102).

### 2) 공표 ICC 릴리스 — `ICS-2024/12` (seed `05_icc_release.json`)
- 단일 candidate `ics/2024-12`(global·committee-published) + **경계 175개** CandidateOutput/Selection.
  값·오차는 chart.ttl(GSSA→exact, GSSP→sym ±moe@2σ). seed bake → **BoundaryRecord 175**(null 0).
- releases 2 → 3 · records 5 → **180**. 이제 테이블·차트·Diff 가 완전한 공표 ICC 를 렌더.

### 3) 차트 5 컬럼 + 소스 토글
- 엔드포인트 리팩터: `build_icc_levels()` 공유. rank 1~5 타일링, 밴드 없는 rank 생략.
  - `GET /api/graphs/{id}/icc-chart/` — 그래프 bake(period+) → 3 컬럼(기존).
  - `GET /api/releases/{id}/icc-chart/`(신규) — 공표 릴리스 → **Eon~Age 5 컬럼**. 미-bake 릴리스 지연 bake.
- 프론트 "ICC 차트" 뷰: **소스 토글**(공표 ICC[기본,5컬럼] / 그래프 bake[3컬럼]) + 릴리스/그래프 선택.
  공식 ICS 색·배경밝기 라벨·로그/선형 스케일 그대로.

## 검증
- `pytest` **78 passed**(신규 release 차트 5-rank 테스트: ranks==Eon..Age, Age≥90, Triassic 색 #812B92).
- seed replace: units 176 · boundaries 175 · releases 3 · records 180(null 0). 프론트 빌드 클린.

## 이월
- 눈금 broken-scale(Phanerozoic 확대 관례) · 라벨 겹침(로그에서 Age 다수) 회피(가로 라벨/줌).
- 재시드 `--mode=replace` 필요(신규 유닛·릴리스). 다음 이미지에 포함.
