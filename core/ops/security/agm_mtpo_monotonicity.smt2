; ==============================================================================
; MTPO TRAJECTORY MONOTONICITY -- SEMANTIC ENCODING (v2, replaces circular v1)
; Logic: QF_ALIA (arrays + linear integer arithmetic)   EXPECTED: unsat
;
; MODEL. A trajectory is a log: an array H : Int -> Int of entries with length n.
; Entry values encode a state delta; the algebraic inverse of delta d is (- d).
;
; MTPO operations are defined by what they DO to the log:
;   expansion          : H' = store(H, n, d)        , n' = n + 1
;   saga contraction   : H' = store(H, n, -H[k])    , n' = n + 1   (append inverse
;                        of an earlier entry k < n; history is never overwritten)
;
; MONOTONICITY (prefix-immutability): n' >= n and for every i < n, H'[i] = H[i].
;
; The negation is asserted: some committed prefix entry changed OR the log shrank.
; UNSAT follows from the array read-over-write axiom, NOT from an assumption
; that MTPO is monotonic.
;
; SCOPE: proves the abstract log model only. It says nothing about integer
; overflow of ranks, memory reordering, crashes, or non-invertible side effects.
; ==============================================================================
(set-logic QF_ALIA)

(declare-const H  (Array Int Int))
(declare-const n  Int)
(declare-const k  Int)          ; entry being compensated
(declare-const d  Int)          ; new delta for expansion
(declare-const op Int)          ; 1 = expansion, 2 = saga contraction

(assert (>= n 0))
(assert (and (>= k 0) (< k n)))
(assert (or (= op 1) (= op 2)))

(declare-const H1 (Array Int Int))
(declare-const n1 Int)

(assert (=> (= op 1) (and (= H1 (store H n d))            (= n1 (+ n 1)))))
(assert (=> (= op 2) (and (= H1 (store H n (- (select H k)))) (= n1 (+ n 1)))))

; --- negation of monotonicity: exists a witness index i that breaks it ---
(declare-const i Int)
(assert (or (< n1 n)
            (and (>= i 0) (< i n) (distinct (select H1 i) (select H i)))))

(check-sat)
(exit)
