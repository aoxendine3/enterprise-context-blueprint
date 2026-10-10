--------------------------- MODULE sovereign_gauntlet ---------------------------
(*
XORAS Sovereign 3-Layer Fail-Closed State Machine Specification
Layer 1: Formal State Model Checking (TLA+)
*)

EXTENDS Integers, Sequences, FiniteSets

VARIABLES state, trinity_votes, quarantine_ledger, evidence_hash

(* State Constants *)
INIT_STATE == "IDLE"
STATES == {"IDLE", "EVALUATING", "AUTHORIZED", "QUARANTINED"}

(* Safety Invariants *)
ZeroStatePollution == 
    state = "QUARANTINED" => Len(quarantine_ledger) > 0

TrinityConsensus2Of3 ==
    state = "AUTHORIZED" => trinity_votes >= 2

FailClosedOnAnomaly ==
    evidence_hash = "INVALID" => state = "QUARANTINED"

(* Initial State *)
Init ==
    /\ state = "IDLE"
    /\ trinity_votes = 0
    /\ quarantine_ledger = << >>
    /\ evidence_hash = "VALID"

(* State Transitions *)
ReceiveSignal(hash_val) ==
    /\ state = "IDLE"
    /\ evidence_hash' = hash_val
    /\ state' = "EVALUATING"
    /\ UNCHANGED <<trinity_votes, quarantine_ledger>>

CastTrinityVote(vote_pass) ==
    /\ state = "EVALUATING"
    /\ IF vote_pass THEN trinity_votes' = trinity_votes + 1 ELSE UNCHANGED trinity_votes
    /\ state' = IF trinity_votes' >= 2 THEN "AUTHORIZED" ELSE "EVALUATING"
    /\ UNCHANGED <<quarantine_ledger, evidence_hash>>

QuarantineAnomaly ==
    /\ state \in {"EVALUATING", "IDLE"}
    /\ (evidence_hash = "INVALID" \/ trinity_votes < 2)
    /\ state' = "QUARANTINED"
    /\ quarantine_ledger' = Append(quarantine_ledger, evidence_hash)
    /\ UNCHANGED <<trinity_votes, evidence_hash>>

Next ==
    \/ \E h \in {"VALID", "INVALID"} : ReceiveSignal(h)
    \/ \E v \in {TRUE, FALSE} : CastTrinityVote(v)
    \/ QuarantineAnomaly

Spec == Init /\ [][Next]_<<state, trinity_votes, quarantine_ledger, evidence_hash>>

=============================================================================
