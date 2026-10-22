# 01 — Research question, hypotheses, non-goals

Status: **draft**. Phase 1 (literature check) was done on 2026-10-22; the gap statement below replaces the hypothesis of
2026-10-17. Gate G1 (proceed / re-scope / stop) is the owner's decision and still open (`TODO.md` Q12).

## Research questions

* **RQ1 (formal).** Can a *bounded, total* runtime monitor for a finite-trace temporal fragment be specified and
  proven correct in Lean 4 at a maintainable proof size? Correctness = end-of-trace agreement with the reference
  LTLf semantics + soundness of early verdicts + a resource bound that depends on the spec, not the trace.
* **RQ2 (systems).** In a VLA + continuous-filter pipeline, does adding the monitor detect (and optionally prevent)
  *task-level* violations that geometric filters cannot express, at acceptable latency and success-rate cost?
* **RQ3 (stretch).** Can model-proposed specifications be machine-checked (in-fragment, sanity conditions) before
  deployment?

## Gap statement (Phase 1, 2026-10-22)

Evidence: `03-related-work.md` sections B and D–H; facts F53–F73. The closest works were read in their relevant
sections, the others only in their abstracts (D-027). Claims of absence are absence of evidence.

**What exists.**

1. *Machine-checked monitors for logics at least as expressive as our fragment.* Formula progression for MLTL (bounded
   LTL on finite traces, with bounded Until and Release) is formalised and proved correct in Isabelle/HOL (F54).
   Progression for LTL3 is proved sound and complete modulo an ideal simplifier (F55). VeriMon monitors metric
   first-order temporal logic (F53). A Coq-verified MTL monitor exists (F57), and so does a Lean 4 machine-checked
   monitor for LLM-agent workflows (F59).
2. *Machine-checked monitors on autonomous systems, but not on learned policies.* LTL traffic rules with verified atomic
   propositions for autonomous vehicles (F56); VeriPhy monitors for hybrid models, compiled to machine code and run on a
   ground robot (`03` row 29); Copilot/Ogma monitors for ROS 2 with SMT-checked compilation (F60).
3. *Temporal logic with foundation-model robots, nothing machine-checked.* STeP monitors STL online on LIBERO, with a
   model-based executor in place of the VLA (F62). RoboGuard and Safety Chip use LTL at the LLM-planner level (F63,
   `03` row 34). SENTINEL and ROVER evaluate offline (F11, `03` row 33). Logic-VLA trains a VLA on STL specifications
   (`03` row 32).
4. *VLA safety layers and failure detectors.* CBF filters enforce geometric or spatial constraints, none temporal
   (F64). Failure detectors
   are learned or heuristic (F65, F66), several on LIBERO with π0 or π0.5. RESCUE shows that detection accuracy does not
   by itself show that acting on alarms helps (F67). AFI detects and intervenes on a related memorisation failure (F68);
   LIBERO-PRO and LIBERO-Plus report the instruction-ignoring form that we measured on LIBERO-90 (F44, F46, F47).

**What we did not find** (F61): a machine-checked monitor applied to the executions of a learned robot policy or VLA.

**Consequences for the contributions (README C1–C4).**

* **C1 alone is not a research contribution.** The MLTL work (F54) uses the same technique, in Isabelle, on a richer
  bounded logic. What our proofs add is small: end-of-trace correctness for every trace length (F54 needs a minimum
  length), syntactic `tt`/`ff` verdicts that are sound for every extension, a syntactic bounded-verdict theorem,
  unbounded `G` and strong `X`, and Lean 4. A resource bound would be a further difference, but it does not hold yet:
  without deduplication, residuals grow linearly when `always` is nested (F73).
* **Claims that are not available:** "first verified monitor in Lean" (F59); "first machine-checked monitor for an
  autonomous system" (F56, `03` row 29); "first temporal-logic monitoring of manipulation on LIBERO" (F62).
* **C2** (Lean = Python by differential testing) is good engineering practice; VeriMon did the same in 2019 (F53).
* **The remaining gap is the intersection**: a machine-checked monitor on the executions of a learned VLA, in the loop.
  It is narrow, and the burden is to show what the proof changes there. For the four specs used so far (`G ¬p` and
  `F[0,K] p`, F45) it changes nothing a reviewer would care about: each is one line of ordinary code.
* **The bar for C3** is set by recent work: comparison with learned detectors on the same π0.5 data (F66), intervention
  value rather than detection accuracy (F67), the memorisation failure mode (F46, F47, F68), and benchmarks with
  explicit requirements (LIBERO-Constrained, F62; LIBERO-Safety, F71).

## Differentiation matrix

✓ yes · ✗ no · ~ partly · ? not checked. `#` refers to the rows of `03-related-work.md`.

| Work | Temporal specs | Machine-checked | Learned policy / VLA | Online | Intervention | Open artifact |
|---|---|---|---|---|---|---|
| MLTL progression (#20) | ✓ MLTL | ✓ Isabelle | ✗ | ~ algorithm only | ✗ | ✓ artifact link; MLTL library on AFP |
| LTL3 progression (#21) | ✓ LTL3 | ✓ Isabelle | ✗ | ~ algorithm only | ✗ | ✓ AFP |
| VeriMon (#22) | ✓ MFOTL | ✓ Isabelle | ✗ | ✓ | ✗ | ✓ AFP |
| Rizaldi et al. (#23) | ✓ LTL, finite traces | ✓ Isabelle, atoms too | ✗ (controller run) | ✗ (recorded run) | ✗ | ? |
| Bollig (#26) | ✓ past-time | ✓ Lean 4 | ✗ (LLM agents) | ✓ | ~ guards choose branches | ? |
| VeriPhy (#29) | ✗ (dL) | ✓ | ✗ | ✓ | ✓ fallback | ? |
| Copilot / Ogma (#30) | ✓ stream specs | ~ SMT, per compilation | ✗ | ✓ | ? | ✓ |
| STeP (#31) | ✓ STL | ✗ | ~ VLA only as a baseline | ✓ | ✓ replanning | ? |
| RoboGuard (#13) | ✓ LTL | ✗ paper theorem | ~ LLM planner | ✓ plan check | ✓ plan repair | ? |
| SENTINEL (#10) | ✓ LTL/CTL | ✗ | ~ LLM agents | ✗ offline | ✗ | ? |
| CBF filters on VLAs (#4–8, #19) | ✗ | ✗ paper proofs (#5) | ✓ | ✓ | ✓ | ~ (#5) |
| ProbeAct (#7) | ✗ state machine | ✗ | ✓ | ✓ | ✓ | ? |
| SAFE, Hide-and-Seek (#35, #36) | ✗ | ✗ | ✓ | ✓ | ✗ detect only | ✓ per abstracts |
| RESCUE (#37) | ✗ | ✗ | ✓ | evaluation | ✓ counterfactual | ? |
| **bounded-brain (2026-10-22)** | ✓ bounded LTLf fragment | ✓ Lean 4 | ~ offline, π0.5 LIBERO traces | ~ online-capable, evaluated offline | ✗ | ✓ |

## Gate G1 (pending: the owner decides)

Kill criterion K1 (`06-risks-and-kill-criteria.md`): stop or re-scope if a machine-checked monitor for the same or a
stronger fragment exists **and** has been integrated with robot policies. The first condition is met (F53–F55); the
second is not, in what we found (F61). K1 therefore does not force a stop, but the project cannot rest on C1.

Options:

* **(a) Proceed as planned** (README C1–C3). Risk: reviewers call C1 known (R1, R2) and C3 incremental (R10).
* **(b) Re-scope to the intersection:** what a machine-checked monitor, with verified atoms as in F56, adds as the
  assured component of a run-time-assurance architecture around a VLA (F23). Needs specs whose checking is not trivial
  (ordering, response, nested obligations, hence bounded Until and a resource bound, F73), online use with an
  intervention, and evaluation against learned detectors and by intervention value (F66, F67).
* **(c) Re-scope to the empirical study:** π0.5 failure modes from privileged traces (F44) and an interpretable,
  specification-based detector (F45) compared with learned ones; verification as supporting material.
* **(d) K1's fallback (a):** the bounded-resource / primitive-recursion theory with a case study. It first needs a
  fragment or simplifier change (F73), and its novelty against F54 and F55 is unclear.
* **(e) Stop** and keep the repository as a documented artifact (K4).

Recommendation (assistant): (b) if the owner can give the project several more months; otherwise (c), aimed at a
workshop. In either case, stop presenting C1 as the main contribution.

## Hypotheses

* H1: The bounded fragment is expressive enough for ≥ 6–10 realistic pick-and-place safety/progress rules.
* H2: Lean proofs for the progression monitor are tractable without Mathlib (a few hundred lines). *Supported: about
  550 lines, 2026-10-18 (F49).*
* H3: Monitor latency is negligible relative to VLA inference and filter periods.
* H4: Task-level violations by a raw VLA are frequent enough in a chosen benchmark to be measurable. *Supported on
  unseen LIBERO-90 tasks; few failures in distribution (F44, F45).*

## Non-goals

* Verifying neural networks or VLA weights.
* Formalizing continuous dynamics, CBF theory, or reachability in Lean (unless Gate G1 widens scope).
* Beating any named robot-learning system at manipulation success.
* Claiming "provable safety" of a physical robot.

## Success criteria

* **Minimum:** C1 complete (Lean theorems proved, `lake build` green) + Python conformance + a documented spec library.
* **Target:** C1 + C2 + C3 in simulation with honest ablations.
* **Stretch:** C4, real-robot demo.
