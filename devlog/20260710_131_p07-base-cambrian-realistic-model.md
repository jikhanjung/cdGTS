# 20260710_131 — P07 Base of Cambrian realistic model (provenance vertical slice)

[계획 P07](20260710_P07_base-cambrian-provenance-slice.md)의 구현. `docs/base-cambrian-vertical-slice.md`
검토에서 시작해, base of Cambrian 하나를 **source → section → horizon → age anchor → correlation →
boundary** 까지 이어지는 실제 추론 그래프로 완성. 대화형으로 모델을 여러 번 다듬으며 수렴했다.
커밋 `09abf6f`~`f110e45`, 이미지 **0.1.45~0.1.47**(테스트 서버 배포·dockerhub push).

## 설계 여정 (왜 이 구조인가)

초안(P07.1/.2)은 section/horizon 을 **provenance 노드**(`category=reference`)로 두고 데이터 노드를
cite 하게 했다. 사용자 피드백으로 방향이 뒤집혔다:

1. **section/horizon 은 데이터 엔티티다** — reference 가 아니라. 그 데이터의 출처를 알고 싶으면 `reference`
   노드를 cite 포트로 따라간다. `reference` = 유일한 인용 노드 한 종류.
2. **한 섹션 안의 이상적 케이스** = 두 ash bed 사이에 index fossil FAD 가 있어, 위·아래 연대(with error)를
   측정하고 그 사이를 **interpolate** → 경계 horizon 의 연대. 이게 하나의 process(모델). 지역마다 나온 연대를
   **종합**(또 하나의 모델)해 최종 경계 연대 → boundary 노드.
3. **실제 base of Cambrian 은 이상형이 깨진 사례** (도메인 정정): GSSP(Fortune Head, *T. pedum* FAD)는
   경계를 **정의**하지만 **연대 측정 가능한 ash bed 가 없다**. 연대는 Oman 등에서 오는데, 거기엔 *T. pedum* 이
   없고(탄산염·증발암상) 경계를 **δ13C BACE** 로 잡는다. 즉 index fossil 과 datable bed 가 **다른 단면·상**에
   있고 δ13C 로 다리를 놓는다 — "정의는 FAD, 연대는 δ13C". 이 **분리**가 오히려 cdGTS 의 차별점을 선명하게 한다.
4. **granularity 는 provenance 로 정한다** — "논리 단계마다 노드"가 아니라, (a) 독립 출처 (b) 독립 교체·재계산
   (c) 파라미터 있는 실제 추론 일 때만 독립 노드. dated ash bed 는 depth+age 를 한 노드(radiometric-uPb)로
   합치고, section 은 **cite 대상**(논문이 섹션을 기술)이라 노드로 승격. NodeGroup 은 cite 를 못 받으므로 section
   은 그룹이 아니라 노드여야 한다.

## 노드 타입 (`seed/02_nodes.json`)

- **`section`** (data): `locality`·`region`·`note`. out 포트 **`h1`/`h2`/`h3`** 로 최대 3 horizon emit.
  cite 대상(data → `cited` 핸들). h* 엣지는 값 없는 **구조적** 엣지지만 section 을 boundary 의 데이터 cone 에
  유지 → 섹션 레벨 인용이 bibliography 로 전파.
- **`horizon`** (data): `depth`(섹션 base 로부터 거리)·`datum`(δ13C BACE, T. pedum FAD…)·`note`. in `section` /
  out `out`. age 없는 undated horizon = 보간 **target**.
- **`radiometric-uPb`·`biostratigraphic`**: `section` 입력 포트 추가(섹션 fan-out 수신).
- (P07.1/.2 잔재였던 section/horizon 의 `citation` out 포트·`category=reference` 는 위로 대체.)
- **`reference`** + DOI 레지스트리 `seed/02b_references.json`(자연키 fixture, manifest 등록): Brasier 1994
  (Episodes, GSSP 비준) · Bowring 2007(AJS, Oman Huqf) · Grotzinger 1995(Science, Namibia) ·
  Bowring 1993(Science, Siberia). DOI 4건 웹 검증.

## 추론 구조 (`example-cambrian-base`, 23 노드)

```
[reference] ─cite─▶ [section] ─h1/h2/h3─▶ [ash bed↑ radiometric-uPb (depth+age)] ─┐
   (×3 dated 섹션:                        [BACE horizon (depth, target)]          ┼─▶ [age-depth-model] ─▶ 섹션 연대
    Oman·Namibia·Siberia)                 [ash bed↓ radiometric-uPb (depth+age)] ─┘
        ↓ (3 섹션 연대)
[cross-section-correlation 종합] ──reference──▶ [calibration-transfer] ──▶ base of Cambrian
[Fortune Head section] ─▶ [T. pedum FAD biostratigraphic] ──target──┘
```

- 섹션별 **bracket→interpolate**: 두 U-Pb ash bed(depth+age)가 BACE horizon(depth-만)을 bracket →
  `age-depth-model` 이 target depth 에서 보간. Oman 538.876 · Namibia 539.0 · Siberia 538.576 Ma.
- **종합**: `cross-section-correlation`(역분산 결합) → **538.824 Ma**.
- **정의 vs 연대**: `calibration-transfer`(reference=dated 연대, target=*T. pedum* FAD signal) → dated 연대를
  FAD-정의 경계로 전달. 숫자 불변(FAD 는 위치 정의, ash bed 가 값) → 최종 **538.82351 Ma**.
- **bibliography**: 각 섹션에 논문 cite → 종합·transfer 통해 경계까지 4건 전파.
- depth/age 는 **illustrative**(구조는 실제 base-of-Cambrian 논리 그대로, 값은 예시).

## 커널 (`engine/kernels.py`)

`age_depth_model`: depth 는 있고 age(moments) 없는 입력 = **보간 target**(경계 horizon)으로 우선 읽고,
없으면 `target_depth` param 폴백. → 사용자 모델("horizon 3개를 입력으로")대로 target 이 그래프 입력에서 나옴.

## 그룹 · example④ 반영 (P07.4)

- 3 dated 섹션 evidence 18 노드 → **NodeGroup "Base Cambrian · δ13C-dated sections"**(container) 하나.
  종합·Fortune Head·calibration-transfer 는 top-level.
- **realistic 모델을 example④(`example-icc-partial`, 전 ICC 조립 그래프)에도 복제·주입**: 옛 flat
  (oman/namibia/siberia/fad-fortunehead → global-age-model) 제거, `calib-transfer → bnd-base-cambrian.age`,
  섹션 그룹 동일 적용. **279 노드**. bnd-base-cambrian 538.795284 → **538.82351**.
- 시드 주의: 자연키 FK 는 참조 노드가 먼저 로드돼야 함 — 노드/그룹은 graph 정의 직후, **엣지는 전 노드 뒤**에.
  gateway 슬러그(`base-cambrian-gw`)는 두 그래프에 각각 존재 → graph 로 매칭해 해당 것만 수정.

## 검증

- **pytest 159 passed** — nodes catalog(19 type) · seed replace(node/edge 카운트) · ICC 차트 타일
  (phanerozoic bottom 538.7953 → **538.8235** 갱신) 포함.
- e2e: 두 그래프 evaluate → 538.82351 · certificate passed · bibliography 4건.

## 배포 / 운영 메모

- 테스트 서버 **m710q**: 브라우저 → **tailscale serve → `127.0.0.1:8011` 컨테이너**(nginx 아님; 로컬 `:80`
  curl 은 무관한 `/srv/www` 정적 페이지). `deploy/host/docker-compose.yml` = web `cdgts` + worker
  `cdgts-worker`, `/srv/cdGTS:/app/hostdb` 디렉터리 마운트(WAL 공유).
- **디자인 반복 중엔** seed(데이터)만 바뀌므로 이미지 재빌드 없이 `docker cp seed/* cdgts:/app/seed/` +
  `docker exec cdgts seed --mode=replace` 로 라이브 반영. **확정 시** 이미지 빌드(0.1.47)로 구워 durability 확보.
- 이 세션에서 `/srv/cdGTS/db.sqlite3` 가 손상(SQLITE_CORRUPT) → 폐기·재생성(disposable prod-mirror).
- **운영(cdgts.paleobytes.info) 미배포** — 0.1.47 dockerhub 준비됨, 승인 시 `deploy.sh` + `seed --mode=replace`.

## 다음

- **운영 반영**(승인 시) · section collapsed 기본값·레이아웃 다듬기.
- 커널: age-depth **spline/MC 경로**에도 target-from-input · 섹션별 δ13C 공유 계통오차(P06 공분산 연계).
- fan-out 이 실제로 필요해지면(섹션 공유 depth 프레임) section→bed 를 값 나르는 엣지로 승격.
