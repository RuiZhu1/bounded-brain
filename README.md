# bounded-brain

**Verified, bounded runtime monitors for robot foundation models.** *(working title)*

[![CI](https://github.com/RuiZhu1/bounded-brain/actions/workflows/ci.yml/badge.svg)](https://github.com/RuiZhu1/bounded-brain/actions/workflows/ci.yml)

> **Status (2026-10-22).** The monitor's correctness theorems are machine-checked in Lean 4 (no `sorry`; see
> [`lean/README.md`](lean/README.md)). A first evaluation on 4,062 π0.5 episodes in LIBERO is in
> [`docs/08-libero-results.md`](docs/08-libero-results.md). The literature check (Phase 1) found that a verified
> progression monitor is not new on its own, so the project was re-scoped to the use of such a monitor in a
> run-time-assurance loop around a VLA ([`docs/01`](docs/01-research-question.md), decision D-028). Read
> [`TODO.md`](TODO.md) for the plan and [`docs/02-facts-register.md`](docs/02-facts-register.md) for what has (and
> has not) been verified.

## The idea in one paragraph

Vision-language-action (VLA) models such as π0 map camera images and a language instruction to
robot actions, but nothing in them guarantees that task-level safety rules hold ("never lift
before the grasp is stable", "release within 50 steps", "never enter the forbidden zone").
Existing safety layers (control-barrier-function and constraint-manifold filters, e.g.
ATACOM applied to π0) enforce *continuous geometric* constraints. We study the complementary
*discrete, temporal* layer: a **bounded, total runtime monitor** for a finite-trace temporal
logic fragment (LTLf), whose correctness is **machine-checked in Lean 4**, used as the assured
component of a **run-time-assurance loop** around an open-source VLA (π0.5 in LIBERO, in
simulation): the monitor checks task-level rules on every step and triggers an intervention when
a rule is violated. Verified monitors as such already exist (closest prior work in
[`docs/01`](docs/01-research-question.md)); what we did not find is one running on the executions
of a learned policy, and that is what this project studies.

## What we do and do not claim

| We aim to show | We do **not** claim |
|---|---|
| The monitor's verdict equals the reference LTLf semantics (Lean theorem). | That the robot is "provably safe". |
| Early `VIOLATED` / `SATISFIED` verdicts are sound. | That perception labels are correct (assumption A1). |
| Every step is a total function, and the monitor state is bounded by a number that depends on the spec, not on the trace length (Lean theorem `size_run_le`; the bound is very large for nested `always`). | That the specs capture human intent (assumption A2). |
| In the loop of a VLA, the monitor runs at negligible latency, and acting on its alarms is worth the false alarms, measured counterfactually and compared with learned failure detectors. | That this beats any particular robot-learning system at manipulation. |
| | That a verified progression monitor is new in itself (see [`docs/01`](docs/01-research-question.md)). |

The honest guarantee is **conditional**: *if* perception labels are correct, *then* the monitor's
verdict is correct with respect to the specification. See
[`docs/04-architecture.md`](docs/04-architecture.md) for assumptions A1–A4.

## Planned contributions (re-scoped 2026-10-22, D-028)

1. **C1 — Verified monitor (a building block, not the main claim).** A bounded LTLf fragment, a progression
   monitor, and Lean proofs of end-of-trace correctness, sound early verdicts and bounded verdicts. **Done** for the
   current fragment ([`lean/`](lean/)), which includes bounded Until for ordering rules, and a proved bound on the size of the monitor state
   (2026-10-23).
2. **C2 — The deployed monitor is the verified code.** **Done so far:** the Lean executable and the Python monitor
   agree on 124,105 generated cases and on all 16,248 LIBERO (episode, spec) pairs (`lean/BBMon.lean`,
   `monitor/tests/test_lean_conformance.py`). **Next:** run the Lean-compiled monitor itself in the control loop.
3. **C3 — Run-time assurance around a VLA (main contribution).** π0.5 in LIBERO with a library of task-level rules
   that need temporal structure (ordering, response), atoms computed from simulator state, and an intervention when
   a rule is violated; evaluated against learned failure detectors and by the value of acting on alarms, using
   counterfactual branches from saved simulator states. *First pass, offline:* 4,062 π0.5 episodes, four simple specs
   (`docs/08`).
4. **C4 (stretch).** Atom definitions checked in Lean against declarative definitions over the simulator state;
   language-model-proposed specs that are machine-checked to lie in the fragment before deployment.

## Repository map

| Path | What lives there |
|---|---|
| [`TODO.md`](TODO.md) | Phased plan with IDs, acceptance criteria, gates, blocking questions |
| [`CLAUDE.md`](CLAUDE.md) | Working agreements for coding agents (read before touching anything) |
| [`docs/`](docs/) | Context, research question, **facts register**, related work, architecture, course mapping, risks, decision log, first LIBERO results (`08`) |
| [`monitor/`](monitor/) | Python reference monitor + exhaustive tests (runs today) |
| [`lean/`](lean/) | Lean 4 project: syntax, semantics, monitor, correctness proofs (no `sorry`), `bbmon` executable |
| [`experiments/`](experiments/) | Colab kit for LIBERO rollouts with privileged traces (`colab/`), offline analysis (`analysis/`) |
| [`paper/`](paper/) | LaTeX skeleton and bibliography |
| [`refs/`](refs/) | Reading notes (paper PDFs are git-ignored) |
| [`course/`](course/) | Local-only course materials (git-ignored; see `docs/05`) |
| [`.github/workflows/`](.github/workflows/), [`Makefile`](Makefile) | CI on every push (see below) and the same checks locally |

## Quickstart

```bash
cd monitor && python3 -m pytest -q                      # Python monitor + exhaustive agreement tests (no Lean needed)
cd lean && lake build                                   # requires elan (see lean/README.md); no warnings
cd paper && latexmk -pdf -outdir=build main.tex         # requires a TeX installation
```

`make help` lists the local targets; `make ci` runs what CI runs.

## Continuous integration

[`.github/workflows/ci.yml`](.github/workflows/ci.yml) runs on every push and pull request (and weekly), on
GitHub's hosted runners:

| Job | What it checks |
|---|---|
| Lean proofs | `lake build --wfail` (any warning, e.g. `declaration uses 'sorry'`, fails); Lean's `leanchecker` replays every declaration through the kernel; `axiom-audit` and [`lean/Checks.lean`](lean/Checks.lean): every declaration uses only `propext`, `Classical.choice`, `Quot.sound`, and the main theorems keep their stated form; builds `bbmon` |
| Independent kernel | [nanoda](https://github.com/ammkrn/nanoda_lib), a second Lean type checker written in Rust, re-checks the exported library ([`lean/scripts/nanoda.sh`](lean/scripts/nanoda.sh)) |
| Lean = Python | the verified Lean monitor (`bbmon`) and the Python monitor agree on 124,105 generated cases |
| Python 3.10–3.14 | monitor tests; the package installs with no dependencies |
| Lint and notebook | `ruff` (pinned rule set); the Colab notebook is regenerated from its kit and must be unchanged |
| Paper | builds [`paper/main.tex`](paper/main.tex); the PDF is attached to the run |

The LIBERO analysis (`experiments/analysis/`) is not run in CI: its input traces (550 MB) are not in the repository.

## Start here (for the next person or agent)

1. This README, then [`CLAUDE.md`](CLAUDE.md).
2. [`TODO.md`](TODO.md) — begin with *Blocking questions* and Phase 0.
3. [`docs/02-facts-register.md`](docs/02-facts-register.md) — do not cite anything marked
   `UNVERIFIED`, `MEMORY` or `DEBUNKED` as fact.
4. [`docs/04-architecture.md`](docs/04-architecture.md) and [`docs/06-risks-and-kill-criteria.md`](docs/06-risks-and-kill-criteria.md).

## Naming

`bounded-brain`: *bounded* recursion and bounded temporal operators (no unbounded search), applied
to a robot's "brain". The name is a nod to the bounded-quantification material in the owner's
Theory of Computation course; it does not imply any capability claim.

## Authors and license

Rui Zhu, sole author. Licensed under the Apache License, Version 2.0 ([`LICENSE`](LICENSE)).
