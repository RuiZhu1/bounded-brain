/-
  BoundedBrain.Formula — syntax and reference semantics of the bounded LTLf fragment.

  Mirrors `monitor/src/bounded_brain/spec.py`. Keep the two in lockstep.

  STATUS: compiles with Lean v4.35.0 (`lake build` green). No `axiom`s. The correctness
  theorems about this semantics are in Monitor.lean (proved 2026-10-18).
-/

namespace BoundedBrain

/-- A label says which atomic propositions hold at one control step. -/
abbrev Label (AP : Type) := AP → Bool

/-- A finite trace is a list of labels (LTLf: finite-trace semantics). -/
abbrev Trace (AP : Type) := List (Label AP)

/-- The specification fragment, in negation normal form (negation only on atoms).

Every temporal operator is structural (`next`, `always`) or bounded
(`alwaysWithin`, `eventuallyWithin`, `untilWithin`): there is no unbounded search. `pending` is an
INTERNAL constructor produced by progression for strong `next`; it must never appear
in a user-written spec (see docs/04-architecture.md, "Pending"). -/
inductive Formula (AP : Type) where
  | tt : Formula AP
  | ff : Formula AP
  | lit : AP → Bool → Formula AP            -- `lit p true` = p, `lit p false` = ¬p
  | conj : Formula AP → Formula AP → Formula AP
  | disj : Formula AP → Formula AP → Formula AP
  | next : Formula AP → Formula AP          -- strong next
  | pending : Formula AP → Formula AP       -- INTERNAL: "a step exists here and φ holds at it"
  | always : Formula AP → Formula AP        -- G φ
  | alwaysWithin : Nat → Formula AP → Formula AP        -- G[0,k] φ
  | eventuallyWithin : Nat → Formula AP → Formula AP    -- F[0,k] φ
  | untilWithin : Nat → Formula AP → Formula AP → Formula AP  -- φ U[0,k] ψ (strong)
  deriving DecidableEq  -- the simplifiers remove repeated conjuncts and disjuncts (D-030)

/-- Number of nodes; memory proxy for the monitor state. -/
def Formula.size {AP : Type} : Formula AP → Nat
  | .tt => 1
  | .ff => 1
  | .lit _ _ => 1
  | .conj φ ψ => 1 + φ.size + ψ.size
  | .disj φ ψ => 1 + φ.size + ψ.size
  | .next φ => 1 + φ.size
  | .pending φ => 1 + φ.size
  | .always φ => 1 + φ.size
  | .alwaysWithin _ φ => 1 + φ.size
  | .eventuallyWithin _ φ => 1 + φ.size
  | .untilWithin _ φ ψ => 1 + φ.size + ψ.size

/-- Reference LTLf semantics: `Sat tr φ i` means "φ holds at position `i` of `tr`".

Positions at or beyond `tr.length` satisfy nothing that needs a step (literals, `next`,
`pending`, `eventuallyWithin`, `untilWithin`) and satisfy vacuous universals (`always`, `alwaysWithin`).
This is the oracle the monitor is proven against; it mirrors `spec.holds` in Python. -/
def Sat {AP : Type} (tr : Trace AP) : Formula AP → Nat → Prop
  | .tt, _ => True
  | .ff, _ => False
  | .lit p b, i => ∃ l, tr[i]? = some l ∧ l p = b
  | .conj φ ψ, i => Sat tr φ i ∧ Sat tr ψ i
  | .disj φ ψ, i => Sat tr φ i ∨ Sat tr ψ i
  | .next φ, i => i + 1 < tr.length ∧ Sat tr φ (i + 1)
  | .pending φ, i => i < tr.length ∧ Sat tr φ i
  | .always φ, i => ∀ j, i ≤ j → j < tr.length → Sat tr φ j
  | .alwaysWithin k φ, i => ∀ j, i ≤ j → j ≤ i + k → j < tr.length → Sat tr φ j
  | .eventuallyWithin k φ, i => ∃ j, i ≤ j ∧ j ≤ i + k ∧ j < tr.length ∧ Sat tr φ j
  | .untilWithin k φ ψ, i =>
      ∃ j, i ≤ j ∧ j ≤ i + k ∧ j < tr.length ∧ Sat tr ψ j ∧ ∀ m, i ≤ m → m < j → Sat tr φ m

end BoundedBrain
