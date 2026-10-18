# 03 — Related work and reading list

Status legend: **READ** (full text/body read) · **SNIPPET** (abstract/snippet only) · **TO-READ**.
Only READ entries may be summarized as fact; others are leads. Search date: 2026-10-17.

## A. Core (read first)

| # | Work | ID / link | Status | Role / takeaway |
|---|---|---|---|---|
| 1 | Towards Safe Robot Foundation Models Using Inductive Biases (ATACOM on π0/Octo) | arXiv 2505.10219 | **READ** | Closest "continuous safety layer on a VLA" baseline; assumptions and limits in facts F1–F6. |
| 2 | Formal Methods in Robot Policy Learning and Verification: A Survey | arXiv 2602.06971 | **READ** (body) | Taxonomy; runtime monitoring §4.4; open problems §5; Lean/Coq/Isabelle not discussed (F8). |
| 3 | Safe RL on the Constraint Manifold: Theory and Applications (Liu et al.) | arXiv 2404.09080 | TO-READ (P0-6) | Source of ATACOM's forward-invariance / ISS guarantees. |

## B. VLA + safety filters (check what they do *not* cover)

| # | Work | ID / link | Status | Note |
|---|---|---|---|---|
| 4 | Your Model Already Knows: Attention-Guided Safety Filter for VLAs | arXiv 2606.09749 | SNIPPET | CBF filter from attention heads; evaluated on SafeLIBERO with moving obstacles. |
| 5 | AEGIS / VLSA (Vision-Language-Safe Action) | arXiv 2512.11891 | SNIPPET | Plug-and-play CBF safety constraint layer with VLM-based assessment. |
| 6 | Safe-Night VLA | arXiv 2603.05754 (alphaxiv audio page) | SNIPPET | GR00T-based, frozen VLM, thermal perception, post-hoc CBF filter. |
| 7 | ProbeAct | arXiv 2606.09740 | SNIPPET | Training-free failure recovery; stateful CBF constraint for repeated failures. |
| 8 | Graph-Fused VLA with semantic safety via CBF | engrXiv 6733 | SNIPPET | LLM-identified semantic rules enforced through CBF certification. |
| 9 | Modular Safety Guardrails Are Necessary for FM-Enabled Robots | arXiv 2602.04056 | SNIPPET | Position paper: monitoring + intervention layers; action/decision/human-centered safety. |
| 10 | SENTINEL: multi-level formal framework for safety *evaluation* | arXiv 2510.12985 | SNIPPET | Temporal-logic safety definitions for evaluation (not a verified runtime monitor). |
| 11 | SafeVLA (Zhang et al.) | arXiv 2503.03480 | TO-READ | Safe-RL alignment of VLAs; cited by ATACOM. |
| 12 | Semantically safe robot manipulation (Brunke et al.) | RA-L 2025 | TO-READ | LLM-generated constraints enforced with CBF; cited by ATACOM. |
| 13 | Safety guardrails for LLM-enabled robots (Ravichandran et al.) | arXiv 2503.07885 | TO-READ | Cited by ATACOM. |
| 14 | Unpacking failure modes of generative policies: runtime monitoring (Agia et al.) | CoRL 2024 | TO-READ | Cited by the survey as runtime monitoring for generative policies. |

## C. Context

| # | Work | ID / link | Status | Note |
|---|---|---|---|---|
| 15 | Embodied Turing Machines: Stateful Code for Robot RSI | arXiv 2610.12369 | SNIPPET → **read before citing** | Code-as-policy with a TM *framing* (F12). Not a basis for safety claims. |
| 16 | π0.7 (Physical Intelligence) | arXiv 2604.15483 | SNIPPET | Current generalist model from PI. |
| 17 | On the (In)Tractability of RL for LTL Objectives (Yang, Littman, Carbin) | arXiv 2111.12679 (IJCAI 2022) | SNIPPET | PAC-learnable iff decidable within a finite horizon (F32); links the bounded fragment to learnability. |
| 18 | Reluplex (Katz et al.) | arXiv 1702.01135 (CAV 2017) | SNIPPET | Verifying ReLU networks is NP-complete (F33): a reason to monitor rather than verify the policy. |

## D. Prior-art leads **from memory (UNVERIFIED — P1-1 must check)**

* LTL runtime verification: Bauer–Leucker–Schallhart (LTL3 monitors); Leucker–Schallhart survey.
* LTLf: De Giacomo–Vardi (finite-trace LTL/LDL); Bacchus–Kabanza (formula progression).
* Verified monitors in proof assistants: VeriMon (Isabelle/HOL, MFOTL); verified LTL monitors in Coq. **If a
  verified LTLf progression monitor already exists, our C1 novelty shrinks to the bounded fragment, the Lean
  development, and the robot integration (see kill criterion K1).**
* Reward machines / automata-theoretic RL (survey §3.1): the same specs viewed as task automata.

## E. Companies (context only)

Physical Intelligence, Skild AI, Generalist publish models and funding news. No public formal-verification work from
them was found in the searches done (F15 covers funding reports; treat as SECONDARY). NVIDIA's Halos for Robotics
(2026-06-22, F30) is a platform-level functional-safety stack; its announcement does not mention runtime monitoring or
formal verification of AI policies.
