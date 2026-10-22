# TODO — bounded-brain

Conventions: `[ ]` open · `[~]` in progress · `[x]` done · **Gate** = a decision point (see
`docs/06-risks-and-kill-criteria.md`). IDs (`P3-3`) are referenced from code (`sorry` tags) and docs.
Update this file in the same change as the work. Last reviewed: 2026-10-22 (Phase 1 literature check; Gate G1 open).

## 0. Questions for the owner

Q1–Q7 were answered by the owner on 2026-10-17. Consequences are marked with →. Follow-ups that are still
open are listed after them.

- [x] **Q1 Hardware.** No robot arm; no local GPU; Google Colab with an A100 is available.
      → Phase 5 runs in simulation on Colab. Phase 6 (real robot) is deferred.
      (Reference point: the ATACOM paper fine-tuned π0 on a single A100, 10k steps, batch 32.)
- [x] **Q2 Time budget.** Answered; recorded in the owner's private notes (`private/`, not in the repository).
- [x] **Q3 Target.** None yet. → Revisit at Gate G1 (venue search is P7-5).
- [x] **Q4 Visibility.** Public repository. License: no preference, choice delegated (P0-5).
- [x] **Q5 Identity.** Sole author: Rui Zhu. Affiliation line not given yet (Q9).
- [x] **Q6 Lean experience.** None. → Phase 3 starts with the easy lemmas (P3-2); budget learning time.
- [x] **Q7 Collaborators.** None. → The mentor part of R3's mitigation is unavailable for now.

Open follow-ups:

- [x] **Q8** Set the K2 time box for P3-3 (in hours), given the time budget (Q2) and no prior Lean experience.
      → Moot: `accepts_iff_sat` was proved on 2026-10-18, so K2 was not needed.
- [ ] **Q9** Affiliation line for the README and the paper (or none).
- [ ] **Q10** An institutional-policy question (risk R6); details in the owner's private notes. The owner's call.
- [ ] **Q11** The owner wants a broader scope than the verified monitor (2026-10-17). Agree on an extended
      roadmap before changing `README.md` / `docs/01`.
- [ ] **Q12** Gate G1: proceed, re-scope or stop. Evidence, options (a)–(e) and the assistant's recommendation are in
      `docs/01-research-question.md` ("Gate G1"). The owner's call; record it in `docs/07`. Related to Q11.

## Phase 0 — Orientation and environment (first session)

- [ ] **P0-1** Read `CLAUDE.md`, all of `docs/`. Skim `monitor/` and `lean/`.
- [~] **P0-2** Install Lean 4 via `elan` on the owner's machine.
      Make `cd lean && lake build` succeed (the skeleton was written without a compiler). Pin
      `lean-toolchain` to an exact version; log it in `docs/07-decision-log.md`.
      *2026-10-17:* pinned to `leanprover/lean4:v4.35.0` (D-012); `lake build` green in the agent's cloud sandbox
      with no source fixes needed (8 tracked `sorry` warnings, no errors). **Remaining:** the owner installs elan on
      their own system (`lean/README.md`) and runs `lake build` once; agents cannot install software there.
- [~] **P0-3** `cd monitor && python3 -m pytest -q` green on the owner's own Python. *2026-10-18:* CI runs the tests on
      Python 3.10–3.14 on every push (57 tests, including the Lean conformance tests). *2026-10-17:* 53 passed on
      Python 3.10.12 in the agent's device VM (no pytest installed there; ran
      `uv run --no-project --with pytest -- python -m pytest -q`); also passed on 3.10 and 3.13 in the scaffolding
      environment. Remaining: add Hypothesis property tests (random formulas/traces) next to the exhaustive tests.
- [x] **P0-4** With the owner's approval: set git identity, make the first commit, push to `origin`.
      *2026-10-18:* first commit pushed to `main` of the public repository, as the owner asked (D-026).
- [x] **P0-5** Decide license and author line; update `README.md`, `monitor/pyproject.toml`, `paper/main.tex`.
      *2026-10-18:* Apache-2.0 (`LICENSE`); author line "Rui Zhu", affiliation left out until Q9 is answered.
- [ ] **P0-6** Read Liu et al., arXiv:2404.09080 (the source of ATACOM's forward-invariance / ISS
      guarantees; cited by 2505.10219 but unread). Notes → `refs/notes/`.
- [x] **P0-7** Once P0-2 is done, add a Lean job to the CI workflow (see P0-8; prefer the official Lean GitHub
      Action, check its README, pin a version). *2026-10-18:* `leanprover/lean-action` v1.6.2 (pinned by commit),
      with `--wfail`, leanchecker and axiom-audit; plus nanoda as an independent kernel (D-025).
- [x] **P0-8** Copy `docs/templates/Makefile.txt` → `Makefile` and `docs/templates/ci.yml.txt` →
      `.github/workflows/ci.yml`. *2026-10-18:* rewritten rather than copied (`Makefile`, `.github/workflows/ci.yml`);
      templates removed.

**Gate G0 (exit):** tests pass, `lake build` is green (with `sorry` warnings only), P0-6 notes written.

## Phase 1 — Literature gap check (1–2 weeks) — *decides whether the project is worth doing*

Done in one session on 2026-10-22 (D-027): relevant sections of the closest works, abstracts of the rest.

- [x] **P1-1** Search for **verified runtime monitors in proof assistants** (Isabelle, Coq/Rocq, Lean,
      HOL, ACL2, Agda) for LTL/LTLf/MFOTL/STL. Unverified leads from memory to check: VeriMon
      (Isabelle/HOL), verified LTL monitors in Coq, LTLf progression (Bacchus & Kabanza; De Giacomo & Vardi).
      *2026-10-22:* closest is MLTL formula progression in Isabelle/HOL (F54); also LTL3 progression (F55), VeriMon
      (F53), Rizaldi et al. (F56), a Coq MTL monitor (F57), a Lean 4 monitor for LLM-agent workflows (F59).
      One search for ACL2 and Agda returned nothing specific to them. `docs/03` D.
- [x] **P1-2** Search for **formally verified components in robot-foundation-model safety stacks**.
      *2026-10-22:* none found (F61). Nearest: temporal logic without proofs (STeP, RoboGuard, Safety Chip, SENTINEL;
      F62, F63) and machine-checked monitors on non-learned systems (F56, F60, VeriPhy). `docs/03` D–E.
- [x] **P1-3** Read the CBF+VLA works listed in `docs/03-related-work.md` (rows marked SNIPPET): which
      constraint types, any task-level/temporal constraints, any machine-checked proof?
      *2026-10-22 (abstracts):* rows 4–8 enforce geometric CBF constraints, with no temporal logic and no
      machine-checked proof (F64); ProbeAct uses a hand-written failure state machine (F65); row 9 is a position paper;
      row 10 evaluates offline with LTL/CTL (F11).
- [x] **P1-4** Targeted re-read: survey (2602.06971) §4.4 runtime monitoring; Agia et al. 2024
      (runtime monitoring of generative policies, CoRL). *2026-10-22:* §4.4 read (F69); Agia et al. abstract only
      (consistency + VLM progress checks on diffusion policies; `docs/03` row 14).
- [x] **P1-5** Inventory the Lean ecosystem: what Mathlib has for computability (`Primrec`, `Partrec`,
      Turing machines — *from memory, verify*), any LTL/temporal-logic or control libraries, any robotics
      libraries. Do not assume; check. *2026-10-22:* F72, `docs/03` H. No temporal logic in Mathlib; CSLib has Büchi
      automata and ω-regular languages; LeanLTL and Lentil for LTL; no control or robotics library found.
- [x] **P1-6** Write the one-page **gap statement + differentiation matrix** in `docs/01-research-question.md`.
      *2026-10-22:* done, with the K1 assessment and options for Gate G1.
- [~] **P1-7** Check which benchmark/sim to use (SafeLIBERO appears in a snippet only): existence,
      license, ease of running. Record in `docs/03`. *2026-10-17:* LIBERO through LeRobot 0.6.1 chosen for the
      first data collection (D-015); SafeLIBERO and LIBERO-plus not checked yet. *2026-10-22:* existence and licenses
      checked for LIBERO-PRO, LIBERO-plus, SafeLIBERO and LIBERO-Safety; LIBERO-Constrained (from STeP) not found
      (F71, `docs/03` G). Remaining: ease of running (none installed yet).

**Gate G1 (decision):** proceed / re-scope / stop, per kill criterion K1. Record in the decision log.
*2026-10-22:* evidence ready; K1 does not force a stop, but C1 cannot be the main contribution (`docs/01`). Decision
pending (Q12).

## Phase 2 — Specification language and monitor design

- [ ] **P2-1** Freeze the fragment (grammar in `docs/04`). Decide on bounded `Until`, weak next.
- [ ] **P2-2** Early verdicts: stay sound-only, or add a residual satisfiability check for completeness?
- [ ] **P2-3** Define the perception→labels interface (atoms, rates, latency budget) and A1 wording.
- [ ] **P2-4** Resource model: define `horizon φ`; state a bound on residual size as a Hypothesis test
      first (`size(run φ tr) ≤ size φ * (horizon φ + 1)` is the candidate; **a constant per-step factor is false**).
      *2026-10-22:* the candidate also fails when `always` is nested (linear growth, F73); restrict the fragment or
      add normalisation first (`docs/04`, "Resource bound").
- [ ] **P2-5** Spec library for pick-and-place: 6–10 specs, each with a natural-language description,
      a formula, and positive/negative traces as unit tests.
- [ ] **P2-6** Complexity of complete early verdicts (can a residual still be satisfied?) for this fragment, with
      bounds in unary vs binary. Literature first (F18 is MEMORY), then course weeks 8–13 (`docs/05`).

## Phase 3 — Lean formalization (core contribution)

- [x] **P3-1** Get `Formula.lean` / `Monitor.lean` compiling; polish naming. *Compiles since 2026-10-17.*
- [x] **P3-2** Prove `sat_shift`, `simpAnd_sat`, `simpOr_sat`, `progress_sat` (key lemma), `acceptsEmpty_iff`.
      *Proved 2026-10-18.*
- [x] **P3-3** Prove `accepts_iff_sat` (main theorem). *Proved 2026-10-18.*
- [x] **P3-4** Prove `violated_sound` and `satisfied_sound`. *Proved 2026-10-18.*
- [ ] **P3-5** Resource bound theorem (after P2-4 fixes the statement).
- [ ] **P3-6** *Bridge to the course:* `run φ` is primitive recursive under a coding of formulas and finite
      labels. Mathlib has `Primcodable`, `Primrec`, `Primrec.list_foldl` (F34); `progress` recurses on the formula
      tree, which needs course-of-values recursion on codes (`docs/05`). Never blocks the main line.
- [x] **P3-7** A `lake exe` command that reads a formula (JSON from `spec.to_dict`) and a JSONL trace and
      prints verdicts, for differential testing.
      *Done 2026-10-18:* `lean/BBMon.lean` (`lake build bbmon`; `bbmon batch` / `bbmon run`).
- [x] **P3-8** Bounded-verdict theorem: for formulas without unbounded `always`, `tr.length ≥ d φ → run φ tr ∈
      {tt, ff}` (d as in `monitor/tests/test_bounded_verdict.py`; exhaustive check passes on 1,000+ small
      formulas). Links bounded minimization to monitorability and to the learnability result F32.
      *Proved 2026-10-18:* `lean/BoundedBrain/BoundedVerdict.lean` (`bounded_verdict`; `verdict_final` adds that
      the verdict is then correct for every continuation of the trace).

Time box: if P3-3 is not done within the budget agreed in Q2, apply kill criterion K2.

## Phase 4 — Implementation and conformance

- [ ] **P4-1** Keep the Python reference in lockstep with Lean (same simplification rules).
- [x] **P4-2** Differential test: Hypothesis-generated formulas/traces → Python vs. Lean executable.
      *Done 2026-10-18 without Hypothesis:* `monitor/tests/test_lean_conformance.py` (67,320 exhaustive small
      cases + 4,000 seeded random ones) and all 16,248 LIBERO (episode, spec) pairs; 0 mismatches (F50).
- [~] **P4-3** Latency benchmark (µs/step). Targets to compare against: VLA chunk rate (~15 Hz) and filter
      rate (50–60 Hz) as reported in the ATACOM paper. *Indicative only:* the Lean binary did 3.67 M monitor
      steps in 1.9 s including JSON parsing (cloud sandbox, F50); a proper per-step benchmark is still to do.

## Phase 5 — Integration and evaluation (simulation)

- [x] **P5-0** Use the owner's expiring Colab compute (80 units, expiring around 2026-10-22) for LIBERO rollouts of
      π0.5 and π0 with privileged traces: `experiments/colab/` (D-015, D-016). Smoke tests passed for π0.5 (single and
      parallel envs, F38); π0's checkpoint does not load in lerobot 0.6.1, so it is excluded (D-019). Main runs
      launched 2026-10-17; the notebook now stops cleanly before the budget or the 12-hour limit and waits for Drive
      before releasing the GPU (D-020). The first session ended after about 8 h (F42); a second session (v9, D-021)
      uses the remaining ~32 units. Done: 4,062 episodes in `data/libero_runs` (git-ignored); results in
      `docs/08` (F43–F45).

- [x] **P5-1** Choose benchmark (from P1-7). Run π0 (open weights) through LeRobot; reproduce one published number.
      Done with π0.5 on LIBERO: 97.4% average vs 97.5% published (F43); π0's checkpoint does not load (F38).
- [ ] **P5-2** Labeler: start from privileged simulator state; later add a perceived-label variant. Keep A1 explicit.
- [ ] **P5-3** Detect-only mode: measure task-level violation rate of the raw VLA.
- [ ] **P5-4** Add a continuous filter baseline (ATACOM / CBF-style; check whether code is released).
- [ ] **P5-5** Enforcement mode: on `VIOLATED`/imminent violation, hold or retreat; measure success-vs-safety trade-off.
- [ ] **P5-6** Perception-noise ablation: show honestly where the guarantee degrades.
- [ ] **P5-7** Statistics: seeds, confidence intervals, no cherry-picked episodes.
- [~] **P5-8** Offline analysis of the Colab traces: LIBERO spec library (P2-5 with predicates recomputed from the
      traces), violation rates per policy and suite, detection time vs. time of failure. First pass done
      (`docs/08`, `experiments/analysis/`, D-022). Next: per-task specs from the BDDL goals (P2-5), per-task
      bounds, a simple learned failure predictor as baseline, perception noise (P5-6).
- [ ] **P5-9** Position the LIBERO-90 finding (F44) against LIBERO-PRO and LIBERO-Plus (F46, F47): read both
      papers in full; check whether π0.5 was evaluated anywhere under language or object perturbations.
      *2026-10-22:* also AFI (F68), which detects and intervenes on a related "memory trap" with π0 and π0.5, and the
      learned detectors that already use π0.5 on LIBERO (F66).

**Gate G5:** if the monitor shows no measurable benefit over the baselines, apply K3 before writing.

## Phase 6 — Optional real robot (deferred: no robot arm, see Q1)

- [ ] **P6-1** Low-cost arm + LeRobot pipeline; repeat the smallest detect-only experiment on hardware.

## Phase 7 — Paper

- [ ] **P7-1** Claims table: every claim → evidence (proof / test / experiment) → file path.
- [ ] **P7-2** Related work from `docs/03` (only verified entries).
- [ ] **P7-3** Limitations: A1–A4, perception, spec adequacy, sim-to-real.
- [ ] **P7-4** Artifact checklist: Lean builds in CI, tests, pinned versions, seeds.
- [ ] **P7-5** Pick a venue; look up current deadlines (unknown at skeleton time; search, do not guess).
- [ ] **P7-6** Motivation section: Rice's theorem and index sets → why runtime monitoring; NP-completeness of
      ReLU-network verification (F33). See `docs/05`.

## Phase 8 — Release

- [ ] **P8-1** License, citation file, archive a DOI, tag `v0.1.0`.

## Stretch (only if gates pass)

- [ ] **S-1** "Code-as-safety": an LLM proposes specs; a verified checker validates the fragment and sanity-checks
      them (named as future work in the ATACOM paper).
- [ ] **S-2** Quantitative semantics (STL robustness) for continuous signals.
- [ ] **S-3** Reward-machine view of the same specs (survey §3).

## Standing tasks

- [ ] Keep `docs/02-facts-register.md` current (add every new fact with its verification status).
- [ ] Log every non-obvious decision in `docs/07-decision-log.md`.
- [ ] Re-run the monitor tests (`cd monitor && python3 -m pytest -q`) before every commit.
