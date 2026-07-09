"""
P06.3b capstone demo (idempotent, add-only) — makes the P06 science engine features *visible*:

  1. Two tiny graphs that differ only by a shared systematic tag, so the coherence gate flips:
     - demo-cov-independent : two Age boundaries joined by an order edge, wide ±, independent → L1b WARN (2σ overlap).
     - demo-cov-shared      : same values/±, but both share a decay-constant → covariance shrinks σ_gap → L1b PASS.
     The order edge is what *asserts* the sequence — L1b/L2 only judge boundaries the user connected.
     Open each in the Editor, press Evaluate, read the consistency chips (Results panel).

  2. Authored governance clamps on the published ICS-2024/12 release (Vault → Clamps tab):
     - range on base-triassic that the value honors (L3a: honored),
     - pin on base-cambrian that the value violates (L3a: violation) → staff "Reconcile (L3b)" moves it.

  3. A retype pair for the Cryogenian base (Vault → Diff): GSSA → GSSP.
     - Demo.Cryogenian.GSSA : base-cryogenian as a decreed GSSA (720 Ma, exact, no error).
     - Demo.Cryogenian.GSSP : same boundary re-typed to a section-based GSSP — value barely moves
       but its *shape* goes scalar→distribution (exact → ±). Diff A→B shows all three axes:
       topology (retype GSSA→GSSP), value (small Δ), and shape (exact → ±). The point: the biggest
       change (the definition + the arrival of uncertainty) is the one a naive value diff can't see.
       (Illustrative numbers — a real GSSP would be an actual interpolation, not seeded here.)

Run:  python manage.py seed_demo         (safe to re-run — get_or_create + rebuild)
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Seed the P06 capstone demo (covariance-gate graphs + authored clamps). Idempotent."

    def handle(self, *args, **opts):
        self._covariance_graphs()
        self._clamps()
        self._retype_demo()

    # --- 1. covariance gate: two graphs identical but for a shared systematic tag ---
    def _covariance_graphs(self):
        from chrono.models import Boundary
        from graph.models import Edge, Gateway, Graph, NodeInstance
        from nodes.models import NodeType

        pub = NodeType.objects.get(slug="published-age")
        unt = NodeType.objects.get(slug="unit")
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
            g.edges.all().delete()
            g.nodes.all().delete()
            g.gateways.all().delete()
            # Layout top→bottom = younger→older (ICC convention): Base Anisian(247) · Olenekian unit · Base Olenekian(249).
            n1 = NodeInstance.objects.create(graph=g, key="pub-olenekian", node_type=pub, nature="boundary",
                                             label="Base Olenekian", params={"distribution": dist(249.0, shared)}, x=120, y=280)
            n2 = NodeInstance.objects.create(graph=g, key="pub-anisian", node_type=pub, nature="boundary",
                                             label="Base Anisian", params={"distribution": dist(247.0, shared)}, x=120, y=40)
            Gateway.objects.create(graph=g, slug=f"{slug}-ole", name="base-olenekian", node=n1, boundary=ole)
            Gateway.objects.create(graph=g, slug=f"{slug}-ani", name="base-anisian", node=n2, boundary=ani)
            # Olenekian time unit spanning the two boundaries — this is the *asserted* span the gate judges.
            # order edge 인터리브: base(older).younger → unit.older , unit.younger → top(younger).older.
            u = NodeInstance.objects.create(graph=g, key="unit-olenekian", node_type=unt, nature="generic",
                                            label="Olenekian", params={}, x=120, y=160)
            Edge.objects.create(graph=g, source=n1, source_port="younger", target=u, target_port="older", kind="order")
            Edge.objects.create(graph=g, source=u, source_port="younger", target=n2, target_port="older", kind="order")
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

    # --- 3. retype pair: Cryogenian base GSSA → GSSP (topology + value + shape diff) ---
    def _retype_demo(self):
        from chrono.models import Boundary
        from releases.models import BoundaryRecord, Release

        # Neighbours are identical in both releases → they don't clutter the diff; only the
        # Cryogenian base changes. Each entry: definition_type, value_ma, uncertainty (Distribution|None), method.
        exact = lambda v: {"fidelity": "exact", "value_ma": v}                      # noqa: E731
        dist = lambda v, s2: {"fidelity": "decomposed", "value_ma": v, "sigma": 2,  # 2σ half-width = s2
                              "budget": {"model": s2}}                               # noqa: E731

        gssa = {
            "base-tonian":     ("GSSA", 1000.0, exact(1000.0), "decreed"),
            "base-cryogenian": ("GSSA", 720.0,  exact(720.0),  "decreed"),
            "base-ediacaran":  ("GSSP", 635.0,  dist(635.0, 0.6), "local-interpolation"),
        }
        gssp = dict(gssa)
        # The retype: same boundary, now a section-based GSSP. Value barely moves; error appears.
        gssp["base-cryogenian"] = ("GSSP", 719.5, dist(719.5, 0.9), "local-interpolation")

        def build(version, note, records):
            rel, _ = Release.objects.get_or_create(
                version=version, defaults={"kind": Release.Kind.PUBLISHED, "is_baseline": False, "note": note})
            rel.note = note
            rel.save(update_fields=["note"])
            rel.records.all().delete()                                              # rebuild → idempotent
            rows = []
            for bslug, (dtype, value, unc, method) in records.items():
                b = Boundary.objects.filter(slug=bslug).first()
                if b is None:
                    continue
                rows.append(BoundaryRecord(release=rel, boundary=b, definition_type=dtype,
                                           value_ma=value, uncertainty=unc, method=method))
            BoundaryRecord.objects.bulk_create(rows)
            self.stdout.write(f"  release {version} ({len(rows)} records)")

        build("Demo.Cryogenian.GSSA", "Illustrative: Cryogenian base as a decreed GSSA (720 Ma, exact).", gssa)
        build("Demo.Cryogenian.GSSP",
              "Illustrative: Cryogenian base re-typed to a section-based GSSP — value barely moves, "
              "uncertainty appears (exact → ±). Diff Demo.Cryogenian.GSSA → this to see all three axes.", gssp)
