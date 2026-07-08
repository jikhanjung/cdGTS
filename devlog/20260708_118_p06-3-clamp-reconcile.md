# 20260708_118 — P06.3 authored Clamp 배선 (L3a verify / L3b reconcile)

[P06](20260708_P06_arc-a-science-engine.md) 3단계. authored `releases.Clamp`(거버넌스 pin/range/order/freeze)를
release 층에 배선. **ICC/bake = verify-only(값 불변, L3a) · GTS/reconcile = 적용(값 이동, L3b)** 계약 분리.
문서 권고대로 자동 joint 대신 authored clamp 로 reconcile(cycles.md).

## 백엔드 (releases/services.py)

- **`clamp_apply(dist, clamp)`** — engine 커널 **재사용**(pin→`Distribution.exact`, range→`range_clamp` 절단정규).
  order/freeze 는 값 불변.
- **`verify_clamps(release)`**(L3a) — 베이크 값이 clamp 을 지키는지 검사, **값 불변**. pin 불일치·range 이탈·
  충돌(동급·다owner) → violations[].
- **`reconcile_release(release)`**(L3b) — clamp 을 records 에 적용, **값 이동**. 반환 (changed, conflicts).
- **충돌 중재** — precedence `pin > range > order > freeze`. 한 경계 다clamp 는 최고 등급 채택; 동급이 서로 다른
  owner 면 conflict 플래그.

## API (ReleaseViewSet)

- `GET /api/releases/{id}/clamps/` → `{clamps, violations}` (L3a, 공개 read).
- `POST /api/releases/{id}/reconcile/` → 소유자/staff 만(`can_write_release`), `{changed, conflicts, release}` (L3b).

## 프론트 (Vault "Clamps" 탭)

- Release 선택 → **Clamps** 모드: authored clamp 표(경계·kind·값·owner·**L3a check**=honored/violation) + staff **Reconcile(L3b)** 버튼.
- clamp 없으면 안내(“/admin 에서 Release→clamps 로 authored”). 시드엔 authored clamp 없음(노드 타입만) → 06.3b 데모/시드 후속.

## 검증

releases/tests.py +6 (range violation·honored pass·pin 적용·pin>range·충돌 owner·API 권한/reconcile). 전체 **pytest 136 passed**.

## 남음 (P06.4 / 06.3b)

- 06.3b: 시드 데모 clamp + Cryogenian GSSA→GSSP 캡스톤(scalar→분포·공유성분 duration·clamp reconcile end-to-end).
- P06.4: 진짜 베이지안 joint 커널(PyMC + 워커) — `joint-inference` 스텁 교체, L5 posterior.
