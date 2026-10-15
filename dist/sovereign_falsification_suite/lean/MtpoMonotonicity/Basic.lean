/-!
# MTPO trajectory monotonicity — machine-checked in Lean 4

Mirrors `agm_mtpo_monotonicity.smt2` / `agm_unconstrained_violation.smt2`:
the log is an SMT-style array `H : Int → Int` with length `n`, and `store` is
the SMT-LIB `store`. This file goes beyond the Z3 encoding in one respect:
the Z3 file checks a *single step*; here monotonicity is proved for
*every finite sequence* of MTPO steps (`reaches_monotone`).

Scope (same as the SMT2): an abstract append-only log. Nothing here models
concurrent writers, ranks, crashes, integer overflow, or non-invertible
side effects.

No `sorry`, no new axioms. `lake build` prints `#print axioms` for every
headline theorem; `check_lean.py` fails if `sorryAx` appears.
-/

namespace Mtpo

/-- SMT-LIB array `store`. -/
def store (H : Int → Int) (i v : Int) : Int → Int :=
  fun j => if j = i then v else H j

/-- A step from `(H, n)` to `(H', n')` is monotone iff the log did not shrink
and every committed entry (index `< n`) is unchanged. -/
def Monotone (H : Int → Int) (n : Int) (H' : Int → Int) (n' : Int) : Prop :=
  n ≤ n' ∧ ∀ i, 0 ≤ i → i < n → H' i = H i

/-- The two MTPO operations: expansion appends `d`; saga contraction of the
entry at `k` appends its algebraic inverse. Neither overwrites history. -/
inductive Step : (Int → Int) × Int → (Int → Int) × Int → Prop
  | expand (H : Int → Int) (n d : Int) :
      Step (H, n) (store H n d, n + 1)
  | saga (H : Int → Int) (n k : Int) :
      Step (H, n) (store H n (-(H k)), n + 1)

/-- Finite sequences of steps. -/
inductive Reaches : (Int → Int) × Int → (Int → Int) × Int → Prop
  | refl (s) : Reaches s s
  | tail {s t u} : Reaches s t → Step t u → Reaches s u

theorem monotone_refl (H : Int → Int) (n : Int) : Monotone H n H n :=
  ⟨Int.le_refl n, fun _ _ _ => rfl⟩

theorem monotone_trans {H H' H'' : Int → Int} {n n' n'' : Int}
    (a : Monotone H n H' n') (b : Monotone H' n' H'' n'') :
    Monotone H n H'' n'' := by
  refine ⟨Int.le_trans a.1 b.1, ?_⟩
  intro i h0 h1
  have h2 : i < n' := Int.lt_of_lt_of_le h1 a.1
  rw [b.2 i h0 h2, a.2 i h0 h1]

/-- One MTPO step is monotone. (Z3: `agm_mtpo_monotonicity.smt2` is `unsat`.) -/
theorem step_monotone {s t : (Int → Int) × Int} (h : Step s t) :
    Monotone s.1 s.2 t.1 t.2 := by
  cases h with
  | expand H n d =>
    refine ⟨by omega, ?_⟩
    intro i _ hi
    have : i ≠ n := by omega
    simp [store, this]
  | saga H n k =>
    refine ⟨by omega, ?_⟩
    intro i _ hi
    have : i ≠ n := by omega
    simp [store, this]

/-- Every finite sequence of MTPO steps is monotone. Stronger than the SMT2
single-step check. -/
theorem reaches_monotone {s t : (Int → Int) × Int} (h : Reaches s t) :
    Monotone s.1 s.2 t.1 t.2 := by
  induction h with
  | refl => exact monotone_refl s.1 s.2
  | tail _ hs ih => exact monotone_trans ih (step_monotone hs)

/-- Destructive AGM contraction: overwrite committed entry `k` in place. -/
def destructive (H : Int → Int) (n k : Int) : (Int → Int) × Int := (store H k 0, n)

/-- Destructive contraction is NOT monotone: explicit witness.
(Z3: `agm_unconstrained_violation.smt2` is `sat`.) -/
theorem destructive_not_monotone :
    ∃ (H : Int → Int) (n k : Int), 0 ≤ k ∧ k < n ∧
      ¬ Monotone H n (destructive H n k).1 (destructive H n k).2 := by
  refine ⟨fun _ => 1, 1, 0, by omega, by omega, ?_⟩
  intro h
  have := h.2 0 (by omega) (by omega)
  simp [destructive, store] at this

/-- Mutant of saga contraction that overwrites entry `k` with its inverse
instead of appending. -/
def sagaMutant (H : Int → Int) (n k : Int) : (Int → Int) × Int :=
  (store H k (-(H k)), n + 1)

/-- The mutant is NOT monotone, so the monotonicity theorem is not vacuous.
(Z3: the mutated MTPO file is `sat`.) -/
theorem mutant_not_monotone :
    ∃ (H : Int → Int) (n k : Int), 0 ≤ k ∧ k < n ∧
      ¬ Monotone H n (sagaMutant H n k).1 (sagaMutant H n k).2 := by
  refine ⟨fun _ => 1, 1, 0, by omega, by omega, ?_⟩
  intro h
  have := h.2 0 (by omega) (by omega)
  simp [sagaMutant, store] at this

end Mtpo

#print axioms Mtpo.step_monotone
#print axioms Mtpo.reaches_monotone
#print axioms Mtpo.destructive_not_monotone
#print axioms Mtpo.mutant_not_monotone
