"""
/healthz — 가벼운 헬스체크 (배포·데이터 계약 P08.5).

smoke 동사가 찌른다: 버전(이미지에 구운 VERSION) + DB 연결 + 핵심 시스템 행 수(0 아님).
스테이크가 낮은 프로젝트라 무겁게 만들지 않는다 — 200/503 + 최소 JSON.
인증 없음(헬스체크는 항상 도달 가능해야 함), GET, 부작용 없음.
"""
from django.http import JsonResponse

from config.version import VERSION


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
    return JsonResponse(body, status=200 if ok else 503)
