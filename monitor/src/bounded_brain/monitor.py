"""Progression-based runtime monitor for the bounded LTLf fragment in spec.py.

Idea (Bacchus & Kabanza-style formula progression, adapted to LTLf): after
consuming one step `sigma`, rewrite the formula into the *residual obligation*
on the rest of the trace. The monitor state is just that residual formula.

Properties we want (and will prove in Lean, see lean/BoundedBrain/Monitor.lean):

  1. Correctness at end of trace:
       accepts(phi, trace)  <=>  holds(trace, 0, phi)
  2. Early verdicts are sound:
       residual == FF  =>  every extension of the prefix violates phi
       residual == TT  =>  every extension of the prefix satisfies phi
     (NOT claimed complete: a residual may be unsatisfiable without having
      been simplified to FF. See docs/04-architecture.md.)
  3. `step` is a total function that always terminates (structural recursion on
     the formula; bounded operators count down). Repeated conjuncts and disjuncts
     are removed (D-030), which keeps residuals from growing with the trace, also
     with nested `Always`; a proved bound is still open (TODO P3-5).

The simplification rules here must be IDENTICAL to the Lean ones (TT/FF
absorption, flattening, and removal of repeated conjuncts and disjuncts keeping
the last occurrence) so the two stay in lockstep.
"""

from __future__ import annotations

from enum import Enum
from typing import Iterable, List, Optional

from .spec import (
    FF,
    TT,
    And,
    Always,
    AlwaysWithin,
    EventuallyWithin,
    Formula,
    Label,
    Lit,
    Next,
    Or,
    Pending,
    Trace,
    UntilWithin,
)


class Verdict(Enum):
    VIOLATED = "violated"  # every extension of the observed prefix violates the spec
    SATISFIED = "satisfied"  # every extension of the observed prefix satisfies the spec
    PENDING = "pending"  # undecided so far


def conjuncts(phi: Formula) -> List[Formula]:
    """The conjunction tree of `phi` flattened, left to right; TT contributes nothing (Lean `Formula.conjuncts`)."""
    if isinstance(phi, TT):
        return []
    if isinstance(phi, And):
        return conjuncts(phi.left) + conjuncts(phi.right)
    return [phi]


def disjuncts(phi: Formula) -> List[Formula]:
    """The disjunction tree of `phi` flattened, left to right; FF contributes nothing (Lean `Formula.disjuncts`)."""
    if isinstance(phi, FF):
        return []
    if isinstance(phi, Or):
        return disjuncts(phi.left) + disjuncts(phi.right)
    return [phi]


def dedup_last(items: List[Formula]) -> List[Formula]:
    """Drop every element that occurs again later in the list, keeping the last occurrence (Lean `dedupLast`)."""
    return [x for i, x in enumerate(items) if x not in items[i + 1:]]


def _right_nested(cls, items: List[Formula]) -> Formula:
    return items[0] if len(items) == 1 else cls(items[0], _right_nested(cls, items[1:]))


def norm_and(items: List[Formula]) -> Formula:
    """FF if one item is FF, else the right-nested conjunction of the items without repetitions (Lean `normAnd`)."""
    if any(isinstance(x, FF) for x in items):
        return FF()
    kept = dedup_last(items)
    return _right_nested(And, kept) if kept else TT()


def norm_or(items: List[Formula]) -> Formula:
    """TT if one item is TT, else the right-nested disjunction of the items without repetitions (Lean `normOr`)."""
    if any(isinstance(x, TT) for x in items):
        return TT()
    kept = dedup_last(items)
    return _right_nested(Or, kept) if kept else FF()


def simp_and(a: Formula, b: Formula) -> Formula:
    """Conjunction with TT/FF absorption, flattening and removal of repeated conjuncts (Lean `simpAnd`, D-030)."""
    return norm_and(conjuncts(a) + conjuncts(b))


def simp_or(a: Formula, b: Formula) -> Formula:
    """Disjunction with TT/FF absorption, flattening and removal of repeated disjuncts (Lean `simpOr`, D-030)."""
    return norm_or(disjuncts(a) + disjuncts(b))


def progress(label: Label, phi: Formula) -> Formula:
    """Residual obligation on the rest of the trace after consuming one step."""
    if isinstance(phi, (TT, FF)):
        return phi
    if isinstance(phi, Lit):
        return TT() if ((phi.name in label) == phi.positive) else FF()
    if isinstance(phi, And):
        return simp_and(progress(label, phi.left), progress(label, phi.right))
    if isinstance(phi, Or):
        return simp_or(progress(label, phi.left), progress(label, phi.right))
    if isinstance(phi, Next):
        return Pending(phi.arg)  # a successor step must exist; arg is checked there
    if isinstance(phi, Pending):
        return progress(label, phi.arg)  # the required step exists: it is `label`
    if isinstance(phi, Always):
        return simp_and(progress(label, phi.arg), phi)
    if isinstance(phi, AlwaysWithin):
        if phi.bound == 0:
            return progress(label, phi.arg)
        return simp_and(progress(label, phi.arg), AlwaysWithin(phi.bound - 1, phi.arg))
    if isinstance(phi, EventuallyWithin):
        if phi.bound == 0:
            return progress(label, phi.arg)
        return simp_or(progress(label, phi.arg), EventuallyWithin(phi.bound - 1, phi.arg))
    if isinstance(phi, UntilWithin):
        if phi.bound == 0:
            return progress(label, phi.right)
        return simp_or(
            progress(label, phi.right),
            simp_and(progress(label, phi.left), UntilWithin(phi.bound - 1, phi.left, phi.right)),
        )
    raise TypeError(f"not a formula: {phi!r}")


def accepts_empty(phi: Formula) -> bool:
    """Does the residual `phi` hold on the empty remaining trace? (LTLf end-of-trace.)"""
    if isinstance(phi, TT):
        return True
    if isinstance(phi, FF):
        return False
    if isinstance(phi, Lit):
        return False
    if isinstance(phi, And):
        return accepts_empty(phi.left) and accepts_empty(phi.right)
    if isinstance(phi, Or):
        return accepts_empty(phi.left) or accepts_empty(phi.right)
    if isinstance(phi, (Next, Pending)):
        return False
    if isinstance(phi, (Always, AlwaysWithin)):
        return True
    if isinstance(phi, (EventuallyWithin, UntilWithin)):
        return False
    raise TypeError(f"not a formula: {phi!r}")


def verdict_of(phi: Formula) -> Verdict:
    if isinstance(phi, FF):
        return Verdict.VIOLATED
    if isinstance(phi, TT):
        return Verdict.SATISFIED
    return Verdict.PENDING


def size(phi: Formula) -> int:
    """Number of nodes; the memory proxy for the monitor state."""
    if isinstance(phi, (TT, FF, Lit)):
        return 1
    if isinstance(phi, (And, Or, UntilWithin)):
        return 1 + size(phi.left) + size(phi.right)
    return 1 + size(phi.arg)  # Next, Pending, Always, AlwaysWithin, EventuallyWithin


def run(phi: Formula, trace: Trace) -> Formula:
    """Fold `progress` over a whole trace; returns the final residual."""
    residual = phi
    for label in trace:
        residual = progress(label, residual)
    return residual


def accepts(phi: Formula, trace: Trace) -> bool:
    """Monitor's end-of-trace answer. Must equal `spec.holds(trace, 0, phi)`."""
    return accepts_empty(run(phi, trace))


class Monitor:
    """Stateful wrapper for online use: feed one label per control step."""

    def __init__(self, spec: Formula) -> None:
        self._spec = spec
        self._residual: Formula = spec
        self._steps = 0

    @property
    def residual(self) -> Formula:
        return self._residual

    @property
    def steps(self) -> int:
        return self._steps

    def step(self, label: Iterable[str]) -> Verdict:
        self._residual = progress(frozenset(label), self._residual)
        self._steps += 1
        return verdict_of(self._residual)

    def verdict(self) -> Verdict:
        return verdict_of(self._residual)

    def finish(self) -> bool:
        """Declare the trace over; exact LTLf answer for the steps seen."""
        return accepts_empty(self._residual)

    def reset(self, spec: Optional[Formula] = None) -> None:
        if spec is not None:
            self._spec = spec
        self._residual = self._spec
        self._steps = 0
