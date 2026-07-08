"""
P06.3b capstone demo (idempotent, add-only) — makes the P06 science engine features *visible*:

  1. Two tiny graphs that differ only by a shared systematic tag, so the coherence gate flips:
     - demo-cov-independent : two adjacent Age boundaries, wide ±, treated independent → L1b WARN (2σ overlap).
     - demo-cov-shared      : same values/±, but both share a decay-constant → covariance shrinks σ_gap → L1b PASS.
     Open each in the Editor, press Evaluate, read the consistency chips (Results panel).

  2. Authored governance clamps on the published ICS-2024/12 release (Vault → Clamps tab):
     - range on base-triassic that the value honors (L3a: honored),
     - pin on base-cambrian that the value violates (L3a: violation) → staff "Reconcile (L3b)" moves it.

Run:  python manage.py seed_demo         (safe to re-run — get_or_create + rebuild)
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Seed the P06 capstone demo (covariance-gate graphs + authored clamps). Idempotent."

    def handle(self, *args, **opts):
        self._covariance_graphs()
        self._clamps()

    # --- 1. covariance gate: two graphs identical but for a shared systematic tag ---
    def _covariance_graphs(self):
        from chrono.models import Boundary
        from graph.models import Gateway, Graph, NodeInstance
        from nodes.models import NodeType

        pub = NodeType.objects.get(slug="published-age")
        ole = Boundary.objects.filter(slug="base-olenekian").first()
        ani = Boundary.objects.filter(slug="base-anisian").first()
        if not (ole and ani):
            self.stdout.write("  (skip covariance graphs — base-olenekian/base-anisian not seeded)")
            return

        def dist(value, shared):
            d = {"fidelity": "decomposed", "value_ma": value, "sigma": 2, "budget": {"model": 3.0}}   # 1σ = 1.5
            if shared:
                d["fidelity"] = "joint"
                d["shared_components"] = [{"ref": "decay-238U", "sigma": 1.4}]   # shared decay constant
            return d

        def build(slug, name, shared):
            g, _ = Graph.objects.get_or_create(slug=slug, defaults={"name": name})
            g.name = name
            g.save(update_fields=["name"])
            g.nodes.all().delete()
            g.gateways.all().delete()
            n1 = NodeInstance.objects.create(graph=g, key="pub-olenekian", node_type=pub, nature="boundary",
                                             label="Base Olenekian", params={"distribution": dist(249.0, shared)}, x=60, y=60)
            n2 = NodeInstance.objects.create(graph=g, key="pub-anisian", node_type=pub, nature="boundary",
                                             label="Base Anisian", params={"distribution": dist(247.0, shared)}, x=60, y=240)
            Gateway.objects.create(graph=g, slug=f"{slug}-ole", name="base-olenekian", node=n1, boundary=ole)
            Gateway.objects.create(graph=g, slug=f"{slug}-ani", name="base-anisian", node=n2, boundary=ani)
            self.stdout.write(f"  graph {slug} ({'shared' if shared else 'independent'})")

        # gap 2.0 Ma, each 1σ 1.5 → 2σ_gap(indep) ≈ 4.24 > 2 → warn; shared Cov 1.96 → σ_gap 0.76, 2σ 1.52 < 2 → pass
        build("demo-cov-independent", "Demo: duration overlap (independent errors → L1b warn)", shared=False)
        build("demo-cov-shared", "Demo: duration resolved (shared systematic → L1b pass)", shared=True)

    # --- 2. authored clamps on the published release (L3a verify / L3b reconcile) ---
    def _clamps(self):
        from chrono.models import Authority, Boundary
        from releases.models import Clamp, Release
        from releases.services import bake_release

        rel = Release.objects.filter(version="ICS-2024/12").first()
        if rel is None:
            self.stdout.write("  (skip clamps — ICS-2024/12 not seeded)")
            return
        if not rel.records.exists():
            bake_release(rel)
        owner, _ = Authority.objects.get_or_create(
            slug="demo-subcommission",
            defaults={"name": "Demo Subcommission", "kind": Authority.Kind.SUBCOMMISSION})

        def clamp(slug, boundary_slug, kind, value, rationale):
            b = Boundary.objects.filter(slug=boundary_slug).first()
            if b is None:
                return
            c, _ = Clamp.objects.get_or_create(
                slug=slug, defaults={"owner": owner, "target_boundary": b, "kind": kind,
                                     "value": value, "rationale": rationale})
            rel.clamps.add(c)
            self.stdout.write(f"  clamp {slug} → {boundary_slug} ({kind})")

        clamp("demo-clamp-triassic", "base-triassic", "range", {"range": [250.0, 253.0]},
              "Demo: range the baked value honors (L3a honored).")
        clamp("demo-clamp-cambrian", "base-cambrian", "pin", {"value": 536.0},
              "Demo: pin the baked value violates → Reconcile (L3b) moves it.")
