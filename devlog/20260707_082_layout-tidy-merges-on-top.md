# 20260707_082 — 배치 정돈: age-unit 균일화 + merge 노드 상단 배치

age unit 재귀 세분(devlog 081) 이후 커진 그래프의 좌표 정돈. 순수 cosmetic(위치만 — eval/cert/bake/chart 무관).

## 변경 (seed/03_graphs.json, 위치만)
- **age-unit 드릴인 균일화** — 각 period 그룹에서 첫 age(맨 아래)·끝 age(맨 위)가 경계열 밖으로 full-step(±70) 튀던 걸 **반스텝(±36)** 으로. 경계열 | unit열이 균일하게 교호(예: ages-cambrian 경계 990~1550 / unit 954~1586).
- **컬럼 merge 상단 정렬** — 5개 컬럼 merge 를 각 컬럼 탑(y=40)보다 100 위(**y=-60**)로 올려 한 줄 정렬.
- **종단 merge 최상단** — `icc-chart` 를 컬럼 merge 들보다 120 위(**y=-180**).

→ merge 흐름(컬럼→종단)이 그래프 상단에 모여 한눈에 보이고, 컬럼들은 아래로 흐른다.

## 비고
- 위치 변경뿐이라 테스트/평가 영향 없음. seed replace 로드 정상(FK 무결).
- 드릴인 멤버는 절대좌표 클러스터(buildView 가 리프레임) — 그룹별 클러스터가 독립적이라 겹쳐도 무방.
