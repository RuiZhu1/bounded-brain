# lean/ — machine-checked correctness of the monitor

Lean 4 project `BoundedBrain`. Goal: prove that the progression monitor agrees with the
reference LTLf semantics (and that early verdicts are sound). This is the formal building block of
the project (see `../TODO.md`, Phase 3); since the re-scope of 2026-10-22 (D-028) it is not the main
contribution, because verified progression monitors already exist (`../docs/01-research-question.md`).
The resource bound (P3-5) was proved on 2026-10-23; the next Lean work on the critical path is the atom definitions
(P3-10).

## Status (2026-10-23)

* **All stated theorems are proved.** `lake build` (Lean `v4.35.0`, D-012) is green with no warnings and no
  `sorry`; `#print axioms` lists only Lean's standard axioms (`propext`, `Classical.choice`, `Quot.sound`).
* The fragment includes bounded Until `φ U[0,k] ψ` (`Formula.untilWithin`, P3-9, D-029, 2026-10-23); every theorem
  below covers it.
* `Monitor.lean`: `sat_shift`, `simpAnd_sat`, `simpOr_sat`, `progress_sat`, `acceptsEmpty_iff` (P3-2),
  `accepts_iff_sat` (P3-3, main theorem), `violated_sound`, `satisfied_sound` (P3-4).
* `Normal.lean`: every residual is in normal form (`norm_progress`); progression commutes with the simplifiers
  (`progress_simpAnd`, `progress_simpOr`) (D-030).
* `BoundedVerdict.lean`: `bounded_verdict` and `verdict_final` (P3-8).
* `Resource.lean`: every residual lies in an explicit finite list `reach φ` (`run_mem_reach`), so
  `(run φ tr).size ≤ resBound φ` for every trace (`size_run_le`, P3-5, D-031).
* `BBMon.lean` (P3-7): executable `bbmon` that runs these verified functions on JSON input; it agrees with the
  Python monitor on every case tried (`monitor/tests/test_lean_conformance.py`, F50).
* Open: primitive-recursion bridge (P3-6); a tighter, computable resource bound.

## Files

| File | Contents | Python mirror |
|---|---|---|
| `BoundedBrain/Formula.lean` | `Label`, `Trace`, `Formula`, `Formula.size`, reference semantics `Sat` | `spec.py` (`holds`) |
| `BoundedBrain/Monitor.lean` | `simpAnd/simpOr`, `progress`, `acceptsEmpty`, `run`, `accepts`; correctness theorems (proved) | `monitor.py` |
| `BoundedBrain/Normal.lean` | normal form of residuals, `progress_simpAnd`, `progress_simpOr` | `tests/test_monitor.py` (commutation test) |
| `BoundedBrain/BoundedVerdict.lean` | `Formula.alwaysFree`, `Formula.verdictDepth`, `bounded_verdict`, `verdict_final` | `tests/test_bounded_verdict.py` |
| `BoundedBrain/Resource.lean` | `reach`, `resBound`, `run_mem_reach`, `size_run_le` | `tests/test_monitor.py` (residual-size tests) |
| `BoundedBrain.lean` | library root (imports the five files) | — |
| `BBMon.lean` | executable `bbmon`: JSON specs and traces in, verdicts out (parser and printer not verified) | `to_dict` / `from_dict` |
| `Checks.lean` | CI checks: the main theorems keep their stated form; every declaration uses only the standard axioms | — |
| `scripts/nanoda.sh` | re-checks the library with nanoda, an independent type checker written in Rust | — |
| `lakefile.toml`, `lean-toolchain`, `lake-manifest.json` | Lake config, pinned Lean version, Lake manifest (no dependencies) | — |

## Install and build

Official instructions: <https://lean-lang.org/install/manual/> (checked 2026-10-17; facts F20).

```bash
curl https://elan.lean-lang.org/elan-init.sh -sSf | sh   # installs elan; choose 1 (default) when asked
source $HOME/.elan/env                                    # or open a new terminal
cd lean
lake build   # first run: elan downloads the pinned toolchain (~600 MB download, ~3 GB on disk)
```

Expected: `Build completed successfully`, with no warnings.

The checks CI runs on every push (`.github/workflows/ci.yml`; `make lean`, `make nanoda` from the repository root):

```bash
lake build --wfail          # any warning fails, including "declaration uses 'sorry'"
lake env leanchecker        # replays every declaration of the package through the kernel
lake env lean Checks.lean   # theorem statements and axioms
bash scripts/nanoda.sh      # second, independent type checker (needs Rust; about 2 minutes)
```

CI also runs `axiom-audit` (through `leanprover/lean-action`).

Differential test against the Python monitor:

```bash
cd lean && lake build bbmon                                # builds .lake/build/bin/bbmon
cd ../monitor && python3 -m pytest -q tests/test_lean_conformance.py   # skipped if bbmon is missing
```

Editor: VS Code with the official extension (`code --install-extension leanprover.lean4`); open the `lean/` folder.

Agent sandboxes cannot reach `release.lean-lang.org`; see `../CLAUDE.md` (environment gotchas) for the manual install.

## Proof roadmap

Done (2026-10-18): `sat_shift`, `simpAnd_sat`, `simpOr_sat`, `progress_sat` (the key lemma), `acceptsEmpty_iff`,
`accepts_iff_sat` (main theorem), `violated_sound`, `satisfied_sound`, `bounded_verdict`, `verdict_final`.

Done (2026-10-23): bounded Until in every theorem (P3-9); normal form and commutation (`Normal.lean`); resource
bound `size_run_le` (P3-5).

Next:
1. Atom definitions over the simulator state (P2-7, P3-10)
2. Optional bridge theorem (P3-6): the monitor step is primitive recursive under a Gödel coding
   (would need Mathlib's `Nat.Primrec`; check the API first)

## Rules

* No `axiom`. No `sorry` unless it is tracked by a TODO ID.
* Keep simplification rules identical to the Python side (flattening and removal of repeated conjuncts and
  disjuncts, D-030).
* Do not add Mathlib unless a task needs it; record the decision.
* The Lean side must stay in the discrete world. Continuous dynamics are out of scope unless
  the Gate G1 decision explicitly changes that.
