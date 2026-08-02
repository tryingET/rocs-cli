---
summary: "Post-ADR implementation plan for Decision 103: a bounded ROCS offline verifier first, followed by separately owned and independently gated P2-P7 work."
read_when:
  - "Planning or implementing any Decision 103 post-ADR slice."
type: "implementation_plan"
status: "proposed"
decision_id: 103
---
# Adopted semantic-routing policy v1 implementation plan

## Authority and readiness

Accepted ADR: `docs/adr/2026-08-02-adopted-semantic-routing-policy-v1.md` at commit `3529ac8c87da58902cfbe31a02f54f50978badd5`.

Exact normative packet:

- commit `94f2d273c5f2ce27959978b82a37a3b2a8088867`;
- tree `fb2588f0623d92b80b46fd4b0f937e346cd32f83`;
- aggregate `20e8df2547bb4816325c7546a3c0a43b0283c6e0589d123e71b809baa7bfe438`;
- packet-manifest SHA-256 `05b39534733a81a2eb806d9c183033d7a0396e11d93c68f6a5f613fb80448fc5`;
- controlling synthesis commit `2295ba63368e9de9aff68779ead033e3cc51b405`.

Before any implementation mutation, the controller records the exact independently accepted plan commit as `p1_implementation_base_commit`, attaches this plan to Decision 103, verifies the AK passport is accepted and ADR-recorded, advances through task reevaluation only after all required artifacts exist, and opens a fresh P1 task with exact paths. No implementation task inherits authority from this prose alone.

## Protected inputs

Every slice recomputes before and after:

- all seven manifest-listed packet byte lengths and SHA-256 values;
- packet aggregate and manifest SHA-256 above;
- ADR bytes at `3529ac8c87da58902cfbe31a02f54f50978badd5`;
- Decision 102 route/discovery compatibility using the existing compatibility verifier;
- `live_acquisition_implemented=false` and no-network capability posture.

No P1 task may modify:

- any manifest-listed Decision 103 packet file or its manifest;
- the accepted ADR;
- Decision 102 packet, golden fixtures, differential fixtures, or compatibility baseline;
- semantic release protocol packet/runtime surfaces unrelated to this verifier.

Any normative packet-byte change stops P1 and requires fresh strict convergence plus a superseding ADR.

## P1 authority boundary

P1 implements only deterministic offline validation over explicit caller-supplied local bytes and conspicuously synthetic fixtures. It may:

- parse strict bounded I-JSON;
- validate closed schema shapes;
- compute RFC 8785 canonical bytes and all 61 domain-separated digests;
- verify synthetic Ed25519 credentials/signatures against caller-pinned keys;
- validate dependency topology, equality joins, authority separation, branch exactness, histories, checkpoints, challenges, and currentness proof shapes;
- return closed safe errors.

P1 may not create policy, D/U/O, credentials, owner facts, publication events, trusted checkpoints, consumer intent, Pi/runtime state, provider/model activity, prompt projection, or automatic preflight. It has no owner-store acquisition method, no network path, no signing method, and no mutation method. Passing a synthetic currentness fixture proves verifier mechanics only.

## P1 implementation slices

Dependency chain:

```text
S0 <- accepted implementation plan
S1 <- accepted S0 review
S2 <- accepted S1 review
S3 <- accepted S2 review
S4 <- accepted S3 review
```

Each slice gets a fresh AK task and exact predecessor commit/tree/evidence. No task opens before predecessor completion and independent acceptance.

### S0 — packaged schema and strict protocol substrate

New files:

- `src/rocs_cli/_bootstrap_assets/semantic-router-adopted-policy-v1.schema.zlib`;
- `src/rocs_cli/semantic_adopted_schema.py`;
- `src/rocs_cli/semantic_adopted_protocol.py`;
- `tests/test_semantic_adopted_protocol.py`;
- `tests/fixtures/semantic-adopted-policy-v1/schema-corpus.json`;
- `tests/verify_semantic_adopted_schema.mjs`.

The generated zlib asset is deterministic level-9 compression of the exact 323,224-byte schema. `semantic_adopted_schema.py` checks compressed and decompressed length/hash before parsing. It exposes bytes only; it does not synthesize or rewrite schema. Existing `_bootstrap_assets/*` package-data wiring is reused without broad packaging changes.

Acceptance:

- duplicate-key rejection, strict UTF-8 and I-JSON scalar/integer rules, no floats, forbidden scalar rejection, parser depth 32, collection items 50,000, and pre-allocation byte ceilings; RFC 8785 preserves string bytes and does not normalize to NFC, so positive NFD fixtures remain byte-distinct and valid where the schema permits them;
- 1 MiB ordinary-object, 16 MiB history, and 32 MiB currentness-proof limits enforced before parse and after canonicalization;
- all 1,115 local `$ref` occurrences resolve, 68 definitions are transitively referenced, the intentionally unreferenced `hexDigest` definition remains syntactically validated, all 69 definitions are preserved byte-exactly, and no local-reference cycle exists;
- `tests/verify_semantic_adopted_schema.mjs` independently implements the packet's used Draft 2020-12 subset with Node standard library only; keywords—including arbitrary local JSON Pointer `$ref`, `type`, `const`, `enum`, `required`, `additionalProperties`, `uniqueItems`, `format`, numeric/string/array limits, `allOf`, exact `oneOf`, `if`/`then`, `prefixItems`, and `items:false`—match Python over every schema-corpus case before S0 acceptance;
- all eight attempt/verdict branches and seven closure/approval projections have positive and overlap-negative fixtures;
- schema/packet protection and Decision 102 compatibility pass.

### S1 — canonical digests and caller-pinned signature verification

New files:

- `src/rocs_cli/semantic_adopted_digests.py`;
- `src/rocs_cli/semantic_adopted_signatures.py`;
- `tests/test_semantic_adopted_digests.py`;
- `tests/test_semantic_adopted_signatures.py`;
- `tests/fixtures/semantic-adopted-policy-v1/cryptographic-vectors.json`;
- `tests/fixtures/semantic-adopted-policy-v1/fixture-provenance.json`;
- `tests/generate_semantic_adopted_fixtures.py`;
- `tests/verify_semantic_adopted_crypto.mjs`.

Required bounded dependency/distribution changes:

- `pyproject.toml`;
- `uv.lock`;
- `src/rocs_cli/_bootstrap_assets/pyproject.toml`;
- `src/rocs_cli/_bootstrap_assets/uv.lock`;
- `src/rocs_cli/wave1.py`.

S1 selects one audited direct Python Ed25519 dependency, declares it in both project and self-contained bootstrap manifests, exact-locks both lockfiles, and includes every new verifier module in the isolated vendored-runtime copy list. Ambient/system fallback is forbidden. The dependency is verify-only in ROCS and independently cross-checked with Node standard cryptography. P1 implements no signing API or private-key custody. The checked-in generator obtains a fresh ephemeral test key from the audited primitive, serializes only public key/message/signature vectors, zeroes/drops private-key references before exit, and emits a provenance record binding generator commit, tool/dependency versions, vector hashes, conspicuously synthetic labels, B0-deny scan, and private-key/secret scan. Fixture generation need not reproduce the random key bytes; verification of the fixed checked-in public vectors is deterministic.

Acceptance:

- exact RFC 8785 bytes and all 61 unique digest-name/domain mappings;
- omitted self-digest fields and raw signature-preimage rules exact;
- canonical raw-32-byte public-key and exact 64-byte signature decoding, canonical base64 re-encoding, and public-key digest checks;
- positive vectors plus changed domain, changed body, wrong key, malformed/non-canonical base64, wrong signature length, non-canonical scalar, small-order key, revoked/expired credential, purpose, issuer, trust-root, and signature negatives;
- Python and independent Node recompute every vector rather than trusting stored booleans;
- fixture provenance and scans prove no checked-in private key/secret and no B0-derived material;
- no key discovery, ambient registry, signing API, network, or secret logging.

### S2 — graph, authority, custody, and execution verifier

New files:

- `src/rocs_cli/semantic_adopted_graph.py`;
- `src/rocs_cli/semantic_adopted_authority.py`;
- `src/rocs_cli/semantic_adopted_execution.py`;
- `tests/test_semantic_adopted_graph.py`;
- `tests/test_semantic_adopted_authority.py`;
- `tests/test_semantic_adopted_execution.py`;
- `tests/fixtures/semantic-adopted-policy-v1/execution-corpus.json`;
- `tests/fixtures/semantic-adopted-policy-v1/candidate-support-corpus.json`;
- `tests/verify_semantic_adopted_execution.mjs`.

Acceptance:

- explicit topological graph follows P3 readiness → P4 candidate → P5 preregistration/activation → channel → challenge → unsigned start subject → request → evaluator signature → launch → optional handoff → receipt → closure → attempt → approvals → verdict → P7 publication;
- every digest back edge, self edge, missing preimage, opaque caller request, or phase-forward dependency rejects;
- candidate validation consumes explicit bounded policy, provenance, inventory, and local owner-repository inputs; it recomputes the Decision 102 policy/provenance parsers and semantic-binding receipt, checks every source record and named path against the candidate's exact commit/tree through the local Git object database, and proves `softwareco/ontology` inventory membership; receipt-only self-consistency, prefix-only ownership, copied core ownership, missing source bytes, and repository/commit/tree/path drift reject;
- twelve-principal cardinality/separation, B0 exposure, exact ten-plus-one contamination coverage, 254/255/256 access histories, and one reservation/process rules validate;
- proof-of-possession, channel/exporter, all deadlines, reservation consumption, custodian-observed spawn, gateway-mediated revocable handle, process termination/reaping, handle close, terminal revoke, and eight branch projections validate;
- missing/late/wrong-signer closure, direct descriptor transfer, retained handle/process/grant, extra invocation/pass, retry, rerun, and non-completed publish reject;
- Python/Node differential outcomes and safe error kinds are byte-identical.

### S3 — publication/currentness verifier and CLI

New files:

- `src/rocs_cli/semantic_adopted_currentness.py`;
- `src/rocs_cli/cli_semantic_adopted.py`;
- `tests/test_semantic_adopted_currentness.py`;
- `tests/test_semantic_adopted_cli.py`;
- `tests/fixtures/semantic-adopted-policy-v1/currentness-corpus.json`;
- `tests/verify_semantic_adopted_currentness.mjs`.

Bounded existing changes:

- `src/rocs_cli/cli_semantic_commands.py`;
- `src/rocs_cli/contracts.py`;
- `README.md`.

CLI surface is explicit-local-file only:

```text
rocs semantic-policy verify-object --input <regular-file>
rocs semantic-policy verify-currentness \
  --proof <regular-file> --request <regular-file> \
  --policy <regular-file> --provenance <regular-file> \
  --inventory <regular-file> --owner-repo <local-git-root>
rocs semantic-policy capabilities
```

`capabilities` must state `live_acquisition_implemented=false`, `signing_implemented=false`, `owner_store_mutation_implemented=false`, and `consumer_activation_implemented=false`.

Acceptance:

- complete append-only publication history, owner head, checkpoint chain, fresh caller challenge, authenticated single-use consumption receipt, external request pins, and action-time proof joins validate;
- stale H1 after H2 withdrawal/revocation, replayed/expired/duplicate challenge, wrong action/candidate/store/channel/key, fork, rollback, skipped checkpoint, capacity exhaustion, or nested-value-as-pin rejects;
- only pass verdicts publish; withdraw/revoke history is preserved and revoke is terminal;
- every path input is opened descriptor-first with `O_NOFOLLOW`, regular-file `fstat`, pre-read size check, bounded chunked reads, and identity/size/mtime recheck; FIFO, device, socket, symlink, unstable, oversized, or blocking-special inputs reject before content read; stdin is unsupported;
- local Git reads use a closed environment, `--no-replace-objects`, no global/system config, no hooks, no alternates/shallow/partial/promisor state, bounded `cat-file --batch-check` before blob reads, and no network; supplied bytes and every provenance source equal exact commit/tree/path blobs;
- validation pre-counts schema-bounded events, graph edges, signatures, and canonicalized bytes and uses linear/indexed joins; worst-case operation count is derived from the packet's 10,000-event/50,000-item ceilings and tested at max/max+1 without an ambient wall-clock claim;
- no cache, no ambient owner root, deterministic stdout, closed safe stderr, and `--debug` compatibility;
- malformed/error paths leak no path, object bytes, key, exception, environment, or secret;
- all pre-existing CLI contracts and Decision 102 route/discovery behavior remain byte-compatible.

### S4 — independent evidence and rollback rehearsal

New files:

- `tests/verify_semantic_adopted_policy.mjs`;
- `tests/verify_semantic_adopted_compatibility.py`;

Run:

```bash
UV_PYTHON=3.12 uv run --frozen python -m unittest discover -s tests -p 'test_*.py' -q
node tests/verify_semantic_adopted_policy.mjs
UV_PYTHON=3.12 uv run --frozen python tests/verify_semantic_adopted_compatibility.py \
  --implementation-base <accepted-plan-commit> \
  --packet-aggregate 20e8df2547bb4816325c7546a3c0a43b0283c6e0589d123e71b809baa7bfe438
./scripts/ci/full.sh
```

S4 independently recomputes packet/asset hashes, schema behavior, 61 domains, every fixture oracle, Python/Node agreement, CLI contracts, safe errors, and Decision 102 compatibility. It verifies only authorized files differ from `p1_implementation_base_commit`.

Rollback rehearsal starts from the final accepted S4 candidate. It first copies the compatibility verifier to a private managed temporary directory, records its SHA-256, and requires an explicit candidate root. In a fresh isolated clone, revert S4, S3, S2, S1, and S0 in reverse order, running the external verifier and surviving tests after each revert. The final tree must equal `p1_implementation_base_commit`; the receipt proves completed P1, including S4-only files, can be removed. Preserve logs and failed evidence; remove only owned scratch.

P1 dogfood is limited to the checked-in synthetic corpus and explicit local files. It may claim parser, digest, signature-verification, graph, execution-shape, publication-history, currentness-shape, compatibility, resource, error, and rollback evidence only. It may not claim live owner currentness or real policy quality.

## P2-P7 owner gates

P1 completion does not open P2 automatically. Each later phase requires a separately reviewed owner handoff and task in the repository that owns the effect.

### P2 — synthetic semantic-owner storage mechanics

Owner: `softwareco/ontology`. Required before task creation: owner acceptance of exact repository identity, candidate/publication paths, CAS/append-only mechanics, capacity reserve, signing/trust distribution boundary, synthetic fixtures, and rollback. No real policy or publication.

### P3 — fresh custody readiness and sealed coordinates

Owner: an explicitly accepted custodian, proposed `softwareco/owned/dspx`. Required before any D disclosure: fresh source/license/consent policy, independent principals, B0 exposure `disproven` for blind roles, sealed D/U/O coordinates, base access history, deletion/incident controls, and signed caller-pinned readiness. Raw U/O never enters ROCS, Git, AK, Pi, sessions, or intercom.

### P4 — visible-D policy authoring and candidate freeze

Owner: `softwareco/ontology`. Policy authors may see D only after accepted P3 evidence. Freeze exact Softwareco inventory, policy/provenance bytes, ten-surface contamination manifest, and candidate. U/O remain hidden.

### P5 — one-shot reservation, preregistration, and activation

Owner: accepted custodian with independent reviewer. Acquire one non-executing reservation, construct the envelope, sign downstream contamination evidence, validate both independently supplied caller requests, construct their closed preexecution bundle, preregister the exact coordinates, validate every preregistration/reservation/equality join, and only then issue one bounded activation. No protected row read or evaluator spawn until every predecessor validates.

### P6 — one immutable protected evaluation and verdict

Owner: custodian for access/execution evidence; distinct independent reviewer for verdict. Exactly one process invocation, two internal passes only on completion, mandatory process/handle closure and terminal revoke, immutable pass/fail/indeterminate evidence, and no mechanical retry. This is the first real-policy dogfood and only if P1-P5 owner gates are current.

### P7 — semantic-owner publication only

Owner: `softwareco/ontology`. Only a reviewed pass verdict may append publish. Withdrawal/revocation are append-only. P7 does not establish production currentness.

After P7, a separate owner task must implement and independently prove trusted acquisition/currentness before any consumer action. Consumer shadowing, Pi/runtime delivery, prompt projection, provider/model evidence, and automatic preflight remain later decisions in that order.

## File-size and dependency discipline

- each new or modified Python/JavaScript module: below 500 LOC and 50KB;
- each test module/verifier: below 1,000 LOC and 80KB;
- data fixtures are hash-manifested and bounded by their protocol ceiling;
- the compressed schema asset is generated deterministically and must stay below 50KB;
- existing modules already near 500 LOC are not extended; new behavior goes in the named modules;
- no dependency is added without exact lock, license/security review, offline deterministic use, and rollback coverage.

## Task-scope template

Every slice task:

- enumerates every allowed path and exact required output;
- forbids all packet/ADR paths and unrelated semantic-release/Decision 102 surfaces;
- depends on the exact accepted predecessor task/evidence;
- records implementation base, predecessor commit/tree, packet aggregate, manifest hash, and B0 exposure before mutation;
- commits only its slice and receives independent review before completion;
- treats timeout/crash/indeterminate effects as non-retryable until disposition is proved.

## Stop conditions

Stop before mutation or before the next phase on packet/ADR drift, schema or Python/Node disagreement, signature primitive uncertainty, unbounded allocation/read, authority substitution, B0-derived fixture content, raw U/O exposure, unexpected repository mutation, live acquisition/signing/store mutation, consumer/Pi/provider/model work, phase/dependency bypass, missing independent review, or rollback uncertainty.
