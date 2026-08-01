---
summary: "Validation, rollout, stop, and rollback contract for Decision 98."
read_when:
  - "Validating or dogfooding Decision 98."
type: "validation_rollout_rollback"
status: "proposed"
decision_id: 98
---
# Validation, rollout, and rollback — correlated Pi agent-prompt observation v0

## Global rules

- Exact commits, trees, commands, counts, settings hashes, source realpaths, and negative claims are evidence.
- Passing package or host tests never proves runtime installation, provider receipt, model input, or benefit.
- Any indeterminate install/reload/provider result stops; do not retry mechanically.
- Use managed `TMPDIR`; preserve unrelated dirty files and pre-existing `.ontology/` paths.

## H0 host validation

Required cases:

1. unique token per prompt execution and equality only across its paired events;
2. overlapping preflights with reversed completion;
3. frozen extended `before_agent_start` and `agent_prompt_ready` event values;
4. complete pre-start chain before assignment and ready event;
5. ready event after agent-state assignment and before provider preparation;
6. handler error compatibility and old extension compatibility;
7. new/resume/fork/reload/shutdown token non-reuse;
8. no token in session entries, messages, provider payload, logs, or error text;
9. immutable capability object contains the exact token only on supporting hosts;
10. docs/types/exports and full coding-agent gates pass.

Stop if owner-main drift changes the ordering seam or if correctness requires durable run state/provider mutation.

## P0 package validation

Required cases:

1. all Decision-89 exact-append/digest/source-order cases remain;
2. unsupported-host precedence;
3. prepared state with private matching token;
4. exact whole-prompt match and mismatch vectors;
5. mismatch leaves contribution survival unknown;
6. latest preparation replaces the slot;
7. nonmatching and repeated ready events are no-ops;
8. overlapping runs cannot misattribute;
9. reset, shutdown, disable, expiry, grant replacement, mode drift, stale request/generation/cwd/compatibility, producer/validation/non-append failures clear correctly;
10. literal six-state command outputs and precedence;
11. no prompt-derived value or token in readback/log/session;
12. exactly one `before_agent_start` and one `agent_prompt_ready` registration;
13. extracted state module keeps `preflight-runtime.ts` at or below 500 LOC;
14. manifests, lockfiles, version `0.2.0`, entrypoint, release metadata, and semantic-release-delivery source/tests are unchanged;
15. focused, quality, full package, packaging/release, AST, and `git diff --check` gates pass.

Stop if the package must publish/rebind Pi, expose a token, retain multiple runs, or change another package.

## R1a integration validation

A deterministic faux provider records whether its call begins. The harness must show:

```text
before_agent_start(token)
-> host assignment
-> agent_prompt_ready(token, assigned prompt)
-> package terminal observation
-> provider preparation/call
```

Negative overlap and mismatch cases must demonstrate omission rather than misattribution. No external network/provider/model is allowed. Preserve complete command/test output and exact candidate identities.

## R1b preflight

Fail closed unless all are recorded:

- one exact Pi profile and applicable project settings;
- settings backup bytes/hash/mode/owner and restoration command;
- current host and ontology package sources/realpaths/commits/trees/versions;
- candidate host/package identities descending from accepted owner lines;
- exactly one configured ontology package after replacement;
- candidate and prior worktrees protected from concurrent mutation;
- one pinned provider/model identity and permission for exactly one bounded call;
- rollback authority independent of extension availability;
- no unrelated dirty settings/repository path in the mutation set.

## R1b live gates

- candidate protocol visible with default-off state;
- exactly one unsuffixed ontology command/tool provenance points to candidate;
- one fresh 30-second-confirmed, 10-minute TUI grant;
- enabled-none before the canary;
- one semantic task only;
- terminal exact-match or mismatch recorded without reinterpretation;
- ordinary status/inspect and optional exact-ID pack behavior remain healthy;
- immediate disable clears state;
- no second provider/model call, publication, default change, or production claim.

A mismatch is a valid dogfood result but blocks success closure until its cause is understood. A provider failure after a terminal observation preserves only agent-state evidence and still triggers rollback.

## B0 gates

Pre-register dataset, gold labels, metrics, floors, exclusions, and runtime coordinates before execution. Require dual annotation plus adjudication. Suggested minimum metrics:

- recall@3 and false-match rate;
- ambiguity and no-match accuracy;
- p50/p95 latency and timeout/unavailable rate;
- rendered bytes/tokens;
- deterministic replay equality.

No B1 task is created unless B0 meets its practical floors.

## Runtime rollback

Rollback is executed after R1b unless separately retained:

1. disable if the candidate command is available;
2. restore exact settings bytes, ownership, mode, source order, and prior sole package source;
3. restore the prior Pi host executable/specification;
4. create a fresh runtime generation;
5. verify prior package/host versions, command/tool source provenance, and ordinary ontology status/inspect behavior;
6. prove the candidate protocol and handler are absent;
7. compare restored settings hash to the preflight hash;
8. leave candidate/prior worktrees and unrelated caches/sessions untouched.

If exact restoration cannot be proved, stop and report partial rollback; do not delete or approximate state.

## Evidence closure

Each stage records evidence in AK under its owner task. Final Decision-98 closure cites:

- accepted H0/P0 commits and reviews;
- R1a harness result;
- R1b before/candidate/restored identities and one-call receipt;
- exact rollback result;
- B0 report and decision about B1;
- KES learning covering the divergent-lineage and unsafe-correlation discoveries.
