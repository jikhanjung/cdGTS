# 20260705_065 — Science CI: 공표 대비 검증

> 프로젝트 핵심 명제("재현 가능한 파이프라인 → 산출물, 과학을 위한 CI")를 에디터에서 **원클릭**으로.
> 그래프 값 편집 → 재bake → **공표 기준 릴리스와 diff** → 이동한 경계·배선 변화 요약. diff 엔진([[]])은 기존 재사용.

## 한 일

### 백엔드 (`releases` · 마이그레이션 0002)
- `Release.is_baseline` 불리언 — 공표 기준 릴리스 표시(diff 대상). 시드에서 **ICS-2024/12** 에 표시.
- `GraphVerifyView` (POST `/api/graphs/{id}/verify/`) — 그래프 재bake → `diff_releases(공표, 그래프)` →
  요약(moved·max|Δ|·added/removed/retyped) 첨부. `value_diff.delta = 그래프 − 공표`(내 편집이 경계를 얼마나 옮겼나).
- 검증 테스트: 값 201.4→210 편집 시 base-jurassic 이 delta 로 등장.

### 프론트 (`VerifyPanel.jsx` · `Editor.jsx`)
- 툴바 **"공표 대비 검증"** 버튼 → `verifyGraph` → 하단 패널. 요약 배지(공표와 동일/상이) + 이동 경계 표
  (공표 / 내 그래프 / Δ, |Δ| 큰 순, 부호별 색) + 토폴로지 칩(＋/－/↺). 작은 Δ(<0.01)는 회색(모델링 노이즈).

## 루프의 의미
- 편집 전 기본: 6 경계만 ≤0.005 Ma 이동(예제 adm 모델 파이프라인 vs 공표), 배선 변화 0 →
  "모델이 공표 ICC 를 근사 재현". 값 하나 바꾸면 그 경계가 큰 Δ 로 떠오름 = CI 루프가 닫힘.

## 검증
- `pytest` **85 passed**(verify diff·요약). 프론트 빌드 클린.

## 배포 노트
- **마이그레이션 releases 0002** + **재시드**(ICS-2024/12 baseline 플래그) 필요.
