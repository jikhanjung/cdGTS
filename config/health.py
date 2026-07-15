"""
/healthz — 가벼운 헬스체크 (배포·데이터 계약 P08.5).

smoke 동사가 찌른다: 버전(이미지에 구운 VERSION) + DB 연결 + 핵심 시스템 행 수(0 아님).
스테이크가 낮은 프로젝트라 무겁게 만들지 않는다 — 200/503 + 최소 JSON.
인증 없음(헬스체크는 항상 도달 가능해야 함), GET, 부작용 없음.

상태 3종 (0.1.68~):
  ok        200 — 정상
  degraded  200 — hourly backup_db.py 가 DB 손상을 발견(센티넬 존재). **서빙은 되고 있다.**
  unhealthy 503 — DB 연결 실패 또는 시스템 시드 부재(빈 이미지 DB 폴백)

degraded 가 왜 503 이 아닌가: 503 의 의미는 "이 컨테이너에 트래픽을 보내지 말라"인데, btree 한 곳이
깨진 것과 서빙 불능은 다르다. 재시작이 고칠 수 없는 조건으로 LB 에서 빼거나 restart 루프를 돌리면 손해만 난다.
smoke 는 status=="ok" 만 통과시키므로 **200 이어도 배포 게이트는 그대로 걸린다** — 트래픽 의미론 없이 게이트만.
"""
from pathlib import Path

from django.conf import settings
from django.http import JsonResponse

from config.version import VERSION

# scripts/backup_db.py 가 DB 디렉터리에 남기는 손상 플래그. 이름을 양쪽에서 맞춘다.
# stat 한 번 — /healthz 에서 integrity_check 를 직접 돌리지 않는 건 의도다(공개·무인증 엔드포인트에
# full scan 을 걸면 DoS 표면이 된다). 비싼 검사는 매시 cron 이 한 번만 한다.
SENTINEL_NAME = "INTEGRITY_FAIL"


def _integrity_sentinel() -> str | None:
    """DB 옆에 손상 플래그가 있으면 그 첫 줄(타임스탬프+사유)을 돌려준다."""
    try:
        sentinel = Path(settings.DATABASES["default"]["NAME"]).parent / SENTINEL_NAME
        return sentinel.read_text().splitlines()[0]
    except (OSError, KeyError, TypeError, IndexError):
        return None                              # 없음 = 정상 (in-memory 테스트 DB 포함)


def healthz(request):
    counts, ok, error = {}, True, None
    try:
        from chrono.models import Boundary
        from graph.models import Graph
        from nodes.models import NodeType

        counts = {
            "node_types": NodeType.objects.count(),
            "boundaries": Boundary.objects.count(),
            "graphs": Graph.objects.count(),
        }
        # 도메인 불변식: 시스템 시드가 실려 있어야 정상(빈 이미지 DB 폴백 검출).
        ok = counts["node_types"] > 0 and counts["boundaries"] > 0
    except Exception as exc:                     # DB 연결/스키마 실패 = unhealthy
        ok, error = False, str(exc)

    body = {"status": "ok" if ok else "unhealthy", "version": VERSION, "counts": counts}
    if error:
        body["error"] = error

    # unhealthy 가 우선 — 연결조차 안 되면 손상 여부는 부차적. 건전할 때만 센티넬을 본다.
    if ok and (sentinel := _integrity_sentinel()):
        body["status"] = "degraded"
        body["integrity"] = sentinel
        return JsonResponse(body, status=200)

    return JsonResponse(body, status=200 if ok else 503)
