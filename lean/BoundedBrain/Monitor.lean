import BoundedBrain.Formula

/-
  BoundedBrain.Monitor — progression-based monitor and its correctness theorems.

  Mirrors `monitor/src/bounded_brain/monitor.py` (same simplification rules: TT/FF absorption,
  flattening, and removal of repeated conjuncts and disjuncts keeping the last occurrence; D-030).

  STATUS (2026-10-23): compiles with Lean v4.35.0; the correctness theorems (TODO P3-2,
  P3-3, P3-4) are proved, with no `sorry`, including bounded Until (P3-9). The bounded-verdict
  theorem (P3-8) is in BoundedVerdict.lean, the resource bound (P3-5) in Resource.lean. Do not merge a
  `sorry` that is not listed in TODO.md.
-/

namespace BoundedBrain

/-- The conjuncts of a formula: its tree of `conj` nodes flattened, left to right. `tt` contributes nothing;
any other formula that is not a `conj` is its own single conjunct. -/
def Formula.conjuncts {AP : Type} : Formula AP → List (Formula AP)
  | .tt => []
  | .conj a b => a.conjuncts ++ b.conjuncts
  | x => [x]

/-- The disjuncts of a formula, dually: `ff` contributes nothing. -/
def Formula.disjuncts {AP : Type} : Formula AP → List (Formula AP)
  | .ff => []
  | .disj a b => a.disjuncts ++ b.disjuncts
  | x => [x]

/-- Drop every element that occurs again later in the list, so that the last occurrence is kept. -/
def dedupLast {α : Type} [DecidableEq α] : List α → List α
  | [] => []
  | x :: xs => if x ∈ xs then dedupLast xs else x :: dedupLast xs

/-- Right-nested conjunction of a list (`tt` for the empty list). -/
def mkConj {AP : Type} : List (Formula AP) → Formula AP
  | [] => .tt
  | [x] => x
  | x :: y :: ys => .conj x (mkConj (y :: ys))

/-- Right-nested disjunction of a list (`ff` for the empty list). -/
def mkDisj {AP : Type} : List (Formula AP) → Formula AP
  | [] => .ff
  | [x] => x
  | x :: y :: ys => .disj x (mkDisj (y :: ys))

/-- Normal conjunction of a list of conjuncts: `ff` if one of them is `ff`, otherwise the right-nested conjunction
of the list with repetitions removed. -/
def normAnd {AP : Type} [DecidableEq AP] (ms : List (Formula AP)) : Formula AP :=
  if .ff ∈ ms then .ff else mkConj (dedupLast ms)

/-- Normal disjunction of a list of disjuncts, dually. -/
def normOr {AP : Type} [DecidableEq AP] (ms : List (Formula AP)) : Formula AP :=
  if .tt ∈ ms then .tt else mkDisj (dedupLast ms)

/-- Conjunction with TT/FF absorption, flattening, and removal of repeated conjuncts (mirrors Python
`simp_and`). Removing repetitions is what keeps residuals small when `always` is nested (D-030, F73). -/
def simpAnd {AP : Type} [DecidableEq AP] (a b : Formula AP) : Formula AP :=
  normAnd (a.conjuncts ++ b.conjuncts)

/-- Disjunction with TT/FF absorption, flattening, and removal of repeated disjuncts (mirrors Python
`simp_or`). -/
def simpOr {AP : Type} [DecidableEq AP] (a b : Formula AP) : Formula AP :=
  normOr (a.disjuncts ++ b.disjuncts)

/-- Residual obligation on the rest of the trace after consuming one step `σ`. -/
def progress {AP : Type} [DecidableEq AP] (σ : Label AP) : Formula AP → Formula AP
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
  | .untilWithin 0 _ ψ => progress σ ψ
  | .untilWithin (k + 1) φ ψ => simpOr (progress σ ψ) (simpAnd (progress σ φ) (.untilWithin k φ ψ))

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
  | .untilWithin _ _ _ => false

/-- Fold `progress` over a whole trace; returns the final residual. -/
def run {AP : Type} [DecidableEq AP] (φ : Formula AP) (tr : Trace AP) : Formula AP :=
  tr.foldl (fun f σ => progress σ f) φ

/-- The monitor's end-of-trace answer. -/
def accepts {AP : Type} [DecidableEq AP] (φ : Formula AP) (tr : Trace AP) : Bool :=
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
  | untilWithin k φ ψ ihφ ihψ =>
    simp only [Sat, List.length_cons]
    constructor
    · rintro ⟨j, hij, hjk, hj, hs, hφ⟩
      obtain ⟨j', rfl⟩ : ∃ j', j = j' + 1 := ⟨j - 1, by omega⟩
      refine ⟨j', by omega, by omega, by omega, (ihψ j').mp hs, fun m hm hmj => ?_⟩
      exact (ihφ m).mp (hφ (m + 1) (by omega) (by omega))
    · rintro ⟨j, hij, hjk, hj, hs, hφ⟩
      refine ⟨j + 1, by omega, by omega, by omega, (ihψ j).mpr hs, fun m hm hmj => ?_⟩
      obtain ⟨m', rfl⟩ : ∃ m', m = m' + 1 := ⟨m - 1, by omega⟩
      exact (ihφ m').mpr (hφ m' (by omega) (by omega))

/-! ### The simplifiers preserve the semantics -/

theorem mem_dedupLast {α : Type} [DecidableEq α] (x : α) (l : List α) : x ∈ dedupLast l ↔ x ∈ l := by
  induction l with
  | nil => simp [dedupLast]
  | cons y ys ih =>
    by_cases h : y ∈ ys
    · simp only [dedupLast, h, ↓reduceIte, ih, List.mem_cons]
      constructor
      · exact Or.inr
      · rintro (rfl | hx)
        · exact h
        · exact hx
    · simp only [dedupLast, h, ↓reduceIte, List.mem_cons, ih]

/-- A formula holds iff all its conjuncts hold. -/
theorem sat_conjuncts {AP : Type} (tr : Trace AP) (i : Nat) (φ : Formula AP) :
    Sat tr φ i ↔ ∀ y ∈ φ.conjuncts, Sat tr y i := by
  induction φ with
  | tt => simp [Formula.conjuncts, Sat]
  | conj a b iha ihb => simp only [Formula.conjuncts, Sat, iha, ihb, List.forall_mem_append]
  | _ => simp [Formula.conjuncts]

/-- A formula holds iff one of its disjuncts holds. -/
theorem sat_disjuncts {AP : Type} (tr : Trace AP) (i : Nat) (φ : Formula AP) :
    Sat tr φ i ↔ ∃ y ∈ φ.disjuncts, Sat tr y i := by
  induction φ with
  | ff => simp [Formula.disjuncts, Sat]
  | disj a b iha ihb =>
    simp only [Formula.disjuncts, Sat, iha, ihb, List.mem_append, or_and_right, exists_or]
  | _ => simp [Formula.disjuncts]

theorem sat_mkConj {AP : Type} (tr : Trace AP) (i : Nat) :
    ∀ l : List (Formula AP), Sat tr (mkConj l) i ↔ ∀ y ∈ l, Sat tr y i
  | [] => by simp [mkConj, Sat]
  | [x] => by simp [mkConj]
  | x :: y :: ys => by
    rw [mkConj, List.forall_mem_cons, ← sat_mkConj tr i (y :: ys)]
    exact Iff.rfl

theorem sat_mkDisj {AP : Type} (tr : Trace AP) (i : Nat) :
    ∀ l : List (Formula AP), Sat tr (mkDisj l) i ↔ ∃ y ∈ l, Sat tr y i
  | [] => by simp [mkDisj, Sat]
  | [x] => by simp [mkDisj]
  | x :: y :: ys => by
    rw [mkDisj]
    simp only [Sat, sat_mkDisj tr i (y :: ys), List.mem_cons, or_and_right, exists_or, exists_eq_left]

theorem sat_normAnd {AP : Type} [DecidableEq AP] (tr : Trace AP) (i : Nat) (ms : List (Formula AP)) :
    Sat tr (normAnd ms) i ↔ ∀ y ∈ ms, Sat tr y i := by
  unfold normAnd
  split
  · rename_i h
    exact ⟨fun hf => (hf : False).elim, fun hall => hall .ff h⟩
  · rw [sat_mkConj]
    simp only [mem_dedupLast]

theorem sat_normOr {AP : Type} [DecidableEq AP] (tr : Trace AP) (i : Nat) (ms : List (Formula AP)) :
    Sat tr (normOr ms) i ↔ ∃ y ∈ ms, Sat tr y i := by
  unfold normOr
  split
  · rename_i h
    exact ⟨fun _ => ⟨.tt, h, trivial⟩, fun _ => trivial⟩
  · rw [sat_mkDisj]
    simp only [mem_dedupLast]

/-- [P3-2] Simplification preserves semantics: a normalised conjunction holds iff both arguments hold. -/
theorem simpAnd_sat {AP : Type} [DecidableEq AP] (tr : Trace AP) (a b : Formula AP) (i : Nat) :
    Sat tr (simpAnd a b) i ↔ Sat tr a i ∧ Sat tr b i := by
  rw [simpAnd, sat_normAnd, sat_conjuncts tr i a, sat_conjuncts tr i b, List.forall_mem_append]

/-- [P3-2] Same for disjunction. -/
theorem simpOr_sat {AP : Type} [DecidableEq AP] (tr : Trace AP) (a b : Formula AP) (i : Nat) :
    Sat tr (simpOr a b) i ↔ Sat tr a i ∨ Sat tr b i := by
  rw [simpOr, sat_normOr, sat_disjuncts tr i a, sat_disjuncts tr i b]
  simp only [List.mem_append, or_and_right, exists_or]

/-- [P3-2] KEY LEMMA (one-step progression).
Consuming a step `σ` and then evaluating the residual at the start of the rest equals
evaluating the original formula at the start of `σ :: tr`.
Proof: induction on `φ`.
  * `next ψ`:   LHS = `1 < len+1 ∧ Sat (σ::tr) ψ 1`; RHS = `Sat tr (pending ψ) 0`
                = `0 < len ∧ Sat tr ψ 0`; use `sat_shift`.
  * `pending ψ`: LHS = `0 < len+1 ∧ Sat (σ::tr) ψ 0`; RHS = `Sat tr (progress σ ψ) 0`; use IH.
  * `always ψ`, `alwaysWithin (k+1) ψ`, `eventuallyWithin (k+1) ψ`: split the quantified
    index at 0 (IH) and `j + 1` (`sat_shift`); `simpAnd_sat` / `simpOr_sat` for the glue.
  * `untilWithin (k+1) φ ψ`: the witness is 0 (ψ holds now, IH on ψ) or `j + 1` (φ holds now, IH on φ,
    and the rest is the until with bound k, via `sat_shift` for both arguments).
  * bound 0 cases reduce to IH on ψ. -/
theorem progress_sat {AP : Type} [DecidableEq AP] (σ : Label AP) (tr : Trace AP) (φ : Formula AP) :
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
  | untilWithin k φ ψ ihφ ihψ =>
    cases k with
    | zero =>
      simp only [progress]
      rw [← ihψ]
      simp only [Sat, List.length_cons]
      constructor
      · rintro ⟨j, _, hj0, _, hs, _⟩
        obtain rfl : j = 0 := by omega
        exact hs
      · intro h
        exact ⟨0, by omega, by omega, by omega, h, fun m _ hm0 => absurd hm0 (by omega)⟩
    | succ k =>
      simp only [progress]
      rw [simpOr_sat, simpAnd_sat, ← ihψ, ← ihφ]
      simp only [Sat, List.length_cons]
      constructor
      · rintro ⟨j, _, hjk, hj, hs, hφ⟩
        cases j with
        | zero => exact Or.inl hs
        | succ j =>
          refine Or.inr ⟨hφ 0 (by omega) (by omega), j, by omega, by omega, by omega,
            (sat_shift σ tr ψ j).mp hs, fun m _ hmj => ?_⟩
          exact (sat_shift σ tr φ m).mp (hφ (m + 1) (by omega) (by omega))
      · rintro (h0 | ⟨h0, j, _, hjk, hj, hs, hφ⟩)
        · exact ⟨0, by omega, by omega, by omega, h0, fun m _ hm0 => absurd hm0 (by omega)⟩
        · refine ⟨j + 1, by omega, by omega, by omega, (sat_shift σ tr ψ j).mpr hs, fun m _ hmj => ?_⟩
          cases m with
          | zero => exact h0
          | succ m => exact (sat_shift σ tr φ m).mpr (hφ m (by omega) (by omega))

/-- [P3-2] End-of-trace acceptance agrees with the semantics on the empty trace. -/
theorem acceptsEmpty_iff {AP : Type} (φ : Formula AP) :
    acceptsEmpty φ = true ↔ Sat ([] : Trace AP) φ 0 := by
  induction φ with
  | conj φ ψ ihφ ihψ => simp [acceptsEmpty, Sat, ihφ, ihψ]
  | disj φ ψ ihφ ihψ => simp [acceptsEmpty, Sat, ihφ, ihψ]
  | _ => simp [acceptsEmpty, Sat]

/-- One step of `run`: `run φ (σ :: tr) = run (progress σ φ) tr` (by `List.foldl_cons`). -/
theorem run_cons {AP : Type} [DecidableEq AP] (φ : Formula AP) (σ : Label AP) (tr : Trace AP) :
    run φ (σ :: tr) = run (progress σ φ) tr := rfl

/-- [P3-3] MAIN THEOREM: the monitor accepts exactly the traces that satisfy the spec.
Proof: induction on `tr` generalizing `φ`, using `progress_sat` and `acceptsEmpty_iff`. -/
theorem accepts_iff_sat {AP : Type} [DecidableEq AP] (φ : Formula AP) (tr : Trace AP) :
    accepts φ tr = true ↔ Sat tr φ 0 := by
  induction tr generalizing φ with
  | nil => exact acceptsEmpty_iff φ
  | cons σ tr ih =>
    unfold accepts
    rw [run_cons, progress_sat]
    exact ih (progress σ φ)

/-- Running over a concatenation is running over the first part, then the second. -/
theorem run_append {AP : Type} [DecidableEq AP] (φ : Formula AP) (tr ext : Trace AP) :
    run φ (tr ++ ext) = run (run φ tr) ext := by
  simp [run, List.foldl_append]

/-- `ff` is a fixed point of the monitor. -/
theorem run_ff {AP : Type} [DecidableEq AP] (ext : Trace AP) : run (.ff : Formula AP) ext = .ff := by
  induction ext with
  | nil => rfl
  | cons σ ext ih => rw [run_cons]; exact ih

/-- `tt` is a fixed point of the monitor. -/
theorem run_tt {AP : Type} [DecidableEq AP] (ext : Trace AP) : run (.tt : Formula AP) ext = .tt := by
  induction ext with
  | nil => rfl
  | cons σ ext ih => rw [run_cons]; exact ih

/-- [P3-4] Early VIOLATED verdict is sound: if the residual is `ff`, no extension satisfies φ.
Proof: `run φ (tr ++ ext) = run (run φ tr) ext = run .ff ext = .ff`, then `accepts_iff_sat`. -/
theorem violated_sound {AP : Type} [DecidableEq AP] (φ : Formula AP) (tr ext : Trace AP)
    (h : run φ tr = .ff) : ¬ Sat (tr ++ ext) φ 0 := by
  rw [← accepts_iff_sat, accepts, run_append, h, run_ff]
  simp [acceptsEmpty]

/-- [P3-4] Early SATISFIED verdict is sound: if the residual is `tt`, every extension satisfies φ. -/
theorem satisfied_sound {AP : Type} [DecidableEq AP] (φ : Formula AP) (tr ext : Trace AP)
    (h : run φ tr = .tt) : Sat (tr ++ ext) φ 0 := by
  rw [← accepts_iff_sat, accepts, run_append, h, run_tt]
  rfl

/-! ## Resource bound (TODO P3-5)

We want a bound on `(run φ tr).size` that depends only on `φ`, not on `tr`. Without removing repeated
conjuncts the size grows linearly when `always` is nested (F73); `simpAnd` / `simpOr` now remove them (D-030).
Normal.lean shows that every residual is in normal form and that progression commutes with the simplifiers;
Resource.lean proves the bound (`size_run_le`). -/

end BoundedBrain
