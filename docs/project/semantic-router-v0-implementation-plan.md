---
summary: "Post-ADR bounded implementation plan for Decision 102 semantic-router-v0."
read_when:
  - "Implementing Decision 102 in rocs-cli."
type: "implementation_plan"
status: "proposed"
decision_id: 102
---
# Semantic router v0 implementation plan

## Authority and readiness

Accepted ADR: `docs/adr/2026-08-01-abstaining-semantic-router-v0.md` at commit `04585ac18ed0c52bed9ce1453a9a8481364070a6`.

Normative packet:

- packet commit `52454f5dd86582290db642b73acc6c5cab8e9e1d`;
- aggregate `417ee5c7148573f80b841a0ae0d22f12ab8152c020c765f9a2a32976a001ba53`;
- packet manifest SHA-256 `0fad833e48d6d2c198ee4f5f8c39d6fea67d59a20a758969b623dbe44fd09d68`;
- compatibility base `0a9d9eed00c4c2875d6a7dd870b8978032c95875`.

Before S0, the controller records the exact reviewed implementation-plan commit as `implementation_base_commit` and verifies the Decision 102 passport is `unblocked`, accepted, ADR-recorded, and ready for post-ADR execution. S0 bases exactly on that commit.

Implementation authority is limited to ROCS development mechanics and task-authorized synthetic fixtures. Every result is development evidence only.

## Protected inputs

No implementation task may modify:

- any of the eight paths listed in `docs/project/semantic-router-v0/packet-manifest.json`;
- `docs/project/semantic-router-v0/packet-manifest.json` itself;
- any path in `docs/project/semantic-router-v0/discovery-compatibility-baseline.json`.

Every slice verifies before and after:

- packet commit is an ancestor;
- all manifest byte lengths and hashes;
- packet aggregate `417ee5c7148573f80b841a0ae0d22f12ab8152c020c765f9a2a32976a001ba53`;
- packet-manifest SHA-256;
- all protected discovery hashes.

New implementation fixtures are exactly:

- `docs/project/semantic-router-v0/golden-fixtures.json`;
- `docs/project/semantic-router-v0/differential-fixtures.json`.

They are not normative packet members and may contain only conspicuously synthetic concepts/policy. Every implementer records B0 exposure. An independent review confirms fixtures are not derived from B0 or real ontology policy.

## Non-authorized work

Do not change protected discovery behavior, tune or execute B0, author real ontology policy, implement adopted/publication semantics, create or execute D/U/O, integrate a consumer/Pi, project prompt context, or introduce providers/models/embeddings/network/learned logic.

## Exact verifier surfaces

New checked-in verifiers:

- `tests/verify_semantic_router_golden.mjs` — independent Node stdlib parser, JCS encoder, route/provenance/request/effective/result digest recomputation, tokenizer/matcher, ordering, state/reason, safe-error, and fixture oracle;
- `tests/verify_semantic_router_compatibility.py` — packet/manifest/protected-hash verification, baseline placeholder substitution, capabilities receipt, existing CLI parser signature, direct discovery normal/error behavior, and protected test execution.

Exact commands from the candidate root:

```bash
node tests/verify_semantic_router_golden.mjs
uv run --frozen python tests/verify_semantic_router_compatibility.py \
  --base 0a9d9eed00c4c2875d6a7dd870b8978032c95875 \
  --packet-aggregate 417ee5c7148573f80b841a0ae0d22f12ab8152c020c765f9a2a32976a001ba53
uv run --frozen python -m unittest discover -s tests -p 'test_*.py' -q
./scripts/ci/full.sh
```

The compatibility verifier resolves baseline `<candidate>` to the current root and `<python>` to the interpreter executing the verifier; it rejects every other placeholder. It uses a closed environment and checks expected exit/stdout/stderr hashes where the baseline defines them.

It also constructs a fixed synthetic corpus/request for exact normal and malformed-error discovery bytes and compares candidate output with output from an isolated checkout at the exact compatibility base under the same interpreter/environment. It compares existing command parser signatures, including safe-error and `--debug` behavior.

## Implementation slices

Slices have mandatory AK dependency edges and predecessor evidence:

```text
S0 <- implementation-plan task
S1 <- S0 accepted review
S2 <- S1 accepted review
S3 <- S2 accepted review
S4 <- S3 accepted review
```

No task opens until its predecessor is completed and independently accepted.

### S0 — Route protocol substrate

New files:

- `src/rocs_cli/_semantic_router_schema.py`;
- `src/rocs_cli/semantic_router_protocol.py`;
- `src/rocs_cli/semantic_router_invariants.py`;
- `docs/project/semantic-router-v0/golden-fixtures.json`;
- `docs/project/semantic-router-v0/differential-fixtures.json`;
- `tests/test_semantic_router_protocol.py`;
- `tests/verify_semantic_router_golden.mjs`;
- `tests/verify_semantic_router_compatibility.py`.

Acceptance:

- embedded schema exact;
- Python and independent Node agree on schema validation, strict I-JSON, canonical bytes, all four route digests plus provenance digest, tokenizer, witnesses, orderings, evidence schedule, admission/routing matrices, capabilities, and safe errors;
- Node computes its own expectations from normative fixtures rather than consuming Python-generated expected values;
- malformed request/policy/provenance/effective/result/nested-discovery objects fail closed;
- parser matrix covers UTF-8/BOM/surrogate failures, whitespace-only exhaustion, max/max+1 bytes, depth/items, trailing JSON, huge scalars, integer syntax/range, duplicate keys, and byte-versus-codepoint query limits;
- exact `invalid_request`, `invalid_policy`, `resource_exhausted`, and `incompatible` mappings;
- packet and discovery protection pass.

### S1 — Policy, provenance, and source capture

New files:

- `src/rocs_cli/semantic_router_policy.py`;
- `tests/test_semantic_router_policy.py`.

Acceptance:

- descriptor-anchored policy/provenance capture with intermediate/final rechecks;
- absolute, symlink, hardlink, non-regular, `.`/`..`, backslash, empty segment, alias, root escape, root overlap, same-content inode replacement, and race cases fail safely;
- policy/provenance absolute preparse maxima apply before request values;
- every alternative has exactly one provenance record;
- Git subprocess uses a closed environment, `--no-replace-objects`, no global/system config, no hooks, and no network;
- reject replace refs, alternates, shallow, partial, or promisor repositories and missing objects;
- source bytes come only from the supplied local object database, never worktree files;
- controlled identity/content change is `snapshot_changed`; other operational failures do not become abstention;
- packet and discovery protection pass.

### S2 — Deterministic interpreter

New files:

- `src/rocs_cli/semantic_router.py`;
- `tests/test_semantic_router.py`.

Acceptance:

- every admission/routing state/reason row covered;
- exact evidence schedule is omission-free, extra-free, scoped, ordered, and query-witnessed;
- tests cover exclusion-only unsupported concepts, non-exact joint routes, exact joint positive/exclusion combinations, and no-joint ambiguity;
- all cumulative budgets are tested alone and simultaneously: clauses, groups, alternatives, normalized bytes, matching work, evidence, witnesses, collection items, parser depth, nested result bytes, and complete result bytes;
- every nested discovery lineage equality is tested;
- observable call-count oracle proves unchanged discovery executes exactly once per successful route invocation and never recursively;
- lexical scores never influence selection;
- fixed safe errors leak no query/path/policy/exception/environment content;
- operational errors never become abstention;
- deterministic repeat bytes exact;
- packet and discovery protection pass.

### S3 — CLI, parser extraction, and contracts

New files:

- `src/rocs_cli/cli_semantic_router.py`;
- `src/rocs_cli/cli_semantic_commands.py`;
- `tests/test_semantic_router_cli.py`.

Bounded existing changes:

- `src/rocs_cli/cli.py`;
- `src/rocs_cli/contracts.py`;
- `README.md`.

`cli_semantic_commands.py` receives behavior-preserving registration for existing discover/discover-capabilities/pack commands plus new route commands. `cli.py` replaces the extracted block with one narrow registration call and must finish below 500 LOC, never larger than its S3 starting LOC. Existing command signatures and behavior are compatibility-gated.

Acceptance:

- stdin-only route request and exact required flags;
- separate route capabilities;
- closed environment, no env file/cache/loose refs/network/ambient owner root;
- parser signatures, `--debug`, safe stderr, and all existing commands unchanged;
- README and command contracts exact;
- packet and discovery protection pass.

### S4 — Full evidence and rollback rehearsal

Run all exact verifier commands and repository gates.

Additionally:

- verify only authorized implementation files differ from `implementation_base_commit`;
- verify all modules/tests remain within file-size budgets;
- run the complete parser, filesystem/Git, resource, lineage, error, compatibility, and repeat matrices;
- independently review implementation and receipts;
- in a fresh isolated clone, revert S3, S2, S1, and S0 in reverse order, running packet/protected checks and relevant tests after each revert;
- final rehearsal target must equal `implementation_base_commit` tree exactly;
- preserve the rehearsal log and remove only owned scratch.

S4 commits no semantic policy or activation artifact.

## File-size discipline

Each new code module stays below 500 LOC/50KB and each test below 1,000 LOC/80KB. S3 must reduce `src/rocs_cli/cli.py` below 500 LOC through the declared behavior-preserving parser extraction. No code-size exception is authorized.

## Task scope template

Each fresh slice task:

- names every allowed path and exact required outputs;
- forbids every packet-manifest and protected-discovery path;
- declares its exact predecessor dependency;
- records `implementation_base_commit`, predecessor commit/tree, packet aggregate, and protected hashes before mutation;
- commits only its slice;
- receives independent review before completion;
- never mechanically retries an indeterminate effect.

## Rollback

Each slice is additive and individually revertible. S4 proves reverse rollback to the exact implementation-base tree. Existing discovery requires no migration. Preserve failed tests, task evidence, and review records.

## Stop conditions

Stop on packet/protected drift, policy meaning outside authorized synthetic fixtures, B0-derived fixture content, schema/embed or cross-language disagreement, unbounded capture, missing security oracle, unexpected mutation, consumer/Pi/provider/model work, dependency bypass, or restoration uncertainty.
