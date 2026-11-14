# XMARS On-Demand Worker Orchestration — Build Blueprint

**Status:** Implementation blueprint and starter contract. Not installed, deployed, or executed against your Google Cloud project or local SSOT. The pasted ADK source establishes seven configured conductors, but does not include the worker runtime, Agent Registry tool schemas, existing MTPO implementation, or MARS verifier. Those must be inspected before wiring or replacing components.

## Target

Preserve DAXX and DAXX-2 through DAXX-8. Replace the instruction-only “12 helpers” claims with a real runtime capability that accepts bounded worker tasks, executes only requested workers, returns attributable results, and records mission events. A conductor may request up to 12 workers per mission; do not launch all 84 by default. Recursive delegation is bounded by maximum depth, budget, and cycle detection.

## Runtime flow

1. Create a mission ID and compile an immutable REASONS specification (requirements/DoD, entities, approach, structure, operations, norms, safeguards).
2. Assign each conductor task a stable task ID, owner conductor, bounded input/context references, allowed capabilities, rank, and read/write footprint.
3. The existing worker dispatcher creates or schedules workers only when called. Each worker reports structured status, artifacts/evidence references, errors, and proposed writes.
4. Existing MTPO implementation orders conflicting state changes and emits advisory events. Ranks alone are not memory synchronization; preserve the current memory ownership/synchronization design.
5. Existing MARS verifier evaluates actual changes. Record approval separately from execution and verified outcome.
6. Return mission events/results to the existing cockpit; use existing memory/journals without migration or duplication.

## Minimal Python contract (illustrative adapter boundary)

This is deliberately a protocol sketch, not a drop-in implementation. Bind it to the existing registry/runtime after inspecting actual tool schemas.

```python
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

@dataclass(frozen=True)
class WorkerTask:
    mission_id: str
    task_id: str
    parent_task_id: str | None
    owner_conductor: str
    worker_role: str
    rank: int
    depth: int
    task_budget: int
    requirements: tuple[str, ...]
    input_refs: tuple[str, ...]  # references, not copied journals
    read_set: tuple[str, ...]
    write_set: tuple[str, ...]
    allowed_tools: tuple[str, ...]

@dataclass
class WorkerResult:
    mission_id: str
    task_id: str
    worker_id: str
    status: Literal['completed', 'failed', 'blocked']
    summary: str
    evidence_refs: list[str] = field(default_factory=list)
    proposed_changes: list[str] = field(default_factory=list)
    error: str | None = None

class WorkerRuntime(Protocol):
    async def execute(self, task: WorkerTask) -> WorkerResult: ...

async def dispatch_batch(runtime: WorkerRuntime,
                         tasks: list[WorkerTask],
                         max_per_conductor: int = 12) -> list[WorkerResult]:
    owners = {t.owner_conductor for t in tasks}
    if len(owners) > 1:
        raise ValueError('one dispatch batch must have one owning conductor')
    if len(tasks) > max_per_conductor:
        raise ValueError('conductor worker limit exceeded')
    if len({t.task_id for t in tasks}) != len(tasks):
        raise ValueError('duplicate task id')
    # Production version must add durable scheduling, cancellation,
    # timeouts, retries, per-worker identity, and audit event writes.
    import asyncio
    return await asyncio.gather(*(runtime.execute(t) for t in tasks))
```

## Required runtime events

`mission_created`, `reasons_compiled`, `worker_requested`, `worker_started`, `worker_completed|failed|blocked`, `mtpo_conflict|advisory|recovery`, `mars_check_started|passed|failed`, `approval_recorded`, `execution_started|succeeded|failed`, `outcome_verified`.

Every event must include mission/task/agent IDs, timestamp, source reference, and status. Do not store secrets or duplicate private memory contents in logs.

## Acceptance tests

- One conductor dispatches two distinct workers; runtime evidence proves both invoked and results attributed correctly.
- Twelve workers for one conductor accepted; thirteen rejected or safely split into separately authorized batches.
- Duplicate task IDs and unauthorized roles rejected.
- Recursion beyond configured depth/budget blocked; cycles detected.
- Injected overlapping write produces the existing MTPO conflict/advisory/recovery behavior, if implemented; otherwise test is marked unavailable, not simulated as passed.
- MARS approval is distinct from execution; failed execution cannot be reported as success.
- Worker/runtime outage, timeout, cancellation, restart, and partial results reported honestly.
- Existing memory stores unchanged; worker context uses scoped references.
- DAXX-4 attack finding and DAXX-6/8 response can be correlated to one mission, without counting helper outputs as conductor votes.

## Integration sequence

1. Inspect Agent Registry MCP schemas and current runtime/dispatcher; inventory existing MTPO, MARS, REASONS, and memory interfaces.
2. Implement the adapter using the existing language/runtime and APIs. Do not assume Python is the production runtime.
3. Add worker dispatch tool to the appropriate conductor configurations; retain the seven visual nodes.
4. Run unit/contract tests in an isolated fixture, then two-worker mission, then 12-worker load test.
5. Test on a branch or isolated environment; preserve current work and memory.
6. Deploy only after review and observed evidence; record exact commit/config revision and test outputs in canonical SSOT.

## Not established by this artifact

No Google project access, deployment, agent invocation, real worker spawn, MTPO operation, MARS pass, memory mutation, or test execution occurred in this chat. The screenshot/configuration and pasted code are inputs, not deployment credentials or runtime traces.
