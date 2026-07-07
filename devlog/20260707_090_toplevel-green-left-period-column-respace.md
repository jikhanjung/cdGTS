# 20260707_090 — top-level 데이터 노드 좌측 이동 · period 컬럼 간격 일관화 (0.1.25-WIP)

seed 좌표만. example-icc-partial top-level 배치 정리. 0.1.25-WIP 재빌드·재시드.

## 1. 초록 데이터 노드 왼쪽 -120
관측 리프(bed25·bed28·oman·namibia·siberia·fad-fortunehead)를 x -120 이동
(bed 590→470, δ13C 입력군 1290→1170). 소비 process 노드·좌측 컬럼과 겹치지 않는 범위.

## 2. period 컬럼(Cenozoic·Mesozoic·Paleozoic) 상하 간격 일관화
경계 노드가 평가 시 연대(≈44px)로 커지면서 기존 "경계→그룹 +42" 가 겹침. 그룹(≈60px)/경계
높이 기준으로 **그룹→경계 +76, 경계→그룹 +60**(시각 간격 ~16px 균일)로 재배치.
- Paleozoic(x=1650) y40→796 · Mesozoic(x=950) y40→388 · Cenozoic(x=250) y40→388.
- 세 컬럼 동일 구조라 일관성 위해 Cenozoic 포함. 그룹 아래에 그 "Base of …" 경계가 붙고 이후 균일 간격.

## 비고
x/y 만 변경. seed 변경 → 배포 시 seed --mode=replace 재시드.
