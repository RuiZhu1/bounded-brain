import BoundedBrain.Monitor

/-
  BoundedBrain.Normal — the normal form produced by `simpAnd` / `simpOr`, and why progression commutes with it.

  `simpAnd a b` flattens both conjunctions, removes repeated conjuncts (keeping the last occurrence) and absorbs
  `tt` / `ff` (D-030). Every residual is in this normal form (`norm_progress`), and progression commutes with the
  simplifiers (`progress_simpAnd`, `progress_simpOr`): progressing a normalised conjunction gives the same formula
  as normalising the progressed arguments. BoundedVerdict.lean uses this through `run_simpAnd` / `run_simpOr`.

  STATUS (2026-10-23): proved, no `sorry`; only Lean's standard axioms.
-/

namespace BoundedBrain

/-! ## `dedupLast` -/

theorem dedupLast_cons_of_mem {α : Type} [DecidableEq α] {x : α} {xs : List α} (h : x ∈ xs) :
    dedupLast (x :: xs) = dedupLast xs := by
  simp [dedupLast, h]

theorem dedupLast_cons_of_not_mem {α : Type} [DecidableEq α] {x : α} {xs : List α} (h : x ∉ xs) :
    dedupLast (x :: xs) = x :: dedupLast xs := by
  simp [dedupLast, h]

theorem nodup_dedupLast {α : Type} [DecidableEq α] (l : List α) : (dedupLast l).Nodup := by
  induction l with
  | nil => exact List.nodup_nil
  | cons x xs ih =>
    by_cases h : x ∈ xs
    · rw [dedupLast_cons_of_mem h]; exact ih
    · rw [dedupLast_cons_of_not_mem h]
      exact List.nodup_cons.mpr ⟨fun hx => h ((mem_dedupLast x xs).mp hx), ih⟩

theorem dedupLast_of_nodup {α : Type} [DecidableEq α] {l : List α} (h : l.Nodup) : dedupLast l = l := by
  induction l with
  | nil => rfl
  | cons x xs ih =>
    rw [List.nodup_cons] at h
    rw [dedupLast_cons_of_not_mem h.1, ih h.2]

theorem dedupLast_dedupLast_append {α : Type} [DecidableEq α] (X Y : List α) :
    dedupLast (dedupLast X ++ Y) = dedupLast (X ++ Y) := by
  induction X with
  | nil => rfl
  | cons x xs ih =>
    by_cases hx : x ∈ xs
    · rw [dedupLast_cons_of_mem hx, ih, List.cons_append,
        dedupLast_cons_of_mem (List.mem_append_left Y hx)]
    · rw [dedupLast_cons_of_not_mem hx, List.cons_append, List.cons_append]
      by_cases hY : x ∈ Y
      · rw [dedupLast_cons_of_mem (List.mem_append_right _ hY),
          dedupLast_cons_of_mem (List.mem_append_right _ hY), ih]
      · have h1 : x ∉ dedupLast xs ++ Y := by simp [mem_dedupLast, hx, hY]
        have h2 : x ∉ xs ++ Y := by simp [hx, hY]
        rw [dedupLast_cons_of_not_mem h1, dedupLast_cons_of_not_mem h2, ih]

theorem dedupLast_append_dedupLast {α : Type} [DecidableEq α] (X Y : List α) :
    dedupLast (X ++ dedupLast Y) = dedupLast (X ++ Y) := by
  induction X with
  | nil => simpa using dedupLast_dedupLast_append Y []
  | cons x xs ih =>
    have hmem : x ∈ xs ++ dedupLast Y ↔ x ∈ xs ++ Y := by simp [mem_dedupLast]
    rw [List.cons_append, List.cons_append]
    by_cases h : x ∈ xs ++ Y
    · rw [dedupLast_cons_of_mem (hmem.mpr h), dedupLast_cons_of_mem h, ih]
    · rw [dedupLast_cons_of_not_mem (fun hh => h (hmem.mp hh)), dedupLast_cons_of_not_mem h, ih]

theorem dedupLast_append_of_forall_mem {α : Type} [DecidableEq α] {A W : List α} (h : ∀ y ∈ A, y ∈ W) :
    dedupLast (A ++ W) = dedupLast W := by
  induction A with
  | nil => rfl
  | cons a as ih =>
    rw [List.cons_append, dedupLast_cons_of_mem (List.mem_append_right _ (h a List.mem_cons_self))]
    exact ih (fun y hy => h y (List.mem_cons_of_mem _ hy))

/-- Removing repetitions before expanding every element into a block does not change the result. -/
theorem dedupLast_flatMap {α β : Type} [DecidableEq α] [DecidableEq β] (g : α → List β) (Z : List α) :
    dedupLast ((dedupLast Z).flatMap g) = dedupLast (Z.flatMap g) := by
  induction Z with
  | nil => rfl
  | cons z zs ih =>
    by_cases hz : z ∈ zs
    · rw [dedupLast_cons_of_mem hz, ih, List.flatMap_cons, dedupLast_append_of_forall_mem]
      intro y hy
      exact List.mem_flatMap.mpr ⟨z, hz, hy⟩
    · rw [dedupLast_cons_of_not_mem hz, List.flatMap_cons, List.flatMap_cons,
        ← dedupLast_append_dedupLast (g z) ((dedupLast zs).flatMap g), ih, dedupLast_append_dedupLast]

/-! ## Conjuncts and disjuncts of normal forms -/

/-- The elements of a list of conjuncts are their own only conjunct. -/
theorem conjuncts_of_mem {AP : Type} {x y : Formula AP} (h : y ∈ x.conjuncts) : y.conjuncts = [y] := by
  induction x with
  | tt => simp [Formula.conjuncts] at h
  | conj a b iha ihb =>
    rw [Formula.conjuncts, List.mem_append] at h
    exact h.elim iha ihb
  | _ => simp only [Formula.conjuncts, List.mem_singleton] at h; subst h; rfl

theorem disjuncts_of_mem {AP : Type} {x y : Formula AP} (h : y ∈ x.disjuncts) : y.disjuncts = [y] := by
  induction x with
  | ff => simp [Formula.disjuncts] at h
  | disj a b iha ihb =>
    rw [Formula.disjuncts, List.mem_append] at h
    exact h.elim iha ihb
  | _ => simp only [Formula.disjuncts, List.mem_singleton] at h; subst h; rfl

theorem conjuncts_mkConj {AP : Type} :
    ∀ {l : List (Formula AP)}, (∀ y ∈ l, y.conjuncts = [y]) → (mkConj l).conjuncts = l
  | [], _ => rfl
  | [x], h => h x List.mem_cons_self
  | x :: y :: ys, h => by
    rw [mkConj, Formula.conjuncts, h x List.mem_cons_self,
      conjuncts_mkConj (fun z hz => h z (List.mem_cons_of_mem _ hz))]
    rfl

theorem disjuncts_mkDisj {AP : Type} :
    ∀ {l : List (Formula AP)}, (∀ y ∈ l, y.disjuncts = [y]) → (mkDisj l).disjuncts = l
  | [], _ => rfl
  | [x], h => h x List.mem_cons_self
  | x :: y :: ys, h => by
    rw [mkDisj, Formula.disjuncts, h x List.mem_cons_self,
      disjuncts_mkDisj (fun z hz => h z (List.mem_cons_of_mem _ hz))]
    rfl

/-- A conjunction of two or more formulas is a single disjunct. -/
theorem disjuncts_mkConj_of_two_le {AP : Type} :
    ∀ {l : List (Formula AP)}, 2 ≤ l.length → (mkConj l).disjuncts = [mkConj l]
  | [], h => absurd h (by simp)
  | [_], h => absurd h (by simp)
  | _ :: _ :: _, _ => rfl

theorem conjuncts_mkDisj_of_two_le {AP : Type} :
    ∀ {l : List (Formula AP)}, 2 ≤ l.length → (mkDisj l).conjuncts = [mkDisj l]
  | [], h => absurd h (by simp)
  | [_], h => absurd h (by simp)
  | _ :: _ :: _, _ => rfl

theorem mkConj_ne_tt {AP : Type} : ∀ {l : List (Formula AP)}, 2 ≤ l.length → mkConj l ≠ .tt
  | [], h => absurd h (by simp)
  | [_], h => absurd h (by simp)
  | _ :: _ :: _, _ => by simp [mkConj]

theorem mkDisj_ne_ff {AP : Type} : ∀ {l : List (Formula AP)}, 2 ≤ l.length → mkDisj l ≠ .ff
  | [], h => absurd h (by simp)
  | [_], h => absurd h (by simp)
  | _ :: _ :: _, _ => by simp [mkDisj]

theorem normAnd_singleton {AP : Type} [DecidableEq AP] {x : Formula AP} (h : x ≠ .ff) : normAnd [x] = x := by
  have hne : Formula.ff ∉ [x] := by simpa [eq_comm] using h
  unfold normAnd
  rw [ite_eq_right hne]
  simp [dedupLast, mkConj]

theorem normOr_singleton {AP : Type} [DecidableEq AP] {x : Formula AP} (h : x ≠ .tt) : normOr [x] = x := by
  have hne : Formula.tt ∉ [x] := by simpa [eq_comm] using h
  unfold normOr
  rw [ite_eq_right hne]
  simp [dedupLast, mkDisj]

/-- Splicing a normalised conjunction into a list and normalising again is the same as normalising once. -/
theorem normAnd_append_conjuncts_normAnd {AP : Type} [DecidableEq AP] (X Y : List (Formula AP))
    (hY : ∀ y ∈ Y, y.conjuncts = [y]) :
    normAnd (X ++ (normAnd Y).conjuncts) = normAnd (X ++ Y) := by
  by_cases hf : Formula.ff ∈ Y
  · have h1 : normAnd Y = .ff := by unfold normAnd; exact ite_eq_left hf
    rw [h1]
    have h2 : Formula.ff ∈ X ++ (Formula.ff : Formula AP).conjuncts := by simp [Formula.conjuncts]
    unfold normAnd; rw [ite_eq_left h2, ite_eq_left (List.mem_append_right _ hf)]
  · have hc : (normAnd Y).conjuncts = dedupLast Y := by
      unfold normAnd; rw [ite_eq_right hf, conjuncts_mkConj]
      intro y hy; exact hY y ((mem_dedupLast y Y).mp hy)
    rw [hc]; unfold normAnd
    have hmem : Formula.ff ∈ X ++ dedupLast Y ↔ Formula.ff ∈ X ++ Y := by simp [mem_dedupLast]
    by_cases hX : Formula.ff ∈ X ++ Y
    · rw [ite_eq_left (hmem.mpr hX), ite_eq_left hX]
    · rw [ite_eq_right (fun h => hX (hmem.mp h)), ite_eq_right hX, dedupLast_append_dedupLast]

theorem normAnd_conjuncts_normAnd_append {AP : Type} [DecidableEq AP] (X Y : List (Formula AP))
    (hX : ∀ y ∈ X, y.conjuncts = [y]) :
    normAnd ((normAnd X).conjuncts ++ Y) = normAnd (X ++ Y) := by
  by_cases hf : Formula.ff ∈ X
  · have h1 : normAnd X = .ff := by unfold normAnd; exact ite_eq_left hf
    rw [h1]
    have h2 : Formula.ff ∈ (Formula.ff : Formula AP).conjuncts ++ Y := by simp [Formula.conjuncts]
    unfold normAnd; rw [ite_eq_left h2, ite_eq_left (List.mem_append_left _ hf)]
  · have hc : (normAnd X).conjuncts = dedupLast X := by
      unfold normAnd; rw [ite_eq_right hf, conjuncts_mkConj]
      intro y hy; exact hX y ((mem_dedupLast y X).mp hy)
    rw [hc]; unfold normAnd
    have hmem : Formula.ff ∈ dedupLast X ++ Y ↔ Formula.ff ∈ X ++ Y := by simp [mem_dedupLast]
    by_cases hXY : Formula.ff ∈ X ++ Y
    · rw [ite_eq_left (hmem.mpr hXY), ite_eq_left hXY]
    · rw [ite_eq_right (fun h => hXY (hmem.mp h)), ite_eq_right hXY, dedupLast_dedupLast_append]

theorem normOr_append_disjuncts_normOr {AP : Type} [DecidableEq AP] (X Y : List (Formula AP))
    (hY : ∀ y ∈ Y, y.disjuncts = [y]) :
    normOr (X ++ (normOr Y).disjuncts) = normOr (X ++ Y) := by
  by_cases hf : Formula.tt ∈ Y
  · have h1 : normOr Y = .tt := by unfold normOr; exact ite_eq_left hf
    rw [h1]
    have h2 : Formula.tt ∈ X ++ (Formula.tt : Formula AP).disjuncts := by simp [Formula.disjuncts]
    unfold normOr; rw [ite_eq_left h2, ite_eq_left (List.mem_append_right _ hf)]
  · have hc : (normOr Y).disjuncts = dedupLast Y := by
      unfold normOr; rw [ite_eq_right hf, disjuncts_mkDisj]
      intro y hy; exact hY y ((mem_dedupLast y Y).mp hy)
    rw [hc]; unfold normOr
    have hmem : Formula.tt ∈ X ++ dedupLast Y ↔ Formula.tt ∈ X ++ Y := by simp [mem_dedupLast]
    by_cases hX : Formula.tt ∈ X ++ Y
    · rw [ite_eq_left (hmem.mpr hX), ite_eq_left hX]
    · rw [ite_eq_right (fun h => hX (hmem.mp h)), ite_eq_right hX, dedupLast_append_dedupLast]

theorem normOr_disjuncts_normOr_append {AP : Type} [DecidableEq AP] (X Y : List (Formula AP))
    (hX : ∀ y ∈ X, y.disjuncts = [y]) :
    normOr ((normOr X).disjuncts ++ Y) = normOr (X ++ Y) := by
  by_cases hf : Formula.tt ∈ X
  · have h1 : normOr X = .tt := by unfold normOr; exact ite_eq_left hf
    rw [h1]
    have h2 : Formula.tt ∈ (Formula.tt : Formula AP).disjuncts ++ Y := by simp [Formula.disjuncts]
    unfold normOr; rw [ite_eq_left h2, ite_eq_left (List.mem_append_left _ hf)]
  · have hc : (normOr X).disjuncts = dedupLast X := by
      unfold normOr; rw [ite_eq_right hf, disjuncts_mkDisj]
      intro y hy; exact hX y ((mem_dedupLast y X).mp hy)
    rw [hc]; unfold normOr
    have hmem : Formula.tt ∈ dedupLast X ++ Y ↔ Formula.tt ∈ X ++ Y := by simp [mem_dedupLast]
    by_cases hXY : Formula.tt ∈ X ++ Y
    · rw [ite_eq_left (hmem.mpr hXY), ite_eq_left hXY]
    · rw [ite_eq_right (fun h => hXY (hmem.mp h)), ite_eq_right hXY, dedupLast_dedupLast_append]

/-- Expanding the conjuncts of a normalised conjunction into blocks: the same as expanding before
normalising, provided `ff` expands to a block that contains `ff`. -/
theorem normAnd_flatMap_conjuncts_normAnd {AP : Type} [DecidableEq AP] (g : Formula AP → List (Formula AP))
    (hg : Formula.ff ∈ g .ff) (Z : List (Formula AP)) (hZ : ∀ y ∈ Z, y.conjuncts = [y]) :
    normAnd ((normAnd Z).conjuncts.flatMap g) = normAnd (Z.flatMap g) := by
  by_cases hf : Formula.ff ∈ Z
  · have h1 : normAnd Z = .ff := by unfold normAnd; exact ite_eq_left hf
    rw [h1]
    have h2 : Formula.ff ∈ (Formula.ff : Formula AP).conjuncts.flatMap g := by
      simpa [Formula.conjuncts] using hg
    unfold normAnd; rw [ite_eq_left h2, ite_eq_left (List.mem_flatMap.mpr ⟨.ff, hf, hg⟩)]
  · have hc : (normAnd Z).conjuncts = dedupLast Z := by
      unfold normAnd; rw [ite_eq_right hf, conjuncts_mkConj]
      intro y hy; exact hZ y ((mem_dedupLast y Z).mp hy)
    rw [hc]; unfold normAnd
    have hmem : Formula.ff ∈ (dedupLast Z).flatMap g ↔ Formula.ff ∈ Z.flatMap g := by
      simp only [List.mem_flatMap, mem_dedupLast]
    by_cases hZf : Formula.ff ∈ Z.flatMap g
    · rw [ite_eq_left (hmem.mpr hZf), ite_eq_left hZf]
    · rw [ite_eq_right (fun h => hZf (hmem.mp h)), ite_eq_right hZf, dedupLast_flatMap]

theorem normOr_flatMap_disjuncts_normOr {AP : Type} [DecidableEq AP] (g : Formula AP → List (Formula AP))
    (hg : Formula.tt ∈ g .tt) (Z : List (Formula AP)) (hZ : ∀ y ∈ Z, y.disjuncts = [y]) :
    normOr ((normOr Z).disjuncts.flatMap g) = normOr (Z.flatMap g) := by
  by_cases hf : Formula.tt ∈ Z
  · have h1 : normOr Z = .tt := by unfold normOr; exact ite_eq_left hf
    rw [h1]
    have h2 : Formula.tt ∈ (Formula.tt : Formula AP).disjuncts.flatMap g := by
      simpa [Formula.disjuncts] using hg
    unfold normOr; rw [ite_eq_left h2, ite_eq_left (List.mem_flatMap.mpr ⟨.tt, hf, hg⟩)]
  · have hc : (normOr Z).disjuncts = dedupLast Z := by
      unfold normOr; rw [ite_eq_right hf, disjuncts_mkDisj]
      intro y hy; exact hZ y ((mem_dedupLast y Z).mp hy)
    rw [hc]; unfold normOr
    have hmem : Formula.tt ∈ (dedupLast Z).flatMap g ↔ Formula.tt ∈ Z.flatMap g := by
      simp only [List.mem_flatMap, mem_dedupLast]
    by_cases hZt : Formula.tt ∈ Z.flatMap g
    · rw [ite_eq_left (hmem.mpr hZt), ite_eq_left hZt]
    · rw [ite_eq_right (fun h => hZt (hmem.mp h)), ite_eq_right hZt, dedupLast_flatMap]

/-! ## The normal form -/

/-- Normal form of residuals: `tt`, `ff`, a non-Boolean formula, or a right-nested conjunction (disjunction) of at
least two distinct normal formulas that are not themselves conjunctions (disjunctions), `tt` or `ff`. -/
inductive Norm {AP : Type} : Formula AP → Prop
  | tt : Norm .tt
  | ff : Norm .ff
  | atom {x : Formula AP} : x.conjuncts = [x] → x.disjuncts = [x] → Norm x
  | conj {l : List (Formula AP)} : 2 ≤ l.length → l.Nodup → (∀ y ∈ l, Norm y) →
      (∀ y ∈ l, y.conjuncts = [y]) → Formula.ff ∉ l → Norm (mkConj l)
  | disj {l : List (Formula AP)} : 2 ≤ l.length → l.Nodup → (∀ y ∈ l, Norm y) →
      (∀ y ∈ l, y.disjuncts = [y]) → Formula.tt ∉ l → Norm (mkDisj l)

theorem norm_of_mem_conjuncts {AP : Type} {x y : Formula AP} (hx : Norm x) (hy : y ∈ x.conjuncts) : Norm y := by
  cases hx with
  | tt => simp [Formula.conjuncts] at hy
  | ff => simp only [Formula.conjuncts, List.mem_singleton] at hy; subst hy; exact Norm.ff
  | atom hc hd => rw [hc, List.mem_singleton] at hy; subst hy; exact Norm.atom hc hd
  | conj hlen hnd hall hcj hff => rw [conjuncts_mkConj hcj] at hy; exact hall y hy
  | disj hlen hnd hall hdj htt =>
    rw [conjuncts_mkDisj_of_two_le hlen, List.mem_singleton] at hy
    subst hy; exact Norm.disj hlen hnd hall hdj htt

theorem norm_of_mem_disjuncts {AP : Type} {x y : Formula AP} (hx : Norm x) (hy : y ∈ x.disjuncts) : Norm y := by
  cases hx with
  | tt => simp only [Formula.disjuncts, List.mem_singleton] at hy; subst hy; exact Norm.tt
  | ff => simp [Formula.disjuncts] at hy
  | atom hc hd => rw [hd, List.mem_singleton] at hy; subst hy; exact Norm.atom hc hd
  | conj hlen hnd hall hcj hff =>
    rw [disjuncts_mkConj_of_two_le hlen, List.mem_singleton] at hy
    subst hy; exact Norm.conj hlen hnd hall hcj hff
  | disj hlen hnd hall hdj htt => rw [disjuncts_mkDisj hdj] at hy; exact hall y hy

/-- A normal formula is its own normalised conjunction of conjuncts ... -/
theorem normAnd_conjuncts_of_norm {AP : Type} [DecidableEq AP] {x : Formula AP} (hx : Norm x) :
    normAnd x.conjuncts = x := by
  cases hx with
  | tt => simp [normAnd, Formula.conjuncts, dedupLast, mkConj]
  | ff => simp [normAnd, Formula.conjuncts]
  | atom hc hd =>
    rw [hc]
    apply normAnd_singleton
    intro h; subst h; simp [Formula.disjuncts] at hd
  | conj hlen hnd hall hcj hff =>
    rw [conjuncts_mkConj hcj]
    unfold normAnd
    rw [ite_eq_right hff, dedupLast_of_nodup hnd]
  | disj hlen hnd hall hdj htt =>
    rw [conjuncts_mkDisj_of_two_le hlen]
    exact normAnd_singleton (mkDisj_ne_ff hlen)

/-- ... and its own normalised disjunction of disjuncts. -/
theorem normOr_disjuncts_of_norm {AP : Type} [DecidableEq AP] {x : Formula AP} (hx : Norm x) :
    normOr x.disjuncts = x := by
  cases hx with
  | tt => simp [normOr, Formula.disjuncts]
  | ff => simp [normOr, Formula.disjuncts, dedupLast, mkDisj]
  | atom hc hd =>
    rw [hd]
    apply normOr_singleton
    intro h; subst h; simp [Formula.conjuncts] at hc
  | conj hlen hnd hall hcj hff =>
    rw [disjuncts_mkConj_of_two_le hlen]
    exact normOr_singleton (mkConj_ne_tt hlen)
  | disj hlen hnd hall hdj htt =>
    rw [disjuncts_mkDisj hdj]
    unfold normOr
    rw [ite_eq_right htt, dedupLast_of_nodup hnd]

theorem norm_mkConj_of_nodup {AP : Type} :
    ∀ {D : List (Formula AP)}, D.Nodup → (∀ y ∈ D, Norm y) → (∀ y ∈ D, y.conjuncts = [y]) →
      Formula.ff ∉ D → Norm (mkConj D)
  | [], _, _, _, _ => Norm.tt
  | [d], _, hn, _, _ => hn d List.mem_cons_self
  | _ :: _ :: _, hnd, hn, hc, hff => Norm.conj (by simp) hnd hn hc hff

theorem norm_mkDisj_of_nodup {AP : Type} :
    ∀ {D : List (Formula AP)}, D.Nodup → (∀ y ∈ D, Norm y) → (∀ y ∈ D, y.disjuncts = [y]) →
      Formula.tt ∉ D → Norm (mkDisj D)
  | [], _, _, _, _ => Norm.ff
  | [d], _, hn, _, _ => hn d List.mem_cons_self
  | _ :: _ :: _, hnd, hn, hd, htt => Norm.disj (by simp) hnd hn hd htt

theorem norm_normAnd {AP : Type} [DecidableEq AP] {ms : List (Formula AP)} (hn : ∀ y ∈ ms, Norm y)
    (hc : ∀ y ∈ ms, y.conjuncts = [y]) : Norm (normAnd ms) := by
  unfold normAnd
  split
  · exact Norm.ff
  · rename_i hff
    exact norm_mkConj_of_nodup (nodup_dedupLast ms)
      (fun y hy => hn y ((mem_dedupLast y ms).mp hy)) (fun y hy => hc y ((mem_dedupLast y ms).mp hy))
      (fun h => hff ((mem_dedupLast _ ms).mp h))

theorem norm_normOr {AP : Type} [DecidableEq AP] {ms : List (Formula AP)} (hn : ∀ y ∈ ms, Norm y)
    (hd : ∀ y ∈ ms, y.disjuncts = [y]) : Norm (normOr ms) := by
  unfold normOr
  split
  · exact Norm.tt
  · rename_i htt
    exact norm_mkDisj_of_nodup (nodup_dedupLast ms)
      (fun y hy => hn y ((mem_dedupLast y ms).mp hy)) (fun y hy => hd y ((mem_dedupLast y ms).mp hy))
      (fun h => htt ((mem_dedupLast _ ms).mp h))

theorem norm_simpAnd {AP : Type} [DecidableEq AP] {a b : Formula AP} (ha : Norm a) (hb : Norm b) :
    Norm (simpAnd a b) := by
  unfold simpAnd
  apply norm_normAnd
  · intro y hy
    rcases List.mem_append.mp hy with hy | hy
    · exact norm_of_mem_conjuncts ha hy
    · exact norm_of_mem_conjuncts hb hy
  · intro y hy
    rcases List.mem_append.mp hy with hy | hy
    · exact conjuncts_of_mem hy
    · exact conjuncts_of_mem hy

theorem norm_simpOr {AP : Type} [DecidableEq AP] {a b : Formula AP} (ha : Norm a) (hb : Norm b) :
    Norm (simpOr a b) := by
  unfold simpOr
  apply norm_normOr
  · intro y hy
    rcases List.mem_append.mp hy with hy | hy
    · exact norm_of_mem_disjuncts ha hy
    · exact norm_of_mem_disjuncts hb hy
  · intro y hy
    rcases List.mem_append.mp hy with hy | hy
    · exact disjuncts_of_mem hy
    · exact disjuncts_of_mem hy

/-- Every residual is in normal form. -/
theorem norm_progress {AP : Type} [DecidableEq AP] (σ : Label AP) (x : Formula AP) : Norm (progress σ x) := by
  induction x with
  | tt => exact Norm.tt
  | ff => exact Norm.ff
  | lit p b =>
    simp only [progress]
    split
    · exact Norm.tt
    · exact Norm.ff
  | conj a b iha ihb => exact norm_simpAnd iha ihb
  | disj a b iha ihb => exact norm_simpOr iha ihb
  | next φ _ => exact Norm.atom rfl rfl
  | pending φ ih => exact ih
  | always φ ih => exact norm_simpAnd ih (Norm.atom rfl rfl)
  | alwaysWithin k φ ih =>
    cases k with
    | zero => exact ih
    | succ k => exact norm_simpAnd ih (Norm.atom rfl rfl)
  | eventuallyWithin k φ ih =>
    cases k with
    | zero => exact ih
    | succ k => exact norm_simpOr ih (Norm.atom rfl rfl)
  | untilWithin k φ ψ ihφ ihψ =>
    cases k with
    | zero => exact ihψ
    | succ k => exact norm_simpOr ihψ (norm_simpAnd ihφ (Norm.atom rfl rfl))

/-! ## Progression commutes with the simplifiers -/

/-- Progressing a formula is normalising the progressed conjuncts. -/
theorem progress_eq_normAnd {AP : Type} [DecidableEq AP] (σ : Label AP) (x : Formula AP) :
    progress σ x = normAnd (x.conjuncts.flatMap (fun y => (progress σ y).conjuncts)) := by
  induction x with
  | tt => simp [progress, Formula.conjuncts, normAnd, dedupLast, mkConj]
  | conj a b iha ihb =>
    rw [Formula.conjuncts, List.flatMap_append]
    show simpAnd (progress σ a) (progress σ b) = _
    rw [simpAnd, iha, ihb, normAnd_conjuncts_normAnd_append, normAnd_append_conjuncts_normAnd]
    · intro y hy
      obtain ⟨z, _, hz⟩ := List.mem_flatMap.mp hy
      exact conjuncts_of_mem hz
    · intro y hy
      obtain ⟨z, _, hz⟩ := List.mem_flatMap.mp hy
      exact conjuncts_of_mem hz
  | _ =>
    simp only [Formula.conjuncts, List.flatMap_cons, List.flatMap_nil, List.append_nil]
    exact (normAnd_conjuncts_of_norm (norm_progress σ _)).symm

/-- Progressing a formula is normalising the progressed disjuncts. -/
theorem progress_eq_normOr {AP : Type} [DecidableEq AP] (σ : Label AP) (x : Formula AP) :
    progress σ x = normOr (x.disjuncts.flatMap (fun y => (progress σ y).disjuncts)) := by
  induction x with
  | ff => simp [progress, Formula.disjuncts, normOr, dedupLast, mkDisj]
  | disj a b iha ihb =>
    rw [Formula.disjuncts, List.flatMap_append]
    show simpOr (progress σ a) (progress σ b) = _
    rw [simpOr, iha, ihb, normOr_disjuncts_normOr_append, normOr_append_disjuncts_normOr]
    · intro y hy
      obtain ⟨z, _, hz⟩ := List.mem_flatMap.mp hy
      exact disjuncts_of_mem hz
    · intro y hy
      obtain ⟨z, _, hz⟩ := List.mem_flatMap.mp hy
      exact disjuncts_of_mem hz
  | _ =>
    simp only [Formula.disjuncts, List.flatMap_cons, List.flatMap_nil, List.append_nil]
    exact (normOr_disjuncts_of_norm (norm_progress σ _)).symm

/-- Progression commutes with the conjunction simplifier. -/
theorem progress_simpAnd {AP : Type} [DecidableEq AP] (σ : Label AP) (a b : Formula AP) :
    progress σ (simpAnd a b) = simpAnd (progress σ a) (progress σ b) := by
  have hatom : ∀ y ∈ a.conjuncts ++ b.conjuncts, y.conjuncts = [y] := by
    intro y hy
    rcases List.mem_append.mp hy with hy | hy <;> exact conjuncts_of_mem hy
  have hblock : ∀ (c : Formula AP), ∀ y ∈ c.conjuncts.flatMap (fun y => (progress σ y).conjuncts),
      y.conjuncts = [y] := by
    intro c y hy
    obtain ⟨z, _, hz⟩ := List.mem_flatMap.mp hy
    exact conjuncts_of_mem hz
  have hL : progress σ (simpAnd a b) =
      normAnd ((a.conjuncts ++ b.conjuncts).flatMap (fun y => (progress σ y).conjuncts)) := by
    rw [progress_eq_normAnd σ (simpAnd a b)]
    exact normAnd_flatMap_conjuncts_normAnd _ (by simp [progress, Formula.conjuncts]) _ hatom
  have hR : simpAnd (progress σ a) (progress σ b) =
      normAnd ((a.conjuncts ++ b.conjuncts).flatMap (fun y => (progress σ y).conjuncts)) := by
    show normAnd ((progress σ a).conjuncts ++ (progress σ b).conjuncts) = _
    rw [progress_eq_normAnd σ a, progress_eq_normAnd σ b, List.flatMap_append,
      normAnd_conjuncts_normAnd_append _ _ (hblock a), normAnd_append_conjuncts_normAnd _ _ (hblock b)]
  rw [hL, hR]

/-- Progression commutes with the disjunction simplifier. -/
theorem progress_simpOr {AP : Type} [DecidableEq AP] (σ : Label AP) (a b : Formula AP) :
    progress σ (simpOr a b) = simpOr (progress σ a) (progress σ b) := by
  have hatom : ∀ y ∈ a.disjuncts ++ b.disjuncts, y.disjuncts = [y] := by
    intro y hy
    rcases List.mem_append.mp hy with hy | hy <;> exact disjuncts_of_mem hy
  have hblock : ∀ (c : Formula AP), ∀ y ∈ c.disjuncts.flatMap (fun y => (progress σ y).disjuncts),
      y.disjuncts = [y] := by
    intro c y hy
    obtain ⟨z, _, hz⟩ := List.mem_flatMap.mp hy
    exact disjuncts_of_mem hz
  have hL : progress σ (simpOr a b) =
      normOr ((a.disjuncts ++ b.disjuncts).flatMap (fun y => (progress σ y).disjuncts)) := by
    rw [progress_eq_normOr σ (simpOr a b)]
    exact normOr_flatMap_disjuncts_normOr _ (by simp [progress, Formula.disjuncts]) _ hatom
  have hR : simpOr (progress σ a) (progress σ b) =
      normOr ((a.disjuncts ++ b.disjuncts).flatMap (fun y => (progress σ y).disjuncts)) := by
    show normOr ((progress σ a).disjuncts ++ (progress σ b).disjuncts) = _
    rw [progress_eq_normOr σ a, progress_eq_normOr σ b, List.flatMap_append,
      normOr_disjuncts_normOr_append _ _ (hblock a), normOr_append_disjuncts_normOr _ _ (hblock b)]
  rw [hL, hR]

end BoundedBrain
