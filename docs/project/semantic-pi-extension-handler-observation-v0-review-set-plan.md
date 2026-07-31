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

1. `docs/project/semantic-pi-extension-handler-observation-v0-problem-brief.md`;
2. `docs/project/semantic-pi-extension-handler-observation-v0-evidence-note.md`;
3. `docs/project/semantic-pi-extension-handler-observation-v0-rfc.md`;
4. `docs/project/semantic-pi-extension-handler-observation-v0-review-set-plan.md`.

For each reviewed repository-relative POSIX path above, compute exact byte length and ordinary SHA-256. Serialize one ASCII row exactly as `path<TAB>byte_length<TAB>sha256<LF>`, where byte length is canonical unsigned decimal and SHA-256 is 64 lowercase hexadecimal characters without a prefix. Sort complete rows by unsigned UTF-8 path bytes, concatenate them with no header or extra bytes, and compute ordinary SHA-256 over that concatenation. Any byte change invalidates lane results.

## Closure mode

`multi_lane_requires_synthesis` with three mandatory lanes:

| Lane | Required question |
|---|---|
| Pi component implementability | Can current `pi-ontology-workflows` integrate the pure producer/outer-wrapper sequence and local record without a host change, second host-ordered handler, heuristic inference, or regression to existing hint/framing behavior? |
| Governance/security | Are host/provider/model/authenticity non-claims impossible to misread, and are self-produced digests kept non-authoritative? |
| Scope/debt | Does the proposal genuinely retire Decision-85 host complexity rather than hiding host claims in package-local wording or tests? |

Each lane returns `ready_for_adr`, `revise_rfc`, or `reject_direction`. Any blocker/material finding prevents synthesis.

These are conceptual subreviews, not three invented AK runtime tracks. The designated synthesizer records their exact-byte results in the review memo/synthesis for AK's active `current_track`; AK decision artifacts, required-track coverage, and legal review closure remain transition authority.

## Mandatory checks

Every lane confirms:

- exact fixed package identity and no `pi-adapter` alias;
- outer handler observes only inner producer resolution, prepares the same value, and assigns one immutable bounded diagnostic slot as its final package operation before the source-level return statement;
- runtime records claim no execution of that return statement, callback return, or promise settlement; separate package-harness evidence stays separate;
- sequential execution with no `Promise.all` supplying acceptance evidence;
- exact append boundary with no substring search, while current non-append framing replacement remains unrecorded and behaviorally preserved;
- disabled observation preserves existing disabled-mode handler behavior and creates no record;
- same-runtime reload/new/resume/fork slot clearing is explicit and makes no re-instantiation claim;
- exact protocol revision, single-slot replacement/clearing, concurrent post-settlement linearization, grant replacement, and observed expiry are closed without an observation ID/generation/history protocol;
- no host acceptance/assignment/readback/final-chain claim;
- no universal guard, stale-host, provider transmission, model influence, public authentication, publication, activation, or production claim;
- compatibility token is not evidence;
- local record is in-memory, self-produced, unsigned, and non-authoritative;
- malformed/failure paths produce no positive record;
- conformance cases do not drive behavior from IDs/expected values;
- Decision 85 and tasks `4331`/`4343` remain immutable non-reusable history;
- accepted supersession requires the supported AK transition of Decision 85 to state/outcome `superseded`; already-resolved link reevaluation values remain historical and the stopped task graphs are never reopened or reused;
- review and accepted ADR remain non-executing; implementation requires a fresh owner-scoped package task and later runtime/release actions require their own authority.

## Legal next move

Only after all three conceptual lanes return `ready_for_adr` with zero blockers/material findings and exact-byte agreement may the designated synthesizer author the required review memo/synthesis for AK's active `current_track`. The controller must attach the governed artifacts, verify `ak decision passport 89 -F json` reports required-track coverage and legal review closure `ready_for_adr`, and follow the AK decision membrane for the next transition. This plan alone cannot advance Decision 89 or open an ADR.
