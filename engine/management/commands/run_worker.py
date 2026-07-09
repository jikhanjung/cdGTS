"""
비동기 평가 워커 (P06.4a) — queued EvalJob 을 폴링해 처리.

배포: web 컨테이너와 별개 프로세스(compose `worker` 서비스, 같은 이미지·DB).
DB-잡 폴링이라 Redis/Celery 같은 브로커 의존이 없다. 나중에 필요하면 Celery 로 교체(잡 로직은
engine.jobs 에 있으니 인터페이스 유지).
"""
import signal
import time

from django.core.management.base import BaseCommand

from engine.jobs import claim_next_job, process_job


class Command(BaseCommand):
    help = "비동기 평가 워커 — queued EvalJob 을 폴링해 evaluate_graph 로 처리."

    def add_arguments(self, parser):
        parser.add_argument("--poll", type=float, default=2.0,
                            help="빈 큐일 때 폴링 간격(초). 기본 2.0")
        parser.add_argument("--once", action="store_true",
                            help="큐를 한 번 비우고 종료(테스트/배치). 기본은 상주.")

    def handle(self, *args, **opts):
        poll, once = opts["poll"], opts["once"]
        self._stop = False
        signal.signal(signal.SIGTERM, self._request_stop)
        signal.signal(signal.SIGINT, self._request_stop)
        self.stdout.write("run_worker: 시작 (SIGTERM/Ctrl-C 로 종료)")
        while not self._stop:
            job = claim_next_job()
            if job is None:
                if once:
                    break
                time.sleep(poll)
                continue
            self.stdout.write(f"  잡 #{job.pk} 처리 중 (graph={job.graph.slug})…")
            process_job(job)
            self.stdout.write(f"  잡 #{job.pk} → {job.status}")
        self.stdout.write("run_worker: 종료")

    def _request_stop(self, *args):
        self._stop = True
