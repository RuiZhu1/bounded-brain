# monitor/ — Python reference implementation

Dependency-free reference implementation of the bounded LTLf monitor. It is the executable
twin of the Lean development in `../lean/` and the oracle for differential testing.

```bash
cd monitor
python3 -m pip install -e ".[dev]"   # or: uv run --with pytest pytest
python3 -m pytest -q                  # 53 tests at the time of writing
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
```

## What is tested

* `holds` (in `spec.py`) is a deliberately naive LTLf oracle.
* `tests/test_monitor.py` checks, exhaustively on all traces up to length 5 over two atoms and
  20 formulas, that the monitor's end-of-trace answer equals the oracle, and that early
  `VIOLATED`/`SATISFIED` verdicts are sound for all short extensions.
* A regression test guards the classic strong-`Next` progression bug (see
  `../docs/04-architecture.md`, "Pending").

## Known limits (by design, for now)

* Early verdicts are **sound but not complete**: a residual can be unsatisfiable without being
  simplified to `FF`. The end-of-trace answer is exact.
* Labels (which atoms are true) are an input. The monitor says nothing about whether
  perception produced them correctly (assumption A1).
