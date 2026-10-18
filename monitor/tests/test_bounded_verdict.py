"""Bounded-verdict property (TODO P3-8), checked exhaustively on small formulas.

For formulas without the unbounded `Always`, define the verdict depth

    d(tt) = d(ff) = d(literal) = 1          d(X f) = 1 + d(f)
    d(G[0,k] f) = d(F[0,k] f) = k + d(f)    d(f & g) = d(f | g) = max(d(f), d(g))

Claim: after any d(f) steps the residual is TT or FF, so the monitor has reached a definite
verdict; the time to a verdict is a bounded minimization (docs/05-course-mapping.md). These are
the formulas "decidable within a finite horizon" (docs/02, F32). Proved in Lean:
lean/BoundedBrain/BoundedVerdict.lean (`bounded_verdict`).
"""

from __future__ import annotations

import itertools
from typing import Iterator, List

from bounded_brain import FF, TT, And, AlwaysWithin, EventuallyWithin, Formula, Lit, Next, Or, run

ATOMS = ("a", "b")
LABELS = [frozenset(c) for r in range(len(ATOMS) + 1) for c in itertools.combinations(ATOMS, r)]
MAX_DEPTH_CHECKED = 5


def verdict_depth(f: Formula) -> int:
    if isinstance(f, (TT, FF, Lit)):
        return 1
    if isinstance(f, Next):
        return 1 + verdict_depth(f.arg)
    if isinstance(f, (AlwaysWithin, EventuallyWithin)):
        return f.bound + verdict_depth(f.arg)
    if isinstance(f, (And, Or)):
        return max(verdict_depth(f.left), verdict_depth(f.right))
    raise TypeError(f"not in the always-free fragment: {f!r}")


def _literals() -> List[Formula]:
    return [Lit(n, p) for n in ATOMS for p in (True, False)]


def _formulas(depth: int) -> List[Formula]:
    base: List[Formula] = [TT(), FF(), *_literals()]
    if depth == 0:
        return base
    out = list(base)
    for f in _formulas(depth - 1):
        out.append(Next(f))
        for k in (0, 1, 2):
            out += [AlwaysWithin(k, f), EventuallyWithin(k, f)]
    small = _formulas(depth - 1) if depth == 1 else base + [Next(x) for x in _literals()]
    for f, g in itertools.product(small, small):
        out += [And(f, g), Or(f, g)]
    return out


def _cases() -> Iterator[tuple]:
    for f in _formulas(2):
        n = verdict_depth(f)
        if n <= MAX_DEPTH_CHECKED:
            yield f, n


def test_verdict_is_reached_within_verdict_depth() -> None:
    checked = 0
    for f, n in _cases():
        for trace in itertools.product(LABELS, repeat=n):
            residual = run(f, list(trace))
            assert isinstance(residual, (TT, FF)), (f, [sorted(s) for s in trace], residual)
            checked += 1
    assert checked > 10_000  # guard against the enumeration silently shrinking


def test_verdict_depth_is_tight_on_examples() -> None:
    # F[0,2] a on a trace where `a` never holds needs all three steps.
    f = EventuallyWithin(2, Lit("a"))
    assert verdict_depth(f) == 3
    assert not isinstance(run(f, [frozenset()] * 2), (TT, FF))
    # Strong next needs the successor step to exist even when its argument is trivial.
    g = Next(TT())
    assert verdict_depth(g) == 2
    assert not isinstance(run(g, [frozenset()]), (TT, FF))
