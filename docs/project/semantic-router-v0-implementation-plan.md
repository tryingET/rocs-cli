---
summary: "Post-ADR bounded implementation plan for Decision 102 semantic-router-v0."
read_when:
  - "Implementing Decision 102 in rocs-cli."
type: "implementation_plan"
status: "proposed"
decision_id: 102
---
# Semantic router v0 implementation plan

## Authority

Accepted ADR: `docs/adr/2026-08-01-abstaining-semantic-router-v0.md` at commit `04585ac18ed0c52bed9ce1453a9a8481364070a6`.

Normative packet:

- packet commit `52454f5dd86582290db642b73acc6c5cab8e9e1d`;
- aggregate `417ee5c7148573f80b841a0ae0d22f12ab8152c020c765f9a2a32976a001ba53`;
- schema `docs/project/semantic-router-v0/protocol.schema.json`;
- invariants `docs/project/semantic-router-v0/invariants.md`;
- compatibility baseline `docs/project/semantic-router-v0/discovery-compatibility-baseline.json`.

Implementation authority is limited to ROCS development mechanics and conspicuously synthetic fixtures. Every result is development evidence only.

## Non-authorized work

Do not:

- change protected discovery files or behavior;
- tune or execute B0;
- author real ontology policy;
- implement adopted/publication/currentness semantics;
- create D/U/O datasets or execute them;
- integrate Pi or another consumer;
- project prompt context;
- introduce provider, model, embedding, network, or learned logic.

## Implementation slices

### S0 — Route protocol substrate

New files:

- `src/rocs_cli/_semantic_router_schema.py` — generated exact embedded route schema;
- `src/rocs_cli/semantic_router_protocol.py` — offline schema registry, strict I-JSON/JCS validation, route digest domains, sequence tokenizer, canonical object verification;
- `src/rocs_cli/semantic_router_invariants.py` — cross-field policy/provenance/effective/result invariants.

Tests:

- `tests/test_semantic_router_protocol.py`;
- `tests/verify_semantic_router_golden.mjs`;
- exact synthetic golden and differential fixtures under `docs/project/semantic-router-v0/`.

Acceptance:

- packaged schema is exact;
- Python and Node agree on all route/provenance/request/effective/result digests;
- duplicate keys, floats, non-I-JSON integers, unknown fields, non-canonical arrays, and invalid external schema IDs fail closed;
- sequence tokenizer preserves duplicates and canonical witness positions;
- no protected discovery hash changes.

### S1 — Policy, provenance, and source capture

New files:

- `src/rocs_cli/semantic_router_policy.py` — bounded descriptor-anchored policy/provenance capture, owner Git blob verification, policy/provenance schema and invariant validation.

Tests:

- `tests/test_semantic_router_policy.py`.

Acceptance:

- absolute, symlink, `.`/`..`, backslash, empty-segment, alias, root-escape, wrong-repository, absent-revision, and digest-drift cases fail safely;
- policy and provenance preparse limits apply before untrusted values;
- every alternative has exactly one provenance record;
- source blobs come from the supplied local Git object database, never the worktree;
- snapshot changes and cleanup failures are distinct safe errors.

### S2 — Deterministic interpreter

New files:

- `src/rocs_cli/semantic_router.py` — clause matching, exact evidence schedule, admission matrix, concept state, joint-route state machine, nested discovery composition, effective execution, result digest.

Tests:

- `tests/test_semantic_router.py`.

Acceptance:

- every state/reason matrix row is covered;
- evidence is omission-free, extra-free, correctly scoped, canonically ordered, and query-witnessed;
- lexical scores never influence admission/selection;
- unchanged discovery executes exactly once and is nested exactly;
- synthetic-only test policies cover single, multi, ambiguity, no support, domain exclusion/conflict, concept conflict, and joint exclusion;
- repeat bytes are identical.

### S3 — CLI and capability surface

New file:

- `src/rocs_cli/cli_semantic_router.py`.

Bounded existing-file additions:

- `src/rocs_cli/cli.py` — `route` and `route-capabilities` parser/dispatch only;
- `src/rocs_cli/contracts.py` — effect-free command contracts;
- `README.md` — development-only command and authority boundary.

Tests:

- `tests/test_semantic_router_cli.py`;
- existing README/CLI and contract tests.

Acceptance:

- automatic route request is stdin-only;
- exact required flags and safe error envelopes;
- no environment file, cache, loose refs, network, or ambient owner root;
- route capabilities are separate;
- existing discover capabilities and direct discovery bytes remain unchanged.

### S4 — Compatibility and full gate

Run:

- protected-file hash verifier from `discovery-compatibility-baseline.json`;
- exact capabilities and independent Node behavior vectors;
- existing discovery protocol, discovery, and CLI tests;
- all new router tests and independent verifier;
- `uv run --frozen python -m unittest discover -s tests -p 'test_*.py' -q`;
- `scripts/ci/full.sh`.

Acceptance:

- all gates pass;
- only authorized files differ from the accepted base;
- no ignored or generated residue beyond repo-owned exclusions;
- independent review accepts implementation and compatibility evidence.

## Task decomposition

Create one fresh scoped AK task per slice. Each task:

- bases on the exact accepted predecessor commit;
- limits allowed and required paths;
- records protected-baseline identities before mutation;
- commits only its authorized slice;
- receives independent review before the next slice opens;
- never mechanically retries an indeterminate effect.

Recommended order: `S0 -> S1 -> S2 -> S3 -> S4`.

S0–S3 may use targeted tests. S4 owns the full gate and final implementation evidence. No later owner stage opens from implementation completion.

## File-size discipline

Keep each new code module below 500 LOC/50KB and each new test file below 1,000 LOC/80KB. Split before crossing the budget. Do not expand existing over-budget `src/rocs_cli/cli.py`; route parser/adapter logic belongs in the new CLI module and existing edits remain narrow registration calls.

## Rollback

Each slice is additive and individually revertible. Final rollback reverts S3 through S0 in reverse order. Protected discovery requires no migration. Preserve task evidence, failed tests, and review records.

## Stop conditions

Stop on:

- protected discovery drift;
- policy meaning authored outside synthetic fixtures;
- any adopted/non-synthetic claim;
- mismatch between schema and embedded copy;
- cross-language digest disagreement;
- ambiguous evidence schedule;
- unbounded parser/capture behavior;
- unexpected filesystem mutation;
- consumer/Pi/provider/model work;
- restoration uncertainty.
