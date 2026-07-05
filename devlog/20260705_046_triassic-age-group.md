# 20260705_046 — Triassic age 노드그룹 (계층을 네트웍에)

> "level(Period vs Age)이 네트웍에 안 보인다" → period 구간을 **노드그룹(span)**, 그 안 age 분할점을
> **경계 점(order 체인)** 으로. Unit(구간) ↔ Boundary(점) 이중성을 네트웍 구조로. 프로토타입 = Triassic.

## 핵심: 공유 경계
- period base = 그 안 **첫 age base**(같은 순간): base-triassic ≡ base-induan(251.902), base-jurassic ≡ base-hettangian(201.4).
- 그래서 그룹 내부는 **분할점 6개**(Olenekian…Rhaetian base)뿐. 양 끝(triassic·jurassic)은 밖의 period 경계.

## 한 일
### NodeGroup seedable
- `NodeGroupManager.get_by_natural_key` + `natural_key=(graph.slug, key)`. `NodeInstance.natural_key.dependencies`
  에 `graph.nodegroup` 추가. 마이그레이션 없음(메서드/매니저). seed 인프라는 이미 대비돼 있었음
  (SEED_MODELS·GRAPH_CHILDREN 에 nodegroup 포함). **첫 seed 되는 그룹.**

### example-icc-partial 확장 (seed 03_graphs)
- 그룹 `triassic-ages`: pub-`{olenekian,anisian,ladinian,carnian,norian,rhaetian}` 6(값=ICS, published-age)
  + 게이트웨이 6 + order 체인 7(triassic→olenekian→…→rhaetian→jurassic).
- **그룹 멤버 = 내부 age 6 + 내부 order 5**(11). period 경계에 tie 하는 order 2(ord-35·ord-41)는 **그룹 밖**
  = 그룹의 older/younger 연결. 접으면 이 둘이 그룹 포트.
- 노드 77→90 · 엣지 76→90 · 게이트웨이 36→42 · 그룹 0→1 · order 35→42.

## 얻은 것
- 계층이 **중첩**으로: period 체인(위) + Triassic 접힌 그룹(드릴인 시 age 체인).
- age가 네트웍에 올라와 **bake 42**(Triassic age 값 산출) → 그래프-소스 ICC 차트가 부분 Age 컬럼.
- 그룹 endpoint tie가 "age들이 period 경계 안" 을, 내부 order가 age 단조성을 검사 → **cert L1 pass**.

## 검증
- reseed replace: 그룹 멤버 11, cert L1 pass, bake 42(base-olenekian 250.8 등), API 직렬화 OK(멤버 group·tie=null).
- `pytest` **80 passed**(신규 그룹 테스트: 멤버 구성·tie 외부·공유경계 induan 비-분할점·L1 pass). 빌드 클린.

## 이월
- 나머지 21 period 로 확장(생성기화) · Epoch(Series) 중간 계층 · 브라우저 육안(접기/드릴인/포트).
- 재시드 `--mode=replace` 필요.
