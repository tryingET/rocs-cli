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

This is a proposed ROCS product contract, not an adopted semantic release or cross-owner decision. R0–R2 may implement the independent discovery primitive. A Pi adapter may dogfood it only behind an explicit, session-scoped development gate that leaves current default behavior unchanged. Release identity, default adapter cutover, consumer adoption, fleet enablement, and mandatory enforcement remain gated by the separate **Semantic Release Capsule and Consumer Adoption Protocol v0** decision.

ROCS owns deterministic retrieval, result integrity, bounded exact-ID packs, and executable command-effect contracts. It does not own ontology meaning, consumer desired state, AK task intent, Pi prompt authority, or model conclusions.

## Problem

ROCS can retrieve an exact ontology ID with `pack`, but an agent beginning with ordinary task language does not know that ID. `pi-ontology-workflows` currently compensates by running `rocs build`, reading generated artifacts, and ranking documents in TypeScript. That creates two retrieval authorities, writes build artifacts during search, and cannot produce a portable, replayable discovery result.

The companion Pi-side architecture is [Pi Semantic Preflight Adapter v0](../../../../softwareco/owned/pi-extensions/packages/pi-ontology-workflows/docs/project/semantic-preflight-adapter-v0.md). This RFC is the primary decision artifact; the companion is a required reviewed input for the cross-repo decision.

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
5. The later Semantic Release Capsule decision supplies the production identity and tool-distribution trust root.

## Controlled-vocabulary preflight

| Term | Kind | Owner | Status in this RFC | Promotion posture |
|---|---|---|---|---|
| `semantic-discovery-request.v0` | protocol schema identifier | ROCS | proposed | code/schema contract after ADR |
| `semantic-discovery-result.v0` | protocol schema identifier | ROCS | proposed | code/schema contract after ADR |
| `rocs-lexical-v0` | algorithm identifier | ROCS | proposed | executable contract after ADR |
| `development_snapshot` | identity variant | ROCS | proposed, unreleased | no ontology promotion implied |
| `release_capsule` | cross-owner identity reference | semantic release owner | reserved dependency | governed by the separate release-capsule decision |
| `matched`, `ambiguous`, `no_match`, `not_applicable`, `unavailable` | adapter outcome projection | Pi adapter | proposed | adapter contract, not ontology vocabulary |

This preflight classifies owner and use. It does not mutate ROCS ontology, AK vocabulary, Prompt Vault, or Pi runtime authority.

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
| Desired capsule, rollout intent, decisions, evidence references | AK / consumer authority |
| Turn-sensitive retrieval UX and prompt adapter | `pi-ontology-workflows` |
| Startup orientation | `pi-society-startup-context` |
| Empirical comparison and optimization | DSPx / Oracle |

## Protocol surfaces

### 1. Discovery request

A caller supplies a closed request containing an identity selector rather than a circular computed identity:

```json
{
  "schema": "semantic-discovery-request.v0",
  "query": "ordinary task language",
  "identity_selector": {
    "kind": "release_capsule",
    "digest": "sha256:..."
  },
  "profile": "review",
  "algorithm": "rocs-lexical-v0",
  "limits": {
    "query_bytes": 16384,
    "corpus_files": 5000,
    "corpus_bytes": 33554432,
    "file_bytes": 1048576,
    "candidates": 12,
    "result_bytes": 65536
  }
}
```

For development mode the selector is `{"kind":"development_snapshot"}` with no caller-supplied snapshot digest. After capture, ROCS emits an `effective_request` containing the resolved semantic identity and effective limits. `caller_request_digest` covers canonical caller-request JSON with no digest field; `effective_request_digest` covers canonical effective-request JSON with no digest field. The result digest covers the final result with `result_digest` omitted. Unknown fields and unsupported schema or algorithm versions fail explicitly.

### 2. Semantic identity

Identity is a tagged union from the first implementation slice:

```text
release_capsule      immutable, approved capsule identity

development_snapshot unreleased local corpus; explicit opt-in only
```

A development snapshot must be labeled `released: false` and bind:

- the raw bytes of every eligible document considered, not only returned candidates;
- manifest/profile bytes and effective layer order;
- logical layer names and paths without machine-local absolute paths;
- resolved ref revision where available plus the actual considered bytes;
- ROCS tool build identity;
- request schema, algorithm, normalization, and Unicode-data versions;
- resource-limit and truncation decisions.

Scoring, evidence, and identity must derive from one immutable in-memory byte snapshot. ROCS must not score cached parsed content and digest a later filesystem read.

The existing intelligence `capsule_digest` is not a Semantic Release Capsule and must not be overloaded as one.

### 3. Discovery result

On successful invocation, ROCS emits a closed result:

```json
{
  "schema": "semantic-discovery-result.v0",
  "caller_request_digest": "sha256:...",
  "effective_request_digest": "sha256:...",
  "effective_request": {},
  "semantic_identity": {
    "kind": "development_snapshot",
    "released": false,
    "digest": "sha256:..."
  },
  "algorithm": {
    "id": "rocs-lexical-v0",
    "normalization": "nfkc-casefold-v0",
    "unicode_data": "..."
  },
  "retrieval": "multiple_candidates",
  "candidates": [
    {
      "rank": 1,
      "ont_id": "core.Agent",
      "kind": "concept",
      "layer": "core",
      "score": 1200,
      "evidence": [
        {"field": "label", "rule": "token_exact", "query_token": "agent"}
      ],
      "document_digest": "sha256:..."
    }
  ],
  "limits": {},
  "truncated": false,
  "result_digest": "sha256:..."
}
```

Allowed retrieval states are:

- `no_candidates`
- `unique_candidate`
- `multiple_candidates`
- `ambiguous_equivalence`
- `low_confidence`

These describe deterministic retrieval, not semantic truth. Several independently relevant candidates are not automatically ambiguity. ROCS does not emit `not_applicable` or `unavailable`: those belong to the consumer adapter.

### 4. Consumer outcome projection

Adapters may project the successful ROCS result and local invocation state into the agreed operator vocabulary:

```text
matched | ambiguous | no_match | not_applicable | unavailable
```

That projection must retain separate machine fields:

```text
invocation: ok | unavailable | timeout | incompatible | resource_exhausted
applicability: applicable | not_applicable | unknown
retrieval: <ROCS retrieval state or absent>
```

This avoids conflating process failure, caller policy, and retrieval. `not_applicable` must come from an explicit deterministic adapter rule or operator mode, never from lexical absence. `unavailable` must never be presented as `no_match`.

## Retrieval algorithm contract

`rocs-lexical-v0` must be fully specified in code and golden fixtures before CLI exposure:

1. Capture eligible bytes once under pre-parse file, per-file, and corpus limits.
2. Parse only validated ontology fields.
3. Normalize with an explicit algorithm and bind the Unicode data version.
4. Tokenize deterministically; define punctuation, duplicate-token, phrase, and empty-query behavior.
5. Score with non-negative integers and closed field/rule weights.
6. Use evidence records with closed field/rule enums; never emit arbitrary matching snippets.
7. Sort by score descending, then ontology ID UTF-8 bytes ascending, then kind.
8. Apply closed confidence and equivalence rules.
9. Serialize canonical UTF-8 JSON and compute `result_digest` after all effective limits are represented.

Filesystem eligibility is closed: regular files only; no symlinks or root escape; no duplicate logical paths or semantic IDs; strict UTF-8; bounded parser depth/collection sizes; and stable pre/post metadata checks around each one-read capture. Any change during capture fails the invocation rather than combining generations.

Initial scored fields may include:

- ontology ID;
- labels;
- synonyms;
- description;
- examples and anti-examples;
- relation targets and types where validated.

The result may reveal that a field matched, but automatic prompt adapters must not copy arbitrary field values into a system prompt.

## Command architecture

Add one top-level operation:

```text
rocs discover --repo . --query <text> [resolution selectors] \
  [--identity release|development] [--json] [closed limits]
```

Properties:

- output is JSON by default for machine adapters; human text is a deterministic projection;
- no artifact output in v0;
- no `build` prerequisite;
- no model or proposal adapter;
- exact-ID `pack` remains a separate command;
- automatic Pi preflight invokes discovery with cache disabled;
- interactive tools may permit the already-declared conditional cache effect.

Schema-3 `contracts` registers the operation and its conditional effects. Request/result/algorithm versions are separate protocol identifiers unless a later decision deliberately bumps the command-contract schema to advertise protocol negotiation.

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
- every effective limit and truncation fact is included in the effective request/result digest.

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
7. **Treat an existing intelligence capsule as a release capsule** — loses release/adoption meaning.
8. **Fleet-enable development snapshots** — establishes ambient unreleased semantics as default authority.

## Acceptance gates

The ROCS slice is complete only when:

- parser operations and schema-3 contracts remain exactly closed;
- request/result schemas reject unknown fields and unsupported versions;
- golden outputs match across supported Python runtimes, locales, corpus order, and cache state;
- scoring, evidence, and identity use the same captured bytes;
- hard query, file, corpus, candidate, parser, and result limits and their reject-versus-truncate rules are proven;
- symlink, root-escape, duplicate-path/ID, invalid-UTF-8, mid-capture-change, and parser-amplification fixtures fail closed;
- automatic cache-disabled discovery leaves repository and cache bytes unchanged;
- ambiguity and multi-intent fixtures never auto-select an ID;
- unavailable, incompatible, and exhausted states cannot become `no_candidates`;
- adversarial text cannot escape into structural result fields;
- existing exact-ID `pack`, intelligence membrane, and transaction behavior remain unchanged.

## Implementation sequence

### R0 — Contract fixtures

- Freeze request/result examples and invalid fixtures.
- Specify `rocs-lexical-v0` weights, normalization, thresholds, and byte ordering.
- Contract the release/development identity union even though release production is deferred.
- Add adversarial corpora and cross-runtime golden test harness.

### R1 — Pure discovery core

- Implement one-read immutable corpus snapshotting and hard resource limits.
- Implement deterministic scoring, evidence, retrieval classification, and digesting.
- Unit-test without CLI or filesystem mutation.

### R2 — CLI and executable effects

- Add `discover` parser and handler.
- Add schema-3 command registration with truthful conditional cache behavior.
- Ensure automatic mode disables cache and implicit environment loading.
- Add parser parity, JSON error, filesystem invariance, and compatibility tests.

### R3 — Opt-in Pi adapter dogfood

- Publish exact protocol fixtures for the Pi port.
- Add development discovery only behind an explicit session-scoped operator gate.
- Preserve current default search behavior and static hinting outside that gate.
- Keep exact-ID `pack` unchanged for explicit follow-up.
- Remove the TypeScript search scorer only during the later adopted default cutover, so normal users never experience an unadopted behavior migration.

### R4 — Release/adoption binding

Blocked until the cross-owner Semantic Release Capsule decision lands:

- resolve adopted capsule identity;
- reject unadopted or incompatible capsules in normal automatic mode;
- emit adoption/use receipt facts for owner-surface capture;
- prove rollback to the previous capsule.

No fleet rollout, mandatory preflight, online registry, embeddings, or model reranking belongs before R4 evidence.
