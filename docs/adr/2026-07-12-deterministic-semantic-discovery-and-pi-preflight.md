---
summary: "Accepts ROCS-owned deterministic semantic discovery with a thin, prompt-run-scoped Pi semantic-preflight adapter and machine-readable cross-language protocol contracts."
read_when:
  - "Implementing semantic discovery in ROCS."
  - "Implementing semantic preflight in pi-ontology-workflows."
  - "Reviewing decision:52 authority or rollout boundaries."
type: "adr"
status: "accepted"
---

# ADR — Deterministic Semantic Discovery and Pi Preflight

## Decision

Accept the target architecture from AK decision `52`:

1. ROCS owns deterministic task-language candidate discovery over one captured semantic corpus.
2. ROCS owns corpus, tool, effective-execution, result, and bound-pack integrity contracts without merging those identities.
3. `pi-ontology-workflows` is a thin adapter for session readiness, bounded prompt-run invocation, safe structural rendering, explicit exact-ID bound-pack follow-up, and operator readback.
4. Automatic system-role content contains structural metadata only; ontology prose remains untrusted tool data.
5. Development dogfood is TUI-confirmed, generation-scoped, timeout-bounded, and default-off.
6. Production semantic release, ROCS tool trust, consumer adoption, default changes, and fleet rollout remain separately gated by decision `53` and later evidence.

## Accepted normative artifacts

Primary:

- `docs/project/semantic-discovery-protocol-v0.md`
- `docs/project/semantic-discovery-v0/protocol.schema.json`
- `docs/project/semantic-discovery-v0/invariants.md`
- `docs/project/semantic-discovery-v0/golden-fixtures.json`
- `docs/project/semantic-discovery-v0/differential-fixtures.json`

Pi companion:

- `packages/pi-ontology-workflows/docs/project/semantic-preflight-adapter-v0.md`
- `packages/pi-ontology-workflows/docs/project/semantic-preflight-v0/prepared-runtime.schema.json`
- `packages/pi-ontology-workflows/docs/project/semantic-preflight-v0/prepared-runtime-fixtures.json`

Controlling review closure:

- `docs/project/semantic-preflight-machine-schema-final-synthesis.md`

## Authority split

| Concern | Owner |
|---|---|
| Ontology meaning and semantic release approval | ontology/semantic owners |
| Deterministic discovery, machine protocol, snapshot and pack verification | ROCS |
| Prompt/session delivery and operator UX | Pi / `pi-ontology-workflows` |
| Desired state, decisions, tasks, rollout intent, evidence references | AK plus consumer owner |
| Production semantic coordinate/tool/adoption contract | decision `53` |
| Empirical behavior comparison | DSPx/Oracle |

## Consequences

### Positive

- Pi, DSPx, and other consumers can share one replayable retrieval authority.
- Python producers and TypeScript verifiers have machine-readable schemas and differential fixtures.
- Ambiguity, no-match, applicability, and invocation failure remain separate.
- Prompt injection risk is reduced by excluding ontology prose from automatic system-role blocks.
- Exact-ID pack provenance is bound to discovery identity.

### Costs

- V0 is Linux/Python-3.12/Unicode-15.0.0 constrained.
- Pi host capability identity must be added before preflight can activate.
- Development runtime preparation needs a verified content-addressed staging path.
- Existing Pi-local search remains temporarily active outside gated development use until later cutover evidence.

## Implementation obligations

Before implementation begins, decision `52` must carry accepted post-ADR:

- implementation plan;
- validation/rollout/rollback plan;
- owner-repo execution tasks linked as `post_adr_execution`.

Implementation must preserve:

- schema/fixture byte identity;
- no model/network authority in ROCS discovery;
- no automatic repository wrapper execution;
- no implicit dotenv or ambient runner overrides;
- no arbitrary ontology prose in automatic system prompts;
- no production or default claim from development dogfood.

## Deferred decisions

Decision `53` owns the unresolved production contract for:

- `semantic_release_coordinate`;
- semantic-owner approval;
- independently pinned ROCS runtime identity;
- consumer dependency intent;
- adoption/use receipts;
- production rollback and later default gates.

This ADR does not pre-accept decision `53`.

## Rejected alternatives

- Pi-local ranking as the durable retrieval authority;
- model/embedding retrieval as deterministic baseline;
- injecting the full ontology or definitions at startup;
- treating wrappers, manifests, mutable `dist/`, or tool version as semantic adoption truth;
- combining semantic corpus and executable identity in one digest.

## Rollback and supersession

Before implementation, rollback is semantic: supersede this ADR and keep current behavior.

After development implementation, rollback disables the session gate and removes the staged development generation while preserving current default search behavior.

Production rollback is not authorized here and must follow decision `53`.
