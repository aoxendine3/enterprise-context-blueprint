; ==============================================================================
; UNCONSTRAINED AGM CONTRACTION -- COUNTER-MODEL            EXPECTED: sat
; Same log model as agm_mtpo_monotonicity.smt2, but contraction is DEFINED as
; destructive retraction: the entry at index k is overwritten in place.
; A satisfying model is a concrete reordering/rewrite of committed history.
; This file exists so the companion UNSAT result is not vacuous.
; ==============================================================================
(set-logic QF_ALIA)

(declare-const H  (Array Int Int))
(declare-const n  Int)
(declare-const k  Int)
(declare-const H1 (Array Int Int))
(declare-const n1 Int)

(assert (>= n 0))
(assert (and (>= k 0) (< k n)))

; destructive contraction: overwrite committed entry k with 0 ("forget it")
(assert (= H1 (store H k 0)))
(assert (= n1 n))

; negation of monotonicity: committed prefix entry changed
(assert (distinct (select H1 k) (select H k)))

(check-sat)
(get-value (n k))
(exit)
