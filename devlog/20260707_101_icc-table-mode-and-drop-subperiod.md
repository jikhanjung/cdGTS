# 20260707_101 — ICC Chart: Table 모드 추가 · Subperiod 컬럼 제거 (0.1.25-WIP)

frontend 전용. 재시드 불필요.

## 1. Table (equal Age) 스케일 모드 추가 (IccChart.jsx)
기존 Log / Linear 에 더해 시간 척도를 무시하고 leaf 셀(Age/Stage)을 균등 높이로 보여주는 표 형식 모드.
- 모든 밴드 경계 age 의 합집합(`breakpoints`)으로 [0,max] 를 최소 구간으로 분할, 각 구간 균등 높이.
- Phanerozoic 은 Age/Stage 가 leaf, Age 세분 없는 Precambrian 은 Period/Era 가 leaf → 그것들이 균등 높이.
- 상위 랭크는 포함 leaf 수만큼 높이 차지 → 테이블처럼 읽힘. 라벨/줌/툴팁/불확실성은 기존 y() 재사용.

## 2. Subperiod 컬럼 제거 (IccChart.jsx)
Subperiod(rank 4 = Mississippian/Pennsylvanian)는 Carboniferous 에만 존재하는 2밴드이고 하위 Epoch
밴드(Lower/Middle/Upper Mississippian·Pennsylvanian)와 age 범위가 정확히 겹침 → 별도 컬럼 낭비.
`levels = data.levels.filter(rank_n !== 4)` 로 컬럼 제거. 세분은 Epoch 컬럼 밴드 이름에 이미 담겨 있어
Epoch 쪽에 합쳐진 형태로 남음(공식 ICC 차트와 동일). 정보 손실 없이 6→5 컬럼.
