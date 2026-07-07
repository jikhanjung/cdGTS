# 20260707_110 — P05.5: 샌드박스 오버라이드 (아크 B seam)

[P05](20260707_P05_arc-c-multiuser-ci-platform.md) 5단계(MVP 밖). 샌드박스 = **baseline Release + 경계별 후보
교체**. 그래프 전체를 편집하지 않고, 공표 baseline에서 특정 경계의 **경쟁 ModelCandidate**만 갈아끼워 재-bake·diff.
아크 B(경쟁모델)와 만나는 지점 — seed에 실제 경쟁 후보 존재(base-cambrian 3·base-proterozoic 2·base-triassic 3).

## 백엔드

- **`Release.kind += sandbox` · `Release.base`**(파생 baseline FK). migration releases.0008.
- **services** — `create_sandbox_release(baseline, user)`(baseline selection 복사 후 bake) ·
  `set_override(sandbox, boundary, candidate|None)`(Selection 교체/리셋 후 재-bake) ·
  `overridable_candidates(release)`(경쟁 후보 >1인 경계 + 옵션·현재·baseline pick). 버전 이름 헬퍼 `_next_seq` 로 정리.
- **엔드포인트**(ReleaseViewSet actions) — `POST releases/{id}/sandbox/`(baseline→내 샌드박스, 인증) ·
  `GET .../candidates/` · `POST .../override/`{boundary,candidate}(owner). **가시성**: 남의 샌드박스는 목록·조회 제외.
- 직렬화에 `base` 노출.

## 프론트

- **Vault**: baseline/published 선택 시 **"Sandbox this →"**(인증). 내 샌드박스 선택 시 **Overrides 모드** 추가 +
  `base`(◇) 배지. 오버라이드 후 임베드 뷰 재렌더(nonce).
- **`Overrides.jsx`**(신규) — 경계별 후보 `<select>`(baseline 표시) + 리셋(↺). 변경 → override → 재-bake.
  Diff 모드로 sandbox vs base 효과 확인.

## 검증

pytest **112 passed**(+2: 샌드박스 복제→오버라이드→리셋 값·diff, 엔드포인트·가시성·권한). build OK.

## 결과 = P05 전체 완료

P05.1~.5 완료. 아크 C(멀티유저 CI) + 아크 B seam(샌드박스 오버라이드) 구현. 인터벌 스코프 권한은 훅만 준비.
**미배포** — 배포 시 관리자·ICS Authority·Membership 세팅 + 브라우저 검증 필요.
