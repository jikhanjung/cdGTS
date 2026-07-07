# 20260707_P04 — Editor → Bake → Vault: 메뉴/아티팩트 재구성 (계획)

아크 C(멀티유저) 착수 전, 정보구조를 먼저 정리한다. C의 공유·fork·PR·비교 단위가 되는
"아티팩트"를 1급 객체로 세우는 선행 작업.

## 배경 / 문제

- 현재 최상위 nav: **Editor · ICC Table · ICC Chart · ICC Narrative · Releases Diff**.
- Editor 외 4개는 전부 "그래프를 bake한 결과물(**Release**)의 뷰"다: Table/Chart/Narrative = 한 Release의
  **표현**, Diff = 두 Release의 **비교**. 즉 (표현 축 × 아티팩트 축)으로 갈라진 것뿐.
- bake 순간이 UI에서 암묵적이고, 결과물(아티팩트)이 1급으로 보이지 않는다.

## 결정 (합의됨)

- 최상위 nav 2개: **Editor** · **Vault**.
- 아티팩트 인스턴스 = **Release**(기존 모델 재사용).
- **Vault** = Release들을 모아 보관·열람·비교하는 창고(불변·오래 보존 뉘앙스). 1개 선택 → 표현 토글
  (Table/Chart/Narrative), 2개 선택 → Diff.
- Editor의 3동사 분리: **Save**(소스 커밋) · **Evaluate**(일시 미리보기, 버림) · **Bake**(이름/버전 붙은
  불변 Release 생성 = "결과물을 하나 만들어내는 순간"). 문서의 "ICC=bake / GTS=narrate"가 이 Bake.

## 현재 상태 / 갭 (코드 확인)

- `bake_graph`(releases/services.py:24–43): `version=graph:<slug>` 릴리스를 get_or_create 후 records를
  **전부 delete→재생성** → **매 bake가 덮어씀. 이력/불변성 없음.** ← P04 핵심 수정점.
- ICC Chart는 그래프를 bake 없이 **라이브로도** 렌더(graphs/{id}/icc-chart ?node=) → live vs baked 경계 정리 필요.
- 뷰 컴포넌트 4종(IccTable·IccChart·Narrate·ReleasesDiff)은 이미 존재 → 작업의 주는 **재배치**.

## 목표 구조

- **Editor**: 편집 + Save/Evaluate + **Bake 버튼**(현재 상태 → 이름/버전·provenance 붙은 Release 스냅샷,
  이력 보존).
- **Vault**: Release 목록(내 bake + 공표 릴리스 ICS-2024/12 등) → 1개 선택 시 표현 토글(Table/Chart/
  Narrative), 2개 선택 시 Diff. 기존 4개 라우트를 Vault 내부 모드로 흡수.

## 단계

- **P04.1 아티팩트 모델(백엔드)** — bake를 불변·버전·보존으로. 덮어쓰기 대신 새 Release 스냅샷 생성
  (version 표기 = 순번/timestamp/사용자 라벨 중 택), provenance 필드(source graph FK + 편집 시점/graph
  content-hash + baked_at). "종류" 구분(bake 스냅샷 vs published 공표 vs baseline). 목록/조회 API.
- **P04.2 Editor Bake 액션(프론트)** — Save/Evaluate/Bake 3버튼 명확화(상태표시와 함께). Bake → 라벨 입력
  (**편집 가능한 기본값 자동 제안**: `GeologicTimeScale.Release.YYYYMMDD.NN`, NN=그날 순번 zero-pad) →
  Release 생성 → Vault로 이동 옵션.
- **P04.3 Vault 허브(프론트)** — nav 2개로 축소. Vault: 목록 + 표현 토글(뷰 4종 재사용) + Diff(2선택).
- **P04.4 live vs baked 경계** — 라이브 미리보기는 Editor 문맥 유지, Vault는 baked Release만.

## 열린 결정

- bake 버전 표기 — **기본 제안 `GeologicTimeScale.Release.YYYYMMDD.NN`**(편집 가능). NN은 그날 순번(zero-pad),
  기존 bake 조회로 증가. **멀티유저(아크 C) 전환 시 중간에 user id 삽입 →
  `GeologicTimeScale.Release.<userid>.YYYYMMDD.NN`**(사용자별 네임스페이스 + `version` 유니크성 자연 확보).
  기존 `graph:<slug>`·`ICS-2024/12` 표기와 공존.
- Release "종류" 명시 필드(kind: bake|published|baseline) 도입 여부 — 현재는 version 문자열/is_baseline로 부분 구분.
- Vault 목록 범위·가시성 — 현재 전부 공개, C에서 소유·가시성 부여.

## 아크 C(→ P05)와의 seam

- Vault의 아티팩트(불변 Release + provenance)가 **C의 공유·fork·PR·비교 단위**. P04에서 아티팩트를 1급으로
  세우면 C는 "아티팩트에 owner·가시성·리뷰를 붙이는 일"로 축소된다.
- **Bake = CD의 deploy/release 순간.** proposed→ratified 승격 워크플로우는 P05(아크 C).
- bake 이름에 **user id 세그먼트 삽입**(`...Release.<userid>.YYYYMMDD.NN`)이 C 전환의 자연스러운 접점 —
  사용자별 네임스페이스가 곧 소유·가시성의 씨앗.
