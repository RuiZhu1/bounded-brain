"""Differential test: the Lean monitor (lean/BBMon.lean, TODO P3-7) against this Python monitor.

`bbmon` runs the Lean functions `progress`, `run` and `accepts` that are proved correct in
lean/BoundedBrain/Monitor.lean. If both monitors give the same verdict and residual size after every
step, the same final residual and the same final answer, the Python monitor computes the verified
function on these cases (contribution C2). Skipped when the Lean executable has not been built
(unless BB_REQUIRE_LEAN=1, as in CI):

    cd lean && lake build bbmon        # or set BB_LEAN_EXE to the binary
"""

from __future__ import annotations

import itertools
import json
import os
import random
import subprocess
import tempfile
from pathlib import Path
from typing import List, Sequence, Tuple

import pytest

from bounded_brain import (
    FF,
    TT,
    Always,
    AlwaysWithin,
    And,
    EventuallyWithin,
    Formula,
    Lit,
    Monitor,
    Next,
    Or,
    UntilWithin,
    accepts,
    size,
    to_dict,
)

REPO = Path(__file__).resolve().parents[2]
EXE = Path(os.environ.get("BB_LEAN_EXE", REPO / "lean" / ".lake" / "build" / "bin" / "bbmon"))
# CI sets BB_REQUIRE_LEAN=1: there a missing binary must fail the tests instead of skipping them.
REQUIRE = os.environ.get("BB_REQUIRE_LEAN") == "1"

pytestmark = pytest.mark.skipif(
    not REQUIRE and not (EXE.is_file() and os.access(EXE, os.X_OK)),
    reason=f"Lean executable not built ({EXE}); run `cd lean && lake build bbmon`",
)

Case = Tuple[Sequence[Formula], Sequence[frozenset]]


def python_result(phi: Formula, trace: Sequence[frozenset]) -> dict:
    m = Monitor(phi)
    verdicts, sizes = [], []
    for label in trace:
        verdicts.append(m.step(label).value)
        sizes.append(size(m.residual))
    return {"verdicts": verdicts, "sizes": sizes, "residual": to_dict(m.residual),
            "accepts": accepts(phi, list(trace))}


def lean_results(cases: List[Case]) -> List[list]:
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "cases.jsonl"
        with open(path, "w") as f:
            for i, (specs, trace) in enumerate(cases):
                row = {"id": i, "specs": [to_dict(s) for s in specs],
                       "trace": [sorted(label) for label in trace]}
                f.write(json.dumps(row) + "\n")
        out = subprocess.run([str(EXE), "batch", str(path)], capture_output=True, text=True,
                             check=True)
    rows = [json.loads(line) for line in out.stdout.splitlines()]
    assert [r["id"] for r in rows] == list(range(len(cases)))
    return [r["results"] for r in rows]


def assert_agree(cases: List[Case]) -> int:
    checked, mismatches = 0, []
    for (specs, trace), results in zip(cases, lean_results(cases)):
        assert len(results) == len(specs)
        for phi, lean in zip(specs, results):
            checked += 1
            py = python_result(phi, trace)
            if py != lean:
                mismatches.append((phi, [sorted(label) for label in trace], py, lean))
    assert not mismatches, mismatches[:3]
    return checked


# ------------------------------------------------------------------------------------------ #

ATOMS = ("a", "b")
LABELS = [frozenset(s) for s in ([], ["a"], ["b"], ["a", "b"])]


def small_formulas() -> List[Formula]:
    """Every formula of nesting depth <= 2 over two atoms, `always` included."""
    base: List[Formula] = [TT(), FF()] + [Lit(n, p) for n in ATOMS for p in (True, False)]
    one: List[Formula] = list(base)
    for f in base:
        one += [Next(f), Always(f)]
        one += [AlwaysWithin(k, f) for k in (0, 1, 2)] + [EventuallyWithin(k, f) for k in (0, 1, 2)]
    one += [And(f, g) for f, g in itertools.product(base, base)]
    one += [Or(f, g) for f, g in itertools.product(base, base)]
    one += [UntilWithin(k, f, g) for f, g in itertools.product(base, base) for k in (0, 1, 2)]
    two: List[Formula] = []
    for f in one:
        two += [Next(f), Always(f), AlwaysWithin(1, f), EventuallyWithin(2, f)]
    pairs = [Next(Lit("a")), Always(Lit("b")), EventuallyWithin(1, Lit("a"))] + base
    two += [And(f, g) for f, g in itertools.product(pairs, pairs)]
    two += [Or(f, g) for f, g in itertools.product(pairs, pairs)]
    two += [UntilWithin(1, f, g) for f, g in itertools.product(pairs, pairs)]
    return one + two


def test_lean_agrees_on_every_small_case() -> None:
    specs = small_formulas()
    traces = [t for n in range(4) for t in itertools.product(LABELS, repeat=n)]
    checked = assert_agree([(specs, t) for t in traces])
    assert checked > 50_000  # guard against the enumeration silently shrinking


def random_formula(rng: random.Random, depth: int) -> Formula:
    atoms = ("a", "b", "c")
    if depth == 0 or rng.random() < 0.25:
        r = rng.random()
        return TT() if r < 0.1 else FF() if r < 0.2 else Lit(rng.choice(atoms), rng.random() < 0.7)
    op = rng.choice(["and", "or", "next", "always", "always_within", "eventually_within", "until_within"])
    if op == "and":
        return And(random_formula(rng, depth - 1), random_formula(rng, depth - 1))
    if op == "until_within":
        return UntilWithin(rng.randint(0, 4), random_formula(rng, depth - 1), random_formula(rng, depth - 1))
    if op == "or":
        return Or(random_formula(rng, depth - 1), random_formula(rng, depth - 1))
    if op == "next":
        return Next(random_formula(rng, depth - 1))
    if op == "always":
        return Always(random_formula(rng, depth - 1))
    cls = AlwaysWithin if op == "always_within" else EventuallyWithin
    return cls(rng.randint(0, 4), random_formula(rng, depth - 1))


def test_lean_agrees_on_random_cases() -> None:
    rng = random.Random(20261018)
    labels = [frozenset(s) for n in range(4) for s in itertools.combinations(("a", "b", "c"), n)]
    cases: List[Case] = []
    for _ in range(400):
        trace = [rng.choice(labels) for _ in range(rng.randint(0, 15))]
        cases.append(([random_formula(rng, 5) for _ in range(10)], trace))
    assert assert_agree(cases) == 4000
