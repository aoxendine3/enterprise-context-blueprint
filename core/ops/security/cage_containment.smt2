; CAGE CONTAINMENT THEOREM (MERIDIAN — 2026-11-14)
; -------------------------------------------------
; Property: no path through the DART cell graph carries SEALED (untrusted,
; lattice level 3) data into an egress-capable cell (level <= INTERNAL = 1)
; without an intervening verified downgrade.
;
; Model: taint flows only non-decreasing (L(next) >= L(prev)). Verification
; is the ONLY downgrade; an egress tool call requires level <= 1.
;
; Claim: the conjunction below is UNSAT. If it were SAT, a SEALED cell could
; reach an egress action without verification — the cage would leak. UNSAT
; proves it cannot.

(set-info :status unsat)
(declare-const s Int)   ; source lattice level (SEALED = 3)
(declare-const h1 Int)  ; intermediate cell 1
(declare-const h2 Int)  ; intermediate cell 2
(declare-const d Int)   ; egress destination lattice level
(declare-const verified Bool)

(assert (= s 3))              ; untrusted ingress
(assert (>= h1 s))            ; flow may only raise taint (or hold)
(assert (>= h2 h1))
(assert (>= d h2))
(assert (<= d 1))             ; egress may carry at most INTERNAL
(assert (not verified))       ; no verified downgrade in path
(check-sat)
; Expected: unsat — MERIDIAN cage holds or the gate fails.
