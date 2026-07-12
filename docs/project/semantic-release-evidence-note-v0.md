---
summary: "Bounded current-state evidence for decision:53 semantic release and adoption review."
read_when:
  - "Reviewing evidence behind decision:53."
type: "evidence_note"
status: "review_pending"
---
# Evidence Note — Semantic Release and Consumer Adoption v0

## Established facts

- Decision `52` is accepted and development execution tasks `3815`, `3817`–`3822` are done.
- ROCS owns strict semantic discovery schemas, canonicalization, immutable snapshots, explicit tool identity, and bound-pack verification.
- Pi host commit `5be4473cc156eb03d0069cc6770f1b95ea9eac97` supplies immutable extension API identity and exact modes.
- Pi adapter commits `2e37f63c40ccca073dddc51c5fdc26ce4a6ccd2f`, `ce606e9e`, and `5719669cf4476f5f33cc9ac082b2de3af6940dd2` supply strict runtime/protocol verification and default-off TUI lifecycle behavior.
- The sanitized vertical receipt at [`../../artifacts/semantic-preflight/decision52-i7-receipt.json`](../../artifacts/semantic-preflight/decision52-i7-receipt.json) proves development discovery and bound pack only; it explicitly records `adopted_runtime=false`.
- ROCS `uv.lock` remains SHA-256 `2faf5bc9a99011b4eeb7c99f3464ee6bdd6f720173c954a4264f246cdb5272f9`.

## Missing production evidence

No accepted artifact currently proves:

- an ontology-owner-approved immutable semantic capsule;
- namespace/version uniqueness and predecessor lineage;
- a consumer-owned exact desired-state intent;
- externally anchored runtime and capsule trust independent of the consumer tree;
- deterministic adoption and use receipt schemas/fixtures;
- compatibility policy fixtures spanning compatible, conditional, breaking, and unknown;
- semantic N→N−1 and no-prior rollback rehearsal;
- independent runtime rollback while preserving semantic receipt history;
- authorization for any production default or fleet behavior.

## Bounded environmental warning

`core/ontology-kernel` currently has concurrent dirty changes, including removal of historical vendored `tools/rocs-cli/**`, `.gitlab-ci.yml` changes, untracked scripts, and untracked `core.AgentExperience`. Review may inspect owner contracts but must not mutate or use that worktree as clean release evidence.

## Review posture

The RFC is architectural prose, not yet a machine contract. Review should prefer schema-first closure before ADR acceptance if ambiguity affects authority, digest identity, compatibility, rollback, publication atomicity, or consumer adoption claims.
