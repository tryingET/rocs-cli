---
summary: "Tier-1 problem brief for deterministic task-language semantic discovery and safe Pi semantic preflight."
read_when:
  - "Reviewing the decision trigger for semantic discovery and Pi preflight."
  - "Determining why this concern requires an AK architecture decision."
type: "problem"
status: "proposed"
---

# Problem Brief — Deterministic Semantic Discovery and Pi Preflight v0

## Trigger

ROCS provides deterministic exact-ID ontology retrieval, while Pi agents normally begin with ordinary task language and do not know the governed ontology IDs they may need. `pi-ontology-workflows` currently fills that gap with a package-local search implementation after `rocs build`.

The result is a cross-owner architecture gap rather than a small search-quality issue.

## Current failure shape

- ROCS and Pi contain separate retrieval behavior.
- Pi search performs a build and reads mutable generated artifacts.
- Search results are not bound to the complete corpus that influenced ranking.
- No portable request/result contract exists for Pi, DSPx, or another consumer.
- Startup knows repository context but not the actual user task.
- Prompt-time ontology injection can accidentally elevate repository-controlled prose into system-role instructions.
- Consumer launchers, environment overrides, mutable source checkouts, and cache effects can introduce ambient execution or identity drift.
- Operational unavailability, lexical no-match, applicability, and ambiguity can be conflated.

## Why this is Tier 1

The proposed correction changes:

- a shared ROCS command and result contract;
- semantic identity and replay expectations;
- the boundary between ROCS semantic retrieval and Pi adapter behavior;
- Pi session lifecycle and prompt composition;
- cross-repo rollout and rollback posture;
- eventual consumer adoption and release-capsule integration.

It therefore changes architecture, shared interfaces, authority boundaries, and default workflow behavior across at least two repositories.

## Desired outcome

Ordinary task language should produce deterministic, replayable semantic candidates from a precisely identified ontology corpus. Pi should deliver only bounded, safe, turn-local orientation and route full semantic retrieval through an explicit exact-ID tool call.

The architecture must remain:

- offline-first;
- deterministic;
- model-optional and proposal-only;
- source-owner-correct;
- non-mutating during automatic preflight;
- explicit about ambiguity, failure, development state, and adoption state.

## Decision boundary

The requested decision is whether to adopt ROCS-owned deterministic discovery with a thin Pi semantic-preflight adapter as the target architecture.

The decision does not itself authorize:

- default or fleet enablement;
- a production release-capsule identity;
- a vendored-runtime trust root;
- mandatory semantic enforcement;
- embeddings or model reranking;
- ontology mutation or semantic release approval.

## Primary artifacts

- [ROCS deterministic discovery RFC](semantic-discovery-protocol-v0.md)
- [Pi semantic-preflight companion RFC](../../../../softwareco/owned/pi-extensions/packages/pi-ontology-workflows/docs/project/semantic-preflight-adapter-v0.md)
- [Evidence note](semantic-preflight-evidence-note-v0.md)
