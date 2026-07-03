# HANDOFF — Current Work Status

**Last updated**: 2026-07-03 (하루 세션으로 **빈 브레인스토밍 저장소 → 개념 코퍼스 13주제(한/영 26파일) + 경계 게이트웨이 스키마 v0**. 흐름: 개념 3(idea 레이어 0–6·node-graph 패러다임·README) → **사례 검증 3**(P–T GSSP 국소보간 251.902±0.024 / 선캄 GSSA 결정 2500 / 캄브리아 GSSP 섹션간상관 538.8±0.6) → **스키마 v0** → **설계 심화 6**(전역 vs 경계별 버전 · 정합성 게이트 Layer 5 L0–L3 · 경쟁모델 네트워크복수후보+릴리스선택 · 순환→**clamp** · 토폴로지 diff · 분포 표현 L0–L5) → **통합 개념지도**. 스키마 §4 열린 질문 5개 전부 정리. 주요 봉합: **provenance 깊이=단일 축** / **clamp가 GSSA·순환·분포 통일**(GSSA=Clamp{pin}=점질량) / **ICC·GTS=bake·narrate 반복** / 게이트웨이·네트워크 2계층 반복 / Layer 5=여러 이름의 한 노드(전역종합=게이트=joint=공분산). 미션 재정의: "자동 계산"이 아니라 "subcommission이 clamp를 놓고 기계가 전파·정합·diff". devlog 001~012 + 커밋 12개 push. 한/영 쌍 유지 규칙 memory 기록. **코드·데이터 포맷·스택은 전면 미정**.)

> 과거 작업 내역은 `devlog/` 에 모두 기록됨. 본 문서는 **현재 상태 + 다음 작업**만 유지.
> 개념 전체 지도는 `docs/concept-map.md`. 항목별 상세 backlog 는 `TODOs.md`. 저장소 성격은 `CLAUDE.md`.

## 현재 상태

- **성격**: 개인 브레인스토밍 저장소 — 코드베이스가 아니라 아이디어 저장소 (CLAUDE.md).
- **문서 코퍼스**: `docs/` 13주제 × 한/영(`_en.md`) = 26파일 + README 한/영. **진입점 `docs/concept-map.md`**.
- **레이어 모델**: 정수 사다리 **0–6** (명명·경계정의·원시관측·국소 age model·상관·전역종합/정합성게이트·배포).
- **스키마**: `docs/boundary-gateway-schema.md` **v0** — 두 다형 축(`definition.type` GSSP|GSSA / `age.method`
  decreed|local-interpolation|cross-section-correlation) + `ModelCandidate`·`Release`·`Clamp`·`identity.lineage`·
  구조화 `uncertainty`. §4 열린 질문 5개 전부 정리, 세 사례 YAML 예시.
- **핵심 원시타입**: **clamp** (subcommission 이 그래프에 놓는 hand-crafted 거버넌스 게이트; GSSA = `Clamp{pin}` 특수사례).
- **미결정**: 데이터 직렬화 포맷 · 코드 · 실제 데이터 소스 연동 (착수 전 논의 필요). **스택은 잠정 Django 5.2**
  (브레인스토밍 종료 후 이 저장소에서 개발 예정 — 사용자 기존 스택 fsis2026 과 동일. 확정 아님).
- **devlog**: `devlog/YYYYMMDD_NNN_title.md`, NNN = 날짜 무관 단조증가 일련번호. 현재 **001~012**.
- **언어 규칙**: `docs/`·README 는 한/영 쌍 유지 (memory `bilingual-docs-convention`, `_en.md` 접미사 + 언어
  전환 링크 + 언어별 상호링크). HANDOFF/TODOs/devlog 는 한글 단독(fsis2026 관행).
- **원격**: `git@github.com:jikhanjung/cdGTS.git`, main 직접 커밋·push (개인 저장소).

## 개념 진척 한 줄 정리

> **개념 → 사례 검증(세 유형) → 스키마 v0(§4 열린 질문 5개 정리) → 통합 지도** 까지 한 바퀴 완주.
> 남은 것: **착수 결정**(데이터 포맷/스택) + 각 설계 문서 말미의 **미해결 열린 질문**(→ TODOs) + 추가 사례 검증.

## 최근 작업 (2026-07-03, 라운드별 상세는 `devlog/`)

- **개념 셋업** (devlog 001) — CLAUDE.md·README·idea.md(레이어)·node-graph-paradigm.md.
- **게이트웨이 재해석 + 사례 2** (002) — 레이어=계약, 중간 티어 발견. P–T(GSSP 국소보간)·선캄 GSSA(결정) 사례.
- **사례 3** (003) — 캄브리아 base(Fortune Head, 섹션 간 correlation이 load-bearing). 중간 티어가 (a)국소보간 /
  (b)섹션간상관 둘로 갈림 확인.
- **i18n** (004) — 전 문서·README 영어판(`_en.md`) + 언어 전환 링크.
- **스키마 v0** (005) — 세 사례를 아우르는 경계 게이트웨이 스키마, 두 다형 축 + 세 예시.
- **설계 심화** (006~011) — 전역 vs 경계별 버전(레코드+매니페스트) / 정합성 게이트(Layer 5, L0–L3, ICC=검증·GTS=재조정) /
  경쟁모델(복수후보+릴리스selection) / 순환(국소=joint추정, 전역=버전나선 + **clamp** 도입) / 토폴로지 diff(값 diff와
  직교, identity.lineage) / 분포 표현(충실도 사다리 L0–L5, 분해예산=공분산). 각 라운드마다 스키마 반영 + §4 항목 정리.
- **통합 개념지도** (012) — 12문서를 잇는 상위 지도 + 수렴점 5개. README 를 지도 구조에 맞춰 재편.

## 다음 작업

### 결정 대기 (즉시)

- [ ] **데이터 직렬화 포맷·착수 논의** — 브레인스토밍을 실제 구조로 넘길지, 넘긴다면 어떤 형태로.
  스택은 **잠정 Django 5.2**(+ PostGIS, 무거운 계산은 별도 과학 스택으로 분리 예상). 확정·세부 미정.
- [ ] **스키마 v0 → v1 승격 여부** — 열린 질문 반영본으로 올릴지, 현행 v0 유지할지.

### 개념 심화 (선택)

- [ ] **추가 사례** — Cryogenian base GSSA→GSSP 전환(진행형) = 토폴로지 diff 실례 / joint·공분산 워크드 예시.
- [ ] **기존 표준 정합 조사** — Macrostrat · GeoSciML/CGI Geologic Timescale · ICS 공식 차트 포맷 · Darwin Core.
- [ ] **미해결 열린 질문** — 각 설계 문서 말미 (최소 clamp 집합, 식별자 lineage 형식, 후보 큐레이션 문지기 등). → `TODOs.md`.
