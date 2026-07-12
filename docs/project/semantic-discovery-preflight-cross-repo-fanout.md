---
summary: "Decision:52 owner-repo execution fan-out across ROCS, Pi host, Pi ontology adapter, and vertical-slice proof."
read_when:
  - "Routing decision:52 implementation tasks."
  - "Checking cross-repo sequencing and owner boundaries."
type: "cross_repo_fanout"
status: "active"
---
# Cross-Repo Fan-Out — Decision 52

## Governing artifacts

- Decision: `52` — accepted and unblocked
- ADR: `docs/adr/2026-07-12-deterministic-semantic-discovery-and-pi-preflight.md`
- Implementation plan: `semantic-discovery-preflight-implementation-plan.md`
- Validation/rollback: `semantic-discovery-preflight-validation-rollout-rollback.md`
- Production dependency: decision `53`

## Owner packages

| Slice | Task | Repo | Depends on | Owner result |
|---|---:|---|---|---|
| I1 protocol substrate | `3815` | `core/rocs-cli` | — | executable Python schema/JCS/digest fixtures |
| I2 discovery core | `3817` | `core/rocs-cli` | 3815 | snapshot + lexical discovery |
| I3 CLI/bound pack | `3818` | `core/rocs-cli` | 3817 | capabilities/discover/bound-pack contracts |
| I4 Pi host identity | `3819` | `softwareco/contrib/pi-mono` | — | immutable host capability identity |
| I5 Pi runner/inspect | `3820` | `softwareco/owned/pi-extensions` | 3818, 3819 | verified runner and gated search |
| I6 prompt lifecycle | `3821` | `softwareco/owned/pi-extensions` | 3820 | TUI-confirmed prompt-run adapter |
| I7 vertical slice | `3822` | `core/rocs-cli` | 3818, 3821 | disposable offline replay/rollback proof |

## Execution route

```text
3815 -> 3817 -> 3818 ─┐
                       ├-> 3820 -> 3821 -> 3822
3819 ─────────────────┘
```

Tasks are linked to decision `52` as `post_adr_execution` and were explicitly reevaluated `still_valid` before unblocking.

## Current ready leaves

- `3815` — ROCS protocol substrate
- `3819` — Pi host capability identity

They may execute in parallel because neither imports the other's authority.

## Non-authorizations

- Do not open production/adoption/default/fleet tasks under decision `52`.
- Do not change ontology meaning.
- Do not treat vertical-slice evidence as decision `53` acceptance.
- Do not reuse cross-repo task links as a second decision gate.
