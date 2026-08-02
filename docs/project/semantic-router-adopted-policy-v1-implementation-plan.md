---
summary: "Corrected r14 post-ADR plan for a bounded synthetic ROCS offline verifier; P2-P7 remain blocked."
read_when:
  - "Planning or implementing any Decision 103 post-ADR slice."
type: "implementation_plan"
status: "proposed"
decision_id: 103
---
# Adopted semantic-routing policy v1 implementation plan — r14

## Authority, supersession, and readiness

This plan is bound only to the unanimously accepted r14 packet and superseding ADR:

- packet commit `0782c4421bbab446c0aa8d6d5ff2f784fcdb81c9`;
- packet tree `18b7607c65181a416294af16a9879d5b3b097e31`;
- packet aggregate SHA-256 `b3c4c60b8a98d5e739498547c8e65b8613a9ce446c1fa4fa252d58fd4169fb98`;
- packet-manifest SHA-256 `5cee262377d7670834b771006fb1482df2d6dab833c928d400b427821700d7dc`;
- accepted ADR `docs/adr/2026-08-02-adopted-semantic-routing-policy-v1.md` at commit `404486c6f20f252848c03df3890f1e75fc8216ba`.

This plan explicitly supersedes the r11 implementation plan at `afffb3bb87ed6642e21bb0985574de9b51dfc4d6` and the rejected attempted correction at `df636f8fdcaf6f8fa098864d25434230809d6298`. Neither is implementation authority. AK tasks 4519 and 4536 are likewise superseded, closed as non-authorizing lineage, and forbidden as a dependency or reusable task/evidence source for every R0-R4 task. In particular, the r11 S0 packaged schema asset and every schema-derived r11 oracle are superseded: they must not be treated as an r14 substrate or accepted evidence.

The r11 S1 RFC 8785, 61-domain digest, raw-signature-preimage, strict Ed25519 verification, and public-only fixture mechanics are intended to remain unchanged by r14. They may be retained only after R1 revalidates them against the accepted r14 schema, packet, corpus, and independently recomputed vectors. Prior S1 acceptance is not inherited.

Before R0, the controller records the independently accepted commit of this plan as `p1_implementation_base_commit`, attaches it to Decision 103, verifies the AK passport and r14 ADR coordinates, and opens a fresh owner-scoped AK task with exact allowed paths. This prose creates no implementation authority.

## Protected inputs and no-live-effects boundary

Before and after every slice, independently recompute:

- all seven packet-manifest byte lengths and SHA-256 values;
- the packet aggregate and packet-manifest SHA-256 above;
- the ADR bytes at `404486c6f20f252848c03df3890f1e75fc8216ba`;
- Decision 102 route/discovery compatibility with the existing compatibility verifier;
- `live_acquisition_implemented=false`, `signing_implemented=false`, `owner_store_mutation_implemented=false`, and `consumer_activation_implemented=false`.

No R0-R4 task may modify the packet, manifest, ADR, Decision 102 packet/fixtures/compatibility baseline, unrelated semantic-release surfaces, owner stores, authoritative refs, credentials, checkpoints, or consumer/runtime state. A packet or ADR byte change stops P1 and requires fresh strict convergence and a superseding ADR.

P1 accepts only explicit caller-supplied local bytes, caller-pinned public authority material, and conspicuously synthetic fixtures. It has no network, signing, secret custody, key discovery, ambient registry, owner-store acquisition/mutation, publication, consumer activation, Pi/runtime, provider/model, prompt-projection, or automatic-preflight capability. Passing synthetic publication/currentness objects proves verifier mechanics only.

## Sequencing and task gates

```text
accepted corrected plan -> R0 -> accepted independent R0 review
                        -> R1 -> accepted independent R1 review
                        -> R2 -> accepted independent R2 review
                        -> R3 -> accepted independent R3 review
                        -> R4 -> accepted independent R4 review
```

Every row requires a fresh AK implementation task and fresh independent review. A task records the exact accepted predecessor commit/tree/evidence and cannot open before predecessor acceptance. Findings are repaired in that same bounded row and re-reviewed; no later row may absorb an unresolved finding.

## R0 — package the exact r14 schema and renew the strict schema corpus

Allowed new or modified paths:

- `src/rocs_cli/_bootstrap_assets/semantic-router-adopted-policy-v1.schema.zlib`;
- `src/rocs_cli/_bootstrap_assets/pyproject.toml` (package-data wiring only);
- `src/rocs_cli/semantic_adopted_schema.py`;
- `src/rocs_cli/semantic_adopted_protocol.py`;
- `tests/test_semantic_adopted_protocol.py`;
- `tests/fixtures/semantic-adopted-policy-v1/schema-corpus.json`;
- `tests/verify_semantic_adopted_schema.mjs`.

R0 replaces, rather than patches or blesses, the r11 S0 asset. The zlib file is the fixed deterministic level-9 zlib compression of the exact r14 `protocol.schema.json`: decompressed length 324,005, decompressed SHA-256 `e5a55c7a6744868bfc05806a0216eaeb4f82b212f60c3961fdc18672e5529647`, compressed length 18,428, and compressed SHA-256 `948530f81173e760f233ef5a87dd699a762d4e04e16476a443ac7e873e9c2a24`. Loading verifies all four fixed values before parsing; the module exposes exact bytes and never synthesizes or rewrites schema.
 The isolated-bootstrap manifest change may only declare the fixed schema asset as package data; dependency, entry-point, build-backend, and runtime behavior changes remain outside R0.

Acceptance:

- strict UTF-8/I-JSON, duplicate-key, integer/scalar, forbidden-float, parser-depth 32, collection-item 50,000, and pre-allocation checks remain fail closed; RFC 8785 preserves string bytes without NFC normalization;
- 1 MiB ordinary-object, 16 MiB history, and 32 MiB currentness-proof limits apply before parse and after canonicalization;
- all local references and definitions are recounted from r14 rather than copied from r11 evidence; arbitrary local JSON Pointer `$ref`, every used Draft 2020-12 keyword, intentionally unreferenced definitions, and cycle absence are tested;
- the Python and Node-standard-library-only validators agree over a regenerated strict corpus containing positive, boundary, max/max+1, overlap-negative, and every closed r14 object shape;
- the corpus specifically covers the new required ontology-inventory source path/raw digest/fixed extractor fields, complete P3 readiness `concept_inventory`, complete request `expected_concept_inventory`, object/digest equality, canonical nonempty Softwareco inventory-source bytes, and rejects r11-shaped omissions;
- all eight attempt/verdict branches and seven closure/approval projections retain positive and overlap-negative schema coverage;
- build both wheel and sdist from the clean R0 tree; install each artifact separately offline into a fresh clean environment with no checkout import path, and prove the installed package contains the fixed compressed asset and loads/decompresses it to the exact r14 bytes; independently build/install the isolated-bootstrap distribution in a third clean environment and prove its vendored asset has the same fixed compressed/decompressed identities and is loadable without ambient/system fallback;
- no r11 corpus expected result is accepted without fresh r14 recomputation; packet protection and Decision 102 compatibility pass.

## R1 — revalidate the unchanged digest/signature mechanics atop R0

Allowed new or modified paths:

- `src/rocs_cli/semantic_adopted_digests.py`;
- `src/rocs_cli/semantic_adopted_signatures.py`;
- `tests/test_semantic_adopted_digests.py`;
- `tests/test_semantic_adopted_signatures.py`;
- `tests/fixtures/semantic-adopted-policy-v1/cryptographic-vectors.json`;
- `tests/fixtures/semantic-adopted-policy-v1/fixture-provenance.json`;
- `tests/generate_semantic_adopted_fixtures.py`;
- `tests/verify_semantic_adopted_crypto.mjs`;
- only if required to preserve the already reviewed direct verify-only primitive: `pyproject.toml`, `uv.lock`, `src/rocs_cli/_bootstrap_assets/pyproject.toml`, `src/rocs_cli/_bootstrap_assets/uv.lock`, and `src/rocs_cli/wave1.py`.

R1 must first show that r14 leaves the 61 domain names/mappings and signature mechanics unchanged. It then recomputes every vector through the accepted R0 parser/schema. No r11 S1 result is accepted by provenance alone.

Acceptance:

- exact RFC 8785 bytes, 61 unique domain mappings, omitted self-digest projections, the separate raw inventory-source SHA-256, and all signature preimages agree in Python and independent Node implementations;
- Ed25519 accepts only canonical base64 encoding of raw 32-byte public keys and exact 64-byte signatures, verifies public-key digests, and checks credential identity, validity, non-revocation, purpose, issuer, trust root, and caller pins;
- positives and changed-domain/body, wrong-key, malformed/noncanonical base64, wrong length, noncanonical scalar, small-order key, expired/revoked credential, purpose/issuer/root negatives are recomputed, not stored booleans;
- the audited dependency remains direct, verify-only, exactly locked in both distributions, copied into the isolated runtime, and has no ambient/system fallback; no dependency change is permitted merely to refresh evidence;
- the generator uses a fresh ephemeral test key but emits only synthetic public key/message/signature material, drops private references before exit, and records generator commit, tool/dependency versions, hashes, synthetic labels, B0-deny scan, and secret/private-material scan;
- no signing API, private material, key discovery, network, secret logging, or live authority appears.

## R2 — fresh r14 graph, authority, real-Git source binding, and execution task

Allowed new or modified paths:

- `src/rocs_cli/semantic_adopted_graph.py`;
- `src/rocs_cli/semantic_adopted_authority.py`;
- `src/rocs_cli/semantic_adopted_execution.py`;
- `tests/test_semantic_adopted_graph.py`;
- `tests/test_semantic_adopted_authority.py`;
- `tests/test_semantic_adopted_execution.py`;
- `tests/fixtures/semantic-adopted-policy-v1/execution-corpus.json`;
- `tests/fixtures/semantic-adopted-policy-v1/candidate-support-corpus.json`;
- `tests/verify_semantic_adopted_execution.mjs`.

R2 is a fresh task, not an amendment to rejected source-binding work. Its support API uses a closed `CandidateSupport` assembled from descriptor-read explicit local files: candidate, policy, provenance, the canonical inventory source, each named provenance source, and one local owner Git repository. `CandidateSupport` is verified evidence, never a caller assertion.

### Constructible r14 source model

The normative construction separates workflow order from Git ancestry; mandatory `S -> I -> C` or `I -> S -> C` ancestry is forbidden:

1. **I exists for P3.** It contains the authoritative canonical inventory-source blob. The verifier proves I's commit/tree and source bytes from the real local ODB and recomputes the inventory preimage. Owner workflow evidence—not Git ancestry—establishes that P3 readiness and its independent request were accepted before P4 policy authoring.
2. **P4 creates source revisions S as needed.** Each Decision 102 policy-authority/provenance-source revision must be a strict ancestor of C. An S may be on a branch independent of I before both histories merge into C; the verifier does not require or infer I→S, S→I, or wall-clock creation order.
3. **P4 then creates snapshot C.** C is a strict descendant of I and of every declared S. C contains exact policy and provenance bytes, byte-identical retained copies of every named S source blob, and the byte-identical canonical inventory source from I at its required path. C never contains candidate-object bytes or a candidate serialization; verification enumerates the bounded complete C tree and rejects any blob byte-equal to the externally supplied canonical candidate bytes.
4. **The candidate is external.** Only after the real C commit and tree IDs exist does the harness/caller construct the candidate object outside Git, binding C as its owner coordinate and I as its nested inventory coordinate. Candidate bytes are explicit local verifier input and are never used to compute C, so no candidate self-hash is possible.

The verifier derives only the normative ancestry relations from the local object graph: I→C and each S→C. It proves each I/S/C commit/tree pair and requires I/C commit and tree pairs to differ; it never claims Git proves P3 acceptance time. Every retained entry is one regular blob (`100644` or `100755`); symlink, gitlink, tree, alias, missing, changed, same-revision, nonancestor, candidate bytes in C, replace-object, shallow, partial/promisor, alternate-ODB, or caller-asserted ancestry fails closed.

The actual r14 P3 preimage is mandatory before readiness validation: the canonical source is exactly the RFC 8785 bytes of the closed object `{"ontology_ids":[...],"schema":"softwareco-ontology-inventory-source.v1"}`, with a nonempty sorted unique `co.software.*` array; its raw SHA-256, path, fixed `rocs-softwareco-ontology-inventory-source-v1` extractor, extracted IDs, ontology snapshot, I commit/tree, and inventory-coordinate digest are recomputed. The signed readiness subject nests that complete inventory object and equal digest. Its independent caller request nests a byte-identical expected object and equal digest. Candidate, preregistration, verdict, and currentness joins retain that exact object/digest. A digest alone, nested assertion, repaired JSON, inventory serialization containing C, or r11-shaped readiness/request rejects.

### Full graph, authority, and execution acceptance

- construct and inspect the full active normative graph, not a fixture-selected subgraph: I preimage -> accepted P3 readiness/request -> P4 S revision(s) -> C snapshot -> externally constructed candidate -> reservation/envelope -> execution-contamination subject and stage approvals/request -> preregistration/activation -> channel -> challenge -> unsigned start subject -> request -> evaluator signature -> launch -> optional handoff -> raw receipt -> closure -> attempt -> verdict-approval subject and post-execution custodian/reviewer approvals -> verdict -> P7 publication; every equality/digest edge is represented;
- reject every back edge, self edge, missing preimage, phase-forward dependency, opaque caller request, and approval over the wrong stage; validate normative `custody_readiness`, `execution_contamination_custodian`, `execution_contamination_independent_review`, `protected_access_activation`, `evaluator_execution_start`, launch/handoff/closure, verdict custodian/reviewer, and publication purposes against their exact subjects and caller pins;
- verify CandidateSupport by reparsing Decision 102 policy/provenance, owner and per-record source-owner authority, retained S/I/C blobs, canonical extraction, selectable inventory membership, and the complete semantic-binding receipt; prefix ownership, copied `core.*`, receipt-only consistency, absent bytes, or coordinate/path drift rejects;
- enforce the full twelve-principal cardinality and separation matrix, exact access rights, B0 exposure, 254/255/256 history boundaries, activation append, closure terminal revoke, reservation consumption, one process, gateway-mediated revocable handles, process reaping, handle closure, and no retained grant/process/descriptor;
- enforce exact timestamps and ordering for credential validity, readiness, reservation, activation, channel, challenge, authorization, launch, handoff, receipt, closure, attempt, approvals, verdict, and publication; changed boundary, late/missing signer, rollback, replay, or reordered history rejects;
- enforce exactly ten ordered pre-attempt contamination rows plus one separately signed downstream execution-contamination attestation, exact source-digest joins, no B0-derived material, and no candidate/envelope digest cycle;
- exercise all eight end-to-end branches: the three `not_started` prefixes, the three interrupted zero-pass prefixes, interrupted one-primary-pass, and completed two-pass; no extra invocation/pass, retry, rerun, repair, branch escalation, or non-completed publish;
- Python and Node independently recompute graph, Git-derived support expectations supplied as retained public fixture facts, authority, timing, history, contamination, and all branch outcomes with byte-identical safe error kinds. Node parity never substitutes caller assertions for Python's Git proof.

## Exact local Git and file resource ceilings

R2 establishes these ceilings and R3 applies them to every verification:

- exactly one explicit local owner repository; no ambient repository and no second ODB;
- at most 16,384 source records and 16,384 unique object IDs; separately, one aggregate ancestry-work budget of at most 16,384 commit visits/records applies across the union of all I-to-C and every S-to-C proof in one verification—not 16,384 per proof. Shared commits are deduplicated by object ID, every traversal charges the same aggregate counter before use, and aggregate max+1 returns `resource_exhausted`, never a partial authority result;
- at most 8 Git subprocesses total per verification;
- at most 12,582,912 stdout bytes and 65,536 stderr bytes per Git subprocess;
- at most 16,777,216 Git stdout bytes and 524,288 Git stderr bytes aggregate, including blob bodies;
- each policy, inventory-source, or named source blob at most 1,048,576 bytes; provenance at most 8,388,608 bytes; deduplicated retained provenance-source bytes at most 1,048,576 bytes aggregate;
- `cat-file --batch-check` precedes body reads; a bounded `rev-list`/ancestry proof precedes acceptance; NUL-delimited tree records are counted before use; excess count/output kills the child and returns `resource_exhausted`;
- the repository root is opened once with `O_DIRECTORY | O_NOFOLLOW`, anchored by descriptor, identity-rechecked after reads, and used with a closed environment, `--no-replace-objects`, no global/system config, hooks, alternates, shallow state, partial/promisor state, network, or external object helper;
- max and max+1 tests independently cover every blob, source, object, ancestry, subprocess, stdout, and stderr ceiling. Schema-bounded events, graph edges, signatures, and canonical bytes are pre-counted and processed with linear/indexed joins; no ambient wall-clock performance claim is made.

## R3 — publication/currentness verifier and explicit-local-file CLI

Allowed new or modified paths:

- `src/rocs_cli/semantic_adopted_currentness.py`;
- `src/rocs_cli/cli_semantic_adopted.py`;
- `tests/test_semantic_adopted_currentness.py`;
- `tests/test_semantic_adopted_cli.py`;
- `tests/fixtures/semantic-adopted-policy-v1/currentness-corpus.json`;
- `tests/verify_semantic_adopted_currentness.mjs`;
- bounded wiring only in `src/rocs_cli/cli_semantic_commands.py`, `src/rocs_cli/contracts.py`, and `README.md`.

CLI:

```text
rocs semantic-policy validate-object --input <regular-file>
rocs semantic-policy verify-bundle \
  --input <role>=<regular-file> [--input <role>=<regular-file> ...] \
  --owner-repo <local-git-root>
rocs semantic-policy verify-currentness \
  --proof <regular-file> --request <regular-file> \
  --candidate <regular-file> --policy <regular-file> \
  --provenance <regular-file> --inventory-source <regular-file> \
  --source <canonical-path>=<regular-file> [--source ...] \
  --owner-repo <local-git-root>
rocs semantic-policy capabilities
```

`verify-bundle` derives a closed required-role set from the primary object, including the P3 inventory source and owner repository whenever readiness/candidate authority is claimed, and rejects missing, extra, or duplicate roles. `validate-object` checks only schema/self-digest, reports `authority_verified=false`, and directs externally supported shapes to `verify-bundle`. It cannot infer owner, key, source, publication, or currentness authority.

Acceptance:

- the three commands have disjoint output schemas; only complete bundle/currentness verification can return `authority_verified=true`;
- publication history, pass-only publication, append-only withdraw/revoke, terminal revoke, owner head, contiguous checkpoint chain, fresh challenge, authenticated single consumption, caller pins, action-time joins, and all exact R2 I/S/C and P3 inventory-preimage relations validate;
- recompute and verify the owner read-attestation signature preimage exactly as `rocs-semantic-policy-receipt-signature-v1\0` plus the raw 32-byte attestation-body digest, and the consumption signature preimage exactly as `rocs-semantic-policy-consumption-signature-v1\0` plus the raw 32-byte consumption-body digest; reject JCS bytes, ASCII digest text, changed domain, wrong body/key, malformed digest, or any other preimage;
- validate the complete closed acquisition capability, clock source, acquisition channel, challenge-consumption store, issuer signing-key, and consumption-signing-key coordinates and approvals: canonical coordinate digests, subjects, purposes, issuers, credentials, public-key digests, trust roots, validity, non-revocation, caller pins, and both signatures must all join; missing, extra, open, identifier-only, ambient, partial-tuple, or proof-nested substitution rejects;
- derive age only from caller-pinned trusted `trusted_now` minus issuer-attested `capture_finished_at`, require strictly positive age within `max_age_seconds`, require monotonic/non-rolled-back trusted time and `clock_uncertainty_ms <= max_clock_uncertainty_ms`, and reject untrusted or rolled-back `trusted_now`, zero/negative age, stale age, excessive/negative uncertainty, capture reversal, or independently chosen `observed_at`;
- explicitly mutate timestamps while retaining old signatures to prove redated read and consumption receipts reject; stale, forked, rolled-back, skipped, replayed, expired, duplicate, wrong action/candidate/store/channel/key, capacity-exhausted, withdrawn/revoked, nested-value-as-pin, or non-pass publication also rejects;
- every file uses descriptor-first `O_NONBLOCK | O_NOFOLLOW`, regular-file `fstat`, pre-read size check, bounded chunked read, and identity/size/mtime recheck; stdin, FIFO, device, socket, symlink, unstable, oversized, or blocking-special input rejects before content use;
- the exact Git ceilings above apply; there is no cache, network, ambient owner root, mocked ODB, or authority fallback;
- deterministic stdout, closed safe stderr, and `--debug` compatibility leak no path, object bytes, key, exception, environment, or secret;
- capabilities reports all four live-effect flags false; Decision 102 and existing CLI contracts remain byte-compatible.

## R4 — independent evidence, synthetic real-Git dogfood, and rollback

Allowed new or modified paths:

- `tests/verify_semantic_adopted_policy.mjs`;
- `tests/verify_semantic_adopted_compatibility.py`;
- `tests/dogfood_semantic_adopted_policy.py`;
- only hash-manifested synthetic fixtures under `tests/fixtures/semantic-adopted-policy-v1/` needed by the dogfood.

R4 runs:

```bash
UV_PYTHON=3.12 uv run --frozen python -m unittest discover -s tests -p 'test_*.py' -q
node tests/verify_semantic_adopted_policy.mjs
UV_PYTHON=3.12 uv run --frozen python tests/dogfood_semantic_adopted_policy.py
UV_PYTHON=3.12 uv run --frozen python tests/verify_semantic_adopted_compatibility.py \
  --implementation-base <accepted-plan-commit> \
  --packet-aggregate b3c4c60b8a98d5e739498547c8e65b8613a9ce446c1fa4fa252d58fd4169fb98
./scripts/ci/full.sh
```

Independent evidence recomputes packet/asset identities, r14 schema behavior, all 61 domains, raw inventory-source digest/extraction, signatures, fixture oracles, Python/Node parity, CLI contracts, safe errors, exact resource ceilings, and Decision 102 compatibility. It proves only authorized paths differ from `p1_implementation_base_commit`.

### Required synthetic dogfood

The dogfood creates a fresh private temporary Git repository with no alternates and ordinary Git commands; mocked `git`, in-memory commit graphs, fake ODB adapters, caller-asserted ancestry, and copied commit/tree strings are forbidden. It first creates I with the canonical authoritative inventory source and obtains full P3 acceptance. Only then it creates one or more strict-descendant S source revisions and strict-descendant C. C retains all required I/S bytes and contains policy/provenance, but no candidate bytes. After C commit/tree exist, the harness constructs the candidate as an external explicit local file. The production verifier proves all objects, ordering, ancestry, trees, modes, and retained bytes.

Using fresh ephemeral synthetic keys, the harness constructs the complete signed P3 readiness subject/receipt and independent request, including byte-identical full inventory objects and equal digests; then the complete P4-P7 synthetic graph, all normative stage-specific signed approvals and caller pins, exact histories/times/contamination, and each of the eight execution/verdict branches. It exercises `validate-object`, `verify-bundle`, and `verify-currentness` through explicit regular files and the real repository. Node dogfood must independently open and inspect that same fresh repository and its actual I, every S, and C commit/tree/blob objects, independently recompute ancestry, retained-byte and candidate-absence facts under the same ceilings, and then verify every branch; Python-derived coordinates, JSON summaries, expected booleans, or other derived Git facts are not Node evidence.

Only public keys/signatures and conspicuously synthetic data may enter retained evidence. Private keys remain only in permission-restricted owned temporary storage/process memory, never enter verifier inputs or logs, and are destroyed after evidence hashes are sealed. The fail-closed private-material scan covers the complete fixture tree, fixture manifests, generated and retained logs/evidence, staged diff, and every new Git object reachable from each R row tip but not from `p1_implementation_base_commit` (including blobs not named by the diff). It detects PEM armor, OpenSSH private keys, PKCS#8/private-key DER encodings, private or symmetric JWK members, mnemonic/raw seed material, and credential/secret candidates encoded as raw bytes, hex, or base64. The only exceptions are an explicit path+field+SHA-256 allowlist of schema-valid public keys, public authority credentials, signatures, and documented synthetic non-secret vectors; type/name heuristics alone never allowlist. Any undecodable candidate, unallowlisted match, scanner error, unreadable object, or scope gap fails closed. B0 deny scanning covers the same scope.

Dogfood must also hit every Git max/max+1 boundary without network, alternates, mocked ODB, live owner refs, live publication/store mutation, signing API, or any P2-P7 effect. The complete repository test suite and `./scripts/ci/full.sh` run after dogfood.

Rollback starts from the final accepted R4 candidate. Before cloning, record the exact accepted single-row commit IDs for R0, R1, R2, R3, and R4 and prove each row commit's parent is the previously accepted row tip; merge, squash, range guesses, labels, or task IDs cannot substitute. Copy the compatibility verifier to a private managed temporary directory, record its SHA-256, and require an explicit candidate root. In a fresh isolated clone, revert those exact commits R4, R3, R2, R1, and R0 in reverse order. After each revert run the external verifier plus the full CI applicable to that surviving tree, including its complete unit/Node checks and `./scripts/ci/full.sh`, rather than only selected surviving tests. After R0 is reverted, run the complete baseline unit/Node/compatibility/full CI suite from `p1_implementation_base_commit` and require byte-identical final tree equality to that commit. Preserve logs and failed evidence; delete only owned scratch. This proves removal of synthetic P1, not rollback of any live authority or effect.

## P2-P7 remain blocked

R0-R4 are synthetic P1 only. P2 storage, P3 real custody/readiness, P4 real D disclosure/policy/candidate, P5 real reservation/activation, P6 protected U/O execution/verdict, and P7 owner publication remain blocked and unauthorized. Each would require a later explicit decision, correct owner repository, fresh owner-scoped AK task, independent review, authority artifacts, and rollback. No R0-R4 fixture, Git repository, signature, currentness result, or AK record may be promoted into those phases.

Trusted live acquisition/currentness, consumer shadowing/adoption, Pi/runtime delivery, prompt projection, provider/model activity, automatic preflight, and fleet rollout remain later decisions after P7; this plan grants no authority for them.

## File and dependency budgets

- each new or modified Python/JavaScript implementation module: below 500 LOC and 50KB;
- each test module/verifier: below 1,000 LOC and 80KB;
- data fixtures are hash-manifested and bounded by protocol/input ceilings;
- deterministic compressed schema asset: below 50KB;
- do not extend an existing module already near 500 LOC; use the named bounded module;
- no dependency without exact locks, license/security review, offline deterministic use, and rollback coverage.

## Per-task scope and stop conditions

Every R0-R4 AK task enumerates exact allowed paths/output, forbids packet/ADR/unrelated surfaces, records implementation base, predecessor commit/tree, r14 packet/manifest identities, and B0 posture, explicitly proves it neither depends on nor reuses AK 4519 or 4536, commits only its row, and receives independent review before the next task. Timeout, crash, or indeterminate behavior is non-retryable until disposition is proved.

Stop before mutation or progression on packet/ADR drift; r11 schema/fixture substitution; Python/Node disagreement; signature uncertainty; malformed or missing P3 inventory preimage; equal, fake, nonancestral, replaced, shallow, partial, alternate, mocked, or over-budget Git evidence; changed retained bytes; unbounded allocation/read/traversal; authority or caller-pin substitution; incomplete graph/stage approval/history/timing/contamination/branch coverage; B0-derived or private fixture material; raw U/O exposure; unexpected repository mutation; live acquisition/signing/store/publication/consumer effect; P2-P7 work; Pi/provider/model work; missing independent review; or rollback uncertainty.
