# 03 — Related work and reading list

Status legend: **READ** (full text, or the named sections, read) · **ABSTRACT** (abstract read from the paper itself) ·
**SNIPPET** (search-result snippet only) · **SECONDARY** (described by another source, named) · **TO-READ**.
In `02-facts-register.md` terms: READ = `VERIFIED-READ`, ABSTRACT and SNIPPET = `VERIFIED-SNIPPET`, SECONDARY =
`SECONDARY`. Only READ entries may be summarized as fact; the others are leads.
Searches: 2026-10-17 (sections A–C, J) and 2026-10-22 (Phase 1, sections B and D–I). The resulting gap statement and
differentiation matrix are in `01-research-question.md`.

## A. Core (read first)

| # | Work | ID / link | Status | Role / takeaway |
|---|---|---|---|---|
| 1 | Towards Safe Robot Foundation Models Using Inductive Biases (ATACOM on π0/Octo) | arXiv 2505.10219 | **READ** | Closest "continuous safety layer on a VLA" baseline; assumptions and limits in facts F1–F6. |
| 2 | Formal Methods in Robot Policy Learning and Verification: A Survey | arXiv 2602.06971 | **READ** (body; §4.4 re-read 2026-10-22) | Taxonomy; runtime monitoring §4.4 splits explicit-specification from implicit (heuristic, OOD, VLM) monitors and names specification-based monitoring of complex robots as future research (F69); no proof assistant mentioned anywhere in the text (F8). |
| 3 | Safe RL on the Constraint Manifold: Theory and Applications (Liu et al.) | arXiv 2404.09080 | TO-READ (P0-6) | Source of ATACOM's forward-invariance / ISS guarantees. |

## B. VLA + safety filters (P1-3: constraint types, temporal constraints, machine-checked proofs)

Checked 2026-10-22: abstracts read from the PDFs, plus a full-text search for temporal-logic and proof-assistant terms
(rows 4–7, 10). Summary: rows 4–8 enforce geometric constraints with control barrier functions; none uses
temporal-logic specifications or a proof assistant (F64).

| # | Work | ID / link | Status | Constraints | Temporal / task-level | Machine-checked |
|---|---|---|---|---|---|---|
| 4 | Your Model Already Knows: Attention-Guided Safety Filter for VLAs (Park et al.) | arXiv 2606.09749 | ABSTRACT | CBF collision avoidance; the target object comes from VLA attention heads, the rest of the scene is treated as obstacles; SafeLIBERO extended with moving obstacles | No | No |
| 5 | AEGIS / VLSA (Hu et al.) | arXiv 2512.11891 (IROS 2026 per arXiv comment) | ABSTRACT | CBF safety-constraint layer, obstacles named by a VLM; forward invariance argued on paper; introduces SafeLIBERO (section G) | No | No |
| 6 | Safe-Night VLA (Yu et al.) | arXiv 2603.05754 (IROS 2026 per arXiv comment) | ABSTRACT | GR00T-N1.5-based, frozen VLM, thermal perception; CBF workspace constraints; real Franka | No | No |
| 7 | ProbeAct (Zhang et al.) | arXiv 2606.09740 | ABSTRACT | Hidden-state probes locate objects; a hand-written kinematic state machine detects grasp, transport and placement failures; hierarchical CBF on repeated-failure locations; LIBERO-plus, OpenVLA-OFT | Discrete failure states, not a temporal-logic spec (F65) | No |
| 8 | Graph-Fused VLA, semantic safety via CBF (Gu, Cheng, Gao) | engrXiv 10.31224/6733 | SNIPPET | LLM-identified unsafe spatial relations and collision bounds enforced through CBF; dual-arm | Per-state semantic rules | Not read |
| 9 | Modular Safety Guardrails Are Necessary for FM-Enabled Robots (Kim et al.) | arXiv 2602.04056 | ABSTRACT | Position paper: monitoring (evaluation) and intervention layers; action, decision and human-centered safety | — | — |
| 10 | SENTINEL (Zhan et al.) | arXiv 2510.12985 | ABSTRACT | LTL/CTL safety specs checked at the semantic, plan and trajectory levels; trajectories merged into a computation tree and model-checked; VirtualHome, AI2-THOR; LLM-based embodied agents | Yes, offline evaluation (F11) | No |
| 11 | SafeVLA (Zhang et al.) | arXiv 2503.03480 | TO-READ | Safe-RL alignment of VLAs; cited by ATACOM. | | |
| 12 | Semantically safe robot manipulation (Brunke et al.) | RA-L 2025 | TO-READ | LLM-generated constraints enforced with CBF; cited by ATACOM. | | |
| 13 | RoboGuard: Safety Guardrails for LLM-Enabled Robots (Ravichandran et al.) | arXiv 2503.07885 (RA-L, accepted Feb 2026, per the PDF header) | READ (abstract, Sect. III) | A root-of-trust LLM turns rules into context-specific LTL; control synthesis with Büchi automata checks and repairs LLM plans over a skill API | Yes (LTL), planner level | No; paper theorem (F63) |
| 14 | Sentinel: runtime monitoring of consistency and progress (Agia et al.) | arXiv 2410.04640, CoRL 2024 | ABSTRACT | Statistical temporal action consistency (STAC) plus VLM progress checks; diffusion policies | No formal spec | No |
| 19 | Neuro-Symbolic Safety Guidance via Constrained Flow Matching (English, Zheng, Ewetz) | arXiv 2607.01378 | ABSTRACT | Collision avoidance as constrained optimisation inside the flow-matching denoising loop; SafeLIBERO | No | No |

## C. Context

| # | Work | ID / link | Status | Note |
|---|---|---|---|---|
| 15 | Embodied Turing Machines: Stateful Code for Robot RSI | arXiv 2610.12369 | SNIPPET → **read before citing** | Code-as-policy with a TM *framing* (F12). Not a basis for safety claims. |
| 16 | π0.7 (Physical Intelligence) | arXiv 2604.15483 | SNIPPET | Current generalist model from PI. |
| 17 | On the (In)Tractability of RL for LTL Objectives (Yang, Littman, Carbin) | arXiv 2111.12679 (IJCAI 2022) | SNIPPET | PAC-learnable iff decidable within a finite horizon (F32); links the bounded fragment to learnability. |
| 18 | Reluplex (Katz et al.) | arXiv 1702.01135 (CAV 2017) | SNIPPET | Verifying ReLU networks is NP-complete (F33): a reason to monitor rather than verify the policy. |

## D. Verified monitors and temporal logics in proof assistants (P1-1)

| # | Work | ID / venue | Status | Logic and what is proved | Robots / CPS | Relation to C1 |
|---|---|---|---|---|---|---|
| 20 | **MLTL formula progression** (Kosaian, Wang, Sloan, Rozier) | LNCS 2026, DOI 10.1007/978-3-032-07021-0_21; arXiv 2410.03465 | READ (abstract, Sects. 1, 3) | MLTL: LTL with closed integer intervals on F, G, U, R over finite traces. Progression formalised in Isabelle/HOL (~3,300 lines); correct for traces at least the formula's computation length, as semantic equivalence to True (output not simplified); errors in the source paper fixed (F54) | MLTL is used on NASA systems, incl. Robonaut2 (row 28) | **Closest prior work to C1**: same technique on a bounded finite-trace logic that also has bounded Until and Release. Differences in our favour are small: end-of-trace correctness for every trace length, syntactic `tt`/`ff` verdicts, early-verdict soundness for all extensions, unbounded `G`, strong `X`, Lean 4. |
| 21 | LTL3 semantics and formula progression (Amjad, van Glabbeek, O'Connor) | EPTCS 412 (EXPRESS/SOS 2024), DOI 10.4204/EPTCS.412.4; AFP `LTL3_Semantics` | READ (abstract, Sect. 5) | Progression for full LTL3 mechanised in Isabelle/HOL; sound and complete up to finite traces, modulo a simplifier that maps every tautology to ⊤ and every absurdity to ⊥; notes possible exponential blow-up (F55) | — | Same verdict notion as our `violated_sound` / `satisfied_sound`, for a richer logic. Our simplifier is weaker (sound only). |
| 22 | VeriMon (Schneider, Basin, Krstić, Traytel) | RV 2019; extended in IJCAR 2020, TACAS 2022; ICTAC 2022 overview; AFP `MFOTL_Monitor` | READ (RV 2019: abstract, Sects. 1, 6) | MFOTL (first-order, metric, past and bounded future) over infinite streams; verdicts sound and eventually complete; executable code extracted; ~3,000 lines; differential testing found discrepancies in two unverified monitors (F53) | — | Much richer logic; same method as C1 + C2 (proof, extracted code, differential testing). |
| 23 | Formalising and monitoring traffic rules for autonomous vehicles (Rizaldi et al.) | iFM 2017, LNCS 10510, DOI 10.1007/978-3-319-66845-1_4 | READ (abstract, Sects. 1, 6, 7) | LTL over finite traces; the atomic propositions (overtaking, safe distance) are defined and verified in Isabelle/HOL; SML code generated; monitor evaluates the semantics on a recorded run (F56) | Autonomous vehicles (one simulated controller run) | Machine-checked monitor **and** verified atoms on an autonomous system. Verified atoms address part of our A1. |
| 24 | A verified online monitor for MTL with quantitative semantics (Chattopadhyay, Mamouras) | RV 2020, DOI 10.1007/978-3-030-60508-7_21 | SECONDARY (via row 20) | Coq formalisation of MTL generating an OCaml past-time monitor (F57) | — | A Coq-verified online monitor. |
| 25 | Towards certified runtime verification (Blech, Falcone, Becker) | ICFEM 2012 | SECONDARY (via row 22) | Coq; monitors for regular expressions extracted; correctness proved per property | — | — |
| 26 | Causal Past Logic for runtime verification of distributed LLM-agent workflows (Bollig) | arXiv 2605.20923 (ICFEM 2026 per arXiv comment) | ABSTRACT (+ introduction) | Past-time logic over distributed workflows; monitor-correctness theorem mechanised in Lean 4 (F59) | LLM agents (software) | A Lean 4 machine-checked monitor already exists: "first verified monitor in Lean" is not available as a claim. |
| 27 | LeanLTL (Vin, Miller, Fremont) | arXiv 2507.01780 (LIPIcs, ITP 2025); github.com/UCSCFormalMethods/LeanLTL (BSD-3-Clause) | READ (abstract, Sects. 1–2, conclusion) | Lean 4 framework embedding LTL and LTLf (strong and weak next) over arbitrary theories; a proof framework, not a monitor; future work: past-time and bounded-time operators (F58) | Examples with Scenic / driving components | Possible reuse for our semantics; no overlap with the monitor proofs. |
| 28 | Embedding online runtime verification for fault disambiguation on Robonaut2 (Kempa et al.) | FORMATS 2020, DOI 10.1007/978-3-030-57628-8_12 | SECONDARY (via row 20) | MLTL monitoring with R2U2 | Robonaut2 (ISS) | Temporal-logic monitoring on a robot; not described as machine-checked. |
| 29 | VeriPhy (Bohrer et al.) / ModelPlex (Mitsch, Platzer) | PLDI 2018; FMSD 49 (2016) | SECONDARY (via row 22; search snippet) | Differential dynamic logic; monitors from verified hybrid models, compiled via CakeML to machine code | Ground robot, AirSim | Verified runtime monitor on a robot, for continuous dynamics, not discrete temporal specs. |
| 30 | CopilotVerifier (Scott et al.) and Ogma (Perez et al.) | PACMPL 7 (ICFP 2023), DOI 10.1145/3607841; arXiv 2209.14030 (FMAS 2022, EPTCS 371) | SNIPPET | Copilot stream monitors compiled to C with a per-compilation bisimulation proof (Crucible/What4, SMT, not a proof assistant); Ogma generates ROS 2 monitor nodes from FRET requirements (F60) | ROS 2 (NASA) | Verified monitor compilation for robots, without learned policies. |
| 42 | Monitoring with verified guarantees (Dauer, Finkbeiner, Schirmer) | arXiv 2110.11755 | ABSTRACT | Lola stream specifications with assume/assert annotations checked by an SMT solver; found safety-critical errors in avionics monitor specifications | Avionics | Verifies the *specification* rather than the monitor algorithm: relevant to our A2 and to C4. |

## E. Temporal logic with foundation-model robots (P1-2)

No machine-checked component was found in any of these (F61). Rows 10 (SENTINEL) and 13 (RoboGuard) are in section B.

| # | Work | ID / link | Status | What it does | Relation to us |
|---|---|---|---|---|---|
| 31 | **STeP** (Torshizi et al.) | arXiv 2607.18580 | READ (abstract, Sect. I, method excerpts) | A reasoning agent writes STL specs; a mainly model-based executor runs them with an online STL robustness monitor and replanning; LIBERO, LIBERO-PRO, new LIBERO-Constrained (49 task–constraint instances); SmolVLA is a baseline (F62) | **Closest work to C3**: temporal-logic monitoring of manipulation on LIBERO, but the VLA is replaced, not monitored, and nothing is machine-checked. Benchmark code not found in the paper. |
| 32 | Logic-VLA (Wang et al.) | arXiv 2608.20556 | ABSTRACT | VLA conditioned on STL specifications (syntax-graph encoder, SFT, preference optimisation); quadcopter navigation; +24.8 to +40.7 pp STL satisfaction | Training-time use of temporal logic, not a monitor. |
| 33 | ROVER, formerly SAFE-SMART (Sakano et al.) | arXiv 2511.17781 | ABSTRACT | Offline STL robustness metrics (TRV, LRV, AVRV) on traces of black-box policies; regulator-guided retraining; racing game, mobile navigation, TurtleBot3 | Offline evaluation, not runtime. |
| 34 | Plug in the Safety Chip (Yang, Raman, Shah, Tellex) | arXiv 2309.09919 (ICRA 2024 per search snippet) | SNIPPET | Natural-language constraints → LTL; an automaton-based monitor prunes unsafe actions of LLM agents; VirtualHome and a real robot | LLM action level; not machine-checked. |

## F. VLA failure detection and runtime monitors (learned or heuristic)

| # | Work | ID / link | Status | Note |
|---|---|---|---|---|
| 35 | SAFE: multitask failure detection for VLAs (Gu et al.) | arXiv 2506.09937, NeurIPS 2025 | ABSTRACT | Detector learned from VLA internal features, evaluated on unseen tasks; OpenVLA, π0, π0-FAST; simulation (incl. LIBERO-10) and real (F66). A natural baseline for our monitor on the same π0.5 data. |
| 36 | Hide-and-Seek (Park et al.) | arXiv 2605.30834 (v2 comment: NeurIPS 2026) | ABSTRACT | Failure detection from trajectory-level labels only; OpenVLA, π0, π0.5; LIBERO, VLABench, real robot (F66). |
| 37 | RESCUE (Ahmedt-Aristizabal et al.) | arXiv 2610.13516 | ABSTRACT | Counterfactual evaluation of monitors (OpenVLA-OFT, π0.5; LIBERO-Spatial, LIBERO-Plus): detection scores do not establish lower intervention cost; with stop-and-reset an idealised detector tolerates only 2.0–3.3% false alarms (F67). Sets the bar for evaluating our monitor (F45). |
| 38 | Affordance Field Intervention (Xu et al.) | arXiv 2512.07472 | ABSTRACT (+ introduction) | Names the "memory trap" (VLAs replay memorised trajectories when the scene changes); detects it and intervenes; π0, π0.5; +20.2% on LIBERO-Pro (F68). A related memorisation failure; F44 is the instruction-ignoring form (as in F46, F47). |
| 39 | ActFovea (Yu et al.) | arXiv 2607.29169 | ABSTRACT | Visual-action consistency safeguard for π0 on LIBERO, with a bounded safe-failure procedure. Code linked in the arXiv comment. |
| 40 | Pre-VLA (Sun et al.); RoVer (Dai et al.) | arXiv 2605.22446; arXiv 2510.10975 | ABSTRACT | Learned verifiers of candidate action chunks (a validity classifier; a process reward model). "Verification" here means learned scoring, not formal verification. |
| 41 | Vision-Language-Action Safety: Threats, Challenges, Evaluations, and Mechanisms (Li et al.) | arXiv 2604.23775 | READ (Sects. 5.2.1–5.2.2; runtime-monitoring benchmarks) | Survey. Runtime monitors listed are heuristic, VLM-based or learned; temporal logic appears through RoboGuard and SAFE-SMART/ROVER; no proof assistant mentioned (F70). |

## G. Benchmarks (P1-7)

Checked 2026-10-22 through the GitHub API and project pages (F71). None was installed or run, so ease of running is
unknown.

| Benchmark | Code | License | Note |
|---|---|---|---|
| LIBERO | github.com/Lifelong-Robot-Learning/LIBERO | MIT | In use (D-015). |
| LIBERO-PRO | github.com/Zxy-MLlab/LIBERO-PRO | MIT | Perturbed objects, initial states, instructions, environments (F46). |
| LIBERO-plus | github.com/sylvestf/LIBERO-plus | none detected | 7 perturbation dimensions, ~10,000 variants. LeRobot's main docs have a LIBERO-plus page; the fork replaces `hf-libero`. Support in lerobot 0.6.1 not checked. |
| SafeLIBERO | github.com/THU-RCSCT/vlsa-aegis | MIT | Obstacles at two safety levels (row 5); used by rows 4 and 19. |
| LIBERO-Safety | github.com/LIBERO-SAFETY/LIBERO-Safety | Apache-2.0 | ECCV 2026 per arXiv comment (arXiv 2606.23686). Safety constraints are per-timestep Boolean state predicates; physical and semantic suites; evaluates OpenVLA, OpenVLA-OFT, π0, π0.5. |
| LIBERO-Constrained | from STeP (row 31) | not found | Spatial, temporal and logical requirements on LIBERO tasks: the closest existing benchmark to our task-level specs. |

## H. Lean ecosystem (P1-5)

Checked 2026-10-22 through directory listings and repository metadata (F72).

* **Mathlib** `Mathlib/Computability/`: Ackermann, AkraBazzi, ContextFreeGrammar, DFA, Encoding, EpsilonNFA, Halting,
  Language, MyhillNerode, NFA, Partrec, PartrecBasis, PartrecCode, Primrec/, RE, RecursiveIn, Reduce,
  RegularExpressions, StateTransition, TuringDegree, TuringMachine/. No temporal logic and no ω-automata.
* **CSLib** (`leanprover/cslib`, Apache-2.0): deterministic, nondeterministic, Büchi, ε- and two-way automata,
  transducers; ω-languages and ω-regular languages; temporal operators over ω-sequences (`Step`, `LeadsTo`); modal logic,
  HML, linear logic; PAC learning. No LTL syntax found by file name.
* **LeanLTL** (row 27); **Lentil** (`verse-lab/Lentil`, Apache-2.0, "proof infrastructure about LTL in Lean 4");
  **Veil** (`verse-lab/veil`, transition systems).
* **Control theory, robotics**: no Lean library found by GitHub search; F16 remains the only lead.

## I. Background (the 2026-10-17 leads from memory, checked)

* Formula progression: Bacchus & Kabanza, *Using temporal logics to express search control knowledge for planning*,
  Artificial Intelligence (2000), DOI 10.1016/S0004-3702(99)00071-5 (metadata via Crossref; credited as the origin of
  progression by row 21). SECONDARY.
* LTLf: De Giacomo & Vardi, *Linear temporal logic and linear dynamic logic on finite traces*, IJCAI 2013, pp. 854–860
  (as cited by row 27). SECONDARY.
* LTL3 monitors: Bauer, Leucker, Schallhart, *Runtime verification for LTL and TLTL*, ACM TOSEM (2011),
  DOI 10.1145/2000799.2000800 (metadata only).
* Rewriting-based monitoring: Roşu & Havelund, *Rewriting-based techniques for runtime verification*, Automated
  Software Engineering (2005), DOI 10.1007/s10515-005-6205-y; cited by row 21 for pathological exponential cases of
  progression. SECONDARY.
* Verified monitors in proof assistants: see section D. The 2026-10-17 warning came true: a verified progression monitor
  for a bounded finite-trace logic exists (row 20), so C1's novelty shrinks to the differences listed there.
* Reward machines / automata-theoretic RL (survey §3.1): the same specs viewed as task automata. Not checked.

## J. Companies (context only)

Physical Intelligence, Skild AI, Generalist publish models and funding news. No public formal-verification work from
them was found in the searches done (F15 covers funding reports; treat as SECONDARY). NVIDIA's Halos for Robotics
(2026-06-22, F30) is a platform-level functional-safety stack; its announcement does not mention runtime monitoring or
formal verification of AI policies.
