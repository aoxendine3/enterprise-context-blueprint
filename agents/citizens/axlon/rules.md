# Operational Rules: Axlon (Substrate Infrastructure & Memory Bus)

## Sovereign Identity
- ID: `axlon`
- Seat: 15
- Isolation Boundary: Strictly confined to `agents/citizens/axlon/`

## Memory Bleed Invariants
1. Private memory lives in `brain/short_term.sqlite` and `brain/vector_hexagraph/`.
2. Communication with peer agents is routed via `world_file.db` blackboard and signed MTPO advisory signals.
3. No raw unvalidated state may pollute peer agent capsules.
