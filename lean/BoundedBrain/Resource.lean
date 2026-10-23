import BoundedBrain.BoundedVerdict

/-
  BoundedBrain.Resource — the monitor state is bounded by a function of the spec alone (TODO P3-5).

  `reach φ` is an explicit finite list that contains every residual of `φ`, whatever the trace (`run_mem_reach`).
  Hence the size of the monitor state never exceeds `resBound φ`, the largest size in that list
  (`size_run_le`), however long the trace is.

  The list is built along the structure of `φ`, using that the monitor runs the two sides of a simplified
  conjunction or disjunction independently (`run_simpAnd`, `run_simpOr`):
    * conjunction, disjunction, bounded operators: every combination of the residuals of the parts;
    * `always φ`: after at least one step the residual is a normalised conjunction of conjuncts of residuals of
      `φ` and of `always φ` itself, i.e. `ff` or `mkConj l` for a list `l` without repetitions drawn from a fixed
      finite list. This is where removing repeated conjuncts (D-030) is needed: without it the residual of
      `always (always p)` grows with the trace (F73).

  `resBound φ` is a bound, not an estimate: for nested `always` it is very large (it counts all orders of all
  subsets of the possible conjuncts). The sizes seen in practice are far smaller (docs/04, "Resource bound").

  STATUS (2026-10-23): proved, no `sorry`; only Lean's standard axioms.
-/

namespace BoundedBrain

/-! ## Lists without repetitions drawn from a given list -/

/-- All lists without repetitions, of length at most `n`, whose elements come from `S`. -/
def nodupListsN {α : Type} [DecidableEq α] : Nat → List α → List (List α)
  | 0, _ => [[]]
  | n + 1, S => [] :: S.flatMap (fun x => (nodupListsN n (S.erase x)).map (x :: ·))

/-- All lists without repetitions whose elements come from `S`. -/
def nodupLists {α : Type} [DecidableEq α] (S : List α) : List (List α) := nodupListsN S.length S

theorem mem_nodupListsN {α : Type} [DecidableEq α] :
    ∀ (n : Nat) (S l : List α), l.Nodup → (∀ y ∈ l, y ∈ S) → l.length ≤ n → l ∈ nodupListsN n S
  | 0, _, [], _, _, _ => by simp [nodupListsN]
  | 0, _, _ :: _, _, _, h => absurd h (by simp)
  | _ + 1, _, [], _, _, _ => by simp [nodupListsN]
  | n + 1, S, x :: l, hnd, hsub, hlen => by
    rw [List.nodup_cons] at hnd
    have hx : x ∈ S := hsub x List.mem_cons_self
    have hl : l ∈ nodupListsN n (S.erase x) := by
      apply mem_nodupListsN n (S.erase x) l hnd.2
      · intro y hy
        have hyx : y ≠ x := fun h => hnd.1 (h ▸ hy)
        exact (List.mem_erase_of_ne hyx).2 (hsub y (List.mem_cons_of_mem _ hy))
      · simp only [List.length_cons] at hlen; omega
    simp only [nodupListsN, List.mem_cons, List.mem_flatMap, List.mem_map]
    exact Or.inr ⟨x, hx, l, hl, rfl⟩

theorem mem_nodupLists {α : Type} [DecidableEq α] {S l : List α} (hnd : l.Nodup) (hsub : ∀ y ∈ l, y ∈ S) :
    l ∈ nodupLists S :=
  mem_nodupListsN _ _ _ hnd hsub (hnd.length_le_of_subset (fun y hy => hsub y hy))

/-! ## The reachable residuals -/

/-- `simpAnd x y` for every `x` in `A` and `y` in `B`. -/
def andAll {AP : Type} [DecidableEq AP] (A B : List (Formula AP)) : List (Formula AP) :=
  A.flatMap (fun x => B.map (simpAnd x))

/-- `simpOr x y` for every `x` in `A` and `y` in `B`. -/
def orAll {AP : Type} [DecidableEq AP] (A B : List (Formula AP)) : List (Formula AP) :=
  A.flatMap (fun x => B.map (simpOr x))

theorem mem_andAll {AP : Type} [DecidableEq AP] {A B : List (Formula AP)} {x y : Formula AP}
    (hx : x ∈ A) (hy : y ∈ B) : simpAnd x y ∈ andAll A B :=
  List.mem_flatMap.mpr ⟨x, hx, List.mem_map.mpr ⟨y, hy, rfl⟩⟩

theorem mem_orAll {AP : Type} [DecidableEq AP] {A B : List (Formula AP)} {x y : Formula AP}
    (hx : x ∈ A) (hy : y ∈ B) : simpOr x y ∈ orAll A B :=
  List.mem_flatMap.mpr ⟨x, hx, List.mem_map.mpr ⟨y, hy, rfl⟩⟩

/-- The residuals of `G[0,k] φ`, given a list `R` of the residuals of `φ`. -/
def reachAW {AP : Type} [DecidableEq AP] (R : List (Formula AP)) (φ : Formula AP) : Nat → List (Formula AP)
  | 0 => .alwaysWithin 0 φ :: R
  | k + 1 => .alwaysWithin (k + 1) φ :: andAll R (reachAW R φ k)

/-- The residuals of `F[0,k] φ`, given a list `R` of the residuals of `φ`. -/
def reachEW {AP : Type} [DecidableEq AP] (R : List (Formula AP)) (φ : Formula AP) : Nat → List (Formula AP)
  | 0 => .eventuallyWithin 0 φ :: R
  | k + 1 => .eventuallyWithin (k + 1) φ :: orAll R (reachEW R φ k)

/-- The residuals of `φ U[0,k] ψ`, given lists of the residuals of `φ` and `ψ`. -/
def reachUW {AP : Type} [DecidableEq AP] (Rφ Rψ : List (Formula AP)) (φ ψ : Formula AP) :
    Nat → List (Formula AP)
  | 0 => .untilWithin 0 φ ψ :: Rψ
  | k + 1 => .untilWithin (k + 1) φ ψ :: orAll Rψ (andAll Rφ (reachUW Rφ Rψ φ ψ k))

/-- The conjuncts from which the residuals of `always φ` are built, given a list `R` of the residuals of `φ`. -/
def alwaysAtoms {AP : Type} (R : List (Formula AP)) (φ : Formula AP) : List (Formula AP) :=
  R.flatMap Formula.conjuncts ++ [.always φ]

/-- A finite list that contains every residual of `φ` (`run_mem_reach`). -/
def reach {AP : Type} [DecidableEq AP] : Formula AP → List (Formula AP)
  | .tt => [.tt]
  | .ff => [.ff]
  | .lit p b => [.lit p b, .tt, .ff]
  | .conj a b => .conj a b :: andAll (reach a) (reach b)
  | .disj a b => .disj a b :: orAll (reach a) (reach b)
  | .next φ => .next φ :: .pending φ :: reach φ
  | .pending φ => .pending φ :: reach φ
  | .always φ => .always φ :: .ff :: (nodupLists (dedupLast (alwaysAtoms (reach φ) φ))).map mkConj
  | .alwaysWithin k φ => reachAW (reach φ) φ k
  | .eventuallyWithin k φ => reachEW (reach φ) φ k
  | .untilWithin k φ ψ => reachUW (reach φ) (reach ψ) φ ψ k

/-- After at least one step, the residual of `always φ` is a normalised conjunction of elements of
`alwaysAtoms R φ`, where `R` contains every residual of `φ`. -/
theorem run_always_normAnd {AP : Type} [DecidableEq AP] (φ : Formula AP) (R : List (Formula AP))
    (hR : ∀ tr, run φ tr ∈ R) :
    ∀ (rest : Trace AP) (σ : Label AP), ∃ L : List (Formula AP),
      (∀ y ∈ L, y ∈ alwaysAtoms R φ) ∧ run (.always φ) (σ :: rest) = normAnd L := by
  have hatoms : ∀ y ∈ alwaysAtoms R φ, y.conjuncts = [y] := by
    intro y hy
    rcases List.mem_append.mp hy with hy | hy
    · obtain ⟨z, _, hz⟩ := List.mem_flatMap.mp hy
      exact conjuncts_of_mem hz
    · rw [List.mem_singleton] at hy; subst hy; rfl
  have hmine : ∀ (tr : Trace AP), ∀ y ∈ (run φ tr).conjuncts, y ∈ alwaysAtoms R φ := fun tr y hy =>
    List.mem_append_left _ (List.mem_flatMap.mpr ⟨run φ tr, hR tr, hy⟩)
  intro rest
  induction rest with
  | nil =>
    intro σ
    refine ⟨(progress σ φ).conjuncts ++ [.always φ], ?_, rfl⟩
    intro y hy
    rcases List.mem_append.mp hy with hy | hy
    · exact hmine [σ] y hy
    · exact List.mem_append_right _ hy
  | cons σ' rest ih =>
    intro σ
    obtain ⟨L', hL', hrun⟩ := ih σ'
    refine ⟨(run φ (σ :: σ' :: rest)).conjuncts ++ L', ?_, ?_⟩
    · intro y hy
      rcases List.mem_append.mp hy with hy | hy
      · exact hmine _ y hy
      · exact hL' y hy
    · rw [run_cons]
      show run (simpAnd (progress σ φ) (.always φ)) (σ' :: rest) = _
      rw [run_simpAnd, hrun, ← run_cons, simpAnd, normAnd_append_conjuncts_normAnd _ _ (fun y hy => hatoms y (hL' y hy))]

/-- Every residual of `φ` is in `reach φ`. -/
theorem run_mem_reach {AP : Type} [DecidableEq AP] (φ : Formula AP) : ∀ tr : Trace AP, run φ tr ∈ reach φ := by
  induction φ with
  | tt => intro tr; rw [run_tt]; exact List.mem_cons_self
  | ff => intro tr; rw [run_ff]; exact List.mem_cons_self
  | lit p b =>
    intro tr
    cases tr with
    | nil => exact List.mem_cons_self
    | cons σ rest =>
      rw [run_cons]
      simp only [progress]
      split
      · rw [run_tt]; simp [reach]
      · rw [run_ff]; simp [reach]
  | conj a b iha ihb =>
    intro tr
    cases tr with
    | nil => exact List.mem_cons_self
    | cons σ rest =>
      rw [run_cons]
      show run (simpAnd (progress σ a) (progress σ b)) rest ∈ _
      rw [run_simpAnd, ← run_cons, ← run_cons]
      exact List.mem_cons_of_mem _ (mem_andAll (iha _) (ihb _))
  | disj a b iha ihb =>
    intro tr
    cases tr with
    | nil => exact List.mem_cons_self
    | cons σ rest =>
      rw [run_cons]
      show run (simpOr (progress σ a) (progress σ b)) rest ∈ _
      rw [run_simpOr, ← run_cons, ← run_cons]
      exact List.mem_cons_of_mem _ (mem_orAll (iha _) (ihb _))
  | next φ ih =>
    intro tr
    match tr with
    | [] => exact List.mem_cons_self
    | [_] => exact List.mem_cons_of_mem _ List.mem_cons_self
    | σ :: σ' :: rest =>
      rw [run_cons, run_cons]
      show run (progress σ' φ) rest ∈ _
      rw [← run_cons]
      exact List.mem_cons_of_mem _ (List.mem_cons_of_mem _ (ih _))
  | pending φ ih =>
    intro tr
    cases tr with
    | nil => exact List.mem_cons_self
    | cons σ rest =>
      rw [run_cons]
      show run (progress σ φ) rest ∈ _
      rw [← run_cons]
      exact List.mem_cons_of_mem _ (ih _)
  | always φ ih =>
    intro tr
    cases tr with
    | nil => exact List.mem_cons_self
    | cons σ rest =>
      obtain ⟨L, hL, hrun⟩ := run_always_normAnd φ (reach φ) ih rest σ
      rw [hrun]
      unfold normAnd
      split
      · exact List.mem_cons_of_mem _ List.mem_cons_self
      · apply List.mem_cons_of_mem _ (List.mem_cons_of_mem _ _)
        exact List.mem_map.mpr ⟨dedupLast L, mem_nodupLists (nodup_dedupLast L)
          (fun y hy => (mem_dedupLast y _).mpr (hL y ((mem_dedupLast y L).mp hy))), rfl⟩
  | alwaysWithin k φ ih =>
    show ∀ tr, run _ tr ∈ reachAW (reach φ) φ k
    induction k with
    | zero =>
      intro tr
      cases tr with
      | nil => exact List.mem_cons_self
      | cons σ rest =>
        rw [run_cons]
        show run (progress σ φ) rest ∈ _
        rw [← run_cons]
        exact List.mem_cons_of_mem _ (ih _)
    | succ k ihk =>
      intro tr
      cases tr with
      | nil => exact List.mem_cons_self
      | cons σ rest =>
        rw [run_cons]
        show run (simpAnd (progress σ φ) (.alwaysWithin k φ)) rest ∈ _
        rw [run_simpAnd, ← run_cons]
        exact List.mem_cons_of_mem _ (mem_andAll (ih _) (ihk rest))
  | eventuallyWithin k φ ih =>
    show ∀ tr, run _ tr ∈ reachEW (reach φ) φ k
    induction k with
    | zero =>
      intro tr
      cases tr with
      | nil => exact List.mem_cons_self
      | cons σ rest =>
        rw [run_cons]
        show run (progress σ φ) rest ∈ _
        rw [← run_cons]
        exact List.mem_cons_of_mem _ (ih _)
    | succ k ihk =>
      intro tr
      cases tr with
      | nil => exact List.mem_cons_self
      | cons σ rest =>
        rw [run_cons]
        show run (simpOr (progress σ φ) (.eventuallyWithin k φ)) rest ∈ _
        rw [run_simpOr, ← run_cons]
        exact List.mem_cons_of_mem _ (mem_orAll (ih _) (ihk rest))
  | untilWithin k φ ψ ihφ ihψ =>
    show ∀ tr, run _ tr ∈ reachUW (reach φ) (reach ψ) φ ψ k
    induction k with
    | zero =>
      intro tr
      cases tr with
      | nil => exact List.mem_cons_self
      | cons σ rest =>
        rw [run_cons]
        show run (progress σ ψ) rest ∈ _
        rw [← run_cons]
        exact List.mem_cons_of_mem _ (ihψ _)
    | succ k ihk =>
      intro tr
      cases tr with
      | nil => exact List.mem_cons_self
      | cons σ rest =>
        rw [run_cons]
        show run (simpOr (progress σ ψ) (simpAnd (progress σ φ) (.untilWithin k φ ψ))) rest ∈ _
        rw [run_simpOr, run_simpAnd, ← run_cons, ← run_cons]
        exact List.mem_cons_of_mem _ (mem_orAll (ihψ _) (mem_andAll (ihφ _) (ihk rest)))

/-! ## The bound -/

/-- The largest size of a formula in `reach φ`. -/
def resBound {AP : Type} [DecidableEq AP] (φ : Formula AP) : Nat :=
  (reach φ).foldr (fun x m => max x.size m) 0

theorem size_le_foldr_max {AP : Type} {x : Formula AP} :
    ∀ {l : List (Formula AP)}, x ∈ l → x.size ≤ l.foldr (fun y m => max y.size m) 0
  | _ :: _, List.Mem.head _ => by simp only [List.foldr_cons]; omega
  | _ :: l, List.Mem.tail _ h => by
    have := size_le_foldr_max (l := l) h
    simp only [List.foldr_cons]; omega

/-- [P3-5] RESOURCE BOUND: the size of the monitor state is bounded by a number that depends on the spec alone,
not on the trace. -/
theorem size_run_le {AP : Type} [DecidableEq AP] (φ : Formula AP) (tr : Trace AP) :
    (run φ tr).size ≤ resBound φ :=
  size_le_foldr_max (run_mem_reach φ tr)

end BoundedBrain
