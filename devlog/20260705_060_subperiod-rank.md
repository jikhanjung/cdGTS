# 20260705_060 — Subperiod(아계) 등급 추가

> Carboniferous 의 Mississippian/Pennsylvanian 아계(Subperiod/Subsystem)를 정식 ICS 등급으로 모델링.
> Period 와 Epoch 사이 새 rank. 현재 Carboniferous 만 사용(sparse 컬럼).

## 한 일

### 등급 체계 (`chrono/models.py` + 마이그레이션 0003)
- **Rank 재번호**: Subperiod=4, Epoch=5, Age=6. 이중 명명 **Subperiod / Subsystem** 추가.
  `_CHRONO_TERM`/`_GEO_TERM` 갱신. `narrate` GEO·`_GEO`(views)도 6등급.

### 데이터 (chart.ttl 정본 — [[ics-chart-ttl-source]])
- **Mississippian** (color #678F66, base 358.86, GSSP) · **Pennsylvanian** (color #7EBCC6, base 323.4, GSSP)
  유닛 2 + 경계 2 추가(units·boundary 175→**177**). Carboniferous epoch 6개를 아계로 재부모.
  색은 chart.ttl `schema:color`(subperiod 개념)에서 직접 추출(stage 색과 다름 — Bashkirian #99C2B5 ≠ Pennsylvanian #7EBCC6).
- 공표 릴리스(05)에 candidateoutput/selection 2쌍. 그래프(03)에 아계 게이트웨이(첫=period 산출노드, 내부=일치 age pub).

### 차트 타일링 재설계 (`build_icc_levels`)
- Subperiod 는 **전 구간을 안 덮는 sparse rank** — 종전 "0부터 타일링"은 Pennsylvanian 밴드를 0까지 늘렸다.
- 새 규칙: 밴드 top = **rank 이하(같거나 굵은) 중 자기보다 젊은 base 의 최대**. coarser 경계(Permian base)가
  아계 밴드를 제 구간에서 닫는다. 부모 FK 불필요(시드 period→era 링크 불완전해도 안전). gapless rank 는 동일.
- **coincidence 허용오차 0.001 Ma**: 같은 GSSP 를 modeled(adm 251.902182) vs published(mesozoic 251.902)로
  미세하게 다르게 산출해도 sliver 밴드가 안 생기게. 실제 최소 경계간격(홀로세 세분 ~0.0035)보다 작아 안전.

## 결과
- 그래프·공표 릴리스 차트 = **6 rank**: Eon 4·Era 10·Period 22·**Subperiod 2**·Epoch 37·Age 102.
  bake 175→**177**. Subperiod: Mississippian[323.4–358.86]·Pennsylvanian[298.9–323.4] 제 구간 폐합.
- `pytest` **82 passed**(subperiod 이중명명·차트·narrate·타일링 폐합 가드). 프론트 빌드 클린.

## 배포 노트 (사용자)
- **마이그레이션 0003 있음** ⚠️ — `migrate` 필요. **재시드 `--mode=replace` 필수**(units/boundary/release/graph 모두 변경).
- 예상: units 177·boundary 177·records 182. example-icc-partial bake 177·그룹 12.

## 남은 것
- 중첩 노드그룹(Period⊃Subperiod⊃Epoch⊃Age 시각 계층)은 미지원([[]]057 한계).
