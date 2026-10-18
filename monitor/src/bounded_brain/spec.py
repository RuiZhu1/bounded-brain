"""Specification language: a bounded LTLf fragment in negation normal form.

Design rules (see docs/04-architecture.md):

* Finite-trace semantics (LTLf). A *trace* is a finite sequence of *labels*; a
  label is the set of atomic propositions that hold at one control step.
* Negation only on atoms (`Lit(name, positive=False)`), so formulas are in NNF.
* Every temporal operator is either structural (`Next`, `Always`) or *bounded*
  (`AlwaysWithin`, `EventuallyWithin`). There is no unbounded search anywhere.
  This mirrors bounded quantification / bounded minimisation from the course
  (see docs/05-course-mapping.md) and keeps monitor cost statically known.
* `Pending` is an INTERNAL constructor produced by progression. Never write it
  in a hand-written spec. It exists because strong `Next` needs an explicit
  "a successor step must exist" obligation; naive progression (Next f -> f)
  is WRONG at the end of a trace. See docs/04-architecture.md, "Pending".

The Lean mirror of this file is lean/BoundedBrain/Formula.lean. Keep the two in
lockstep (constructor names, semantics, simplification rules).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, FrozenSet, Sequence, Union

Label = FrozenSet[str]
Trace = Sequence[Label]


@dataclass(frozen=True)
class TT:
    """Always true."""


@dataclass(frozen=True)
class FF:
    """Always false."""


@dataclass(frozen=True)
class Lit:
    """An atomic proposition (or its negation) evaluated at the current step."""

    name: str
    positive: bool = True


@dataclass(frozen=True)
class And:
    left: "Formula"
    right: "Formula"


@dataclass(frozen=True)
class Or:
    left: "Formula"
    right: "Formula"


@dataclass(frozen=True)
class Next:
    """Strong next: a next step must exist and `arg` must hold there."""

    arg: "Formula"


@dataclass(frozen=True)
class Pending:
    """INTERNAL: 'a step exists here, and `arg` holds at it'. Not for user specs."""

    arg: "Formula"


@dataclass(frozen=True)
class Always:
    """G arg: `arg` holds at every remaining step (vacuously true if none)."""

    arg: "Formula"


@dataclass(frozen=True)
class AlwaysWithin:
    """G[0,bound] arg: `arg` holds at every remaining step among the next bound+1."""

    bound: int
    arg: "Formula"

    def __post_init__(self) -> None:
        if self.bound < 0:
            raise ValueError("bound must be >= 0")


@dataclass(frozen=True)
class EventuallyWithin:
    """F[0,bound] arg: `arg` holds at some remaining step among the next bound+1."""

    bound: int
    arg: "Formula"

    def __post_init__(self) -> None:
        if self.bound < 0:
            raise ValueError("bound must be >= 0")


Formula = Union[TT, FF, Lit, And, Or, Next, Pending, Always, AlwaysWithin, EventuallyWithin]


# --------------------------------------------------------------------------- #
# Convenience constructors (user-facing; all stay inside the fragment)
# --------------------------------------------------------------------------- #


def atom(name: str) -> Lit:
    return Lit(name, True)


def not_atom(name: str) -> Lit:
    return Lit(name, False)


def implies(antecedent: str, consequent: str) -> Or:
    """Step-local implication between two atoms: (not a) or b."""
    return Or(not_atom(antecedent), atom(consequent))


def never(name: str) -> Always:
    """G (not name)."""
    return Always(not_atom(name))


def conj(*formulas: Formula) -> Formula:
    if not formulas:
        return TT()
    result = formulas[0]
    for f in formulas[1:]:
        result = And(result, f)
    return result


def disj(*formulas: Formula) -> Formula:
    if not formulas:
        return FF()
    result = formulas[0]
    for f in formulas[1:]:
        result = Or(result, f)
    return result


# --------------------------------------------------------------------------- #
# Reference semantics (the specification the monitor must agree with)
# --------------------------------------------------------------------------- #


def holds(trace: Trace, i: int, phi: Formula) -> bool:
    """Direct LTLf semantics: does `phi` hold at position `i` of the finite `trace`?

    Positions at or beyond len(trace) satisfy nothing that needs a step
    (literals, Next, Pending, EventuallyWithin) and satisfy vacuous universals
    (Always, AlwaysWithin). Deliberately naive and slow: this is the oracle.
    """
    n = len(trace)
    if isinstance(phi, TT):
        return True
    if isinstance(phi, FF):
        return False
    if isinstance(phi, Lit):
        return i < n and ((phi.name in trace[i]) == phi.positive)
    if isinstance(phi, And):
        return holds(trace, i, phi.left) and holds(trace, i, phi.right)
    if isinstance(phi, Or):
        return holds(trace, i, phi.left) or holds(trace, i, phi.right)
    if isinstance(phi, Next):
        return i + 1 < n and holds(trace, i + 1, phi.arg)
    if isinstance(phi, Pending):
        return i < n and holds(trace, i, phi.arg)
    if isinstance(phi, Always):
        return all(holds(trace, j, phi.arg) for j in range(i, n))
    if isinstance(phi, AlwaysWithin):
        return all(holds(trace, j, phi.arg) for j in range(i, min(i + phi.bound, n - 1) + 1))
    if isinstance(phi, EventuallyWithin):
        return any(holds(trace, j, phi.arg) for j in range(i, min(i + phi.bound, n - 1) + 1))
    raise TypeError(f"not a formula: {phi!r}")


# --------------------------------------------------------------------------- #
# JSON-friendly interchange form (used for Lean <-> Python differential tests)
# --------------------------------------------------------------------------- #


def to_dict(phi: Formula) -> Dict[str, Any]:
    if isinstance(phi, TT):
        return {"op": "tt"}
    if isinstance(phi, FF):
        return {"op": "ff"}
    if isinstance(phi, Lit):
        return {"op": "lit", "name": phi.name, "positive": phi.positive}
    if isinstance(phi, And):
        return {"op": "and", "left": to_dict(phi.left), "right": to_dict(phi.right)}
    if isinstance(phi, Or):
        return {"op": "or", "left": to_dict(phi.left), "right": to_dict(phi.right)}
    if isinstance(phi, Next):
        return {"op": "next", "arg": to_dict(phi.arg)}
    if isinstance(phi, Pending):
        return {"op": "pending", "arg": to_dict(phi.arg)}
    if isinstance(phi, Always):
        return {"op": "always", "arg": to_dict(phi.arg)}
    if isinstance(phi, AlwaysWithin):
        return {"op": "always_within", "bound": phi.bound, "arg": to_dict(phi.arg)}
    if isinstance(phi, EventuallyWithin):
        return {"op": "eventually_within", "bound": phi.bound, "arg": to_dict(phi.arg)}
    raise TypeError(f"not a formula: {phi!r}")


def from_dict(data: Dict[str, Any], *, allow_internal: bool = False) -> Formula:
    """Inverse of `to_dict`. `pending` is rejected unless `allow_internal=True`."""
    op = data["op"]
    if op == "tt":
        return TT()
    if op == "ff":
        return FF()
    if op == "lit":
        return Lit(data["name"], bool(data.get("positive", True)))
    if op == "and":
        return And(
            from_dict(data["left"], allow_internal=allow_internal),
            from_dict(data["right"], allow_internal=allow_internal),
        )
    if op == "or":
        return Or(
            from_dict(data["left"], allow_internal=allow_internal),
            from_dict(data["right"], allow_internal=allow_internal),
        )
    if op == "next":
        return Next(from_dict(data["arg"], allow_internal=allow_internal))
    if op == "pending":
        if not allow_internal:
            raise ValueError("'pending' is internal and not allowed in user specs")
        return Pending(from_dict(data["arg"], allow_internal=allow_internal))
    if op == "always":
        return Always(from_dict(data["arg"], allow_internal=allow_internal))
    if op == "always_within":
        return AlwaysWithin(int(data["bound"]), from_dict(data["arg"], allow_internal=allow_internal))
    if op == "eventually_within":
        return EventuallyWithin(int(data["bound"]), from_dict(data["arg"], allow_internal=allow_internal))
    raise ValueError(f"unknown op: {op!r}")
