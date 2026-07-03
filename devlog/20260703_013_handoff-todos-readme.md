# 20260703_013 — HANDOFF/TODOs 도입 + README 개념지도 정합 + 스택 잠정

> 브레인스토밍 단계 devlog. 요약 수준.

## 한 일

### 1. README 를 개념 지도 구조에 맞춰 재편 (한/영)
- 상태 blurb 갱신(스키마 v0 반영), **레이어 척추 0–6 섹션** 신설.
- 문서 목록을 평평한 나열 → **concept-map "여기서 시작" 진입점** + 개념/사례/스키마·설계 3그룹.
- **핵심 수렴점 섹션** 추가(provenance 깊이 / clamp / ICC·GTS), 상태에 `devlog/` 포인터.

### 2. HANDOFF.md · TODOs.md 신규 (fsis2026 형식, 루트·한글 단독)
- **HANDOFF.md** — Last updated 밀집 요약(하루 세션 전체) + 현재 상태 + 개념 진척 + 최근 작업(001~012) + 다음 작업.
- **TODOs.md** — §0 착수 결정 / §1 추가 사례 / §2 설계 문서별 미해결 열린 질문(6갈래+idea) / §3 유지 관리.
- 역할 분담(HANDOFF=헤드라인, TODOs=상세)·상호 참조 fsis2026 관행 따름.

### 3. 스택 잠정 방향 기록
- **잠정 Django 5.2**(+ PostGIS, 무거운 계산은 별도 과학 스택 분리 예상; fsis2026 패턴 재사용). "아마도" =
  미확정, 브레인스토밍 종료 후 이 저장소에서 개발 예정.
- HANDOFF §현재상태·다음작업, TODOs §0 반영. memory `planned-stack-django` 저장(스캐폴딩 금지 명시).

## 커밋

- (이 커밋) README 한/영 재편 + HANDOFF/TODOs 신규 + 스택 잠정 반영 + devlog 013.

## 다음 후보

- 착수 결정(데이터 포맷/스택 확정) 또는 추가 사례(Cryogenian 전환 = 토폴로지 diff 실례).
- 미해결 열린 질문은 TODOs §2 참조.
