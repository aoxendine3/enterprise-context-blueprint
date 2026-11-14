# Security Policy

## Reporting a vulnerability

If you believe you have found a security flaw in XORAS, we want to know immediately.

**Do not open a public issue.** Email: `security@xoras.io` (PGP available on request).  
We acknowledge within 48 hours. We aim to ship a fix within 14 days for critical findings.

## What we consider in scope

- Privilege escalation through the agent swarm (unverified capability claims)
- Bypasses of the dual-witness gate or the Trinity Gate
- Merkle-DAG tampering — any way to advance an artifact without the dual witness agreeing
- WORM violations — any way to delete or overwrite committed evidence silently
- Data or key exfiltration through the conductor API or any agent runtime

## What is NOT in scope

- Issues in third-party dependencies (report them upstream; we will track them)
- Findings about deprecated artifacts in `barn/` (they are quarantined, not active)

## Disclosure

We practice coordinated disclosure. If you report in good faith, we will credit you in the changelog.
