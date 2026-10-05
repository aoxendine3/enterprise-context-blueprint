# workspaces/attestation_service/schema.surql
# Sovereign SurrealDB Attestation Ledger Schema
# Locked LinJu Unification: Single Signed Root (CL4, XORAS, Cherry)

DEFINE TABLE attestation_edge SCHEMAFULL;

DEFINE FIELD source ON attestation_edge TYPE string;
DEFINE FIELD target ON attestation_edge TYPE string;
DEFINE FIELD signed_proof ON attestation_edge TYPE string;
DEFINE FIELD root_hash ON attestation_edge TYPE string;
DEFINE FIELD permissions ON attestation_edge TYPE string;
DEFINE FIELD expires_at ON attestation_edge TYPE datetime;
DEFINE FIELD revoked ON attestation_edge TYPE bool DEFAULT false;
DEFINE FIELD timestamp ON attestation_edge TYPE datetime DEFAULT time::now();

DEFINE INDEX idx_edge_lookup ON attestation_edge COLUMNS source, target, revoked;
DEFINE INDEX idx_root_hash ON attestation_edge COLUMNS root_hash;
