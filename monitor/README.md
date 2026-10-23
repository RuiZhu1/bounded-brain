# monitor/ — Python reference implementation

Dependency-free reference implementation of the bounded LTLf monitor. It is the executable
twin of the Lean development in `../lean/` and the oracle for differential testing.

```bash
cd monitor
python3 -m pip install -e ".[dev]"   # or: uv run --with pytest pytest
python3 -m pytest -q                  # 71 tests on 2026-10-23; 2 are skipped without the Lean executable
```

## Example

```python
from bounded_brain import Always, EventuallyWithin, Monitor, atom, implies

# "Only lift when the grasp is stable" and "release within 50 control steps".
lift_safety = Always(implies("lift_cmd", "grasp_stable"))
m = Monitor(lift_safety)

m.step({"approach"})                       # Verdict.PENDING
m.step({"lift_cmd", "grasp_stable"})       # Verdict.PENDING
m.step({"lift_cmd"})                       # Verdict.VIOLATED  (no stable grasp)

# An ordering rule with bounded Until: "do not place before the drawer is open; open it within 3 steps".
from bounded_brain import UntilWithin, not_atom
order = Monitor(UntilWithin(3, not_atom("place"), atom("drawer_open")))
order.step({"approach"})                   # Verdict.PENDING
order.step({"place"})                      # Verdict.VIOLATED  (placed while the drawer was closed)
```

## What is tested

* `holds` (in `spec.py`) is a deliberately naive LTLf oracle.
* `tests/test_monitor.py` checks, exhaustively on all traces up to length 5 over two atoms and
  26 formulas (bounded Until included), that the monitor's end-of-trace answer equals the oracle, and that early
  `VIOLATED`/`SATISFIED` verdicts are sound for all short extensions.
* `tests/test_bounded_verdict.py` checks the bounded-verdict property; `tests/test_lean_conformance.py` compares the
  monitor with the Lean executable (`../lean/BBMon.lean`) step by step.
* A regression test guards the classic strong-`Next` progression bug (see
  `../docs/04-architecture.md`, "Pending").

## Known limits (by design, for now)

* Early verdicts are **sound but not complete**: a residual can be unsatisfiable without being
  simplified to `FF`. The end-of-trace answer is exact.
* Labels (which atoms are true) are an input. The monitor says nothing about whether
  perception produced them correctly (assumption A1).
* The size of the monitor state is bounded by a number that depends on the spec alone (Lean `size_run_le`), but that
  number is very large when `Always` is nested over a disjunction; observed sizes are small
  (`../docs/04-architecture.md`, "Resource bound").
