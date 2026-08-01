---
summary: "Source-grounded evidence and claim limits for Decision 98."
read_when:
  - "Validating the Decision 98 agent-prompt observation seam."
type: "evidence_note"
status: "proposed"
decision_id: 98
---
# Evidence note — Pi agent-prompt observation v0

## Package baseline

AK task `4407` corrected the original Decision-89 lineage error:

- live-lineage base `0b6ed8b9d722e5128ed9b38ce4eba78d46321add`;
- reconciled candidate `96f3b699b77b941522e0cada76672276919e2d6e`;
- package tree `396630b4cf329d2e1a2a03fa9e4cb219381e89eb`, version `0.2.0`;
- focused 34/34 and full 103 passed, 1 skipped, 0 failed;
- accepted review `dispatch-1785562937712`;
- AK evidence `5748`–`5751`.

No runtime action occurred.

## Host evidence and discovered gap

At Pi host revision `0e773d7b0e17dacbe766e174570ab38ef619ff75`, `emitBeforeAgentStart()` awaits and chains handlers; `AgentSession` assigns the combined prompt before agent execution; `agent_start` follows and `getSystemPrompt()` reads agent state.

Strict review nevertheless found two blockers:

1. Pi can overlap asynchronous prompt preflights before `_isAgentRunActive` is set, while current events expose no shared run identity. A single slot can therefore be consumed by the wrong `agent_start`.
2. Existing `prompt.system.chain.v1` does not guarantee assignment-before-observation, shared correlation, or `getSystemPrompt()` semantics at that seam.

Consequently, Decision 98 must require an owner-supplied host capability rather than infer the contract from one host revision.

## Required host contract

Proposed capability `prompt.agent-state.observation.v1` guarantees:

- one opaque host-generated `promptRunToken` per prompt execution;
- the same token is present in `before_agent_start` and a new `agent_prompt_ready` event;
- `agent_prompt_ready` fires after the complete `before_agent_start` chain and assignment to Pi agent state, but before the corresponding provider turn begins;
- `event.systemPrompt` is the assigned Pi agent-state prompt for that token;
- tokens are process-local correlation values only, not authority, credentials, or durable identity.

The package stores only the latest token in closure state, never returns or persists it, and ignores nonmatching events. This resolves overlap without a collection.

## Claim ladder

| Boundary | Decision 89 | Decision 98 proposal |
|---|---:|---:|
| exact append prepared | yes | referenced |
| matching host run correlated | no | yes |
| assigned whole agent prompt exactly matched prepared bytes | no | yes/no |
| contribution survived inside a modified prompt | no | unknown |
| provider payload/transmission/model behavior | no | no |

## Evaluation ladder

- **B0 — retrieval usefulness:** deterministic ROCS relevance, ambiguity, no-match, latency, and block-cost evaluation against adjudicated prompts; no model claim.
- **B1 — behavioral mediation pilot:** randomized correct/disabled/sham arms on one pinned provider/model; asks whether context changes observable pack-selection and semantic behavior; not a production-benefit claim.
- **B2 — meaningful benefit:** powered held-out study with preregistered practical margin, safety/cost limits, and fixed runtime identities; only the measured setup is supported.

A pinned provider/model TUI canary in rollout is engineering integration evidence. It is not B1 or B2 unless executed under their preregistered experimental contracts.

## Ownership

- `core/rocs-cli`: Decision-98 architecture/ADR and semantic claim wording.
- Pi host owner: capability/event implementation and host tests.
- `pi-extensions` / `pi-ontology-workflows`: package state/readback implementation and package tests.
- Pi operator/runtime owner: settings replacement, reload/start, rollback, and TUI canary evidence.
- ROCS semantic owner: B0 gold/retrieval evidence.
- DSPx/Oracle: B1/B2 empirical analysis.
- AK: task, decision, evidence, and lineage references only.
