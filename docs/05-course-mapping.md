# 05 — Course mapping (Theory of Computation) → project

Course: a one-semester *Theory of Computation* course (Winter 2026). Part I follows Davis, Sigal & Weyuker,
*Computability, Complexity, and Languages* (2nd ed.); Part II uses Arora & Barak and Sipser.

**Course materials are local only** (`course/` is git-ignored; the slides and exercise sheets belong to the
instructor). Never put solutions to course exercises in this public repository.

## What has been read

All five files provided so far were read in full on 2026-10-17 (text extraction): `L01_pr.pdf` (34 pp.),
`L02_bmin.pdf` (20 pp.), `T01_pr.pdf` (11 pp.), `T02_coding.pdf` (28 pp.), `G01_Computability.pdf` (5 pp.,
28 exercises). Later lectures are known only from the schedule below; anything about them is `UNVERIFIED`.

## Schedule (Lecture 1)

Part I, computability: (1) primitive recursive functions, PRC classes; (2) bounded minimization, sequence coding;
(3) language S, partially computable functions, unbounded minimization; (4) program coding, halting problem,
Church's thesis; (5) universality, snapshot and step-counter functions; (6) main theorems; (7) c.e. sets, Rice's
theorem; (8) reducibilities. Part II, complexity: (9) Turing machines; (10) P and NP; (11) Cook–Levin;
(12) NP-complete problems, coNP, EXP; (13) space complexity.

## Mapping: course → project

| Week | Course content (source) | Where it shows up in this project | Strength |
|---|---|---|---|
| 1 | Primitive recursion scheme h(t+1) = g(h(t), …) (L01) | `run φ tr = foldl progress φ tr` is this scheme over the trace: the state after t+1 steps is `progress σ_t` applied to the state after t. | High |
| 1 | Structural induction on construction trees; PRC classes (L01) | The Lean proofs in `Monitor.lean` are structural inductions on `Formula`: show the property for atoms, then that each constructor preserves it. | High |
| 1 | Tetration is primitive recursive (T01) | Primitive recursive does not mean fast. Totality of the monitor says nothing about speed, hence the separate resource bound (P3-5). | Medium |
| 2 | Bounded quantifiers (∀t)≤y, (∃t)≤y stay in a PRC class (L02) | `alwaysWithin k` / `eventuallyWithin k` in `Sat` are bounded quantifiers over the next k+1 positions. "Only bounded operators" is this theorem used as a design rule for specs. | High |
| 2 | Bounded minimization (L02, T02) | First-violation and first-success times (`success_step` in the Colab traces); the bounded-verdict theorem (P3-8, proved 2026-10-18) says the time to a definite verdict is a bounded minimization. | High |
| 2 | Pair and sequence coding, prefixes `pref(x,k)`, concatenation `x⌢y` (L02, T02) | A trace is a sequence of labels. `violated_sound` / `satisfied_sound` are statements about a prefix `tr` and every concatenation `tr ++ ext`. Coding is what P3-6 needs. | High |
| 2 | Fibonacci with pairs: carry a small state, not the history (T02); course-of-values recursion | The progression monitor carries a residual formula (small state). A naive monitor stores the whole history and re-evaluates it: course-of-values recursion, with memory growing with the trace. P3-5 makes the difference precise. | High |
| 3 | Unbounded minimization; partial functions (schedule) | An unbounded "eventually" is an unbounded search: a monitor may never reach a verdict. That is why the fragment has no unbounded `F` or `U`. | High (conceptual) |
| 4–5 | Halting problem; step-counter function STP(x, y, t) (schedule) | "Goal reached within k steps" is decided step by step, like STP with a time bound; "eventually" is not. `F[0,k]` is the step-counter idea applied to robot tasks. | Medium (analogy) |
| 7 | Rice's theorem; index sets (schedule) | No algorithm decides nontrivial behavioural properties of arbitrary programs, so we check one execution at a time instead. The verdict depends only on the observed trace, not on which network produced it (index-set-style extensionality): the precise sense in which the monitor is model-agnostic. | High (motivation) |
| 7 | c.e. and co-c.e. sets (schedule) | A violation of "never X" has a finite witness; satisfaction of an unbounded "always" never does. Analogy only; the exact statement is the safety/co-safety classification of runtime verification. | Medium (analogy) |
| 8, 10–13 | Reductions; P, NP, Cook–Levin; PSPACE (schedule) | Verifying ReLU networks is NP-complete (F33), one reason not to verify the policy itself. Open question P2-6: the complexity of complete early verdicts. | Medium–High |

## Strengthening the link (tasks, also in TODO.md)

* **P3-6** `run φ` is primitive recursive under a coding of formulas and finite labels. Mathlib provides
  `Primcodable`, `Primrec` and `Primrec.list_foldl` (F34). `progress` recurses on the formula tree, so this needs
  course-of-values recursion on codes. The public repo uses Mathlib's coding; a version
  with the course's coding ⟨x, y⟩ = 2^x(2y+1) − 1 is a private exercise.
* **P3-8** Bounded-verdict theorem (proved 2026-10-18 in `lean/BoundedBrain/BoundedVerdict.lean`). For formulas without the unbounded `always`, let d(tt) = d(ff) = d(literal) = 1,
  d(X φ) = 1 + d(φ), d(G[0,k] φ) = d(F[0,k] φ) = k + d(φ), d(φ ∧ ψ) = d(φ ∨ ψ) = max(d(φ), d(ψ)). Claim: if
  `tr.length ≥ d(φ)` then `run φ tr` is `tt` or `ff`. Checked exhaustively in `monitor/tests/test_bounded_verdict.py`
  (1,046 small formulas, every trace of length d(φ) ≤ 5, no counterexample; the bound is reached on some traces).
  These formulas are "decidable within a finite horizon", the class that Yang et al. (F32) show to be exactly the
  PAC-learnable LTL objectives, so the same boundedness gives guaranteed verdicts and learnability.
* **P2-6** Complexity of complete early verdicts: is deciding whether a residual can still be satisfied in P,
  NP-complete or PSPACE-complete for this fragment, with bounds written in unary or binary? Check the literature first
  (LTLf results are MEMORY only, F18), then use the reductions from weeks 8–12.
* **P7-6** Motivation section of the paper: Rice's theorem and index sets lead to runtime monitoring; NP-completeness
  of network verification (F33).
* **Learning Lean (private, `course/`)**: formalize lecture examples, not sheet exercises (bounded quantifiers preserve
  primitive recursiveness, pair coding) as warm-ups for P3-2.

## What the course does not cover but the project needs

Finite automata and temporal logics (LTL, LTLf, STL; Mathlib has DFA, NFA and regular expressions, F34); interactive
theorem proving (Lean); robot learning (imitation learning, VLAs, reinforcement learning); control theory (CBFs,
reachability).

## What the course does *not* give

* Robot capability (data, compute, training): no.
* Safety of a physical robot: no (termination is not safety; facts register D1).
* By itself, an advantage over any robot-learning system: no. Its value here is the bounded-computation design rule,
  the proof techniques, and the limits that motivate monitoring.
