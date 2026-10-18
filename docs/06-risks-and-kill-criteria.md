# 06 — Risks, gates, kill criteria

Decide gates with the owner; write the outcome in `07-decision-log.md`.

## Risks

| ID | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | **Prior art** already covers verified LTLf monitors in a proof assistant (see facts F19). | Medium | High | Phase 1 before any heavy work. Differentiate by the *bounded* fragment, Lean development, robot integration, evaluation. |
| R2 | Reviewers see a progression monitor as "textbook". | Medium | Medium | Emphasize the mechanized proof, the strong-`Next` subtlety, resource bound, end-to-end VLA integration, open artifact. Consider a workshop/artifact venue first. |
| R3 | Lean proof effort exceeds the owner's time (new to Lean). | Low (2026-10-18: correctness theorems proved, F49) | High | Time box (K2); start with the easy lemmas; ask for a Lean-experienced mentor (Q7). |
| R4 | Perception labels are the real bottleneck; the guarantee is vacuous in practice. | High | Medium | State A1 loudly; perception-noise ablation (P5-6); privileged-state first. |
| R5 | No hardware / GPU. | Unknown | Medium | Simulation-only plan; reuse open weights; small fine-tunes. |
| R6 | Institutional obligations or IP policy limit publication or licensing. | Unknown | High | The owner's call (Q10); details in the owner's private notes. |
| R7 | Scope creep (STL, continuous Lean, LLM specs, real robot). | High | Medium | Stretch items gated; Lean stays discrete. |
| R8 | Overclaiming (the origin message's style). | Medium | High | `CLAUDE.md` ground rules 2–3; claims table (P7-1). |
| R9 | Benchmark/tooling unavailable (SafeLIBERO seen only in a snippet). | Medium | Medium | P1-7 early; fall back to LIBERO/LeRobot sim. |

## Gates and kill criteria

* **K1 (end of Phase 1).** If a published, machine-checked monitor for the same or a stronger fragment exists *and*
  has been integrated with robot policies, **stop or re-scope** to: (a) the primitive-recursion/bounded-resource
  bridge + a case study, or (b) a different gap found in P1-3.
* **K2 (Phase 3 time box).** If `accepts_iff_sat` is not proved within the budget agreed in Q2, **drop the proof
  scope to the easy lemmas + extensive tests**, and re-title the contribution ("tested monitor with partial
  mechanization"). Do not silently stretch the timeline.
* **K3 (Gate G5).** If integration shows no measurable difference in task-level violation rate vs. the baselines,
  pause and reassess before writing the paper (the honest outcome may be a negative/analysis workshop paper).
* **K4 (owner).** If the owner's time budget drops below what Phase 3 needs, freeze at the last gate and keep the
  repo as a documented artifact.

## Early-warning signals

* Phase 1 search turns up three or more near-identical works.
* Lean build/proof effort per lemma is >2× estimates after the first three lemmas.
* The spec library (P2-5) cannot be expressed in the fragment without unbounded operators.
