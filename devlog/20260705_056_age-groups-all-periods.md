# 20260705_056 — 전 period age 노드그룹 (계층 완성 ①)

> Triassic 프로토타입([046])을 **전 period로 일반화**. 각 period = age 세분 노드그룹.
> "22 period + Epoch" 작업의 **1단계(ages)**. Epoch 계층 + orphan 정리는 2단계.

## 한 일 (생성기 → seed `03_graphs`)
- period 별로 **내부 age 분할점**(base ≠ period base) pub+gateway + order 체인 생성. 체인 양끝은 period 경계에 tie
  (older=period base 산출노드, younger=더 젊은 period base 산출노드). 내부는 older/younger 세로포트, tie 는 그룹 밖.
- 수제 Triassic 그룹은 제거 후 균일 재생성. 그룹 `ages-<period>`, order `oa-<younger>`.
- 결과: 노드 90→**255** · 엣지→264 · 게이트웨이 42→**120** · 그룹 1→**11**. cert L1·L2 pass. bake 42→**120**.

## 커버리지
- age 세분 있는 **11 period** 모두 그룹화(Quaternary…Cambrian). 84 내부 분할점.
- 제외: 첫-age(=period base, 공유 경계라 period 게이트웨이가 대표) ~11개 — 정상.
- **미포함: Carboniferous** ⚠️ — 그 age 들이 Mississippian/Pennsylvanian(**subperiod**, Eon~Age 범위 밖이라 미시드)
  아래라 계보가 period 로 안 이어짐. → 2단계에서 subperiod 처리와 함께.

## 검증
- reseed replace: cert {L1,L2 pass}, bake 120, 11 그룹, `ages-triassic` 멤버 11(6 pub+5 order). API 직렬화 OK.
- `pytest` **81 passed**(bake 120·age-groups-all-periods 테스트 갱신). 마이그레이션·프론트 변경 없음.

## 2단계 (다음)
- **Epoch(Series) 계층** — 각 period 그룹에 epoch 분할점(rank 4) 체인 추가 → 그래프-bake 5 rank(공표 릴리스와 대칭).
- **`early-triassic` orphan 정리** — induan 을 lowertriassic 으로 재부모, base-None 중복 유닛 제거.
- **Carboniferous** — Mississippian/Pennsylvanian subperiod 를 계보에 반영.
