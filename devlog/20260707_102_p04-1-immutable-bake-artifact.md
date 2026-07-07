# 20260707_102 — P04.1: 불변 Bake 아티팩트 (백엔드)

[P04](20260707_P04_editor-bake-vault-restructure.md) 1단계. bake를 덮어쓰기 → **불변·명명·보존 스냅샷**으로.

## 변경

- **Release 모델**: `kind`(published|bake|transient) + `source_graph` FK(provenance) 추가.
  `version` max_length 50→80(`GeologicTimeScale.Release.YYYYMMDD.NN` 수용). ordering=`-created_at`.
  migration releases.0004(스키마) + 0005(데이터: 기존 `graph:*` → transient).
- **services**:
  - `snapshot_graph(graph, label=None)` — **새 불변 Release(kind=bake)** 생성(덮어쓰지 않음), source_graph 기록.
  - `next_release_version()` — `GeologicTimeScale.Release.YYYYMMDD.NN`(그날 순번 zero-pad).
  - `bake_graph` — verify용 scratch `graph:<slug>`(kind=transient, Vault 숨김)로 유지, 레코드 빌드는
    `_write_graph_records`로 공유.
- **views**: `GraphBakeView.POST` → `snapshot_graph`(label body 옵션), `GET` → 이름 제안(`{suggested}`).
  `ReleaseViewSet` — Vault 목록에서 transient 제외 + `?kind=` 필터, list는 경량 `ReleaseListSerializer`.
- **serializers**: `ReleaseListSerializer`(records 없이 kind/source_graph/created_at/record_count),
  `ReleaseSerializer`에 kind/source_graph/created_at 추가.

## 검증

pytest **96 passed**(+5 신규: 불변·명명·순번·transient 재사용·Vault 제외). test_seed의 bake 엔드포인트
단언을 새 스냅샷 동작(kind=bake·GeologicTimeScale.Release.*·source_graph)으로 갱신.
프론트: `listReleases`가 transient scratch 제외(더 깔끔), `bakeGraph`는 스냅샷 생성으로 개선.

## 다음

P04.2(Editor Bake 버튼 + Save/Evaluate/Bake 구분 + 이름 제안 프리필) · P04.3(Vault 허브). 배포는 P04
프론트까지 묶어서(스키마 migration 포함 재시드/마이그레이트 필요).
