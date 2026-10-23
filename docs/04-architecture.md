# 04 — Architecture, specification fragment, guarantees

Status: **design draft** — freeze in Phase 2 (P2-1).

*Re-scoped 2026-10-22 (D-028):* the monitor is the assured component of a run-time-assurance loop around the VLA
(π0.5 in LIBERO). In the diagram below, the continuous filter is optional context, and "hold / retreat" becomes the
intervention, to be designed in P2-8. The fragment gained bounded Until on 2026-10-23 (P3-9, D-029) and must keep
residuals bounded (P2-4).

## System view

```
 camera / proprio ──► Perception ──► labels (set of atoms per step) ──► MONITOR(φ) ──► verdict
        │                                                                   │            │
        ▼                                                                   ▼            ▼
   VLA (π0 via LeRobot) ──► action chunk ──► Continuous filter ──► Robot   log / hold / retreat
                                              (ATACOM / CBF)
```

* **Perception → labels.** Maps observations (or privileged simulator state at first) to a *label*: the set of
  atomic propositions true at this control step (`grasp_stable`, `lift_cmd`, `in_forbidden_zone`, …).
* **Monitor.** Consumes one label per step, maintains a residual formula, outputs `PENDING / SATISFIED / VIOLATED`.
* **Policy + filter.** Unchanged from existing work. The filter handles continuous geometry; the monitor handles
  discrete/temporal task rules.
* **Reaction.** Detect-only first (logging). Enforcement mode: on `VIOLATED` or imminent violation, hold/retreat.

## Specification fragment (grammar)

```
φ ::= tt | ff
    | p | ¬p                      -- literals; negation only on atoms (NNF)
    | φ ∧ φ | φ ∨ φ
    | X φ                         -- strong next: a next step must exist
    | G φ                         -- always (over the rest of the finite trace)
    | G[0,k] φ                    -- always within the next k+1 steps
    | F[0,k] φ                    -- eventually within the next k+1 steps
    | φ U[0,k] ψ                  -- ψ within the next k+1 steps, φ at every step before it (strong)
```

Internal only: `pending φ` ("a step exists here and φ holds at it"), produced by progression.

Why this shape: **every operator is structural or bounded**, so the monitor step is a total function with no
unbounded search. Bounded `G[0,k]`/`F[0,k]`/`U[0,k]` are bounded quantifiers over a window of the trace (cf. course
Lecture 2). Unbounded `F`/`U` are omitted on purpose. Bounded `U[0,k]` was added on 2026-10-23 for ordering rules such
as "do not place the bowl before the drawer is open" (`¬place U[0,k] drawer_open`; P3-9, D-029). It is strong: a step
where ψ holds must exist within the window. A weak variant (`φ W ψ`) is not in the fragment; add it only if the spec
library (P2-5) needs it.

## Semantics (LTLf, reference)

Trace = finite list of labels. `holds(trace, i, φ)` / Lean `Sat tr φ i`. Positions at/after the end satisfy
nothing that needs a step (literals, `X`, `pending`, `F[0,k]`, `U[0,k]`) and satisfy vacuous universals (`G`, `G[0,k]`).
Code: `monitor/src/bounded_brain/spec.py` and `lean/BoundedBrain/Formula.lean`.

## Monitor by formula progression

`progress σ φ` rewrites φ into the obligation on the rest of the trace after consuming step σ:

| φ | `progress σ φ` |
|---|---|
| `p` / `¬p` | `tt` or `ff` depending on σ |
| `φ ∧ ψ`, `φ ∨ ψ` | `simpAnd/simpOr (progress σ φ) (progress σ ψ)` |
| `X φ` | `pending φ` |
| `pending φ` | `progress σ φ` |
| `G φ` | `simpAnd (progress σ φ) (G φ)` |
| `G[0,k] φ` | `k=0`: `progress σ φ`; else `simpAnd (progress σ φ) (G[0,k-1] φ)` |
| `F[0,k] φ` | `k=0`: `progress σ φ`; else `simpOr (progress σ φ) (F[0,k-1] φ)` |
| `φ U[0,k] ψ` | `k=0`: `progress σ ψ`; else `simpOr (progress σ ψ) (simpAnd (progress σ φ) (φ U[0,k-1] ψ))` |

End of trace: `acceptsEmpty` = `tt`→true, `ff`→false, literals→false, `X`/`pending`→false, `G`/`G[0,k]`→true,
`F[0,k]`/`U[0,k]`→false, `∧`/`∨` compositional. Early verdicts: residual `ff` ⇒ VIOLATED, `tt` ⇒ SATISFIED.

### Design note: why `pending` exists (a bug we caught)

The naive rule `progress σ (X φ) = φ` is **wrong** at the end of a trace: `X (G a)` on a one-step trace must be
*false* (strong next needs a successor step), but the residual `G a` is vacuously true on the empty remainder.
`pending φ` records the obligation "a step must exist"; it is discharged by the next `progress` and fails
`acceptsEmpty`. The Python test suite contains a regression for this
(`test_strong_next_needs_a_successor_step`), and mutating `progress` to the naive rule makes the exhaustive
agreement test fail. The Lean key lemma `progress_sat` (TODO P3-2) is only true with `pending`.

### Early verdicts are sound, not complete

`VIOLATED` is reported only when the residual is syntactically `ff`. A residual may be unsatisfiable on every
extension without having been simplified to `ff` (e.g. contradictory pending obligations). The end-of-trace answer
is exact. Completeness would need a satisfiability check on the residual (TODO P2-2).

### Resource bound (proved 2026-10-23, P3-5)

Per-step residual growth is **not** a constant factor (`G φ` conjoins one new residual per step). Alive obligations age
and expire after at most `horizon φ` steps (sum of `X`-depth and bounds), so the candidate bound is
`size(run φ tr) ≤ size φ · (horizon φ + 1)`. Empirical check so far (one spec, 5000 random steps): spec size 5, worst
residual 8. To be stated precisely (P2-4) and proved (P3-5).

This candidate fails when `always` is nested: an inner `G` never expires, and without deduplication every step adds a
copy, so `G (G p)` grows from 3 to 1,203 nodes in 400 steps (F73, 2026-10-22). P2-4 must first restrict the fragment
(no `always` under `always`) or add normalisation (e.g. deduplicating conjuncts), and the Lean and Python simplifiers
must change together.

**Resolution (2026-10-23, D-030, D-031).** `simpAnd` / `simpOr` now flatten conjunctions (disjunctions), drop
`tt` (`ff`), collapse on `ff` (`tt`), and remove repeated conjuncts (disjuncts), keeping the last occurrence. In Lean,
every residual is in this normal form and progression commutes with the simplifiers (`lean/BoundedBrain/Normal.lean`),
and `size_run_le` proves `(run φ tr).size ≤ resBound φ` for every trace (`lean/BoundedBrain/Resource.lean`): the
monitor state is bounded by a number that depends on the spec alone. `resBound φ` is the largest size in an explicit
finite list `reach φ` that contains every residual; it is small for flat specs (6 for `G ¬grasp_wrong`, 14 for the
collateral spec, 10 for `G (G p)`) but combinatorially large for `always` nested over a disjunction, where it is not
computable in practice (F78). Observed peaks are smaller: `G (G p)` stays at 6 nodes and
`G (released → G ¬grasp)` at 8 over 400 steps (F76). A tighter, computable bound and a per-step time bound are
not formalised.

## Assumptions and guarantees

* **A1 (perception).** The labels given to the monitor are correct for the atoms used.
* **A2 (specification).** The formula captures the intended safety/progress rule.
* **A3 (actuation).** The fallback (hold/retreat) is executed and is itself safe in the situation.
* **A4 (timing).** Monitor step time is below the control period; labels arrive at the control rate.

| ID | Guarantee | Depends on | Evidence |
|---|---|---|---|
| G1 | Monitor verdict = LTLf semantics; early verdicts sound | none beyond the definitions | Lean (P3-3, P3-4) — proved 2026-10-18 (F49) |
| G2 | Step cost and memory bounded by a function of the spec | none | Memory: Lean `size_run_le` (P3-5), proved 2026-10-23 (F77); step cost: not formalised (each step is structural recursion over a state of bounded size) |
| G3 | Executed trace satisfies φ (enforcement) | A1, A3, A4 and a model of what the fallback can do | out of scope for the first paper; do not claim |

## Interchange format (Lean ↔ Python differential tests)

* Formula: `spec.to_dict` JSON, e.g. `{"op":"always","arg":{"op":"or","left":{"op":"lit","name":"lift_cmd","positive":false},"right":{"op":"lit","name":"grasp_stable","positive":true}}}`.
  Bounded Until: `{"op":"until_within","bound":k,"left":φ,"right":ψ}`.
* Trace: JSONL, one object per step: `{"t": 0, "labels": ["grasp_stable"]}`.
* Output: JSONL of `{"t": n, "verdict": "pending|satisfied|violated"}` plus a final `{"accepts": true|false}`.
