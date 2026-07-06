"""
seed — 통합 초기 데이터(seed/) 를 로드.

두 모드:
  --mode=replace  seed 범위(+파생물) 를 flush 후 전체 로드. (깨끗한 재구축)
  --mode=add      자연키로 **없는 것만** insert (기존 행 보존). 증분 시드.

fixture 는 자연키(pk 없음)라 add 모드에서 pk 충돌이 없다(설계 devlog P02).
그래프/릴리스는 **원자 단위**: slug/version 이 이미 있으면 그 자식(노드·엣지·게이트웨이·selection)까지
통째 skip. 레지스트리/후보 행은 자연키 단위로 판정.

BoundaryRecord(=bake 산출) 는 seed 에 없고, 로드 후 릴리스별 bake 로 생성.
--dry-run 은 트랜잭션 안에서 실제 경로를 실행한 뒤 롤백(정확한 미리보기).
"""
import json
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.core import serializers
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

SEED_DIR = Path(settings.BASE_DIR) / "seed"

# 로드 의존 순서(부모 먼저). replace 삭제는 이 역순.
SEED_MODELS = [
    "chrono.Authority", "chrono.Unit", "chrono.Boundary",
    "chrono.BoundaryLineage", "chrono.Ratification", "chrono.Locality",
    "nodes.NodeType", "nodes.Port",
    "graph.Graph", "graph.NodeGroup", "graph.NodeInstance", "graph.Edge", "graph.Gateway",
    "releases.ModelCandidate", "releases.Clamp", "releases.CandidateOutput",
    "releases.Release", "releases.Selection",
]
# 파생물 — replace 시 함께 정리(cascade 로도 지워지나 명시).
DERIVED_MODELS = [
    "releases.BoundaryRecord",
    "engine.NodeResult", "engine.CoherenceCertificate", "engine.EvalRun",
]

GRAPH_CHILDREN = {"graph.nodeinstance", "graph.edge", "graph.gateway", "graph.nodegroup"}
RELEASE_CHILDREN = {"releases.selection"}


class Command(BaseCommand):
    help = "통합 초기 데이터(seed/) 로드 (replace | add)."

    def add_arguments(self, parser):
        parser.add_argument("--mode", choices=["replace", "add"], default="add",
                            help="replace=전체 재구축 / add=없는 것만 추가(기본)")
        parser.add_argument("--dry-run", action="store_true", help="실행 후 롤백 — 변경 없이 미리보기")
        parser.add_argument("--no-bake", action="store_true", help="로드 후 릴리스 bake 생략")

    def handle(self, *args, **opts):
        mode, dry, no_bake = opts["mode"], opts["dry_run"], opts["no_bake"]
        manifest = json.loads((SEED_DIR / "manifest.json").read_text(encoding="utf-8"))
        version = manifest["version"]
        paths = [SEED_DIR / f for f in manifest["fixtures"]]
        for p in paths:
            if not p.exists():
                raise CommandError(f"seed 파일 없음: {p}")

        self.stdout.write(f"seed version {version} · mode={mode}" + (" · DRY-RUN" if dry else ""))

        with transaction.atomic():
            if mode == "replace":
                deleted = self._delete_all()
                inserted = self._load_all(paths)
                self.stdout.write(f"  deleted {deleted} · inserted {inserted}")
                new_versions = None                      # 전부 bake
            else:
                inserted, skipped, new_versions = self._add_load(paths)
                self.stdout.write(f"  inserted {inserted} · skipped {skipped}")

            baked = 0
            if not no_bake and not dry:
                baked = self._bake(new_versions)

            if dry:
                transaction.set_rollback(True)
                self.stdout.write(self.style.WARNING("  DRY-RUN → 롤백(변경 없음)"))

        self.stdout.write(self.style.SUCCESS(f"완료 (version {version}, bake {baked} releases)"))

    # --- replace ---
    def _delete_all(self):
        # 자기참조 PROTECT FK(예: chrono.Unit.parent)는 일괄 delete 를 막는다
        # (자식이 부모를 참조 → ProtectedError). 삭제 전에 self-FK 를 null 로 끊는다.
        for label in SEED_MODELS:
            model = _model(label)
            if model is None:
                continue
            self_fks = [
                f.name for f in model._meta.fields
                if f.is_relation and f.remote_field.model is model and f.null
            ]
            if self_fks:
                model.objects.update(**{name: None for name in self_fks})
        n = 0
        for label in DERIVED_MODELS + list(reversed(SEED_MODELS)):
            model = _model(label)
            if model is not None:
                n += model.objects.all().delete()[0]
        return n

    def _load_all(self, paths):
        count = 0
        deferred = []
        for obj in _load(paths):
            obj.save()
            count += 1
            if getattr(obj, "deferred_fields", None):
                deferred.append(obj)
        for obj in deferred:                     # 2패스: 지연된 forward-ref FK 확정
            obj.save_deferred_fields()
        return count

    # --- add: 없는 것만 insert (그래프/릴리스 원자) ---
    def _add_load(self, paths):
        skip_graphs, skip_releases = set(), set()
        inserted, skipped, new_versions = 0, 0, []
        deferred = []

        for obj in _load(paths):
            inst = obj.object
            label = inst._meta.label_lower

            if label == "graph.graph":
                if _exists(inst):
                    skip_graphs.add(inst.slug); skipped += 1; continue
            elif label in GRAPH_CHILDREN:
                if inst.graph.slug in skip_graphs:       # 부모가 기존 → 원자 skip
                    skipped += 1; continue
            elif label == "releases.release":
                if _exists(inst):
                    skip_releases.add(inst.version); skipped += 1; continue
                new_versions.append(inst.version)
            elif label in RELEASE_CHILDREN:
                if inst.release.version in skip_releases:
                    skipped += 1; continue
            elif _exists(inst):                          # 레지스트리/후보: 자연키 단위
                skipped += 1; continue

            obj.save()
            inserted += 1
            if getattr(obj, "deferred_fields", None):
                deferred.append(obj)

        for obj in deferred:                     # 2패스: 지연된 forward-ref FK 확정
            obj.save_deferred_fields()
        return inserted, skipped, new_versions

    def _bake(self, only):
        from releases.services import bake_release
        Release = _model("releases.Release")
        qs = Release.objects.all() if only is None else Release.objects.filter(version__in=only)
        n = 0
        for rel in qs:
            bake_release(rel); n += 1
        return n


# --- helpers ---
def _model(label):
    try:
        return apps.get_model(label)
    except LookupError:
        return None


def _load(paths):
    for p in paths:
        # handle_forward_references: 순환 자연키 FK(예: NodeGroup.lower/upper ↔ NodeInstance.group)를
        # 지연 해석. 해석 안 된 필드는 obj.deferred_fields 로 남아 전체 로드 후 save_deferred_fields() 로 확정.
        yield from serializers.deserialize(
            "json", p.read_text(encoding="utf-8"),
            use_natural_foreign_keys=True, handle_forward_references=True,
        )


def _exists(inst):
    """인스턴스의 자연키가 DB 에 이미 있으면 True."""
    Model = inst.__class__
    try:
        Model.objects.get_by_natural_key(*inst.natural_key())
        return True
    except Model.DoesNotExist:
        return False
