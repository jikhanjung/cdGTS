# 20260715_150 — 매시 무결성 게이트: 탐지가 아니라 **로테이션 오염 방지**

> 성격: **운영 안전망.** [devlog 149 addendum](20260715_149_order-node-and-clamp-category-removal.md#addendum-2026-07-15--배포-중-발견-sync-cdgts-dbsh-가-테스트-db-를-깨뜨리고-있었다)
> (테스트 DB 2회 손상)의 후속. 계기: 사용자 — *"prod DB 무결성도 매시 자동으로 체크하게 해줄까?"*
> 릴리스: **0.1.68**

## 1. 진짜 위험은 "늦게 아는 것"이 아니다

손상을 몇 시간 늦게 아는 건 불편할 뿐이다. 진짜 위험은 그 몇 시간 동안 **복구 대상이 사라진다**는 것이다.

`backup_db.py` 는 `src.backup(dst)`(online backup API)로 스냅샷을 뜬다. 이건 소스 페이지를 **충실히** 복사한다 —
검증하지 않는다. 그래서 소스가 깨져 있으면:

```
06:00  손상 발생
07:00  깨진 스냅샷 생성 → 채택 → 가장 오래된 성한 것 1개 prune
08:00  깨진 스냅샷 … 성한 것 1개 더 prune
  ⋮
19:00  RETAIN_COUNT=12 소진 → **성한 스냅샷 0개.** 남은 12개는 전부 같은 손상의 사본.
```

**백업이 스스로를 오염시킨다.** 149 의 테스트 DB 손상이 prod 에서 일어났다면 정확히 이 경로였다
(그때 손상은 약 9시간 미탐지였다 — 위 표에서 19:00 까지 4시간 남은 지점).

> 그래서 이건 "모니터링을 하나 더 붙이자"가 아니다. **백업의 전제 조건을 고치는 일**이다.
> 검증되지 않은 백업은 백업이 아니라 백업의 사본이다.

## 2. 규칙은 두 줄

```
1. 스냅샷이 integrity_check 에 걸리면 → 채택하지 않는다 + prune 을 건너뛴다
2. DB 디렉터리에 센티넬을 남긴다 → /healthz degraded → smoke 실패
```

**(1) 이 본체다.** 아무도 안 보고 있어도 자동으로 성한 스냅샷을 지킨다. **(2) 는 사람에게 닿는 경로**다.

## 3. 왜 로그가 아니라 센티넬인가

prod crontab 에 **`MAILTO` 가 없다.** cron 실패는 `backup/backup.log` 에만 남고, 그 파일은 아무도 안 읽는다.
**읽히지 않는 검사는 연극이다** — 붙여봐야 "검사가 있다"는 착각만 생긴다.

그래서 사람이 **이미** 보는 곳에 물렸다: 배포마다 도는 `smoke`.

| 후보 | 판정 |
|---|---|
| `backup.log` 에만 기록 | ✗ 아무도 안 읽음 (현 상태와 동일) |
| `MAILTO` 설정 | △ 메일 인프라 의존, 3-repo 호스트 공용 설정 — 별건 |
| `/healthz` 가 직접 `integrity_check` | ✗ **공개·무인증 엔드포인트에 full scan = DoS 표면** |
| **cron 이 검사 → 센티넬 파일 → healthz 는 `stat` 만** | ✔ 비싼 건 매시 1회, healthz 는 그대로 가볍다 |

## 4. 센티넬이 `backup/` 이 아니라 `db/` 에 있는 이유

0.1.64 가 컨테이너 시야에서 `backup/`·`.env`·배포 스크립트를 **의도적으로** 뺐다(blast radius 축소).
컨테이너가 보는 건 `/srv/cdGTS/db` → `/app/hostdb` 뿐이다.

→ 센티넬을 `db/INTEGRITY_FAIL` 에 둔다. **마운트를 되돌리지 않고**, 의미상으로도 "DB 가 깨졌다" 플래그는 DB 옆이 맞다.
경로는 `Path(settings.DATABASES['default']['NAME']).parent / 'INTEGRITY_FAIL'` 로 유도 — 규약이 한 곳에서만 온다.

## 5. degraded 는 왜 503 이 아닌가

503 의 의미는 **"이 컨테이너에 트래픽을 보내지 말라"** 다. btree 한 곳이 깨진 것과 서빙 불능은 다르다 —
앱은 여전히 답하고 있고, **재시작이 고칠 수 없는 조건**으로 LB 에서 빼거나 restart 루프를 돌리면 손해만 난다.

그러면 게이트는 어떻게 걸리나? `smoke.sh` 는 `status == "ok"` 만 통과시킨다. **200 이어도 배포는 막힌다.**
→ 트래픽 의미론은 건드리지 않고 게이트만 얻는다.

| 상태 | HTTP | 뜻 |
|---|---|---|
| `ok` | 200 | 정상 |
| `degraded` | **200** | DB 손상 감지(센티넬 존재). **서빙은 된다** |
| `unhealthy` | 503 | DB 연결 실패 / 시스템 시드 부재 |

`unhealthy` 가 `degraded` 보다 우선 — 연결조차 안 되면 손상 여부는 부차적이다.

## 6. 자동화가 하지 않는 것

smoke 실패는 **자동 롤백을 부르지 않는다**(deploy.sh 는 exit 1 + 안내만). 이건 의도다 —
DB 손상에 대해 롤백은 **답이 아닐 수 있다**. `--db=keep` 은 손상을 그대로 두고, `--db=restore` 는 스냅샷을
복원하는데 그 스냅샷이 성한지는 사람이 판단해야 한다. 그래서 smoke 는 손상 시 **배포 문제가 아님을 명시**하고
복구 후보 위치를 알려주는 데서 멈춘다.

## 7. 무엇을 만들었나

| 층 | 내용 |
|---|---|
| `scripts/backup_db.py` | `integrity_check()`(mode=ro) · `raise_sentinel()`/`clear_sentinel()`(자기해제) · **채택 전 게이트** · main 의 prune 건너뛰기 · exit 1 |
| `config/health.py` | `_integrity_sentinel()` — stat 1회. `degraded`(200) + `integrity` 필드(센티넬 첫 줄) |
| `deploy/host/smoke.sh` | degraded 전용 분기 — "배포 문제 아님" + 복구 후보 경로 + 해제법 |
| `deploy/host/deploy.sh` | FATAL 안내문 `--force-recreate cdgts` → `--force-recreate`(§9) |
| 테스트 | `scripts/test_backup_db.py` **15종** 신규 + `test_healthz.py` 4종 추가 (pytest 174 → **192**) |
| (부수) | 스냅샷 **`journal_mode=DELETE`** — 아카이브에 WAL 은 무의미하고, mode=ro 검사가 고아를 남긴다(§10) |

**증거 사본**: 손상 스냅샷은 버리지 않고 `backup/cdgts_INTEGRITY_FAIL.corrupt` **1개만** 보존 —
최초가 가장 정보가 많고, 매시 쌓이면(1.1MB × 24/day) 디스크가 샌다. 확장자가 `.sqlite3` 가 아니라
`prune_old()` 의 glob 에도 안 걸린다(테스트로 못 박음).

## 8. 로테이션 오염이 가설이 아님을 테스트가 증명한다

`test_corrupt_source_is_not_promoted` 는 실제 sqlite DB 의 3번째 페이지를 쓰레기로 덮고(헤더는 살려서
"열리지만 깨진" 상태 — 우리가 실제로 겪은 그 상태) `backup_one()` 을 돌린다.

**센티넬과 증거 사본이 생긴다** = 예외 경로가 아니라 **무결성 경로를 탔다** = `backup()` 이 손상을
예외 없이 충실히 복사했다. §1 의 오염 메커니즘이 이제 실측이다.

`test_main_skips_prune_when_integrity_fails` 는 그 짝: 과거 스냅샷 4개 + `RETAIN_COUNT=2` 로도 **4개가 전부 산다.**

## 9. 사용자 질문이 잡아낸 잔재

> *"테스트 서버에서 깨진 원인은 cdgts 는 down 인데 worker 는 아니어서였잖아. 운영서버에서는 그런 문제가 없게 구성되어 있어?"*

전수 감사 결과 **prod 는 안전하고, 우연이 아니다** — 운영 DB 는 *"일부 정지 후 파일 교체"* 의 대상이 된 적이 없다:

| prod 경로 | 방식 | 안전 근거 |
|---|---|---|
| `deploy.sh` pre_deploy 스냅샷 | `docker compose down`(서비스명 없음) | 웹+워커 둘 다 내린 정지 사본 |
| `rollback.sh` restore | `down` → `up -d`(둘 다 서비스명 없음) | 동일 |
| `backup_db.py` | online backup API | **정지 자체가 불필요** — writer 상주를 전제로 설계된 API |
| `sync-cdgts-db.sh` **pull** | prod 에서 `src.backup()` → scp | prod 는 **소스**지 대상이 아님. 파일 교체 없음 |

즉 두 층이 독립적으로 막고 있다: 파일을 교체하는 경로는 0.1.60(devlog 144)이 이미 전 서비스 정지로 고쳤고,
라이브 DB 를 읽는 경로는 애초에 정지가 필요 없는 방식을 쓴다. 149 의 sync 버그는 `$DEV_DB` 만 겨냥했다.

**다만 하나 남아 있었다** — `deploy.sh` 의 DB 바인딩 FATAL 안내문이 `docker compose up -d --force-recreate cdgts`
를 권했다. 손상은 아니지만(서로 다른 파일이라 WAL 공유 없음) 그대로 따르면 **워커만 낡은 `DATABASE_PATH` 로 남아
이미지 내부 DB 를 계속 본다.** 같은 단일-서비스 가정이 **조언 형태로** 살아 있었던 것. → 서비스명 제거.

> 149 의 교훈("워커가 생긴 순간 모든 단일-서비스 가정이 버그가 됐다")은 **실행 코드만 훑어서는 부족했다.**
> 문서·안내문·주석에 박힌 가정도 같은 전수 점검 대상이다 — 사람이 그걸 읽고 실행하니까.

## 10. 게이트가 자기 자신을 물었다 — `mode=ro` 가 고아를 만든다

단위 테스트 14종이 전부 통과한 뒤 **테스트서버 라이브 DB 에 실제로 돌려보니** 부산물이 나왔다:

```
cdgts_20260715_15.sqlite3.tmp-shm    ← 32KB
cdgts_20260715_15.sqlite3.tmp-wal    ← 0B
```

원인은 **내가 방금 넣은 `integrity_check` 자신**이다. `backup()` 은 소스의 저널 모드까지 복사하므로
스냅샷이 WAL 로 뜨는데, **WAL DB 는 리더도 `-shm` 이 필요하다.** `mode=ro` 커넥션은 그걸 만들어놓고
**치울 권한이 없어** 프로세스가 끝나도 남는다. `prune_old()` 의 glob 은 `*.sqlite3` 라 **영구 누적**.

→ 해법은 커넥션 관리가 아니라 **스냅샷을 DELETE 모드로 내리는 것**: 아카이브에 동시 writer 는 없다.
`-wal`/`-shm` 이 **애초에 존재하지 않으므로** 문제가 사라진다. 덤으로 이건 `sync-cdgts-db.sh` 가
*이미 전제하고 있던 계약*("스냅샷은 일관된 단일 파일(-wal/-shm 없음)")을 코드로 못 박은 것이기도 하다.

### 오귀인 정정 (또)

발견 직후 나는 이걸 **"devlog 147 에서 내가 심은 잠복 버그"** 라고 단정했다. `with sqlite3.connect(...)` 가
close 가 아니라 트랜잭션 컨텍스트라는 유명한 함정이 종전 코드에 있었기 때문이다. **틀렸다.** prod 실측:

```
고아 -wal/-shm 개수: 0        정상 스냅샷: 12
```

`backup_db.py` 는 cron 이 띄우는 **단명 프로세스**라 종료 시 GC 가 커넥션을 닫으며 체크포인트했다 — 실해가 없었다.
증거도 갈렸다: 옛 파일은 `.tmp` 없는 `-wal`, 내 것만 `.tmp-wal`. **고아는 오늘 내가 만든 것이다.**

> [149 §교훈](20260715_149_order-node-and-clamp-category-removal.md#교훈)의 "성급한 자기귀인 주의"를 적어놓고
> **같은 라운드에서 반대 방향으로 또 틀렸다** — 그때는 남의 버그를 내 탓으로, 이번엔 내 버그를 과거 탓으로.
> 공통 원인은 하나: **그럴듯한 메커니즘을 찾자마자 실측을 건너뛴 것.** `ls prod/backup` 한 번이면 됐다.

명시적 `close()` 는 그대로 둔다 — GC 타이밍에 기대는 정합성은 계약이 아니고, `integrity_check` 는 정적인
파일을 봐야 한다. 다만 **주석은 "종전 코드에 실해는 없었다"고 정확히 적었다**(귀인 오류가 코드에 화석화되지 않게).

### 이 라운드에서 단위 테스트가 못 잡은 이유

`env` 픽스처의 합성 DB 는 **기본 저널 모드(delete)** 였다. 운영은 WAL(`settings.py` 의 `init_command`).
→ 재현 조건이 픽스처에 없었다. `test_backup_leaves_no_wal_siblings` 는 소스를 **명시적으로 WAL 로 올린 뒤**
"스냅샷 외 파일이 하나도 없을 것"을 단언한다 — `*.tmp` 만 보던 종전 단언은 `.tmp-wal` 을 통과시켰다.

> **"부산물 없음"을 화이트리스트(`*.tmp` 없음)가 아니라 전수(`iterdir()` 에 dest 외 아무것도 없음)로 단언할 것.**
> 화이트리스트는 내가 상상한 실패만 잡는다.

## 11. 부채 / 안 한 것

- ⚠️ **3-repo 정렬 예외**: fcmanager·fsis2026 의 `backup_db.py` 에는 아직 없다([devlog 147](20260714_147_three-repo-consistency-align.md)
  이 동형화해둔 걸 cdGTS 가 선행 — P08 때와 같은 **파일럿**). 검증 후 포팅. 두 repo 는 nginx tar 등 소스가 더 많아 조사 선행 필요.
- **`rollback.sh --db=restore` 는 복원할 스냅샷을 검사하지 않는다.** 오염된 로테이션에서 골라 복원하면 손상을
  되살린다. 이번 게이트가 오염 자체를 막으므로 위험은 크게 줄었지만, 복원 직전 `integrity_check` 1회는 여전히
  값싼 방어다 → 다음 라운드.
- **센티넬 stale 창**: 복구 후 다음 정시까지 최대 1시간 degraded 로 남는다(smoke 가 계속 실패). 의도적으로
  자동 해제를 rollback 에 넣지 않았다 — 복원한 스냅샷이 성한지 검증하지 않은 채 플래그만 지우면 거짓 `ok` 가 된다.
  급하면 `rm /srv/cdGTS/db/INTEGRITY_FAIL`(smoke 안내문에 명시).
- `MAILTO` 는 여전히 미설정. 센티넬은 **배포 시점**에만 사람에게 닿는다 — 배포가 뜸하면 탐지도 뜸하다.
  (prune 보존은 배포와 무관하게 동작하므로 안전망 자체는 유효.)

## 관련

- [devlog 149](20260715_149_order-node-and-clamp-category-removal.md) addendum — 손상 2회의 근본 원인(sync 스크립트)
- [devlog 144](20260713_144_p08-close-deploy-validation.md) — `up -d cdgts` → `up -d`(같은 가정의 첫 수정)
- [devlog 147](20260714_147_three-repo-consistency-align.md) — 3-repo 동형화(이번에 의도적으로 이탈)
- [DEPLOY.md](../DEPLOY.md) 0.1.68 · [deploy/README.md](../deploy/README.md)
