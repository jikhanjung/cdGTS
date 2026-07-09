"""
비동기 평가 잡 처리 (P06.4a) — 워커(`manage.py run_worker`)와 뷰가 공유하는 순수 로직.

커널은 아직 해석적이라 잡이 하는 일 = 동기 evaluate_graph 와 동일. 이번 라운드는 **인프라**
(잡 큐 + 워커 + 원자적 클레임)만 들이고, 진짜 MCMC 커널은 P06.4b 에서 여기 위에 얹는다.
"""
from django.utils import timezone

from .evaluate import evaluate_graph


def claim_next_job():
    """
    가장 오래된 queued 잡을 원자적으로 running 으로 전이하고 반환. 없으면 None.
    SQLite(단일 라이터) 가정 — compare-and-set(`update(... where status='queued')`)의
    영향 행수로 이중 클레임을 막는다. 경합에서 놓치면 다음 후보로 넘어간다.
    """
    from .models import EvalJob

    while True:
        job = EvalJob.objects.filter(status="queued").order_by("id").first()
        if job is None:
            return None
        claimed = EvalJob.objects.filter(pk=job.pk, status="queued").update(
            status="running", started_at=timezone.now())
        if claimed:
            job.refresh_from_db()
            return job
        # 다른 워커가 먼저 채감 — 다음 후보 재조회.


def process_job(job):
    """
    running 잡을 평가해 done/failed 로 마감. 평가 예외는 잡아 error 에 남기고 failed 로.
    (워커 루프가 한 잡 실패로 죽지 않게.) 마감된 잡을 반환.
    """
    try:
        run = evaluate_graph(job.graph)
        job.run = run
        job.status = "done"
        job.error = ""
    except Exception as exc:                     # noqa: BLE001 — 실패를 상태로 보존
        job.status = "failed"
        job.error = f"{type(exc).__name__}: {exc}"
    job.finished_at = timezone.now()
    job.save(update_fields=["run", "status", "error", "finished_at"])
    return job
