# Naming — cdGTS

*English · [한국어](naming.md)*

Decisions and rationale for the project name and its typography. (Single source of truth for the style rules.)

## Final form

```markdown
# cdGTS

**Continuously Deployed Geologic Time Scale**

*A graph-based geologic time scale engine.*
```

- Product name: **cdGTS**
- Full name: **Continuously Deployed Geologic Time Scale**
- Tagline: *A graph-based geologic time scale engine*

## Core meaning

cdGTS reimagines the static Geologic Time Scale not as a table or figure but as an **executable data/process engine built from nodes and dependencies**.

- Geologic time units and boundaries are represented as nodes.
- Each node depends on others.
- When a boundary or unit changes, dependent nodes update automatically.
- The whole GTS can be recomputed, or only the affected part regenerated incrementally.
- The result: the GTS is not a static chart but a **continuously updated and deployed, graph-based system**.

## Name candidates

- **cdGTS — Continuously Deployed** *(chosen)* — inspired by CI/CD. Fits the core idea that "a change propagates and updates automatically." Evokes CI/CD, build systems, and dependency graphs for developers; for geologists it reads clearly once expanded on first use.
- **ciGTS — Continuously Integrated** — possible, but "integration" leans toward *merging* many changes. cdGTS is about **change propagation and output regeneration**, so CD fits better than CI.
- **cGTS** — short, but `c` is ambiguous (continuous / computational / composable / connected / compiled). Doesn't convey the core idea directly.

## Style rules

- **geologic** (not *geological*). As in `geologic time`, `geologic time scale`, `geologic map`, `geologic unit` — it suits **formal terms, data, and system names**. *geological* is more general/descriptive (geological history / evidence / interpretation).
- **Time Scale** — two words (not *TimeScale*).
- A **space before the parenthesis**: `cdGTS (Continuously Deployed Geologic Time Scale)`.
- Put the **title and tagline on separate lines** for a clean README / document header.

## Recommended README opening

> cdGTS is a graph-based geologic time scale engine that represents chronostratigraphic units and boundaries as interconnected nodes. Changes propagate through dependency relationships, allowing the geologic time scale to be rebuilt incrementally and reproducibly.

More technical:

> cdGTS models the Geologic Time Scale as an executable dependency graph, where boundaries, stages, series, systems, and higher-level units are represented as nodes whose derived properties can be updated automatically when upstream information changes.
