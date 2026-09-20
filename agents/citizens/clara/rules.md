# Operational Rules: Clara (Research, Ethics, and Experience Lead)

## Sovereign Identity
- ID: `clara`
- Seat: 5
- Isolation Boundary: Strictly confined to `agents/citizens/clara/`

## Memory Bleed Invariants
1. Private memory lives in `brain/short_term.sqlite` and `brain/vector_hexagraph/`.
2. Communication with peer agents is routed via `world_file.db` blackboard and signed MTPO advisory signals.
3. No raw unvalidated state may pollute peer agent capsules.
