"""Small-scope exhaustive tests: the monitor must agree with the LTLf oracle.

These are the executable twins of the Lean theorems in lean/BoundedBrain/Monitor.lean:

  * test_end_of_trace_matches_oracle   <->  accepts_iff_sat      (TODO P3-3)
  * test_early_verdicts_are_sound      <->  violated_sound / satisfied_sound (TODO P3-4)
  * test_residual_size_is_bounded      <->  resource bound (TODO P3-5); the bound asserted
    here is an empirical sanity check for ONE spec, not a theorem.
"""

from __future__ import annotations

import itertools
import random
from typing import Iterator, List, Tuple

import pytest

from bounded_brain import (
    FF,
    TT,
    And,
    Always,
    AlwaysWithin,
    EventuallyWithin,
    Formula,
    Monitor,
    Next,
    Or,
    UntilWithin,
    Verdict,
    accepts,
    atom,
    holds,
    implies,
    never,
    not_atom,
    progress,
    run,
    size,
)

A, B = "a", "b"
LABELS = [frozenset(s) for s in ([], [A], [B], [A, B])]


def all_traces(max_len: int) -> Iterator[Tuple[frozenset, ...]]:
    for n in range(max_len + 1):
        yield from itertools.product(LABELS, repeat=n)


FORMULAS: List[Formula] = [
    TT(),
    FF(),
    atom(A),
    not_atom(A),
    And(atom(A), atom(B)),
    Or(atom(A), atom(B)),
    Next(atom(A)),
    Next(Next(atom(A))),
    Next(Always(atom(A))),  # guards against naive "Next f -> f" progression
    Always(implies(A, B)),  # G (a -> b)
    Always(Or(not_atom(A), Next(atom(B)))),  # G (a -> X b)
    AlwaysWithin(2, atom(A)),
    EventuallyWithin(2, atom(A)),
    And(Always(atom(A)), EventuallyWithin(1, atom(B))),
    Or(Next(atom(A)), atom(B)),
    AlwaysWithin(1, EventuallyWithin(1, atom(A))),
    EventuallyWithin(0, atom(A)),
    AlwaysWithin(0, Next(atom(A))),
    Always(Always(implies(A, B))),
    And(Next(atom(A)), Next(not_atom(A))),
    UntilWithin(0, atom(A), atom(B)),
    UntilWithin(2, atom(A), atom(B)),
    UntilWithin(3, not_atom(B), atom(A)),  # no b before a, and a within 4 steps (an ordering rule)
    UntilWithin(1, atom(A), Next(atom(B))),
    UntilWithin(2, EventuallyWithin(1, atom(B)), Always(atom(A))),
    Always(Or(not_atom(A), UntilWithin(1, atom(A), atom(B)))),  # G (a -> a U[0,1] b)
]


@pytest.mark.parametrize("phi", FORMULAS, ids=repr)
def test_end_of_trace_matches_oracle(phi: Formula) -> None:
    for trace in all_traces(5):
        assert accepts(phi, trace) == holds(trace, 0, phi), (phi, trace)


@pytest.mark.parametrize("phi", FORMULAS, ids=repr)
def test_early_verdicts_are_sound(phi: Formula) -> None:
    for prefix in all_traces(3):
        residual = run(phi, prefix)
        for ext in all_traces(2):
            sat = holds(tuple(prefix) + tuple(ext), 0, phi)
            if residual == FF():
                assert not sat, ("VIOLATED but an extension satisfies", phi, prefix, ext)
            if residual == TT():
                assert sat, ("SATISFIED but an extension violates", phi, prefix, ext)


def test_strong_next_needs_a_successor_step() -> None:
    phi = Next(Always(atom(A)))
    assert accepts(phi, [frozenset([A])]) is False  # no second step exists
    assert accepts(phi, [frozenset([A]), frozenset([A])]) is True
    assert accepts(phi, [frozenset(), frozenset([A])]) is True  # first step is unconstrained


def test_empty_trace_conventions() -> None:
    assert accepts(Always(atom(A)), []) is True  # vacuous
    assert accepts(EventuallyWithin(3, atom(A)), []) is False
    assert accepts(atom(A), []) is False
    assert accepts(not_atom(A), []) is False  # literals need a step


def test_bound_validation() -> None:
    with pytest.raises(ValueError):
        AlwaysWithin(-1, atom(A))
    with pytest.raises(ValueError):
        EventuallyWithin(-1, atom(A))
    with pytest.raises(ValueError):
        UntilWithin(-1, atom(A), atom(B))


def test_until_is_strong_and_bounded() -> None:
    phi = UntilWithin(2, atom(A), atom(B))
    assert accepts(phi, []) is False  # the step where b holds must exist
    assert accepts(phi, [frozenset([A])]) is False  # a held, but b never came
    assert accepts(phi, [frozenset([B])]) is True  # b at once: a is not needed
    assert accepts(phi, [frozenset([A]), frozenset([A]), frozenset([B])]) is True
    assert accepts(phi, [frozenset([A])] * 3 + [frozenset([B])]) is False  # b came one step too late
    assert accepts(phi, [frozenset(), frozenset([B])]) is False  # a failed before b


# ----------------------------- robot-flavoured specs ------------------------ #


def test_open_drawer_before_placing() -> None:
    # "Do not place the bowl before the drawer is open; open it within 3 steps."
    spec = UntilWithin(3, not_atom("place"), atom("drawer_open"))
    m = Monitor(spec)
    assert m.step({"approach"}) is Verdict.PENDING
    assert m.step({"drawer_open"}) is Verdict.SATISFIED
    m2 = Monitor(spec)
    assert m2.step({"approach"}) is Verdict.PENDING
    assert m2.step({"place"}) is Verdict.VIOLATED  # placed while the drawer was closed


def test_lift_requires_stable_grasp() -> None:
    spec = Always(implies("lift_cmd", "grasp_stable"))
    m = Monitor(spec)
    assert m.step({"approach"}) is Verdict.PENDING
    assert m.step({"grasp_stable"}) is Verdict.PENDING
    assert m.step({"lift_cmd", "grasp_stable"}) is Verdict.PENDING
    assert m.step({"lift_cmd"}) is Verdict.VIOLATED  # lifting without a stable grasp
    assert m.step({"grasp_stable"}) is Verdict.VIOLATED  # violations are permanent
    assert m.finish() is False


def test_release_within_deadline() -> None:
    spec = EventuallyWithin(3, atom("released"))
    m = Monitor(spec)
    for _ in range(3):
        assert m.step(set()) is Verdict.PENDING
    assert m.step(set()) is Verdict.VIOLATED  # 4th step (index 3) was the last chance

    m2 = Monitor(spec)
    m2.step(set())
    m2.step({"released"})
    assert m2.verdict() is Verdict.SATISFIED


def test_never_enter_zone() -> None:
    m = Monitor(never("in_forbidden_zone"))
    for _ in range(100):
        assert m.step({"moving"}) is Verdict.PENDING
    assert m.step({"in_forbidden_zone"}) is Verdict.VIOLATED


# ----------------------------- resource bound -------------------------------- #


def test_residual_size_is_bounded() -> None:
    """Monitor memory is a function of the spec, not of the trace length."""
    spec = Always(Or(not_atom(A), Next(atom(B))))  # G (a -> X b)
    rng = random.Random(0)
    m = Monitor(spec)
    worst = size(spec)
    for _ in range(5000):
        label = {x for x in (A, B) if rng.random() < 0.5}
        if m.step(label) is Verdict.VIOLATED:
            m.reset()  # restart after a violation so we keep exploring states
        worst = max(worst, size(m.residual))
    assert worst <= 2 * size(spec) + 4, worst


def test_progress_never_touches_user_visible_constructors_it_should_not() -> None:
    # progress on a Lit never returns a Lit: it collapses to TT/FF immediately.
    assert progress(frozenset([A]), atom(A)) == TT()
    assert progress(frozenset(), atom(A)) == FF()
    assert progress(frozenset(), not_atom(A)) == TT()
