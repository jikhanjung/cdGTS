"""
seed — 통합 초기 데이터(seed/) 를 로드.

두 모드:
  --mode=replace  시스템 정의 데이터를 픽스처와 정합(upsert + 프룬). 운영 데이터는 안 건드림.
  --mode=add      자연키로 **없는 것만** insert (기존 행 보존). 증분 시드.

**레인 경계(배포·데이터 계약, devlog P08).** replace 는 *시스템 정의 데이터*(개발자 저작 레지스트리·
예제 그래프·공표/데모 릴리스 = owner NULL)만 건드리고, *운영 데이터*(학자 fork 그래프·bake·Proposal =
owner set)는 절대 건드리지 않는다. 판별자 = `owner IS NULL`.

replace 전략(참조 무결성 보존):
  - **레지스트리**(chrono·nodes·references·candidate·Release·Selection) = **자연키 upsert**(제자리 갱신).
    pk 를 보존해야 운영 데이터의 PROTECT/CASCADE 참조(Proposal.baseline→Release,
    Selection.candidate→ModelCandidate, 운영 Selection/Record→chrono.Boundary)가 깨지지 않는다.
  - **graph 계열**(NodeInstance·Edge·Gateway 는 자연키 없음 → upsert 불가) = 시스템 그래프(owner NULL)만
    통째 삭제(CASCADE) 후 재생성. 운영 참조는 전부 SET_NULL 이라 안전.
  - **파생물**(BoundaryRecord·engine 산출) = 시스템 스코프만 비우고 시스템 릴리스 재-bake.
  - 픽스처에서 사라진 시스템 행은 prune(스코프 한정).

fixture 는 자연키(pk 없음)라 add 모드에서 pk 충돌이 없다(설계 devlog P02).
그래프/릴리스는 add 에서 **원자 단위**: slug/version 이 이미 있으면 그 자식(노드·엣지·게이트웨이·selection)까지
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

# 로드 의존 순서(부모 먼저). replace 프룬은 이 역순.
SEED_MODELS = [
    "chrono.Authority", "chrono.Unit", "chrono.Boundary",
    "chrono.BoundaryLineage", "chrono.Ratification", "chrono.Locality",
    "nodes.NodeType", "nodes.Port", "references.Reference",
    "graph.Graph", "graph.NodeGroup", "graph.NodeInstance", "graph.Edge", "graph.Gateway",
    "releases.ModelCandidate", "releases.Clamp", "releases.CandidateOutput",
    "releases.Release", "releases.Selection",
]
# 파생물 — replace 시 시스템 스코프만 정리 후 재-bake(운영 bake·eval 캐시는 보존).
DERIVED_MODELS = [
    "releases.BoundaryRecord",
    "engine.NodeResult", "engine.CoherenceCertificate", "engine.EvalRun",
]

# graph.* 는 자연키 없는 자식을 포함 → upsert 불가. 시스템 그래프는 삭제+재생성한다.
GRAPH_MODELS = {"graph.graph", "graph.nodegroup", "graph.nodeinstance", "graph.edge", "graph.gateway"}

# 운영(owner-set) 데이터를 보존하려 삭제/프룬을 시스템 소유 행으로 한정하는 필터.
# 여기 없는 레지스트리 모델(chrono·nodes·references·candidate)은 전량 시스템으로 취급.
SYSTEM_SCOPE = {
    "graph.graph": {"owner__isnull": True},
    "releases.release": {"owner__isnull": True},
    "releases.selection": {"release__owner__isnull": True},
    "releases.boundaryrecord": {"release__owner__isnull": True},
    "engine.evalrun": {"graph__owner__isnull": True},
    "engine.noderesult": {"eval_run__graph__owner__isnull": True},
    "engine.coherencecertificate": {"eval_run__graph__owner__isnull": True},
}

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
                inserted, updated, removed = self._replace(paths)
                self.stdout.write(f"  inserted {inserted} · updated {updated} · removed {removed}")
                bake_only, bake_system = None, True      # 시스템 릴리스만 재-bake
            else:
                inserted, skipped, new_versions = self._add_load(paths)
                self.stdout.write(f"  inserted {inserted} · skipped {skipped}")
                bake_only, bake_system = new_versions, False

            baked = 0
            if not no_bake and not dry:
                baked = self._bake(bake_only, system_only=bake_system)

            if dry:
                transaction.set_rollback(True)
                self.stdout.write(self.style.WARNING("  DRY-RUN → 롤백(변경 없음)"))

        self.stdout.write(self.style.SUCCESS(f"완료 (version {version}, bake {baked} releases)"))

    # --- replace (시스템 정의 데이터만; 운영 데이터 보존) ---
    def _replace(self, paths):
        removed = 0

        # 1) 시스템 그래프(owner NULL) 통째 삭제 → 자식·eval 은 CASCADE. 운영 그래프는 보존
        #    (운영 fork 의 forked_from·릴리스 source_graph 는 SET_NULL 이라 딸려 삭제되지 않음).
        Graph = _model("graph.Graph")
        removed += Graph.objects.filter(owner__isnull=True).delete()[0]
        #    파생 bake 는 릴리스 upsert 로 pk 가 유지돼 CASCADE 되지 않음 → 시스템 것만 비우고 재-bake.
        for label in DERIVED_MODELS:
            model = _model(label)
            if model is not None:
                removed += _scoped_qs(model, label.lower()).delete()[0]

        # 2) 픽스처 스트림 로드. graph.* = 신규 insert(방금 삭제), 나머지 = 자연키 upsert(pk 보존).
        inserted = updated = 0
        seen = {}
        deferred = []
        for obj in _load(paths):
            inst = obj.object
            label = inst._meta.label_lower
            if label in GRAPH_MODELS:
                inserted += 1
            else:
                nk = _natural_key(inst)
                if nk is not None:
                    seen.setdefault(label, set()).add(nk)
                    pk = _existing_pk(inst)
                    if pk is not None:
                        inst.pk = pk                 # 제자리 갱신(UPDATE) → 참조 무결성 유지
                        updated += 1
                    else:
                        inserted += 1
                else:
                    inserted += 1
            obj.save()
            if getattr(obj, "deferred_fields", None):
                deferred.append(obj)
        for obj in deferred:                         # 2패스: 지연된 forward-ref FK 확정
            obj.save_deferred_fields()

        # 3) 픽스처에서 사라진 시스템 레지스트리 행 prune(스코프 한정). graph.* 은 1)에서 이미 처리됨.
        removed += self._prune(seen)
        return inserted, updated, removed

    def _prune(self, seen):
        n = 0
        for label in reversed(SEED_MODELS):
            key = label.lower()
            if key in GRAPH_MODELS:
                continue                             # 그래프는 삭제+재생성으로 이미 정합
            model = _model(label)
            if model is None:
                continue
            keep = seen.get(key, set())
            stale_pks = [o.pk for o in _scoped_qs(model, key) if _natural_key(o) not in keep]
            if not stale_pks:
                continue
            self_fks = [f.name for f in model._meta.fields
                        if f.is_relation and f.remote_field.model is model and f.null]
            if self_fks:                             # 자기참조 PROTECT/CASCADE 를 끊고 삭제
                model.objects.filter(pk__in=stale_pks).update(**{name: None for name in self_fks})
            n += model.objects.filter(pk__in=stale_pks).delete()[0]
        return n

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

    def _bake(self, only, system_only=False):
        from releases.services import bake_release
        Release = _model("releases.Release")
        qs = Release.objects.all() if only is None else Release.objects.filter(version__in=only)
        if system_only:                              # 운영 bake 는 건드리지 않음
            qs = qs.filter(owner__isnull=True)
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


def _scoped_qs(model, label_lower):
    """모델의 시스템 소유 행 queryset(SYSTEM_SCOPE 없으면 전량)."""
    scope = SYSTEM_SCOPE.get(label_lower)
    return model.objects.filter(**scope) if scope else model.objects.all()


def _natural_key(inst):
    nk = getattr(inst, "natural_key", None)
    if nk is None:
        return None
    try:
        return tuple(nk())
    except Exception:
        return None


def _existing_pk(inst):
    """인스턴스의 자연키에 해당하는 기존 행의 pk (없으면 None)."""
    Model = inst.__class__
    try:
        return Model.objects.get_by_natural_key(*inst.natural_key()).pk
    except (Model.DoesNotExist, AttributeError):
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
