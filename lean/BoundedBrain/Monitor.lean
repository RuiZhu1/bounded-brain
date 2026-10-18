import BoundedBrain.Formula

/-
  BoundedBrain.Monitor — progression-based monitor and its correctness theorems.

  Mirrors `monitor/src/bounded_brain/monitor.py` (same simplification rules: only
  TT/FF absorption, NO deduplication).

  STATUS (2026-10-18): compiles with Lean v4.35.0; the correctness theorems (TODO P3-2,
  P3-3, P3-4) are proved, with no `sorry`. Open: the resource bound (P3-5) and the
  bounded-verdict theorem (P3-8). Do not merge a `sorry` that is not listed in TODO.md.
-/

namespace BoundedBrain

/-- Conjunction with TT/FF absorption (order of rules matches Python `simp_and`). -/
def simpAnd {AP : Type} : Formula AP → Formula AP → Formula AP
  | .ff, _ => .ff
  | _, .ff => .ff
  | .tt, b => b
  | a, .tt => a
  | a, b => .conj a b

/-- Disjunction with TT/FF absorption (order of rules matches Python `simp_or`). -/
def simpOr {AP : Type} : Formula AP → Formula AP → Formula AP
  | .tt, _ => .tt
  | _, .tt => .tt
  | .ff, b => b
  | a, .ff => a
  | a, b => .disj a b

/-- Residual obligation on the rest of the trace after consuming one step `σ`. -/
def progress {AP : Type} (σ : Label AP) : Formula AP → Formula AP
  | .tt => .tt
  | .ff => .ff
  | .lit p b => if σ p == b then .tt else .ff
  | .conj φ ψ => simpAnd (progress σ φ) (progress σ ψ)
  | .disj φ ψ => simpOr (progress σ φ) (progress σ ψ)
  | .next φ => .pending φ                  -- a successor step must exist
  | .pending φ => progress σ φ             -- the required step exists: it is σ
  | .always φ => simpAnd (progress σ φ) (.always φ)
  | .alwaysWithin 0 φ => progress σ φ
  | .alwaysWithin (k + 1) φ => simpAnd (progress σ φ) (.alwaysWithin k φ)
  | .eventuallyWithin 0 φ => progress σ φ
  | .eventuallyWithin (k + 1) φ => simpOr (progress σ φ) (.eventuallyWithin k φ)

/-- Does the residual hold on the empty remaining trace? (LTLf end-of-trace.) -/
def acceptsEmpty {AP : Type} : Formula AP → Bool
  | .tt => true
  | .ff => false
  | .lit _ _ => false
  | .conj φ ψ => acceptsEmpty φ && acceptsEmpty ψ
  | .disj φ ψ => acceptsEmpty φ || acceptsEmpty ψ
  | .next _ => false
  | .pending _ => false
  | .always _ => true
  | .alwaysWithin _ _ => true
  | .eventuallyWithin _ _ => false

/-- Fold `progress` over a whole trace; returns the final residual. -/
def run {AP : Type} (φ : Formula AP) (tr : Trace AP) : Formula AP :=
  tr.foldl (fun f σ => progress σ f) φ

/-- The monitor's end-of-trace answer. -/
def accepts {AP : Type} (φ : Formula AP) (tr : Trace AP) : Bool :=
  acceptsEmpty (run φ tr)

/-! ## Correctness theorems

All proofs below are complete (no `sorry`). `#print axioms accepts_iff_sat` lists only Lean's standard axioms
(`propext`, `Classical.choice`, `Quot.sound`). -/

/-- [P3-2] Shifting the trace by one step shifts positions by one.
Proof: induction on `φ` (for every position `i`); the quantified cases move the witness index by one. -/
theorem sat_shift {AP : Type} (σ : Label AP) (tr : Trace AP) (φ : Formula AP) (i : Nat) :
    Sat (σ :: tr) φ (i + 1) ↔ Sat tr φ i := by
  induction φ generalizing i with
  | tt => simp [Sat]
  | ff => simp [Sat]
  | lit p b => simp [Sat]
  | conj φ ψ ihφ ihψ => simp [Sat, ihφ, ihψ]
  | disj φ ψ ihφ ihψ => simp [Sat, ihφ, ihψ]
  | next φ ih => simp [Sat, ih]
  | pending φ ih => simp [Sat, ih]
  | always φ ih =>
    simp only [Sat, List.length_cons]
    constructor
    · intro h j hij hj
      exact (ih j).mp (h (j + 1) (by omega) (by omega))
    · intro h j hij hj
      obtain ⟨j', rfl⟩ : ∃ j', j = j' + 1 := ⟨j - 1, by omega⟩
      exact (ih j').mpr (h j' (by omega) (by omega))
  | alwaysWithin k φ ih =>
    simp only [Sat, List.length_cons]
    constructor
    · intro h j hij hjk hj
      exact (ih j).mp (h (j + 1) (by omega) (by omega) (by omega))
    · intro h j hij hjk hj
      obtain ⟨j', rfl⟩ : ∃ j', j = j' + 1 := ⟨j - 1, by omega⟩
      exact (ih j').mpr (h j' (by omega) (by omega) (by omega))
  | eventuallyWithin k φ ih =>
    simp only [Sat, List.length_cons]
    constructor
    · rintro ⟨j, hij, hjk, hj, hs⟩
      obtain ⟨j', rfl⟩ : ∃ j', j = j' + 1 := ⟨j - 1, by omega⟩
      exact ⟨j', by omega, by omega, by omega, (ih j').mp hs⟩
    · rintro ⟨j, hij, hjk, hj, hs⟩
      exact ⟨j + 1, by omega, by omega, by omega, (ih j).mpr hs⟩

/-- [P3-2] Simplification preserves semantics. Proof: case split on the two arguments (100 cases, each closed
by unfolding `simpAnd` and `Sat`). -/
theorem simpAnd_sat {AP : Type} (tr : Trace AP) (a b : Formula AP) (i : Nat) :
    Sat tr (simpAnd a b) i ↔ Sat tr a i ∧ Sat tr b i := by
  cases a <;> cases b <;> simp [simpAnd, Sat]

/-- [P3-2] Same for disjunction. -/
theorem simpOr_sat {AP : Type} (tr : Trace AP) (a b : Formula AP) (i : Nat) :
    Sat tr (simpOr a b) i ↔ Sat tr a i ∨ Sat tr b i := by
  cases a <;> cases b <;> simp [simpOr, Sat]

/-- [P3-2] KEY LEMMA (one-step progression).
Consuming a step `σ` and then evaluating the residual at the start of the rest equals
evaluating the original formula at the start of `σ :: tr`.
Proof: induction on `φ`.
  * `next ψ`:   LHS = `1 < len+1 ∧ Sat (σ::tr) ψ 1`; RHS = `Sat tr (pending ψ) 0`
                = `0 < len ∧ Sat tr ψ 0`; use `sat_shift`.
  * `pending ψ`: LHS = `0 < len+1 ∧ Sat (σ::tr) ψ 0`; RHS = `Sat tr (progress σ ψ) 0`; use IH.
  * `always ψ`, `alwaysWithin (k+1) ψ`, `eventuallyWithin (k+1) ψ`: split the quantified
    index at 0 (IH) and `j + 1` (`sat_shift`); `simpAnd_sat` / `simpOr_sat` for the glue.
  * bound 0 cases reduce to IH on ψ. -/
theorem progress_sat {AP : Type} (σ : Label AP) (tr : Trace AP) (φ : Formula AP) :
    Sat (σ :: tr) φ 0 ↔ Sat tr (progress σ φ) 0 := by
  induction φ with
  | tt => simp [Sat, progress]
  | ff => simp [Sat, progress]
  | lit p b =>
    by_cases h : σ p = b
    · simp [Sat, progress, h]
    · simp [Sat, progress, h]
  | conj φ ψ ihφ ihψ => simp only [Sat, progress, simpAnd_sat, ihφ, ihψ]
  | disj φ ψ ihφ ihψ => simp only [Sat, progress, simpOr_sat, ihφ, ihψ]
  | next φ ih =>
    show (0 + 1 < (σ :: tr).length ∧ Sat (σ :: tr) φ (0 + 1)) ↔ (0 < tr.length ∧ Sat tr φ 0)
    rw [sat_shift, List.length_cons]
    exact and_congr (by omega) Iff.rfl
  | pending φ ih => simp [Sat, progress, ih]
  | always φ ih =>
    simp only [progress]
    rw [simpAnd_sat, ← ih]
    simp only [Sat, List.length_cons]
    constructor
    · intro h
      refine ⟨h 0 (by omega) (by omega), fun j _ hj => ?_⟩
      exact (sat_shift σ tr φ j).mp (h (j + 1) (by omega) (by omega))
    · rintro ⟨h0, h⟩ j _ hj
      cases j with
      | zero => exact h0
      | succ j => exact (sat_shift σ tr φ j).mpr (h j (by omega) (by omega))
  | alwaysWithin k φ ih =>
    cases k with
    | zero =>
      simp only [progress]
      rw [← ih]
      simp only [Sat, List.length_cons]
      constructor
      · intro h
        exact h 0 (by omega) (by omega) (by omega)
      · intro h j _ hj0 _
        obtain rfl : j = 0 := by omega
        exact h
    | succ k =>
      simp only [progress]
      rw [simpAnd_sat, ← ih]
      simp only [Sat, List.length_cons]
      constructor
      · intro h
        refine ⟨h 0 (by omega) (by omega) (by omega), fun j _ hjk hj => ?_⟩
        exact (sat_shift σ tr φ j).mp (h (j + 1) (by omega) (by omega) (by omega))
      · rintro ⟨h0, h⟩ j _ hjk hj
        cases j with
        | zero => exact h0
        | succ j => exact (sat_shift σ tr φ j).mpr (h j (by omega) (by omega) (by omega))
  | eventuallyWithin k φ ih =>
    cases k with
    | zero =>
      simp only [progress]
      rw [← ih]
      simp only [Sat, List.length_cons]
      constructor
      · rintro ⟨j, _, hj0, _, hs⟩
        obtain rfl : j = 0 := by omega
        exact hs
      · intro h
        exact ⟨0, by omega, by omega, by omega, h⟩
    | succ k =>
      simp only [progress]
      rw [simpOr_sat, ← ih]
      simp only [Sat, List.length_cons]
      constructor
      · rintro ⟨j, _, hjk, hj, hs⟩
        cases j with
        | zero => exact Or.inl hs
        | succ j => exact Or.inr ⟨j, by omega, by omega, by omega, (sat_shift σ tr φ j).mp hs⟩
      · rintro (h0 | ⟨j, _, hjk, hj, hs⟩)
        · exact ⟨0, by omega, by omega, by omega, h0⟩
        · exact ⟨j + 1, by omega, by omega, by omega, (sat_shift σ tr φ j).mpr hs⟩

/-- [P3-2] End-of-trace acceptance agrees with the semantics on the empty trace. -/
theorem acceptsEmpty_iff {AP : Type} (φ : Formula AP) :
    acceptsEmpty φ = true ↔ Sat ([] : Trace AP) φ 0 := by
  induction φ with
  | conj φ ψ ihφ ihψ => simp [acceptsEmpty, Sat, ihφ, ihψ]
  | disj φ ψ ihφ ihψ => simp [acceptsEmpty, Sat, ihφ, ihψ]
  | _ => simp [acceptsEmpty, Sat]

/-- One step of `run`: `run φ (σ :: tr) = run (progress σ φ) tr` (by `List.foldl_cons`). -/
theorem run_cons {AP : Type} (φ : Formula AP) (σ : Label AP) (tr : Trace AP) :
    run φ (σ :: tr) = run (progress σ φ) tr := rfl

/-- [P3-3] MAIN THEOREM: the monitor accepts exactly the traces that satisfy the spec.
Proof: induction on `tr` generalizing `φ`, using `progress_sat` and `acceptsEmpty_iff`. -/
theorem accepts_iff_sat {AP : Type} (φ : Formula AP) (tr : Trace AP) :
    accepts φ tr = true ↔ Sat tr φ 0 := by
  induction tr generalizing φ with
  | nil => exact acceptsEmpty_iff φ
  | cons σ tr ih =>
    unfold accepts
    rw [run_cons, progress_sat]
    exact ih (progress σ φ)

/-- Running over a concatenation is running over the first part, then the second. -/
theorem run_append {AP : Type} (φ : Formula AP) (tr ext : Trace AP) :
    run φ (tr ++ ext) = run (run φ tr) ext := by
  simp [run, List.foldl_append]

/-- `ff` is a fixed point of the monitor. -/
theorem run_ff {AP : Type} (ext : Trace AP) : run (.ff : Formula AP) ext = .ff := by
  induction ext with
  | nil => rfl
  | cons σ ext ih => rw [run_cons]; exact ih

/-- `tt` is a fixed point of the monitor. -/
theorem run_tt {AP : Type} (ext : Trace AP) : run (.tt : Formula AP) ext = .tt := by
  induction ext with
  | nil => rfl
  | cons σ ext ih => rw [run_cons]; exact ih

/-- [P3-4] Early VIOLATED verdict is sound: if the residual is `ff`, no extension satisfies φ.
Proof: `run φ (tr ++ ext) = run (run φ tr) ext = run .ff ext = .ff`, then `accepts_iff_sat`. -/
theorem violated_sound {AP : Type} (φ : Formula AP) (tr ext : Trace AP)
    (h : run φ tr = .ff) : ¬ Sat (tr ++ ext) φ 0 := by
  rw [← accepts_iff_sat, accepts, run_append, h, run_ff]
  simp [acceptsEmpty]

/-- [P3-4] Early SATISFIED verdict is sound: if the residual is `tt`, every extension satisfies φ. -/
theorem satisfied_sound {AP : Type} (φ : Formula AP) (tr ext : Trace AP)
    (h : run φ tr = .tt) : Sat (tr ++ ext) φ 0 := by
  rw [← accepts_iff_sat, accepts, run_append, h, run_tt]
  rfl

/-! ## Resource bound (TODO P3-5)

We want a bound on `(run φ tr).size` that depends only on `φ`, not on `tr`. A constant
factor per step is FALSE (`always` adds a copy per step); the right statement is of the
shape `(run φ tr).size ≤ φ.size * (φ.horizon + 1)` where `horizon` sums the `next`-depth and
the bounds. First state it as a Hypothesis test in Python (monitor/tests), then prove it here.
Define `Formula.horizon` first. -/

end BoundedBrain
