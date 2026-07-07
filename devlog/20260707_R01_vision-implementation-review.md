# 20260707_R01 — 초기 비전 대비 구현 현황 전반 리뷰

`docs/` 초기 구상 · 설계 문서 9종 · 실제 코드(chrono·nodes·graph·engine·releases + 프론트) 3자 대조.
(병렬 조사 3건: 핵심 비전 문서 / 설계 메커니즘·열린질문 / 구현 인벤토리.)

## 한 줄 결론

뼈대·배관은 거의 다 놓였다(그래프 엔진·티어×카테고리·bake/narrate·증분평가·ICC 차트·정합성 L1/L2 —
실동작·배포됨). 가장 야심찼던 두 축은 미착수: **(A) 확률적·베이지안 결합 추정 "진짜 과학 엔진",
(C) 여러 학자가 붙는 "과학을 위한 CI" 플랫폼(인증·소유·샌드박스)**. 현재 = "잘 만든 단일 사용자
그래프 에디터 + 결정론적 파이프라인". 원래 비전의 절반쯤.

## 초기 아이디어 → 구현 상태

| 초기 구상 | 현재 | 상태 |
|---|---|---|
| 노드 그래프(DAG) 산출물 | Graph·NodeInstance·Edge + React Flow + topo 평가 | ✅ 견고 |
| 레이어 L0–6 | 티어×카테고리로 접힘 | 🔄 개념 진화 |
| 게이트웨이 아키텍처 | chrono·graph·releases 3티어 + Gateway | ✅ 견고 |
| 증분 재평가 | content-hash(sha1) 캐시 | ✅ 견고(CI 핵심) |
| ICC=bake / GTS=narrate | bake_release·bake_graph / narrate(결정적 템플릿) | ✅ 견고 |
| Science CI | graphs/{id}/verify vs baseline | ✅ 동작 |
| 경계·구간 이중성(cell complex) | nature·NodeGroup.kind/unit/lower/upper·Edge.kind=order | ✅ 완료 |
| clamp pin/range/order/freeze | pin·range·order 실동작 | ⚠️ 부분(freeze·거버넌스 미연결) |
| 정합성 L0–L5 | L0·L1(order edge)·L2(duration) | ⚠️ 부분(L1b·L2 warn·L3 없음) |
| Distribution L0–L5 | L0–L3 실사용 | ⚠️ 부분(L4 joint·L5 full 껍데기) |
| 확률적 전파(MC/Bayesian) | spline age-depth = CubicSpline+MC | ⚠️ 얕음(베이지안 없음) |
| 순환(joint/버전 spiral) | joint-inference=역분산 가중합(해석적) | ⚠️ 스텁 |
| 경쟁 모델(Candidate/Selection) | 데이터 구조만 | ⚠️ 로직 없음 |
| topology diff | slug 집합 diff+retype | ⚠️ lineage 미소비 |
| 공간(PostGIS/분산 provenance) | Locality=평범한 lat/lon | ❌ 미착수 |
| 인증·소유·샌드박스 | 전 API AllowAny | ❌ 미착수 |
| 상호운용(Macrostrat·GeoSciML) | 없음 | ❌ 미착수 |

## 바뀐 것 (개념 진화 — 대체이지 미구현 아님)

1. **L0–6 선형 레이어 → 티어×카테고리.** 레이어 번호는 노드의 *종류*와 *위치*를 혼동. DAG에선 위치가
   라벨일 수 없다 → 종류(data/process/clamp)만 1급, 레이어는 "읽는 순서"로만 생존.
2. **order 노드 → order 엣지.** boundary-span-duality 재설계: 경계는 포함이 아니라 참조(group.lower/upper),
   order는 연결. order 노드 137개 소거, 예제 노드 수 거의 반감. 하나의 GSSP를 여러 span이 공유(cell complex).
3. **미션 재정의.** "기계가 자동 계산" → "사람이 책임 clamp를 놓고, 기계가 전파·정합·diff". idea §7의 큰
   갈림길("계산 엔진 vs 발표값+출처")에 대한 제3의 실용적 답 — 현재 구현이 이 지점.

## 남은 큰 작업 (테마별)

### A. 과학 엔진 심화 (가장 깊은 미완 — 프로젝트 난이도를 가르는 축)
- 진짜 joint/베이지안 커널(PyMC + 별도 워커). 현재 실커널은 age-depth 하나, 나머지 pass-through.
- Distribution L4(joint)·L5(full): 공유성분 태그 + 희소 공분산 → duration 오차 제대로.
- 정합성 게이트: L1b(2σ 겹침 warn)·L2 warn 임계·L3a 검증/L3b reconcile. L1 게이트웨이 fallback 스텁 → 연대순.

### B. 거버넌스·릴리스 성숙 (구조는 있는데 로직이 빔)
- clamp 통합: releases.Clamp(authored) ↔ graph clamp 노드/order 엣지 배선(현재 미연결).
- 경쟁 모델 선택: 큐레이션 게이트키퍼·모델 정체성/버전·envelope/BMA·global vs local candidate 정합.
- 전역 vs 경계별 버전: manifest/lockfile·전역 이벤트 표현.
- lineage 기반 topology diff: BoundaryLineage 소비(split/merge를 delete+add로 오인 방지).

### C. 멀티유저 플랫폼 ("CI for science"의 미완 절반)
- 인증·소유·샌드박스 권한(현재 AllowAny). "내 브랜치 시대표" fork + PR 워크플로우.
- **프로젝트 이름값("continuously deployed")의 정체성인데 아직 단일 사용자 도구** — 가장 큰 간극.

### D. 공간 차원
- PostGIS: Locality PointField, 지리적 분산 provenance, locality별 노드그룹.

### E. 상호운용 / 데모
- Macrostrat·GeoSciML/CGI·ICS 포맷 왕복; git tag/semver/CI 매핑.
- Cryogenian GSSA→GSSP retype 실데모(topology diff + clamp 제거 + scalar→분포). joint/공분산 워크드 예시. R01 코드 리뷰(본 회차).

## 다음 단계

방향 하나를 고른다면 A(차별점의 원천, 도메인 난이도 높음) vs C(이름값 실현, 표준적 웹 작업). 사용자와
합의 후 P 시리즈 실행 계획으로 발전(→ 별도 devlog P04+).
