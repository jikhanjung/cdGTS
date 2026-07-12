"""
P06.3b capstone demo (idempotent, add-only) — makes the P06 science engine features *visible*:

  1. Two tiny graphs that differ only by whether the shared decay-constant dependency is MODELLED — the
     correct-vs-naive contrast, so the coherence gate flips:
     - demo-cov-shared      : both U-Pb ages consume ONE decay-238U calibration node → the systematic is
                              recorded as a shared source → covariance shrinks σ_gap → L1b PASS.
     - demo-cov-independent : the naive treatment — no calibration node; each age carries the full ± inline,
                              untagged → errors added in quadrature (Cov 0) → L1b WARN.
     ²³⁸U decay constant is one physical value → decay-238U is exactly ONE node, present only in the graph
     that records the dependency. Chain (shared): [calibration-constant] --calibration--> [radiometric-uPb
     age] --age--> [boundary]. The systematic is authored ONCE on the node (single source of truth, provenance
     visible as an edge) — not a magic string hand-typed onto each boundary. The order edge asserts the
     sequence (L1b/L2 only judge boundaries the user connected). Open each in the Editor, Evaluate, read chips.

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

        bnd = NodeType.objects.get(slug="boundary")
        upb = NodeType.objects.get(slug="radiometric-uPb")
        cal = NodeType.objects.get(slug="calibration-constant")
        unt = NodeType.objects.get(slug="unit")
        ole = Boundary.objects.filter(slug="base-olenekian").first()
        ani = Boundary.objects.filter(slug="base-anisian").first()
        if not (ole and ani):
            self.stdout.write("  (skip covariance graphs — base-olenekian/base-anisian not seeded)")
            return

        # ²³⁸U decay constant is ONE physical value — so decay-238U is exactly ONE node, and it lives only in
        # the graph that *records* the shared dependency. The contrast is correct-vs-naive, not "two constants":
        #   shared      : both U-Pb ages consume ONE decay-238U node → each authors only its analytical σ
        #                 (≈0.5385); the node supplies the systematic σ 1.4 (folded into marginal → √(0.5385²+
        #                 1.4²)=1.5) AND tags it shared → durations correlate → L1b PASS.
        #   independent : the naive treatment — the shared dependency is NOT modelled (no calibration node).
        #                 Each age carries the full ± inline (analytical 0.5385 ⊕ systematic 1.4), untagged →
        #                 errors added in quadrature, Cov 0 → L1b WARN.
        # Marginal value+± are identical across the two graphs; only the provenance (the node + wires) differs.
        analytical = {"fidelity": "decomposed", "sigma": 1, "budget": {"analytical": 0.5385}}          # 1σ 0.5385
        marginal = {"fidelity": "decomposed", "sigma": 1, "budget": {"analytical": 0.5385, "systematic": 1.4}}  # 1σ 1.5, untagged

        def cal_params():
            # value_ma is a linearization reference only (unused downstream — never flows as an age);
            # what propagates is the systematic σ 1.4, auto-tagged with ref="decay-238U" by the kernel.
            return {"symbol": "decay-238U", "kind": "decay-constant",
                    "distribution": {"fidelity": "decomposed", "value_ma": 248.0, "sigma": 1,
                                     "budget": {"systematic": 1.4},
                                     "note": "U decay-const systematic (linearized ~248 Ma; only σ propagates)"}}

        def build(slug, name, shared):
            g, _ = Graph.objects.get_or_create(slug=slug, defaults={"name": name})
            g.name = name
            g.save(update_fields=["name"])
            g.edges.all().delete()
            g.nodes.all().delete()
            g.gateways.all().delete()

            # Layout: calibration (left) → age (mid) → boundary (right). top→bottom = younger→older.
            # shared → one decay-238U node feeds both ages; independent → no calibration node at all.
            cal_node = None
            if shared:
                cal_node = NodeInstance.objects.create(graph=g, key="cal-decay238u", node_type=cal, nature="generic",
                                                       label="λ238U", params=cal_params(), x=0, y=160)

            def boundary_chain(tag, label, value, boundary, y):
                age_dist = {**(analytical if shared else marginal), "value_ma": value}
                a = NodeInstance.objects.create(graph=g, key=f"age-{tag}", node_type=upb, nature="generic",
                                                label=f"U-Pb {value} Ma", params={"distribution": age_dist}, x=190, y=y)
                b = NodeInstance.objects.create(graph=g, key=f"bnd-{tag}", node_type=bnd, nature="boundary",
                                                label=label, params={}, x=380, y=y)
                if cal_node is not None:
                    Edge.objects.create(graph=g, source=cal_node, source_port="value", target=a, target_port="calibration", kind="data")
                Edge.objects.create(graph=g, source=a, source_port="age", target=b, target_port="age", kind="data")
                Gateway.objects.create(graph=g, slug=f"{slug}-{tag}", name=f"base-{tag}", node=b, boundary=boundary)
                return b

            b_ole = boundary_chain("olenekian", "Base Olenekian", 249.0, ole, 280)
            b_ani = boundary_chain("anisian", "Base Anisian", 247.0, ani, 40)

            # Olenekian time unit spanning the two boundaries — the *asserted* span the gate judges.
            # order edge 인터리브: base(older).younger → unit.older , unit.younger → top(younger).older.
            u = NodeInstance.objects.create(graph=g, key="unit-olenekian", node_type=unt, nature="generic",
                                            label="Olenekian", params={}, x=380, y=160)
            Edge.objects.create(graph=g, source=b_ole, source_port="younger", target=u, target_port="older", kind="order")
            Edge.objects.create(graph=g, source=u, source_port="younger", target=b_ani, target_port="older", kind="order")
            self.stdout.write(f"  graph {slug} ({'shared decay-238U node' if shared else 'naive independent (no node)'})")

        # gap 2.0 Ma, each marginal 1σ 1.5. indep: Cov 0 → 2σ_gap ≈ 4.24 > 2 → warn.
        # shared: one node → Cov 1.96 → Var_gap 0.58 → 2σ_gap ≈ 1.52 < 2 → pass.
        build("demo-cov-independent", "Demo: duration overlap (naive independent errors → L1b warn)", shared=False)
        build("demo-cov-shared", "Demo: duration resolved (shared decay-238U node → L1b pass)", shared=True)

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
