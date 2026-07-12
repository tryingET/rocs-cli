---
summary: "Proposed deterministic semantic-discovery protocol owned by ROCS for task-language candidate retrieval and bounded exact-ID follow-up."
read_when:
  - "Designing or implementing task-sensitive ontology discovery in ROCS."
  - "Building a consumer adapter that needs replayable semantic candidates."
  - "Reviewing semantic preflight authority, determinism, or safety boundaries."
type: "rfc"
status: "proposed"
---

# RFC — Deterministic Semantic Discovery Protocol v0

## Status and decision membrane

This is a proposed ROCS product contract under `decision:52`, not an adopted semantic release or implementation authorization. Every R/P phase below is candidate post-ADR sequencing. No discovery implementation, Pi dogfood, task creation, default cutover, consumer adoption, fleet enablement, or mandatory enforcement is authorized until the applicable AK decision and post-ADR artifacts permit it. Production semantic release, ROCS tool trust, and consumer adoption remain gated by `decision:53`, whose RFC is [Semantic Release Capsule and Consumer Adoption Protocol v0](semantic-release-capsule-and-consumer-adoption-protocol-v0.md).

ROCS owns deterministic retrieval, result integrity, bounded exact-ID packs, and executable command-effect contracts. It does not own ontology meaning, consumer desired state, AK task intent, Pi prompt authority, or model conclusions.

## Problem

ROCS can retrieve an exact ontology ID with `pack`, but an agent beginning with ordinary task language does not know that ID. `pi-ontology-workflows` currently compensates by running `rocs build`, reading generated artifacts, and ranking documents in TypeScript. That creates two retrieval authorities, writes build artifacts during search, and cannot produce a portable, replayable discovery result.

The companion Pi-side architecture is [Pi Semantic Preflight Adapter v0](../../../../softwareco/owned/pi-extensions/packages/pi-ontology-workflows/docs/project/semantic-preflight-adapter-v0.md). This RFC is the primary decision artifact; the companion is a required reviewed input for the cross-repo decision.

Lifecycle inputs:

- [problem brief](semantic-preflight-problem-brief-v0.md)
- [evidence note](semantic-preflight-evidence-note-v0.md)
- [attempt-1 review synthesis requiring revision](semantic-preflight-review-synthesis-v0.md)
- [attempt-2 review synthesis requiring revision](semantic-preflight-rereview-synthesis-v1.md)
- [attempt-3 review synthesis requiring revision](semantic-preflight-review3-synthesis-v2.md)

This revision responds to all three syntheses; prior reviewed revisions remain immutable at commits `71a7fdc`, `c9591ba`, and `71eba70`.

The missing ROCS primitive is:

```text
task language + exact semantic corpus identity + closed retrieval config
→ deterministic candidates + match evidence + bounded result + digest
```

Discovery identifies candidates. It does not certify semantic relevance or select a meaning on behalf of an operator or agent.

## Options considered

### A. Keep exact-ID retrieval only

This preserves ROCS but leaves ordinary task-language grounding ambient and dependent on agent luck. It does not solve the problem.

### B. Keep or expand Pi-local ranking

This is locally convenient but creates a second semantic retrieval implementation, requires build artifacts, and cannot serve DSPx or other consumers consistently. Rejected as the target.

### C. ROCS-owned deterministic discovery with thin adapters

ROCS captures and ranks one bound corpus; Pi and other consumers validate and render the result without reimplementing ranking. This is the proposed direction.

### D. Model or embedding retrieval as the baseline

This may become advisory evidence later, but it is not replayable semantic authority and creates network/model/version dependence. Rejected for v0.

## Decision requested

Approve as the target architecture:

1. ROCS owns deterministic task-language candidate discovery and complete considered-corpus identity.
2. Pi owns only session readiness, bounded invocation, state projection, and safe structural rendering.
3. Exact-ID `pack` remains the explicit full-content retrieval step.
4. Development dogfood is session-scoped opt-in; default cutover waits for release/adoption authority.
5. AK `decision:53` must separately accept production semantic-release identity, ROCS distribution trust, consumer adoption, and their distinct owner facts before any production cutover.

## Controlled-vocabulary preflight

| Term | Kind | Owner | Status in this RFC | Promotion posture |
|---|---|---|---|---|
| `semantic-discovery-request.v0` | protocol schema identifier | ROCS | proposed | code/schema contract after ADR |
| `semantic-discovery-result.v0` | protocol schema identifier | ROCS | proposed | code/schema contract after ADR |
| `rocs-lexical-v0` | algorithm identifier | ROCS | proposed | executable contract after ADR |
| `development_snapshot` | identity variant | ROCS | proposed, unreleased | no ontology promotion implied |
| `semantic_release_coordinate` | reserved production coordinate | decision:53 owner split | not implemented by decision:52 | source: decision:53 RFC; no ontology promotion implied |
| `matched`, `ambiguous`, `no_match`, `not_applicable`, `unavailable` | adapter outcome projection | Pi adapter | proposed | adapter contract, not ontology vocabulary |
| `no_candidates`, `unique_candidate`, `multiple_candidates`, `ambiguous_equivalence`, `low_confidence` | retrieval-state enum | ROCS | proposed | executable protocol contract after ADR |
| `ok`, `unavailable`, `timeout`, `incompatible`, `resource_exhausted` | invocation-state enum | Pi adapter | proposed | adapter projection after ADR |
| `applicable`, `not_applicable`, `unknown` | applicability-state enum | Pi adapter | proposed | adapter projection after ADR |
| `adopted_runtime`, `development_runtime` | runner identity kind | Pi adapter | proposed | production variant gated by later adoption decision |

Retrieval source for proposed ROCS tokens is this RFC and, after acceptance, the executable protocol/capability fixtures. No ontology semantic reference is claimed for machine protocol enums. This preflight classifies owner and use; it does not mutate ROCS ontology, AK vocabulary, Prompt Vault, or Pi runtime authority.

## Non-goals

Protocol v0 does not:

- load an entire ontology into a prompt;
- invoke a model, embedding service, network, shell callback, or generated code;
- mutate ontology or managed `dist/` artifacts;
- infer AK task authority or consumer desired state;
- approve a semantic release or adoption;
- silently resolve ambiguity;
- make free-form ontology prose safe to place in a system prompt;
- provide fleet rollout or mandatory preflight enforcement.

## Owner boundaries

| Concern | Owner |
|---|---|
| Shared meaning and semantic release approval | `core/ontology-kernel` and ontology owners |
| Discovery algorithm, snapshot capture, command contract, exact-ID pack | `core/rocs-cli` |
| Desired semantic release coordinate, rollout intent, decisions, evidence references | AK / consumer authority |
| Turn-sensitive retrieval UX and prompt adapter | `pi-ontology-workflows` |
| Startup orientation | `pi-society-startup-context` |
| Empirical comparison and optimization | DSPx / Oracle |

## Protocol surfaces

### 1. Discovery request

A caller supplies closed canonical JSON through `rocs discover --request-json -`. `--request-file <path>` is allowed only for explicit interactive use; stdin and file are mutually exclusive. V0 has no convenience flags, eliminating precedence ambiguity.

```json
{
  "schema": "semantic-discovery-request.v0",
  "query": "ordinary task language",
  "identity_selector": {"kind": "development_snapshot"},
  "profile": "review",
  "algorithm": "rocs-lexical-v0",
  "limits": {
    "query_bytes": 16384,
    "corpus_files": 5000,
    "corpus_bytes": 33554432,
    "file_bytes": 1048576,
    "parser_depth": 32,
    "collection_items": 10000,
    "candidates": 12,
    "result_bytes": 65536
  }
}
```

`semantic_release_coordinate` is reserved but rejected as `unsupported_identity` until decision:53 closes lawfully and its accepted contract is implemented. Unknown fields and unsupported versions fail explicitly.

### 2. Separate identity domains

V0 never overloads one semantic digest:

| Identity | Covers | Does not cover |
|---|---|---|
| `corpus_snapshot_digest` | canonical manifest of every considered manifest/profile/document raw byte string, logical path, layer order, and resolved ref fact | query, algorithm, tool, limits, ranking |
| `document_digest` | one exact raw ontology-document byte string | logical path or ranking |
| `tool_identity` | immutable ROCS executable/source generation selected by the adapter | ontology corpus |
| `effective_execution_digest` | caller request, corpus snapshot, tool identity, algorithm/Unicode version, effective limits | result candidates |
| `result_digest` | complete successful result | its own digest field |
| `pack_digest` | exact returned pack envelope and bytes | discovery result |

A future `semantic_release_coordinate` will point to an externally governed semantic release and expected `corpus_snapshot_digest`; it will not attest ROCS executable bytes or consumer adoption. The existing intelligence `capsule_digest` remains unrelated.

### 3. Canonical encoding and hashes

Every schema is closed and rejects unknown or missing fields. All protocol objects use RFC 8785 JSON Canonicalization Scheme with an additional closed restriction: numbers are non-negative integers only; duplicate keys, floats, invalid Unicode, and non-I-JSON values fail. UTF-8 is mandatory.

Every hash is lower-case `sha256:` plus 64 hexadecimal digits:

```text
sha256(ASCII(domain) || 0x00 || canonical_or_raw_bytes)
```

Closed domains are:

```text
rocs.caller-request.v0
rocs.corpus-snapshot.v0
rocs.document.v0
rocs.tool-identity.v0
rocs.effective-execution.v0
rocs.discovery-result.v0
rocs.pack.v0
```

Closed digest preimages are:

- caller request: the exact validated `semantic-discovery-request.v0` object;
- corpus snapshot: `{schema, profile, roots, resolved_refs, entries}`; each root is exactly `{root_id, layer, layer_order, kind}`, each ref exactly `{layer, layer_order, locator, resolved_revision}`, and each entry exactly `{logical_path, layer, layer_order, kind, raw_byte_length, document_digest}`;
- tool identity: exactly `{kind, manifest_digest, python_version, unicode_data, digest}`, where `digest` uses `rocs.tool-identity.v0` over the first four fields;
- effective execution: exactly `{schema, caller_request_digest, corpus_snapshot_digest, tool_identity, algorithm, effective_limits}`; `algorithm` is exactly `{id, unicode_data}` and `effective_limits` has exactly the eight request limit keys;
- result: exactly `{schema, caller_request_digest, corpus_snapshot_digest, tool_identity, effective_execution_digest, algorithm, retrieval, candidates, effective_limits, truncated, result_digest}`; each candidate is exactly `{rank, ont_id, kind, layer, score, matched_query_tokens, evidence, document_digest}` and each evidence item exactly `{field, rule, query_token}` using closed enums;
- pack: exactly `{schema, corpus_snapshot_digest, root_id, root_document_digest, config, documents, pack_digest}`; config is exactly `{max_depth, rel_types, include_relation_defs, max_docs, max_bytes}` and each document exactly `{ont_id, kind, logical_path, document_digest, text}`.

Logical paths are NFC-normalized UTF-8 POSIX paths relative to a declared logical layer root; backslash, absolute paths, `.`/`..`, empty segments, and normalization collisions fail. Roots sort by layer order then root ID; refs sort by layer order; entries sort by logical-path UTF-8 bytes. Manifest/profile bytes are entries too. Digests always cover raw bytes; normalization is used only for retrieval.

### 4. Snapshot capture contract

V0 supports Linux, Python 3.12, Unicode data 15.0.0, and local case-sensitive filesystems providing stable `lstat`/`fstat` identity. Other environments return `incompatible`.

Capture is a deterministic quiescent-snapshot proof, not a transactional filesystem snapshot:

1. Resolve profile/layers without implicit `.env`; derive logical root IDs from declared layer names, record effective profile, layer order, locators, and exact resolved revisions.
2. Enumerate manifests, profiles, and eligible ontology documents in UTF-8-byte path order.
3. Reject symlinks, reparse-like aliases, non-regular files, root escape, duplicate logical paths/IDs, invalid UTF-8, and exceeded limits.
4. Open with no-follow semantics; compare device, inode, size, `mtime_ns`, and `ctime_ns` before/after the one raw-byte read.
5. Re-enumerate and recapture the entire generation immediately.
6. Accept only when both canonical snapshot manifests and byte digests are identical; otherwise return `snapshot_changed`.

Scoring, evidence, document digests, and later snapshot-bound pack retrieval use the accepted captured bytes. Parsed-cache content is forbidden in automatic mode.

### 5. Discovery result

A successful result contains the effective execution identity:

```json
{
  "schema": "semantic-discovery-result.v0",
  "caller_request_digest": "sha256:...",
  "corpus_snapshot_digest": "sha256:...",
  "tool_identity": {"kind":"development_runtime","manifest_digest":"sha256:...","python_version":"3.12.x","unicode_data":"15.0.0","digest":"sha256:..."},
  "effective_execution_digest": "sha256:...",
  "algorithm": {"id": "rocs-lexical-v0", "unicode_data": "15.0.0"},
  "retrieval": "multiple_candidates",
  "candidates": [{
    "rank": 1,
    "ont_id": "core.Agent",
    "kind": "concept",
    "layer": "core",
    "score": 900,
    "matched_query_tokens": ["agent"],
    "evidence": [{"field": "label", "rule": "token_exact", "query_token": "agent"}],
    "document_digest": "sha256:..."
  }],
  "effective_limits": {},
  "truncated": false,
  "result_digest": "sha256:..."
}
```

Retrieval states are `no_candidates`, `unique_candidate`, `multiple_candidates`, `ambiguous_equivalence`, and `low_confidence`. They describe candidates, never truth.

### 6. Consumer outcome projection

Adapters retain separate machine dimensions:

```text
invocation: ok | unavailable | timeout | incompatible | resource_exhausted
applicability: applicable | not_applicable | unknown
retrieval: <ROCS state or absent>
projection: matched | ambiguous | no_match | not_applicable | unavailable
```

`not_applicable` is adapter policy, never lexical absence. `unavailable` and exhaustion cannot become `no_match`.

## Normative `rocs-lexical-v0` algorithm

1. Runtime Unicode data must equal `15.0.0` or invocation is incompatible.
2. Normalize every string by NFKC, then Unicode casefold, then map every maximal run of Unicode whitespace to one ASCII space and trim.
3. Tokens are maximal non-empty runs whose code points have Unicode general category starting `L` or `N`. Query tokens are deduplicated in first-occurrence order. Empty normalized query is `invalid_request`.
4. Eligible fields are exact validated values only: `ont.id`, each `ont.labels[]`, each `ont.synonyms[]`, `ont.description`, each `ont.examples[]`, each `ont.anti_examples[]`, and validated relation type/target strings. Unknown or wrong-typed fields fail ontology validation before scoring.
5. For each unique query token and field family, add the family weight at most once per candidate when any value in that family contains the token: ID 500, label 400, synonym 350, description 100, relation 80, example 50. Repeated values never multiply weight. If any anti-example contains the token, subtract 200 once after all positive families. Scores clamp at zero and must fit unsigned 32-bit integer range.
6. For each family, add at most one phrase bonus per candidate when any complete normalized value equals the complete normalized query: ID 1000, label 800, synonym 700, description 200, relation 160, example 100. If any anti-example exactly equals the query, subtract 400 once.
7. `matched_query_tokens` is the first-occurrence-ordered subset receiving any positive family match. Emit positive and anti-example evidence in field-family order, then rule (`phrase_exact`, `token_exact`, `anti_phrase`, `anti_token`), then query-token order. Evidence contains enums and query tokens, never ontology prose.
8. Candidates with score below 100 are excluded. Sort by score descending, ontology-ID UTF-8 bytes ascending, then kind (`concept` before `relation`).
9. Compute retrieval over the full eligible set before top-K projection:
   - none: `no_candidates`;
   - all scores below 300: `low_confidence`;
   - one candidate: `unique_candidate`;
   - top two have equal score and identical matched-query-token sets: `ambiguous_equivalence`;
   - otherwise: `multiple_candidates`.
10. Apply top-K only after classification; set `truncated=true` when eligible candidates are omitted.

Metamorphic fixtures must prove enumeration-order invariance, top-K monotonicity, locale/environment invariance, one-byte mutation identity drift, equivalent canonical requests, and Python-producer/TypeScript-verifier equality.

## Limits and errors

All limit fields are required positive integers; caller values may range from 1 through the defaults shown above. `parser_depth` counts nested YAML/JSON collection levels with the root at 1. `collection_items` is corpus-wide across parsed mapping keys and sequence elements. `corpus_files` includes manifests, profiles, and documents. Query bytes are measured on the exact raw UTF-8 request value before ROCS normalization. Corpus bytes include manifest/profile/document raw bytes. Result bytes measure the final canonical result including the 72-byte `sha256:` digest string; implementation computes the digest over the omitted-field object, inserts it, then enforces the limit. Fixed-envelope overflow fails.

Query, corpus, file, parser, collection, and result excess return `resource_exhausted`; candidate count alone truncates. The machine error envelope is closed:

```json
{"ok":false,"error":{"schema":"rocs-error.v0","kind":"incompatible|invalid_request|invalid_ontology|resource_exhausted|snapshot_changed|unsupported_identity|internal","message":"fixed safe text","caller_request_digest":"sha256:... or null"}}
```

Errors are JSON on stdout in machine mode, diagnostics only on stderr, and exit `1`; no partial result is valid. `caller_request_digest` is null only when bytes cannot be decoded as one valid request object; otherwise it is present even for unsupported schema/algorithm/identity. Mapping is closed: schema/algorithm/query/flag errors → `invalid_request`; platform/Unicode/capability mismatch → `incompatible`; layer/ref resolution or ontology schema failure → `invalid_ontology`; limits → `resource_exhausted`; generation drift → `snapshot_changed`; reserved production coordinate → `unsupported_identity`; uncategorized defects → `internal`. Caller wall-clock timeout remains a Pi invocation state, not a ROCS result.

## Command and capability architecture

Candidate post-ADR operations:

```text
rocs discover-capabilities --json
rocs discover --repo . --request-json - --json --no-index-cache --no-env-file
rocs pack <ont_id> --repo . --expected-snapshot-digest sha256:... \
  --expected-document-digest sha256:... --json --no-index-cache --no-env-file
```

`discover-capabilities` is the negotiation owner and returns supported request/result/error/algorithm/Unicode/platform versions with effect `none`. Schema-3 `contracts` registers all operations and conditional effects; it does not carry protocol schemas.

The bound pack mode verifies a fresh accepted snapshot and selected root digest before emitting the closed pack envelope with `corpus_snapshot_digest`, `root_document_digest`, per-document `document_digest`, and `pack_digest`. A mismatch fails; adapter metadata cannot manufacture provenance. Existing unbound exact-ID pack may remain for explicit interactive use but is never valid automatic-preflight follow-up.

Automatic production mode uses a prepared verified runtime and exact argv. The environment is exactly `HOME=<operator home>`, `PATH=/usr/bin:/bin`, `LANG=C.UTF-8`, `LC_ALL=C.UTF-8`, `PYTHONNOUSERSITE=1`, `PYTHONDONTWRITEBYTECODE=1`, `ROCS_WORKSPACE_ROOT=<explicit canonical workspace>`, `ROCS_WORKSPACE_REF_MODE=strict`, and no other inherited keys. It uses absolute interpreter/module paths, no implicit dotenv, and no ROCS cache or repository writes. Development-runtime preparation may write a disclosed external content-addressed cache during explicit TUI enablement; prompt-run discovery does not invoke `uv` or write that cache.

### Internal modules

Expected owner-local structure:

- `src/rocs_cli/discovery.py` — immutable snapshot, normalization, scoring, classification, canonical result;
- `src/rocs_cli/cli_ontology_utility.py` — command adapter;
- `src/rocs_cli/cli.py` — parser registration;
- `src/rocs_cli/contracts.py` — operation and effect declaration;
- `src/rocs_cli/id_index.py` — reuse or extract stable logical path handling;
- `src/rocs_cli/model.py` / `repo_view.py` — load from captured bytes rather than rereading for digesting;
- `tests/test_semantic_discovery.py` — golden, adversarial, budget, identity, and filesystem tests.

Do not put discovery ranking into `id_index.py`, and do not extend `pack.py` to accept free-text roots. Discovery and exact-ID graph expansion are separate capabilities.

## Trust and rendering boundary

Ontology text is governed semantic content but remains untrusted instruction data. A digest proves byte identity, not prompt safety.

Automatic adapters may inject only structurally validated fields:

- `ont_id`;
- kind;
- logical layer identifier;
- integer score;
- closed evidence rule names;
- release/development identity and result digest.

They must not automatically inject definitions, bodies, Markdown, examples, paths, marker-like text, or arbitrary frontmatter into the system role. Full semantic content is retrieved through an explicit exact-ID `pack` tool result after candidate resolution.

## Error and resource behavior

ROCS uses ordinary non-zero machine-readable errors for:

- unsupported protocol or algorithm;
- invalid query;
- unavailable or incompatible release identity;
- corpus/query/result limit exhaustion;
- invalid ontology content;
- resolution failure.

Limit behavior is closed:

- query, corpus-file, corpus-byte, per-file, parser, and result-byte excess fail with `resource_exhausted` before a successful result;
- `candidates` is a deterministic top-K projection and sets `truncated=true` when otherwise eligible candidates are omitted;
- retrieval classification is computed over the full scored set before top-K projection, so truncation cannot turn multiple candidates into a unique candidate;
- every effective limit and truncation fact is included in the effective-execution/result digest.

Limit exhaustion is not `no_candidates`. Wall-clock timeout belongs to the caller because time-dependent cutoffs would make ROCS output nondeterministic.

Automatic discovery must run with:

- no implicit `.env` loading;
- explicit workspace root/profile/ref mode;
- strict ref resolution for released identities;
- a minimal allowlisted process environment;
- index cache disabled, or a truthful declared cache effect outside automatic mode.

## Adversarial conclusions incorporated

The design rejects the following tempting shortcuts:

1. **Raw candidate cards in the system prompt** — prompt-injection privilege escalation.
2. **Automatic execution of arbitrary consumer `scripts/rocs.sh`** — repository code gains hidden pre-turn execution authority.
3. **One outcome enum for all failures and relevance states** — process, policy, and retrieval become indistinguishable.
4. **Digest only selected candidates** — omitted document changes can alter ranking without identity drift.
5. **Use current Pi TypeScript ranking as a second implementation** — creates divergent semantic retrieval authority.
6. **Cross-turn cache before stable corpus identity** — stale reuse is cheaper than proving freshness and therefore unsafe.
7. **Treat an existing intelligence capsule as a semantic release coordinate** — loses release/adoption meaning.
8. **Fleet-enable development snapshots** — establishes ambient unreleased semantics as default authority.

## Acceptance gates

The ROCS slice is complete only when:

- parser operations and schema-3 contracts remain exactly closed;
- request/result schemas reject unknown fields and unsupported versions;
- golden outputs match across supported Python 3.12/Unicode 15.0.0 environments, locales, corpus order, and cache state;
- scoring, evidence, and identity use the same captured bytes;
- hard query, file, corpus, candidate, parser, and result limits and their reject-versus-truncate rules are proven;
- symlink, root-escape, duplicate-path/ID, invalid-UTF-8, mid-capture-change, and parser-amplification fixtures fail closed;
- automatic cache-disabled discovery leaves repository and cache bytes unchanged;
- ambiguity and multi-intent fixtures never auto-select an ID;
- unavailable, incompatible, and exhausted states cannot become `no_candidates`;
- adversarial text cannot escape into structural result fields;
- existing unbound exact-ID `pack`, intelligence membrane, and transaction behavior remain non-regressed while bound-pack mode is additive.

## Candidate post-ADR implementation sequence

This section is proposal detail only. It is not an AK `implementation_plan` artifact and authorizes no task or mutation before ADR and post-ADR planning.

### R0 — Contract fixtures

- Freeze request/result examples and invalid fixtures.
- Encode the reviewed `rocs-lexical-v0`, canonicalization, errors, limits, and byte ordering as independent fixtures.
- Implement only `development_snapshot`; keep the production release coordinate rejected/reserved.
- Add adversarial corpora and cross-runtime golden test harness.

### R1 — Pure discovery core

- Implement one-read immutable corpus snapshotting and hard resource limits.
- Implement deterministic scoring, evidence, retrieval classification, and digesting.
- Unit-test without CLI or filesystem mutation.

### R2 — CLI and executable effects

- Add `discover-capabilities`, `discover`, and bound-pack parser/handlers.
- Add schema-3 registrations with truthful effects.
- Ensure automatic mode disables cache and implicit environment loading.
- Add parser parity, JSON error, filesystem invariance, and compatibility tests.

### R3 — Opt-in Pi adapter dogfood

- Publish exact protocol fixtures for the Pi port.
- Add development discovery only behind explicit TUI confirmation and the session-generation gate.
- Preserve current default search behavior and static hinting outside that gate.
- Use ROCS bound-pack mode for discovery follow-up; preserve unbound pack only as interactive compatibility.
- Remove the TypeScript search scorer only during the later adopted default cutover, so normal users never experience an unadopted behavior migration.

### R4 — Release/adoption binding

Blocked until a concrete AK decision coordinate accepts the separate semantic-release, ROCS-tool-trust, and consumer-adoption owner contracts:

- resolve adopted semantic coordinate without merging executable trust into it;
- reject unadopted or incompatible capsules in normal automatic mode;
- emit adoption/use receipt facts for owner-surface capture;
- prove semantic coordinate rollback and independent adapter/runtime rollback.

## Default and rollout phase matrix

| Phase | Ranking owner | Identity/runner | Automatic behavior | AK task posture | Rollback |
|---|---|---|---|---|---|
| Pre-ADR | current behavior | none | unchanged | no implementation tasks | not applicable |
| Development dogfood | ROCS candidate path only | development snapshot + prepared development runtime | TUI session opt-in only | post-ADR task required | disable session and remove staged cache |
| Adopted canary | ROCS | decision:53 semantic release coordinate + independently pinned runtime | named TUI canary only | decision:53 accepted + adoption receipt + named task | semantic N→N−1 when present, otherwise disable to current behavior; package/runtime rollback |
| Explicit search default | ROCS | adopted identities | `ontology_inspect search` cutover only | evidence-gated task | restore prior package version |
| Automatic preflight default | ROCS | adopted identities | separate decision/evidence gate | separately linked task | disable feature/package rollback |
| Fleet | ROCS | fleet policy | separately authorized | rollout tasks | policy rollback plus pinned prior generations |

Startup orientation remains independent and may report availability only; it does not become default concept injection. One-consumer evidence can authorize a canary, not package or fleet defaults.

No fleet rollout, mandatory preflight, online registry, embeddings, or model reranking belongs before R4 evidence.
