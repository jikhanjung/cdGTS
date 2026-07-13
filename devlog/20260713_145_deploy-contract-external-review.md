# 20260713_145 — 배포·데이터 계약 외부 검토분 cdGTS 적용

[P08](20260713_P08_deploy-data-contract-retrofit.md)/[144](20260713_144_p08-close-deploy-validation.md) 로 계약 파일럿을
착지한 뒤, cross-project 계약(`../devdocs/wiki/deploy-data-contract.md`)에 **2026-07-13 외부 설계 검토**로 추가된 항목이
있었다 — 그 시점엔 **계약 정의에만 반영**되고 정렬 완료 프로젝트의 스크립트·매니페스트는 구계약 그대로였다(계약 §롤아웃:
"각 repo 다음 접점에 맞춘다"). 이번 라운드가 cdGTS 의 그 접점 — 새 항목 넷을 코드에 적용.

## 왜 지금

계약 §rollback 은 초판의 **유일한 내부 논리 결함**을 지적했다: 롤백을 "이전 이미지 + DB 스냅샷 복원"으로 묶으면,
배포 후 운영자가 입력한 데이터까지 pre-deploy 스냅샷으로 되돌려 **rollback 자신이 불변식("파이프라인은 운영 데이터를
나르지도 지우지도 않는다")을 깬다.** cdGTS `rollback.sh` 가 정확히 그 구계약이었다(무조건 최신 스냅샷 복원).

## 한 일

- **롤백 코드/DB 분리** (`deploy/host/rollback.sh` 재작성):
  - `--db=keep`(기본) — 이미지 태그만 전환, 현재 DB 유지(운영 데이터 보존). 삭제 아니라 전환.
  - `--db=restore` — 서비스 정지 → 이전 이미지 전환 → pre_deploy 스냅샷 복원(WAL torn-copy 방지 위해 정지 후 복원).
  - **keep 가드** — 직전 배포가 migration 을 적용했으면 이전 코드가 새 스키마와 비호환일 수 있어 keep 을 막고
    `--db=restore`/`--force` 로 승격. 판정 = 스냅샷 `.mig` 사이드카(배포 전 적용 migration 수) vs 현재 컨테이너 비교.
    사이드카 없으면(구 스냅샷) 미상으로 두고 진행(대부분 무migration).
- **`.mig` 사이드카 기록** (`deploy/host/deploy.sh` 스냅샷 블록) — prod 스냅샷 직전(컨테이너 정지 전) `showmigrations
  --plan` 적용 수를 `${SNAP}.mig` 에 기록. retention 정리에 `.mig` 포함. keep 가드가 repo 없이 판정하게 하는 근거.
- **매니페스트 필드** (`deploy/deploy.toml`) — `contract_version = 1`(계약 판 명시) · `rollback_db = "keep"`(롤백 기본
  DB 정책 선언, 스크립트 기본값과 일치). rollback 동사 시그니처도 `[--db=keep|restore]` 로 갱신.
- **self-heal 추출 안전망** (`deploy/host/_extract_and_deploy.sh`) — 이미지에서 꺼낸 스크립트를 교체 전 `bash -n`
  문법 검사에 통과시키고, 기존 파일은 `<f>.previous` 로 보존한 뒤 원자 rename. 깨진 새 스크립트가 **작동하던
  부트스트랩 경로까지 함께 망가뜨리지 않게** 하는 최소 안전망. deploy/smoke/rollback + 래퍼 2 + 추출기 자신에 적용.

## 검증

- `bash -n` 전 스크립트 통과. rollback 인자 파싱(usage 가드·`--db=`·`--force`·unknown flag 거부) 로컬 확인.
- 실제 롤백/self-heal 경로(docker 필요)는 실배포에서 검증 예정. 코드·스크립트만·마이그레이션 없음.

## 배포 주의

호스트 파일은 self-heal 로 **이미지에서** 온다 → 새 `rollback.sh`·`deploy.sh`·`_extract_and_deploy.sh` 가 서버에 반영되려면
이 코드를 담은 이미지로 **1회 배포**해야 한다. 안전망(bash -n)·`.previous` 는 그 다음 배포부터 완전 동작(추출기 자기 치유 관례).

## 문서 정합

`DEPLOY.md`(상시 불변식 §롤백 + 0.1.61 릴리스 노트) · `deploy/README.md`(rollback 구성 행) · `deploy.toml`(필드·동사).
계약 원본은 이미 이 항목들을 정의·보유 → cdGTS 는 **정의 → 구현** 격차를 좁힌 것(계약 문서 자체는 무변경).

*근거: `../devdocs/wiki/deploy-data-contract.md`(§동사 rollback·매니페스트 `contract_version`/`rollback_db`·self-heal 안전망·§롤아웃 구현 상태) · [144](20260713_144_p08-close-deploy-validation.md).*
