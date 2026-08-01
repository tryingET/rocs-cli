---
summary: "Source-grounded evidence and claim limits for Decision 98."
read_when:
  - "Validating the Decision 98 retention-observation seam."
type: "evidence_note"
status: "proposed"
decision_id: 98
---
# Evidence note — Pi agent-prompt retention observation v0

## Verified package baseline

Decision-89 R0 was first implemented on a divergent local branch and was not suitable for installation. AK task `4407` corrected the lineage:

- live/default-lineage base: `0b6ed8b9d722e5128ed9b38ce4eba78d46321add`;
- reconciled candidate: `96f3b699b77b941522e0cada76672276919e2d6e`;
- package tree: `396630b4cf329d2e1a2a03fa9e4cb219381e89eb`;
- package version: `0.2.0`;
- focused result: 34 passed, 0 failed;
- full package result: 103 passed, 1 skipped, 0 failed;
- independent review: `dispatch-1785562937712` accepted after the same-key completion-order case was added;
- AK evidence: `5748` through `5751`.

No install, reload, runtime, provider, or model action occurred under task `4407`.

## Verified Pi-host ordering

At Pi host source revision `0e773d7b0e17dacbe766e174570ab38ef619ff75`:

- `packages/coding-agent/src/core/extensions/runner.ts` `emitBeforeAgentStart()` awaits each handler in extension order and chains returned `systemPrompt` values;
- `packages/coding-agent/src/core/agent-session.ts` awaits that combined result and assigns it to `agent.state.systemPrompt` before agent execution;
- Pi subsequently emits `agent_start`;
- `ExtensionContext.getSystemPrompt()` reads the current session agent-state prompt;
- `docs/extensions.md` documents that `agent_start` follows `before_agent_start` and that `getSystemPrompt()` reports Pi's current system prompt, while provider-level rewrites remain separate.

This supports a bounded runtime observation at `agent_start`. It does not make the package record authentic against co-resident extensions, nor does it attest a provider payload.

## Claim ladder

| Boundary | Decision 89 | Proposed Decision 98 |
|---|---:|---:|
| exact package append prepared | yes | referenced |
| package callback progressed to host `agent_start` | no | yes, bounded to the matching slot |
| Pi agent-state prompt at `agent_start` matched prepared digest | no | yes/no observation |
| final provider-specific payload | no | no |
| bytes transmitted or received | no | no |
| model input or influence | no | no |

A `retained` result means only that the byte length and domain-separated digest observed through `ctx.getSystemPrompt()` at `agent_start` equal the prepared return prompt fields. A `replaced` result means they do not equal. Digest equality is ordinary byte-comparison evidence, not provenance or semantic correctness.

## Operational gap

Default user settings currently select a local live-worktree package source rather than the reconciled candidate. Local-path package identity is resolved by absolute path, so adding a second candidate path can load duplicate extensions. A later R1 task must replace the old source, prove exactly one configured package, reload, verify the protocol revision, and exercise rollback.

## Empirical gap

Neither Decision 89 nor this proposed Decision 98 shows that ROCS candidates are relevant or improve agent behavior. Retrieval relevance (B0) and model-mediated benefit (B1/B2) require separate semantic-owner and DSPx/Oracle evaluation. Provider/model use remains separately gated.
