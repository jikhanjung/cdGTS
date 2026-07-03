# TODOs

cdGTS(**continuously deployed Geologic Time Scale**) 브레인스토밍의 작업 백로그.
개념 전체 지도는 [docs/concept-map.md](docs/concept-map.md), 현재 상태 헤드라인은 [HANDOFF.md](HANDOFF.md).

> **HANDOFF.md** 는 짧은 현재상태/다음작업 헤드라인,
> 본 문서는 **미해결 항목별 상세**(주로 각 설계 문서 말미의 열린 질문).
> `devlog/` 시리즈가 라운드별 변경 기록. 저장소 성격·작업 방식은 `CLAUDE.md`.

---

## 0. 착수 결정 (브레인스토밍 → 구조)

> 아직 코드·스키마 직렬화·스택 **전면 미정.** 아래는 실제 개발 착수 전 결정할 것.

- [ ] **데이터 직렬화 포맷** — 스키마 v0(YAML 예시)를 실제 포맷으로 굳힐지 (JSON Schema / SQL / RDF·GeoSciML 등).
- [ ] **기술 스택** — **잠정 Django 5.2**(+ PostGIS; fsis2026 과 동일 스택·배포·권한 패턴 재사용). 무거운
  계산(베이지안 age-depth·joint 추정·정합성 게이트)은 Django 오케스트레이션 + 별도 과학 스택(numpy/scipy/PyMC)
  분리 예상. 평가 엔진·노드 그래프 UI 세부 미정. 확정 아님.
- [ ] **스키마 v0 → v1 승격** — 아래 열린 질문 반영본으로 올릴지 여부.
- [ ] **범위 결정** — Layer 5(정합성 게이트)·순환 joint 추정을 실제 *계산*까지 할지, "발표값+출처+clamp" 수준에서
      시작할지 (idea §7 — provenance 깊이 축의 다른 이름).

## 1. 추가 사례 검증

> 세 유형(GSSP 국소보간 / GSSA 결정 / GSSP 섹션간상관)은 완료. 모델을 더 조일 사례.

- [ ] **Cryogenian base GSSA→GSSP 전환** — 진행 중인 실제 재배선. **토폴로지 diff·clamp 제거·값 모양 변화
      (스칼라→분포)** 의 살아있는 예시. (topology-diff §6 에 스케치만 있음)
- [ ] **joint·공분산 워크드 예시** — 두 경계가 tracer/붕괴상수를 공유해 지속시간 오차가 상관되는 구체 사례
      (coherence-gate L2 / distribution C 를 실데이터로).
- [ ] **middle-type 변형** — correlation tier (b) 가 다봉(경쟁 상관가설)으로 나타나는 사례.

## 2. 설계 문서별 미해결 열린 질문

### 2.1 전역 vs 경계별 버전 ([versioning-global-vs-per-boundary](docs/versioning-global-vs-per-boundary.md) §5)

- [ ] 전역 릴리스 = **복사 스냅샷** vs **매니페스트/락파일** — 확정.
- [ ] 정합성 게이트를 **검증(validation)** 수준 vs **공동추정(joint inference)** 까지.
- [ ] **단조 순서 불변식** — hard constraint vs lint/경고 (대표 경계엔 드물지만 세밀 구간엔 필요).
- [ ] **공유 노드 재보정** 같은 전역 이벤트가 다수 경계 버전을 한꺼번에 bump 하는 것의 표기.
- [ ] **토폴로지/집합 변경**(경계 추가·삭제·개명) 버전의 위치 (경계 밖 전역 층?).
- [ ] **샌드박스 오버라이드**(베이스라인 + 델타) 스키마 표현.
- [ ] **인용**이 (경계 버전 + 전역 릴리스)를 함께 가리키는 최소 형식.
- [ ] **상관된 불확실성**(공유 오차 구조)의 릴리스 보존.

### 2.2 정합성 게이트 ([coherence-gate](docs/coherence-gate.md) §6)

- [ ] **L3b 재조정값**("릴리스 보정값")을 레코드값과 나란히 인용·표기하는 법. (→ 잠정: authored clamp 로, cycles §6)
- [ ] **L1b 겹침 WARN** 을 릴리스가 차단 vs 통과시키는 정책 (대표 경계 vs 세밀 구간 차등).
- [ ] **공분산 추적 범위** — 전체 공분산 행렬 vs 공유성분 태그만.
- [ ] **게이트 버전**(`gate_version`) — 검사 규칙이 바뀌면 과거 인증서의 지위.

### 2.3 경쟁 모델 ([competing-models](docs/competing-models.md) §7)

- [ ] **후보 큐레이션 문지기** — 샌드박스 후보 중 ICC 가 고려하는 후보 집합에 무엇이 드나.
- [ ] **모델 정체성/버전** — 입력이 바뀐 재실행은 새 후보 vs 같은 후보의 새 버전.
- [ ] **포락 가중치** — 모델 평균 시 가중치를 누가/어떻게.
- [ ] **조합 폭발** — 경계 N × 후보 M × 정합 제약 관리.
- [ ] **전역 후보 부분 채택** 시 정합성 유지.

### 2.4 순환 / clamp ([cycles](docs/cycles.md) §10)

- [ ] **최소 clamp 집합** — 모든 사이클을 끊는 최소 clamp 자동 제안 + 사람 승인.
- [ ] **버전 나선 수렴 판정·감쇠(damping)** 기준.
- [ ] **동시추정 노드 스코프 분할** — 전부 결합 불가 → 분할이 들여오는 근사.
- [ ] **clamp 간 충돌** — 두 subcommission clamp 가 경계에서 모순 시 중재.

### 2.5 토폴로지 diff ([topology-diff](docs/topology-diff.md) §9)

- [ ] **식별자 영속성 & lineage 형식** — 안정 id 부여 주체·영속성, split/merge lineage 기록 형식.
- [ ] **토폴로지 입도** — 줌 레벨에 따라 값 변화이기도 토폴로지 변화이기도 → 어느 층에서 diff 정의.
- [ ] **대규모 재배선 정렬** — id 우선 + 휴리스틱 + 미정렬 플래그.
- [ ] **selection diff vs 구조 diff** — ModelCandidate A→B 교체 분류.

### 2.6 분포 표현 ([distribution-representation](docs/distribution-representation.md) §9)

- [ ] **모델 간 다봉** — 분포에 담을지 selection 층으로 뺄지 (내부오차=분포 / 모델간=포락, 분리가 깔끔).
- [ ] **사후 샘플 저장·버전** — 무거움 → 참조, 임베드 금지.
- [ ] **레거시 `± 2σ`뿐 데이터**의 우아한 저하(L1).
- [ ] **희소 공분산 재구성 정확도** — 공유성분 태그만으로 충분한가.
- [ ] **canonical rung 확정** — 경계 정본 L2/L3 + joint(L4) 릴리스 층 (잠정 방향, 미확정).

### 2.7 idea 원래 열린 질문 ([idea](docs/idea.md) §7 — 일부는 clamp/provenance 로 재프레이밍됨)

- [ ] **권위 vs 실험 경계** — sandbox 결과와 공식 ICC 구분, 개인 fork 시대표 허용 범위.
- [ ] **기존 포맷 정합** — Macrostrat / GeoSciML·CGI / ICS 공식 배포 형식. (§1 사례와 함께)
- [ ] **버전 전략 구체화** — git 태그 · 시맨틱 버저닝 · 자동 검증(CI) 매핑.

## 3. 유지 관리

- [ ] **한/영 쌍 동기화** — 새 문서·수정 시 KR/EN 함께 (memory `bilingual-docs-convention`).
- [ ] **devlog 일련번호** 단조증가 유지 (현재 012 까지).
