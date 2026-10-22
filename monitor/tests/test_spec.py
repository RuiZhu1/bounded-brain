from __future__ import annotations

import pytest

from bounded_brain import (
    TT,
    Always,
    AlwaysWithin,
    EventuallyWithin,
    Next,
    Or,
    Pending,
    UntilWithin,
    atom,
    conj,
    disj,
    from_dict,
    holds,
    implies,
    not_atom,
    to_dict,
)


def test_roundtrip_user_formulas() -> None:
    phi = conj(
        Always(implies("lift_cmd", "grasp_stable")),
        EventuallyWithin(10, atom("released")),
        AlwaysWithin(3, not_atom("collision")),
        Next(Or(atom("a"), not_atom("b"))),
        UntilWithin(5, not_atom("place"), atom("drawer_open")),
    )
    assert from_dict(to_dict(phi)) == phi
    assert to_dict(UntilWithin(2, atom("a"), atom("b"))) == {
        "op": "until_within", "bound": 2,
        "left": {"op": "lit", "name": "a", "positive": True},
        "right": {"op": "lit", "name": "b", "positive": True},
    }


def test_internal_constructor_is_rejected_in_user_specs() -> None:
    data = to_dict(Pending(atom("a")))
    with pytest.raises(ValueError):
        from_dict(data)
    assert from_dict(data, allow_internal=True) == Pending(atom("a"))


def test_unknown_op_rejected() -> None:
    with pytest.raises(ValueError):
        from_dict({"op": "until"})


def test_empty_conj_and_disj() -> None:
    assert holds([], 0, conj()) is True
    assert holds([], 0, disj()) is False
    assert conj() == TT()


def test_oracle_basic_cases() -> None:
    t = [frozenset({"a"}), frozenset(), frozenset({"a"})]
    assert holds(t, 0, atom("a"))
    assert not holds(t, 1, atom("a"))
    assert holds(t, 0, Next(not_atom("a")))
    assert not holds(t, 2, Next(atom("a")))  # no step after the last one
    assert not holds(t, 0, Always(atom("a")))
    assert holds(t, 0, EventuallyWithin(2, atom("a")))
    assert holds(t, 1, EventuallyWithin(1, atom("a")))
    assert not holds(t, 1, EventuallyWithin(0, atom("a")))
