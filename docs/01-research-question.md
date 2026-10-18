# 01 — Research question, hypotheses, non-goals

Status: **draft**. The gap statement below is a hypothesis until Phase 1 (Gate G1) confirms it.

## Research questions

* **RQ1 (formal).** Can a *bounded, total* runtime monitor for a finite-trace temporal fragment be specified and
  proven correct in Lean 4 at a maintainable proof size? Correctness = end-of-trace agreement with the reference
  LTLf semantics + soundness of early verdicts + a resource bound that depends on the spec, not the trace.
* **RQ2 (systems).** In a VLA + continuous-filter pipeline, does adding the monitor detect (and optionally prevent)
  *task-level* violations that geometric filters cannot express, at acceptable latency and success-rate cost?
* **RQ3 (stretch).** Can model-proposed specifications be machine-checked (in-fragment, sanity conditions) before
  deployment?

## Gap hypothesis (to be confirmed in Phase 1)

> Continuous-constraint safety layers for VLAs (CBF/ATACOM-style) are well developed; temporal task-level
> monitoring appears mostly in evaluation (e.g. SENTINEL) or informal guardrails. We could not find a
> *machine-checked* monitor for such specs integrated with a VLA pipeline.

Differentiation matrix to fill in P1-6 (rows = related works, columns = temporal specs? machine-checked?
VLA integration? runtime enforcement? open artifact?).

## Hypotheses

* H1: The bounded fragment is expressive enough for ≥ 6–10 realistic pick-and-place safety/progress rules.
* H2: Lean proofs for the progression monitor are tractable without Mathlib (a few hundred lines).
* H3: Monitor latency is negligible relative to VLA inference and filter periods.
* H4: Task-level violations by a raw VLA are frequent enough in a chosen benchmark to be measurable.

## Non-goals

* Verifying neural networks or VLA weights.
* Formalizing continuous dynamics, CBF theory, or reachability in Lean (unless Gate G1 widens scope).
* Beating any named robot-learning system at manipulation success.
* Claiming "provable safety" of a physical robot.

## Success criteria

* **Minimum:** C1 complete (Lean theorems proved, `lake build` green) + Python conformance + a documented spec library.
* **Target:** C1 + C2 + C3 in simulation with honest ablations.
* **Stretch:** C4, real-robot demo.
