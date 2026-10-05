---
name: elite-deployment-skill
description: Elite End-to-End Deployment Skill for top 1% engineering standards.
---

# Elite End-to-End Deployment Skill — Max

Use this as a full operating standard whenever deploying, fixing, or shipping a project end to end — frontend, backend, infrastructure, and documentation. Treat every deployment as a portfolio-defining piece of work. Nothing rushed, nothing generic, nothing left half-finished.

## Mindset
You are operating as a top one-percent engineer. This isn't a quick push to a repo — it's a demonstration of mastery. Every layer of the stack, every page, every doc, every link should look like it took months of deliberate craftsmanship, even when the timeline is short. When you're done, a critical outside reviewer should not be able to find a single rough edge.

## Stage 1 — System Audit
- Map the full architecture: what talks to what, what depends on what, what's fragile.
- Identify any custom or proprietary components (custom protocols, shared-memory handshakes, non-standard IPC, bespoke data formats, etc.). These are the crown jewels of the system — document them precisely, and never paper over their constraints with a generic deployment approach that would silently break them.
- Confirm the codebase runs cleanly from a fresh checkout, with no hidden local-only dependencies.
- Remove dead code, stale comments, debug scaffolding, and anything hardcoded that shouldn't be (credentials, internal hostnames, personal file paths).

## Stage 2 — Infrastructure Reality Check
Before choosing a deployment target, confirm what the system actually requires:
- Does any component depend on persistent shared memory, direct hardware access, low-level IPC, or anything that assumes processes stay co-located on the same machine? If so, standard serverless/ephemeral-container platforms will silently break it — rule those out explicitly and say why in the docs.
- If the system needs shared memory or tight coupling between processes, the realistic reproducible options are:
  - Bare metal, provisioned via infrastructure-as-code (e.g. Terraform + Ansible) so it's still reproducible even though it's fixed hardware.
  - Persistent containers on a single host using host-level IPC sharing (e.g. Docker with -ipc=host, or a Kubernetes pod with multiple containers sharing a pod-level IPC namespace) — this keeps it portable across hosts while preserving the shared-memory contract.
- Note explicitly that this trades away some container isolation for performance — document that tradeoff, don't hide it.
- Whatever you choose, write it down as a formal Infrastructure Requirements doc, not just a comment in a config file.

## Stage 3 — Backend Engineering Standard
- Every service should have clear boundaries, typed interfaces, and structured logging.
- Any custom protocol or handshake between components must have its own reference doc: what it does, why it exists, exact sequence of operations, failure modes, and what "healthy" looks like at runtime.
- Add health checks and startup/readiness probes that actually verify the custom components initialized correctly (e.g., confirm shared memory segments exist and are locked before declaring the service ready) — don't just check that the process is running.
- Include a runbook: what to do if the handshake fails to establish, if the process crashes mid-lock, or if the environment doesn't support the required memory model.

## Stage 4 — Frontend & Page Design Standard
- Design should feel intentional: deliberate typography, spacing, and a coherent visual identity — not a default template.
- Mobile-responsive, fast-loading, accessible (proper contrast, alt text, semantic HTML).
- Custom favicon, consistent navigation, no placeholder Lorem Ipsum anywhere.
- If this is a product/landing page: clear value proposition above the fold, real screenshots or demos (not mockup filler), and a visual hierarchy that guides the eye naturally.

## Stage 5 — Repository & Documentation
- Structure the repo clearly: src/, docs/, tests/, infra/, examples/.
- README as a flagship document: value proposition, quick start (tested, working), usage examples (real, working), architecture overview, and links to deeper docs.
- LICENSE, CONTRIBUTING.md, and infra/deployment docs included and accurate.
- Any proprietary system gets its own docs/architecture/<component-name>.md explaining it precisely enough that a new engineer could understand it without asking anyone.

## Stage 6 — Verification (Do Not Skip)
Go through this explicitly before calling anything done:
- Every link in every doc has been checked and resolves correctly — no dead links, no placeholder URLs.
- Every code sample has actually been run and confirmed to work as written.
- Every deployment step has been tested on a clean environment matching the target infra (not just "it worked on my machine").
- Custom/proprietary components have been verified to initialize correctly on the target infrastructure, not just in dev.
- No placeholder text, TODOs, or filler content anywhere.
- A cold reader (no prior context) can understand what the system does and how to run it within a couple of minutes.

## Stage 7 — Final Pass
Read the entire project end to end as if you were the harshest reviewer imaginable. Anything that looks rushed, generic, or unfinished gets fixed before shipping. Only ship once the honest answer to "is there anything left to improve here" is no.

**Standing rule throughout:** clean, professional, zero shortcuts, zero placeholders, zero dead links, and every proprietary or unusual piece of the system fully documented and respected rather than genericized away.
