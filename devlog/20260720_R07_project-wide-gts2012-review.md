# 20260720_R07 — 프로젝트 전반 및 GTS2012 비교 리뷰

> **성격: 종합 검토(as-built review).** 현재 cdGTS **v0.1.70**의 스키마·그래프 엔진·과학 커널·릴리스·
> 권한·프론트엔드·테스트·운영 문서를 검토하고, `docs/GTS2012*.md` 32개 문서(총 약 45,000줄)에서 반복되는
> 과학·데이터 요구사항과 비교했다.
>
> [R06](20260720_R06_gts2012-corpus-vs-implementation.md)이 GTS2012 코퍼스와 구현 범위의 대조에 집중했다면,
> 본 문서는 그 결과를 프로젝트 전체의 **코드 무결성·보안·거버넌스·문서 정합성**까지 확장한 리뷰다.

## 한 줄 결론

cdGTS는 “지질시대표를 실행·비교·배포 가능한 그래프로 다룬다”는 개념을 증명하는 PoC로 상당히 잘 만들어졌다.
특히 전체 ICC 계층, 그래프 편집, 평가, bake, diff, 운영 배포가 한 흐름으로 연결된 점이 강하다.

다만 GTS2012가 요구하는 과학 모델과 비교하면 현재 중심은 아직 **과학 계산 엔진**보다 **그래프 기반 릴리스·검토
플랫폼**에 가깝다. 더 중요하게는 불변 릴리스와 제안 검토 무결성, 비공개 그래프 접근, 증분 캐시 무효화에 실제
코드 결함이 있다.

---

## 1. 우선 고쳐야 할 실제 문제

### 1.1 제안·비준·릴리스가 실제로는 불변이 아니다 — 높음

현재 제안은 그래프의 고정 revision이 아니라 편집 가능한 `Graph`를 직접 참조한다.

- 소유자는 `proposed`나 `ratified` 상태에서도 그래프를 계속 편집할 수 있다
  ([`GraphAccessPermission`](../graph/permissions.py#L26)).
- `GraphSerializer`에 `status`가 쓰기 가능한 필드로 포함되어 있어 사용자가 API로 직접 `ratified` 상태를 지정할
  수 있다 ([`GraphSerializer`](../graph/serializers.py#L84)).
- 비준 시 “검토 당시 그래프”가 아니라 `proposal.graph`의 **현재 내용**을 bake한다
  ([`ratify_proposal`](../releases/services.py#L208)).
- 릴리스의 `source_graph`는 스냅샷이 아니라 편집 가능한 그래프를 가리키는 FK다
  ([`Release.source_graph`](../releases/models.py#L145)).
- 릴리스 소유자는 `/bake/`를 다시 호출할 수 있고, `bake_release()`는 기존 레코드를 삭제·재작성한다
  ([Release bake action](../releases/views.py#L46), [`bake_release`](../releases/services.py#L235)).

따라서 출력 레코드는 최초 bake 시 복사되지만, 결과를 만든 provenance graph revision 전체는 얼지 않는다. 특히
graph bake 릴리스에 selection이 없다면 재-bake가 기존 레코드를 지우고 빈 릴리스를 만들 가능성도 있다.

이 점에서 [`docs/introduction_review.md`](../docs/introduction_review.md)의 “전체 provenance 그래프의 불변
스냅샷은 목표”라는 판단이 코드 기준으로 맞다. `source_graph` FK가 존재한다는 사실만으로 그래프가 캡처되는 것은
아니다.

#### 권장 구조

1. canonical graph JSON과 content hash를 갖는 `GraphRevision` 도입
2. Proposal이 live graph가 아니라 exact revision을 참조
3. `status`를 API에서 read-only로 변경
4. proposed/ratified graph 직접 편집 금지 — 변경은 fork에서만
5. Release가 exact graph revision/hash를 참조
6. bake/published release의 destructive re-bake 금지

### 1.2 비공개 그래프가 평가 API에서 노출된다 — 높음

그래프 CRUD와 bake/verify/chart는 `visible_graphs()`를 사용하지만 평가 API는 예외다.

[`EvaluateView`](../engine/views.py#L13)는 `AllowAny`이고 `Graph.objects`를 직접 조회한다. 따라서 숫자 PK를 알면
익명 사용자나 다른 사용자가 비공개 sandbox의:

- 최신 평가 결과를 읽고,
- 새 평가를 실행하고,
- 비동기 작업을 생성할 수 있다.

`EvalJobView`도 job PK만으로 결과를 반환한다. 기존 가시성 회귀 테스트는 bake·verify·ICC chart를 검사하지만
evaluate/job 경로는 빠져 있다.

#### 권장 조치

- EvaluateView도 `visible_graphs(request.user)`로 조회
- EvalJob 조회 시 연결된 graph의 가시성 검사
- 익명 `POST evaluate` 허용 여부 재검토 및 rate limit 적용
- 비공개 graph evaluate/job 404 회귀 테스트 추가

### 1.3 증분 캐시가 배선 변경을 놓칠 수 있다 — 높음

현재 content hash는 다음만 사용한다.

```text
node type + params + sorted(upstream content hashes)
```

구현: [`content_hash`](../engine/evaluate.py#L23).

source node identity, source/target port, edge kind가 hash에 들어가지 않는다. 따라서 동일 hash 입력을 다른 포트로
옮기거나 동일 내용 노드 사이에서 재배선하면, 실제 계산 의미나 provenance가 바뀌었는데도 이전 결과를 캐시에서
재사용할 수 있다. calibration처럼 **어느 포트로 들어오느냐**가 계산을 바꾸는 커널에서 특히 위험하다.

최소한 다음 tuple을 결정적으로 정렬해 hash에 넣어야 한다.

```text
(source node key, source port, target port, edge kind, upstream hash)
```

비가환 커널, 동일값 leaf 재배선, calibration 포트 이동에 대한 회귀 테스트가 필요하다.

### 1.4 보정상수 설명에 아직 실제 오류가 남아 있다 — 중간

소개문은 정확하게 고쳐졌지만 node seed 설명은 여전히 다음을 주장한다.

> Change it → every dependent age re-computes

근거: [`seed/02_nodes.json`](../seed/02_nodes.json#L27).

실제 `radiometric_age` 커널은 `value_ma`를 바꾸지 않고 공분산 성분만 추가한다
([`radiometric_age`](../engine/kernels.py#L108)). 이 설명은 자동 생성 node manual에도 들어가므로 다음처럼 고쳐야 한다.

```text
값 변경 → 현재는 하류 cache invalidation 및 shared covariance 재배선
의존 방사연대 값 rescale → R04 L2 로드맵
```

---

## 2. GTS2012 요구와 현재 구현 비교

32개 GTS2012 문서는 반복해서 다음 구조로 수렴한다.

1. 관측과 해석의 분리
2. formal boundary와 물리적 GSSP의 분리
3. local event와 global correlation의 분리
4. 최종 경계연대와 그것을 계산한 model version의 분리
5. 불확실성·상관·모델 선택·결정 provenance의 보존

| GTS2012에서 도출되는 요구 | 현재 구현 | 평가 |
|---|---|---|
| Stage·formal boundary·GSSP·수치연대 분리 | `Unit`·`Boundary`·`Locality`·`BoundaryRecord` | 기본 구조는 좋음 |
| 관측·해석·상관·공식 결정 분리 | generic node/edge와 authored leaf | 표현 가능하지만 타입 깊이 부족 |
| 시료·측정·표준·분류군·occurrence·biozone | 대부분 자유 JSON 또는 없음 | 큰 공백 |
| 상대척도와 age model의 재계산 | 선형/CubicSpline 보간 | 제한적 vertical slice |
| 다중 proxy와 상관 가설 비교 | graph fork·배선·일부 diff | authored wiring 수준 |
| 불확실성·공분산·duration | Distribution·shared component·L1b/L2 | 유용한 부분 구현 |
| 후보·투표·비준·버전 provenance | Proposal·Membership·Release | 방향은 강하나 revision 무결성 결함 |
| 모델·배선 변경 diff | 값·shape·추가/삭제·GSSA/GSSP retype | node/edge diff 없음 |

### 2.1 Chapter 2 — 형식 경계와 물리적 기준점

[Chapter 2의 cdGTS 해석](../docs/GTS2012_Chap_2_Gradstein_Ogg_2012_Chronostratigraphic_Scale_요약.md#L519)은
다음을 분리한다.

```text
Stage ≠ boundary
formal boundary ≠ GSSP point
GSSP point ≠ marker
GSSP definition ≠ estimated numerical age
local observed event ≠ global correlation
```

현재 `Boundary`·`Locality`·`BoundaryRecord`는 이 구조의 뼈대를 제공한다. 그러나 `Locality`는 위치·좌표·층준만
담으며 다음이 정규화되어 있지 않다.

- primary/secondary marker
- section/formation/member/bed와 보존 상태
- original ratification rationale
- candidate section 비교와 투표
- 이후의 correlation reassessment

generic node params로 표현할 수는 있지만 검색·검증 가능한 domain object는 아니다.

### 2.2 Chapter 14 — 실제 시간척도 계산

[Chapter 14](../docs/GTS2012_Chap_14_Agterberg_Hammer_Gradstein_2012_Statistical_Procedures_요약.md#L1058)는
다음을 독립 요소로 요구한다.

- radiometric analysis와 internal/external error
- stratigraphic placement distribution
- graphic correlation/CONOP 등 relative scale과 그 version
- smoothing factor와 cross-validation
- monotonicity constraint
- outlier 판정·불확실성 재조정
- Monte Carlo boundary interval과 duration

현재 [`age_depth_model`](../engine/kernels.py#L240)은 고정된 depth에 대해 선형 또는 단순 `CubicSpline` 보간을
수행한다. spline 경로의 MC도 입력 연대의 정규 draw를 고정된 깊이에 전파하는 수준이다. 다음은 없다.

- 층서 위치 불확실성 draw
- smoothing spline/SF 선택
- LOOCV
- 단조성 강제
- outlier model
- hiatus/piecewise model
- model ensemble

따라서 현재 age-depth는 GTS2012 Chapter 14 구현이 아니라 그 전파 구조를 증명하는 vertical slice로 보는 것이
정확하다.

### 2.3 Chapter 21 — 물리적 GSSP와 변화하는 해석

[Chapter 21](../docs/GTS2012_Chap_21_Melchin_Sadler_Cramer_2012_The_Silurian_Period_요약.md#L1231)은
물리적 GSSP, ratification 당시 taxon concept, 이후의 revised taxon concept, 현재 상관 평가, 수치 보정을 함께
보존해야 함을 보여준다.

현재 registry에는 stable `Boundary`와 `Locality`는 있지만 다음 revision 계층이 없다.

- `TaxonConcept`
- `Occurrence` / local bioevent
- `BoundaryRationale`
- 시간에 따라 복수로 쌓이는 `BoundaryCorrelationAssessment`

이는 Silurian에 한정된 문제가 아니라 Cambrian·Carboniferous·Jurassic 등 period chapter 전반에서 반복된다.

### 2.4 실제 계산 커널의 현재 깊이

[`KERNELS`](../engine/kernels.py#L293)에 등록된 실제 process 계산은 제한적이다.

- `age-depth-model`: 선형/CubicSpline 보간
- `joint-inference`: 독립 추정의 역분산 평균
- `cross-section-correlation`: 위와 같은 평균이며 signal 자체는 읽지 않음
- `calibration-transfer`, `merge`, `unit` 등 미등록 process: 첫 non-null 입력 pass-through

즉 magnetic polarity, astrochronology, isotope reference curve, biochronology/CONOP, sequence stratigraphy는
NodeType 이름이나 authored leaf로는 나타낼 수 있지만 실제 domain kernel은 아니다.

다음 과학 아크는 기존 R05의 `tie-point → composite-scale → age-model` 경로가 가장 타당하다. correlation을
평균 커널로 취급하는 대신, 상관 가설과 상대척도를 1급 provenance object로 만드는 것이 GTS2012 전 장의 공통
요구와 맞는다.

---

## 3. 스키마·검증 부채

### 3.1 `params_schema`가 서버 계약이 아니다

`NodeType.params_schema`는 에디터 컨트롤과 문서 생성에 쓰이지만, `NodeInstance.params` 저장 시 서버에서 실제로
검증되지 않는다. `Distribution.from_dict()`의 불변식 검사도 API 입력 경로에는 적용되지 않는다.

따라서 다음 데이터도 저장될 수 있다.

- unknown fidelity
- exact distribution + non-empty uncertainty budget
- 음수 uncertainty
- 잘못된 sigma level
- 커널이 필요로 하는 필드가 없는 params

과학 결과를 release로 내보내려면 UI validation이 아니라 서버 canonical validation이 필요하다.

### 3.2 포트 선언 일부가 강제되지 않는다

[`GraphSerializer.validate`](../graph/serializers.py#L101)는 포트 이름과 방향은 확인하지만 다음은 검사하지 않는다.

- source/target port datatype 호환성
- `Port.multiple=False`에 여러 edge가 들어오는지
- duplicate edge
- process별 필수 입력 수

결과적으로 타입 그래프가 유효해 보여도 커널은 첫 입력만 조용히 선택하거나 `None`을 반환할 수 있다.

### 3.3 joint/cycle 표현은 아직 약속에 가깝다

`joint-inference`가 cycle breaker로 존재하면 저장을 허용하지만, 평가는 남은 cycle node를 임의 순서로 한 번만
계산한다. 비동기 worker로 보내더라도 커널은 동일한 역분산 평균이다. 따라서 현재 cycle support는 진짜 동시추정이
아니라 향후 joint solver의 API seam이다.

---

## 4. 릴리스·diff·거버넌스 평가

### 강점

- `BoundaryRecord`가 경계 값·definition type·분포·참고문헌을 버전별로 복사한다.
- GSSA/GSSP retype과 uncertainty shape 변화를 값 diff와 분리한다.
- fork→propose→review→ratify 흐름이 실제 API와 UI로 연결되어 있다.
- `affected` boundary 목록과 `can_ratify(proposal)` signature가 향후 scope governance의 seam을 남긴다.
- L1 authored order, L1b 공분산 인지 2σ warn, L2 duration 검사가 실행된다.

### 한계

- `diff_releases()`의 topology diff는 boundary add/remove/retype이며 graph node/edge diff가 아니다.
- Proposal이 reviewed revision을 고정하지 않는다.
- membership 하나만 있으면 어느 구간 제안이든 비준할 수 있다.
- 동시 ratify에 대한 proposal/baseline row locking이 없다.
- release source graph가 mutable하므로 완전 재현이 안 된다.

현재 기능을 “경계 출력·shape·경계 집합/정의 타입 diff”라고 부르는 것은 정확하다. “전체 provenance 배선 diff”나
“원본 그래프까지 얼린 불변 릴리스”라고 부르는 것은 아직 과장이다.

---

## 5. 문서 코퍼스 검토

### 5.1 잘된 점

- 32개 장 모두 끝에 chapter-level 출처를 제공한다.
- 각 장의 `cdGTS 관점` 절이 단순 요약을 넘어 domain modeling 후보를 풍부하게 제공한다.
- Chapter 2·6·14·21과 period chapter들이 서로 다른 사례에서 같은 구조로 수렴한다.
- 2012 당시 상태를 명시하는 문서가 많아 역사적 스냅샷임을 어느 정도 드러낸다.

### 5.2 개선할 점

1. [`concept-map.md`](../docs/concept-map.md#L28)는 아직 `clamp`를 NodeType category로 표시한다. 실제 코드는
   `data/process/reference`다 ([`NodeType.Category`](../nodes/models.py#L24)).
2. concept map의 참고 문헌 영역은 과거 GTS2012 요약 2개만 연결하며 새 32개 문서를 인덱싱하지 않는다.
3. HANDOFF의 “14주제 × 한/영” 설명도 현재 GTS2012 한국어 단독 코퍼스를 반영하지 않는다.
4. `Chap32`만 underscore가 빠지고, 일부 파일은 `Summary`, 나머지는 `요약`이라 정렬·자동화가 불안정하다.
5. 장 전체 출처만 있고 긴 문서의 세부 주장에 page-level citation이 없다.
6. 원문 요약과 cdGTS의 설계 해석이 후반 heading으로는 구분되지만, 문서 전면 metadata에는 구분이 없다.

권장 front matter:

```yaml
document_type: secondary-summary
source: The Geologic Time Scale 2012, Chapter N
source_state_as_of: 2012
source_derived_sections: 1-N
cdgts_interpretation_sections: N+1-M
canonical_current_status: false
```

GTS2012의 연대·비준 상태는 역사적 입력이고 현재 ICC seed는 별도 source edition을 가진다는 점도 명시해야 한다.

---

## 6. 테스트·빌드·운영 상태

### 검증 결과

- `pytest -q`: **192 passed**
- `python manage.py check`: 통과
- frontend `npm run build`: 통과
- Git 작업 트리: 검토 전후 변경 없음(본 문서 추가 전 기준)

### 발견된 품질 게이트 공백

- `python manage.py makemigrations --check --dry-run`은
  `graph/migrations/0011_alter_nodeinstance_nature.py`가 필요하다고 보고한다.
- `.github/workflows`가 없어 저장소 자체의 자동 CI가 없다.
- frontend package script에는 lint·unit test·typecheck가 없다.
- Playwright smoke는 5개이며 fork/edit/propose, drill-in, context menu을 의도적으로 다루지 않는다.
- 현재 192개 테스트가 통과하지만 private evaluate leak, proposed graph mutation, status bypass, graph bake destructive
  re-bake, wiring-aware cache invalidation은 테스트하지 않는다.

테스트 수보다 **불변식 기반 회귀 테스트**를 보강하는 것이 중요하다.

---

## 7. 권장 우선순위

### P0 — 신뢰 경계 복구

1. private evaluate/EvalJob 가시성 수정
2. graph status read-only 및 proposed/ratified 편집 차단
3. Proposal→GraphRevision 고정
4. bake/published release 재-bake 차단
5. Release에 graph snapshot/hash 보존

### P1 — 계산 무결성

1. wiring-aware content hash
2. params/distribution server validation
3. port datatype·multiplicity 검증
4. calibration node 설명 정정
5. missing migration 추가와 CI에서 `makemigrations --check`

### P2 — 과학 모델 깊이

1. R05 `tie-point`
2. derived `composite-scale`
3. correlation hypothesis toggle → graph/release diff
4. stratigraphic-position uncertainty를 포함한 age-model
5. R04 L2 calibration rescale
6. 필요성이 입증된 뒤 joint/Bayesian solver

### P3 — 문서 정합성

1. GTS2012 32장 index 추가
2. source summary와 cdGTS interpretation metadata 분리
3. concept-map의 clamp/category와 열린 상태 갱신
4. node manual을 재생성해 코드·seed 설명 정합화

---

## 최종 평가

cdGTS의 비전은 GTS2012의 구조와 매우 잘 맞는다. 특히 다음 두 명제는 충분히 검증되었다.

```text
formal boundary와 estimated age는 다르다.
경계 값은 authored leaf 또는 versioned model output이어야 한다.
```

현재 vertical slice도 의미가 크지만, 과학 모델보다 릴리스·거버넌스 표면이 먼저 성숙하면서 그 표면이 약속하는
불변성과 검토 무결성을 코드가 아직 완전히 보장하지 못한다.

따라서 다음 단계는 새 과학 기능을 넓게 추가하기 전에 **GraphRevision/불변 Release → 가시성 → wiring hash** 세
기반을 먼저 고치는 것이다. 그 위에 R05 상관 provenance와 Chapter 14 수준의 age-model을 순차적으로 올리는 것이
가장 안전하다.
