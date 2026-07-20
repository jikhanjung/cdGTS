# cdGTS Quick Start — fork Example ④ and make an edit

*English · [한국어](quickstart.md)*

A five-minute hands-on for first-time users. Open the app → sign in → **fork** the largest example graph →
change one value → watch it propagate to the boundary ages. For what cdGTS *is*, read the
[introduction](introduction_en.md) first if you like.

> **Before you start.** Accounts are **invite-only** (no public signup) — sign in with the credentials you
> were given. You can **browse read-only without an account**; only `fork`, editing, and saving need a login.

## 0. Open the app

Go to **<https://cdgts.paleobytes.info>**. The top nav has **Editor · Vault · Proposals · Bibliography**.
You land on **Editor**.

## 1. Sign in

Top-right **Login** → username + password → **Sign in**. Your username appears in the nav once in (with ★ if
staff). *No account? Skip this and follow along read-only through step 3.*

## 2. Open Example ④

In the Editor's top-left **graph dropdown**, pick
**"Example ④: Partial ICC — assembling 3 boundaries (P–T · Cambrian base · Precambrian GSSA)"**.

It is the largest example — three boundaries assembled with full provenance: **Permian–Triassic** (GSSP,
Meishan) · **Base of Cambrian** (cross-continental correlation) · **Precambrian GSSA** (a decreed number).
~280 nodes.

## 3. Look around (read-only)

- On load it **auto-evaluates**, attaching results to every node. **Boundary nodes (◈)** show their age (Ma).
- **Zoom / pan**: Ctrl/⌘+wheel to zoom, drag to pan. Click any node → the **Inspector** (right) shows its parameters.
- It's a system graph, so you see a **🔒 Read-only** badge — you can't edit it yet.

## 4. Fork it (your own copy)

Click **`Fork to edit →`** in the toolbar (or **Actions ▾ → Fork…**). Confirm the name (defaults to `… (fork)`)
and you'll see **"Forked → … · yours to edit"** — now editing **your copy**, with **Save** enabled.
*(Not signed in? The button reads "Sign in to fork".)*

## 5. Change one value

1. Click a **data leaf** feeding a boundary (e.g. **Base of Triassic**) — a cited observation such as a
   U–Pb radiometric age or a published age (the blue leaf nodes).
2. In the **Inspector** (right), edit a value — e.g. the distribution's **`value_ma`** — to a different number.
3. The status flips to **● Unsaved**.

## 6. Save and see the result

- Click **Save** → **✓ Saved**.
- **Actions ▾ → Evaluate** re-runs the graph and reattaches results; the boundary ages and the results panel
  update to the new value. *(Evaluate and Verify run on the **saved** graph, so **Save first** after editing.)*

## 7. One-click diff against the published chart ★

**Actions ▾ → Verify vs published** compares your edited graph to the published baseline (ICC `ICS-2024/12`)
and summarizes it in one line:

> `vs published: N moved · max |Δ| X Ma · wiring ＋A/－R/↺T`

= **N boundaries moved**, largest change **X Ma**, plus a wiring (added / removed / retyped) summary. This is
the core cdGTS loop — *if we bring in this new evidence, what changes?* — as a reproducible artifact, not hand
arithmetic.

## 8. (Optional) Bake it and view in the Vault

**Actions ▾ → Bake…** freezes the current results into an **immutable Release**. Switch to the **Vault** tab to
view that release as an **ICC chart, table, or narrative**, and to **diff** it against another release.

---

What you just did traces the two ideas behind cdGTS — the **engine** (change a value, the boundaries recompute)
and **versioning** (freeze a release, diff it). To go deeper:

- [Introduction](introduction_en.md) — what cdGTS is and why it exists.
- [Concept map](concept-map_en.md) — tiers, node categories, and the full document map.
- **No harm done**: a fork is **your own copy**, so the original system graph is untouched — experiment freely.
