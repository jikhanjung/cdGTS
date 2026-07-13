# 20260713_143 — git-free 배포 (P08.6)

[P08](20260713_P08_deploy-data-contract-retrofit.md) 의 마지막 항목. 운영 서버의 **앱 소스 체크아웃(git pull) 의존을
배포 경로에서 제거**. 이로써 P08(레인 경계·매니페스트·동사·헬스·git-free)이 전부 착지.

## 문제

기존 배포는 운영 호스트에서 `git pull` → `sync_to_srv.sh`(repo 의 `deploy/host/*` → `/srv/cdGTS`) → `deploy.sh`.
= 운영 서버에 **이미지(Docker Hub) + repo 소스** 둘 다 필요. 그런데 배포에 실제로 쓰는 소스는 `deploy/host/*`
(compose·deploy.sh·smoke·rollback·maintenance)뿐이고, 앱 코드는 이미 이미지 안에 있다.

## 열쇠 — host 파일은 이미 이미지에 있었다

Dockerfile 이 `COPY . .` 라 `deploy/host/*` 가 이미 이미지 `/app/deploy/host/` 에 실린다(`.dockerignore` 는
devlog·docs 만 제외, deploy 는 포함). 0.1.55 이미지로 확인: compose·deploy.sh·deploy-prod/dev·maintenance 존재.
→ 새 아티팩트 파이프라인 불필요, **이미지에서 추출**만 하면 된다.

## 한 일

- **`deploy/host/_extract_and_deploy.sh`**(신규, 공유 코어) — `DEPLOY_SNAPSHOT` + 버전을 받아 이미지 pull →
  `docker create` + `docker cp` 로 `/app/deploy/host/{compose,deploy.sh,smoke.sh,rollback.sh,maintenance}` 를
  `/srv/cdGTS` 로 추출(구버전 이미지에 없는 파일은 관용적으로 skip) → 갓 추출한 `deploy.sh` 로 `exec` 위임.
- **`deploy-prod.sh`/`deploy-dev.sh`** — 2줄 래퍼를 `_extract_and_deploy.sh` 호출로 재작성(prod=스냅샷1/dev=0).
  실행 중 자신을 덮어쓰지 않도록 래퍼·코어는 추출 대상에서 제외(안정 부트스트랩).
- **`sync_to_srv.sh`** — **부트스트랩/래퍼 갱신 전용**으로 강등(상시 배포에서 빠짐). 호스트 상시 파일 =
  `.env` + `deploy-prod/dev.sh` + `_extract_and_deploy.sh`.
- **`build.sh`** 마지막 안내를 git-free 흐름(`deploy-{prod,dev}.sh X.Y.Z`)으로 갱신. Dockerfile 에 host 파일이
  이미지에 실림을 명시하는 주석. `deploy.toml [verbs]` = deploy(git-free)·bootstrap 분리.

## 검증

- 추출 시뮬레이션(로컬 0.1.55 이미지 → temp): compose·deploy.sh·maintenance 추출 + smoke/rollback(구버전
  미포함) **관용 skip** 확인 → 구버전 롤백 대상에도 안전. 0.1.56 이미지엔 5개 전부 실림.
- `bash -n` 전 스크립트 통과. 코드(Python)·테스트 무변경.

## 부트스트랩(0.1.56 1회)

기존 호스트의 `deploy-prod/dev.sh` 는 옛 2줄 버전이라, **이번 릴리스만** repo 머신에서 `sync_to_srv.sh` 1회로
새 래퍼(+`_extract_and_deploy.sh`)를 설치해야 한다. 이후 릴리스는 `deploy-{prod,dev}.sh X.Y.Z` 만으로 git 불필요.
(DEPLOY.md 0.1.56 항목에 명시.)

## 남은 것 / 범위 밖

- dolfinid SSH 인증 자체는 호스트 이슈(계약 §운영 git pull 제거의 "결정 게이트 분리"는 원터치 트리거 별건).
- P08 완료 → **0.1.56 실배포로 최종 검증**(seed replace 운영 데이터 보존·[6/6] smoke·git-free 추출).

*근거: `../devdocs/wiki/deploy-data-contract.md`(운영 git pull 제거) · [P08](20260713_P08_deploy-data-contract-retrofit.md).*
