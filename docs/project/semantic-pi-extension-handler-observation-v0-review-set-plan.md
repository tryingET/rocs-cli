---
summary: "Strict review plan for Decision 89 extension-local handler observation v0."
read_when:
  - "Running Decision 89 convergence reviews."
type: "review_set_plan"
status: "proposed"
---
# Review set plan — extension-local handler observation v0

## Frozen set

Review identical committed bytes for:

1. `semantic-pi-extension-handler-observation-v0-problem-brief.md`;
2. `semantic-pi-extension-handler-observation-v0-evidence-note.md`;
3. `semantic-pi-extension-handler-observation-v0-rfc.md`;
4. this review-set plan.

Compute path, byte length, and SHA-256 rows sorted by UTF-8 path, then hash the row concatenation. Any byte change invalidates lane results.

## Closure mode

`multi_lane_requires_synthesis` with three mandatory lanes:

| Lane | Required question |
|---|---|
| Pi component implementability | Can `pi-ontology-workflows` implement the producer/outer-wrapper sequence and local record without a host change or heuristic inference? |
| Governance/security | Are host/provider/model/authenticity non-claims impossible to misread, and are self-produced digests kept non-authoritative? |
| Scope/debt | Does the proposal genuinely retire Decision-85 host complexity rather than hiding host claims in package-local wording or tests? |

Each lane returns `ready_for_adr`, `revise_rfc`, or `reject_direction`. Any blocker/material finding prevents synthesis.

## Mandatory checks

Every lane confirms:

- exact fixed package identity and no `pi-adapter` alias;
- outer handler observes only inner producer resolution and forwards the same value;
- sequential execution with no `Promise.all`;
- exact append boundary with no substring search;
- no host acceptance/assignment/readback/final-chain claim;
- no universal guard, stale-host, provider transmission, model influence, public authentication, publication, activation, or production claim;
- compatibility token is not evidence;
- local record is in-memory, self-produced, unsigned, and non-authoritative;
- malformed/failure paths produce no positive record;
- conformance cases do not drive behavior from IDs/expected values;
- Decision 85 and tasks `4331`/`4343` remain immutable non-reusable history;
- no implementation authority before accepted ADR and fresh owner tasks.

## Legal next move

Only a synthesis with all three `ready_for_adr` lanes, zero blockers, zero material findings, exact-byte agreement, and explicit insertion-claim retirement may advance Decision 89 to `decision_pending` and open an ADR.
