import Lean
import BoundedBrain

/-!
  Checks run by CI after `lake build` (`lake env lean Checks.lean`). Each fails the run with an error.

  1. The main theorems still have the statements the project states in README.md and docs/08.
     A change to one of these statements must be deliberate: update this file in the same change.
  2. No declaration in the `BoundedBrain` namespace depends on an axiom other than Lean's standard three
     (`propext`, `Classical.choice`, `Quot.sound`). In particular no `sorryAx`, which every `sorry`
     introduces, and no project-specific `axiom`.
-/

open BoundedBrain

/-! ## 1. Statements of the main theorems

Since 2026-10-23 (D-030) the monitor needs `[DecidableEq AP]`: the simplifiers remove repeated conjuncts and
disjuncts, which compares formulas. The statements are otherwise unchanged. -/

/-- Main theorem: the monitor accepts exactly the traces that satisfy the spec. -/
example {AP : Type} [DecidableEq AP] (φ : Formula AP) (tr : Trace AP) :
    accepts φ tr = true ↔ Sat tr φ 0 :=
  accepts_iff_sat φ tr

/-- An early VIOLATED verdict holds for every continuation of the trace. -/
example {AP : Type} [DecidableEq AP] (φ : Formula AP) (tr ext : Trace AP) (h : run φ tr = .ff) :
    ¬ Sat (tr ++ ext) φ 0 :=
  violated_sound φ tr ext h

/-- An early SATISFIED verdict holds for every continuation of the trace. -/
example {AP : Type} [DecidableEq AP] (φ : Formula AP) (tr ext : Trace AP) (h : run φ tr = .tt) :
    Sat (tr ++ ext) φ 0 :=
  satisfied_sound φ tr ext h

/-- Without unbounded `always`, a verdict is reached after `verdictDepth φ` steps. -/
example {AP : Type} [DecidableEq AP] (φ : Formula AP) (hφ : φ.alwaysFree = true) (tr : Trace AP)
    (h : φ.verdictDepth ≤ tr.length) : run φ tr = .tt ∨ run φ tr = .ff :=
  bounded_verdict φ hφ tr h

/-- ... and that verdict is final and correct for every continuation. -/
example {AP : Type} [DecidableEq AP] (φ : Formula AP) (hφ : φ.alwaysFree = true) (tr ext : Trace AP)
    (h : φ.verdictDepth ≤ tr.length) : Sat (tr ++ ext) φ 0 ↔ run φ tr = .tt :=
  verdict_final φ hφ tr ext h

/-- The size of the monitor state is bounded by a number that depends on the spec alone (P3-5). -/
example {AP : Type} [DecidableEq AP] (φ : Formula AP) (tr : Trace AP) :
    (run φ tr).size ≤ resBound φ :=
  size_run_le φ tr

/-! ## 2. Axioms -/

open Lean Elab Command in
/-- Fails unless every declaration in `BoundedBrain` uses only Lean's standard axioms. -/
elab "#assert_standard_axioms" : command => do
  let allowed : List Name := [``propext, ``Classical.choice, ``Quot.sound]
  let mut checked : Nat := 0
  for (name, _) in (← getEnv).constants.map₁.toList do
    if (`BoundedBrain).isPrefixOf name then
      for ax in ← collectAxioms name do
        unless allowed.contains ax do
          throwError m!"{name} depends on the axiom {ax}"
      checked := checked + 1
  if checked < 50 then
    throwError m!"only {checked} declarations found in BoundedBrain; is the library imported?"
  logInfo m!"{checked} declarations in BoundedBrain use only propext, Classical.choice, Quot.sound"

#assert_standard_axioms
