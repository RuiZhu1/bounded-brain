import BoundedBrain.Monitor

/-
  BoundedBrain.BoundedVerdict — the monitor decides every `always`-free spec within a bounded
  number of steps (TODO P3-8).

  For a formula without the unbounded `always`, define its verdict depth `d φ`
  (`Formula.verdictDepth`; mirrors `verdict_depth` in monitor/tests/test_bounded_verdict.py):

      d tt = d ff = d (lit p b) = 1            d (next φ) = 1 + d φ        d (pending φ) = d φ
      d (G[0,k] φ) = d (F[0,k] φ) = k + d φ    d (φ ∧ ψ) = d (φ ∨ ψ) = max (d φ) (d ψ)

  `bounded_verdict`: after any `d φ` steps the residual is `tt` or `ff`.
  `verdict_final`: that verdict is then final and correct for every continuation of the trace.

  In course terms (docs/05-course-mapping.md): the time to a definite verdict is a bounded
  minimization, bounded by `d φ`; these are the specs "decidable within a finite horizon" (F32).

  STATUS (2026-10-18): proved, no `sorry`; only Lean's standard axioms.
-/

namespace BoundedBrain

/-- No unbounded `always` anywhere in the formula. -/
def Formula.alwaysFree {AP : Type} : Formula AP → Bool
  | .tt | .ff | .lit _ _ => true
  | .conj φ ψ | .disj φ ψ => φ.alwaysFree && ψ.alwaysFree
  | .next φ | .pending φ => φ.alwaysFree
  | .always _ => false
  | .alwaysWithin _ φ | .eventuallyWithin _ φ => φ.alwaysFree

/-- Verdict depth `d φ` (see the file header). The `always` case is never used: `bounded_verdict`
requires `alwaysFree`. -/
def Formula.verdictDepth {AP : Type} : Formula AP → Nat
  | .tt | .ff | .lit _ _ => 1
  | .conj φ ψ | .disj φ ψ => max φ.verdictDepth ψ.verdictDepth
  | .next φ => 1 + φ.verdictDepth
  | .pending φ => φ.verdictDepth
  | .always φ => φ.verdictDepth
  | .alwaysWithin k φ | .eventuallyWithin k φ => k + φ.verdictDepth

/-- Every formula needs at least one step for a verdict. -/
theorem Formula.one_le_verdictDepth {AP : Type} (φ : Formula AP) : 1 ≤ φ.verdictDepth := by
  induction φ <;> simp [Formula.verdictDepth] <;> omega

/-! Absorption laws of the simplifiers, valid for every argument (not only constructors). -/

@[simp] theorem simpAnd_ff_left {AP : Type} (x : Formula AP) : simpAnd .ff x = .ff := rfl
@[simp] theorem simpAnd_ff_right {AP : Type} (x : Formula AP) : simpAnd x .ff = .ff := by cases x <;> rfl
@[simp] theorem simpAnd_tt_left {AP : Type} (x : Formula AP) : simpAnd .tt x = x := by cases x <;> rfl
@[simp] theorem simpAnd_tt_right {AP : Type} (x : Formula AP) : simpAnd x .tt = x := by cases x <;> rfl
@[simp] theorem simpOr_tt_left {AP : Type} (x : Formula AP) : simpOr .tt x = .tt := rfl
@[simp] theorem simpOr_tt_right {AP : Type} (x : Formula AP) : simpOr x .tt = .tt := by cases x <;> rfl
@[simp] theorem simpOr_ff_left {AP : Type} (x : Formula AP) : simpOr .ff x = x := by cases x <;> rfl
@[simp] theorem simpOr_ff_right {AP : Type} (x : Formula AP) : simpOr x .ff = x := by cases x <;> rfl

/-- Progression commutes with the conjunction simplifier. -/
theorem progress_simpAnd {AP : Type} (σ : Label AP) (a b : Formula AP) :
    progress σ (simpAnd a b) = simpAnd (progress σ a) (progress σ b) := by
  cases a <;> cases b <;>
    (try simp only [progress, simpAnd_tt_left, simpAnd_tt_right, simpAnd_ff_left, simpAnd_ff_right]) <;> rfl

/-- Progression commutes with the disjunction simplifier. -/
theorem progress_simpOr {AP : Type} (σ : Label AP) (a b : Formula AP) :
    progress σ (simpOr a b) = simpOr (progress σ a) (progress σ b) := by
  cases a <;> cases b <;>
    (try simp only [progress, simpOr_tt_left, simpOr_tt_right, simpOr_ff_left, simpOr_ff_right]) <;> rfl

/-- The monitor runs the two sides of a simplified conjunction independently. -/
theorem run_simpAnd {AP : Type} (a b : Formula AP) (tr : Trace AP) :
    run (simpAnd a b) tr = simpAnd (run a tr) (run b tr) := by
  induction tr generalizing a b with
  | nil => rfl
  | cons σ tr ih => rw [run_cons, run_cons, run_cons, progress_simpAnd, ih]

/-- The monitor runs the two sides of a simplified disjunction independently. -/
theorem run_simpOr {AP : Type} (a b : Formula AP) (tr : Trace AP) :
    run (simpOr a b) tr = simpOr (run a tr) (run b tr) := by
  induction tr generalizing a b with
  | nil => rfl
  | cons σ tr ih => rw [run_cons, run_cons, run_cons, progress_simpOr, ih]

/-- A residual that is a definite verdict. -/
abbrev IsVerdict {AP : Type} (f : Formula AP) : Prop := f = .tt ∨ f = .ff

/-- Definite verdicts are closed under the simplifiers. -/
theorem simpAnd_isVerdict {AP : Type} {a b : Formula AP} (ha : IsVerdict a) (hb : IsVerdict b) :
    IsVerdict (simpAnd a b) := by
  rcases ha with rfl | rfl <;> rcases hb with rfl | rfl <;> simp [IsVerdict]

theorem simpOr_isVerdict {AP : Type} {a b : Formula AP} (ha : IsVerdict a) (hb : IsVerdict b) :
    IsVerdict (simpOr a b) := by
  rcases ha with rfl | rfl <;> rcases hb with rfl | rfl <;> simp [IsVerdict]

/-- [P3-8] Bounded verdict: without unbounded `always`, the monitor reaches `tt` or `ff` after at most
`φ.verdictDepth` steps. -/
theorem bounded_verdict {AP : Type} (φ : Formula AP) (hφ : φ.alwaysFree = true) (tr : Trace AP)
    (h : φ.verdictDepth ≤ tr.length) : IsVerdict (run φ tr) := by
  induction φ generalizing tr with
  | tt => exact Or.inl (run_tt tr)
  | ff => exact Or.inr (run_ff tr)
  | lit p b =>
    cases tr with
    | nil => simp [Formula.verdictDepth] at h
    | cons σ rest =>
      rw [run_cons]
      simp only [progress]
      split
      · exact Or.inl (run_tt rest)
      · exact Or.inr (run_ff rest)
  | conj a b iha ihb =>
    simp only [Formula.alwaysFree, Bool.and_eq_true] at hφ
    simp only [Formula.verdictDepth] at h
    cases tr with
    | nil => have := a.one_le_verdictDepth; simp at h <;> omega
    | cons σ rest =>
      have ha := iha hφ.1 (σ :: rest) (by omega)
      have hb := ihb hφ.2 (σ :: rest) (by omega)
      rw [run_cons]
      simp only [progress]
      rw [run_simpAnd, ← run_cons, ← run_cons]
      exact simpAnd_isVerdict ha hb
  | disj a b iha ihb =>
    simp only [Formula.alwaysFree, Bool.and_eq_true] at hφ
    simp only [Formula.verdictDepth] at h
    cases tr with
    | nil => have := a.one_le_verdictDepth; simp at h <;> omega
    | cons σ rest =>
      have ha := iha hφ.1 (σ :: rest) (by omega)
      have hb := ihb hφ.2 (σ :: rest) (by omega)
      rw [run_cons]
      simp only [progress]
      rw [run_simpOr, ← run_cons, ← run_cons]
      exact simpOr_isVerdict ha hb
  | next φ ih =>
    simp only [Formula.alwaysFree] at hφ
    simp only [Formula.verdictDepth] at h
    have := φ.one_le_verdictDepth
    match tr with
    | [] => simp at h <;> omega
    | [_] => simp at h <;> omega
    | σ :: σ' :: rest =>
      rw [run_cons]
      simp only [progress]
      rw [run_cons]
      simp only [progress]
      rw [← run_cons]
      exact ih hφ (σ' :: rest) (by simp at h ⊢; omega)
  | pending φ ih =>
    simp only [Formula.alwaysFree] at hφ
    simp only [Formula.verdictDepth] at h
    have := φ.one_le_verdictDepth
    cases tr with
    | nil => simp at h <;> omega
    | cons σ rest =>
      rw [run_cons]
      simp only [progress]
      rw [← run_cons]
      exact ih hφ (σ :: rest) h
  | always φ ih => simp [Formula.alwaysFree] at hφ
  | alwaysWithin k φ ih =>
    simp only [Formula.alwaysFree] at hφ
    have := φ.one_le_verdictDepth
    induction k generalizing tr with
    | zero =>
      simp only [Formula.verdictDepth] at h
      cases tr with
      | nil => simp at h <;> omega
      | cons σ rest =>
        rw [run_cons]
        simp only [progress]
        rw [← run_cons]
        exact ih hφ (σ :: rest) (by omega)
    | succ k ihk =>
      simp only [Formula.verdictDepth] at h ihk
      cases tr with
      | nil => simp at h <;> omega
      | cons σ rest =>
        rw [run_cons]
        simp only [progress]
        rw [run_simpAnd, ← run_cons]
        exact simpAnd_isVerdict (ih hφ (σ :: rest) (by omega)) (ihk rest (by simp at h <;> omega))
  | eventuallyWithin k φ ih =>
    simp only [Formula.alwaysFree] at hφ
    have := φ.one_le_verdictDepth
    induction k generalizing tr with
    | zero =>
      simp only [Formula.verdictDepth] at h
      cases tr with
      | nil => simp at h <;> omega
      | cons σ rest =>
        rw [run_cons]
        simp only [progress]
        rw [← run_cons]
        exact ih hφ (σ :: rest) (by omega)
    | succ k ihk =>
      simp only [Formula.verdictDepth] at h ihk
      cases tr with
      | nil => simp at h <;> omega
      | cons σ rest =>
        rw [run_cons]
        simp only [progress]
        rw [run_simpOr, ← run_cons]
        exact simpOr_isVerdict (ih hφ (σ :: rest) (by omega)) (ihk rest (by simp at h <;> omega))

/-- [P3-8] After `d φ` steps the verdict is final: the trace satisfies `φ` however it continues
exactly when the residual is `tt`. -/
theorem verdict_final {AP : Type} (φ : Formula AP) (hφ : φ.alwaysFree = true) (tr ext : Trace AP)
    (h : φ.verdictDepth ≤ tr.length) : Sat (tr ++ ext) φ 0 ↔ run φ tr = .tt := by
  rcases bounded_verdict φ hφ tr h with htt | hff
  · exact ⟨fun _ => htt, fun _ => satisfied_sound φ tr ext htt⟩
  · exact ⟨fun hs => absurd hs (violated_sound φ tr ext hff), fun ht => by rw [hff] at ht; cases ht⟩

end BoundedBrain
