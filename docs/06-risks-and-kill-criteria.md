# 06 — Risks, gates, kill criteria

Decide gates with the owner; write the outcome in `07-decision-log.md`.

## Risks

| ID | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | **Prior art** already covers verified LTLf monitors in a proof assistant (see facts F19). | **Realised for C1** (2026-10-22: MLTL progression F54, LTL3 progression F55, VeriMon F53) | High | Do not present C1 as the main contribution; re-scope at Gate G1 (`01-research-question.md`); differentiate by use on learned-policy executions, which was not found (F61). |
| R2 | Reviewers see a progression monitor as "textbook". | High (2026-10-22: a mechanised progression for a richer bounded logic exists, F54) | Medium | As R1. The strong-`Next` subtlety and the syntactic verdict theorems are small differences, not a selling point. A resource bound would differ more but does not hold yet (F73). |
| R3 | Lean proof effort exceeds the owner's time (new to Lean). | Low (2026-10-18: correctness theorems proved, F49) | High | Time box (K2); start with the easy lemmas; ask for a Lean-experienced mentor (Q7). |
| R4 | Perception labels are the real bottleneck; the guarantee is vacuous in practice. | High | Medium | State A1 loudly; perception-noise ablation (P5-6); privileged-state first. |
| R5 | No hardware / GPU. | Unknown | Medium | Simulation-only plan; reuse open weights; small fine-tunes. |
| R6 | Institutional obligations or IP policy limit publication or licensing. | Unknown | High | The owner's call (Q10); details in the owner's private notes. |
| R7 | Scope creep (STL, continuous Lean, LLM specs, real robot). | High | Medium | Stretch items gated; Lean stays discrete. |
| R8 | Overclaiming (the origin message's style). | Medium | High | `CLAUDE.md` ground rules 2–3; claims table (P7-1). |
| R9 | Benchmark/tooling unavailable (SafeLIBERO seen only in a snippet). | Low (2026-10-22: SafeLIBERO, LIBERO-PRO, LIBERO-plus and LIBERO-Safety exist with public code, F71; none run yet) | Medium | P1-7 early; fall back to LIBERO/LeRobot sim. |
| R10 | The VLA monitoring field moves fast: 2026 work already covers temporal-logic monitoring on LIBERO (F62), learned failure detection with π0.5 on LIBERO (F66), the value of acting on alarms (F67) and memorisation failures (F46, F47, F68). | High | High | Compare against these on the same data; claim only what they do not do; re-run the related-work search before writing (P7-2). |

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

* Phase 1 search turns up three or more near-identical works. *2026-10-22, for C1:* two closely matching works (F54,
  F55) and one richer one (F53); K1 assessment in `01-research-question.md` ("Gate G1").
* Lean build/proof effort per lemma is >2× estimates after the first three lemmas.
* The spec library (P2-5) cannot be expressed in the fragment without unbounded operators.
