---
summary: "Validation, staged rollout, stop conditions, and rollback contract for Decision 85 insertion evidence v1."
read_when:
  - "Validating or rolling out Decision 85 implementation."
  - "Checking live, production, or rollback authority for insertion evidence v1."
type: "validation_rollout_rollback"
status: "accepted_plan"
---
# Validation / Rollout / Rollback — Semantic Pi insertion evidence v1

## Scope and authority

This contract gates the operator-authorized path from isolated implementation through bounded production. AK evidence `5583` records the exact all-phases authorization. Authorization does not expand the accepted insertion-only claim or bypass AK/owner gates. Immutable Decisions 53/71/80/82/84 and failed tasks `4230`, `4250`, `4278`, and `4298` remain untouched.

Before implementation, Decision 85 must have all continuation artifacts attached, every linked `post_adr_execution` task explicitly reevaluated, passport `ready_for_unblocked=true`, and state exactly `unblocked`.

## Source-integrity preflight

Before each owner task:

- verify five-file aggregate `272c892af593ff10ddb056b1914f20372308fe8a47ca28b3ca04ca8e27882991`;
- verify vector SHA-256 `e23437e075f49c36e7487deeec2ab8126cd8fb14c0dbf07bf48d17e466525ed4`;
- verify accepted-object aggregate `e1a715cd868bdd9807eecb798b29ac02342697cc2afd9ac8eb7d9b6296b97a7e`;
- use a fresh isolated worktree at an explicit base commit;
- record, but never clean/overwrite, unrelated shared-checkout changes;
- reject every `pi-adapter` identity and predecessor packet/resolver/recovery/SQL/seccomp/Wasm import.

Planning observed dirty shared bases `pi-mono@5be4473cc156eb03d0069cc6770f1b95ea9eac97` and `pi-extensions@0066fa49594ffa718f763113c2d191c842fcd5d8`. They are observations, not mandated candidate bases. Owners select and record actual bases without absorbing dirty bytes by convenience.

## Validation gates

### G0 — Protocol and oracle independence

- Draft 2020-12 bundle has exactly six named top-level schemas and local references only.
- Python and Node `26.1.0` separately parse frozen sources and execute all 16 cases and 13 fixtures.
- Each owns its strict parser, NFC/JCS, eight digest domains, raw-byte hashing, event scheduler, and state machine.
- Neither validator nor host/component/integration implementation imports behavioral output from another implementation, generated file, expected field, or case ID.
- Every implementation executes from inputs/events first and reads `expected` only afterward for comparison/reporting.
- Unreachable, unused, duplicate, or hook-incompatible events fail.
- Both validators reproduce 3 accepted cases and all frozen aggregates.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 docs/project/semantic-pi-insertion-evidence-v1/validate_vectors.py
node docs/project/semantic-pi-insertion-evidence-v1/validate_vectors.mjs
uv run --frozen python -m unittest discover -s tests -p 'test_semantic_pi_insertion_conformance.py' -v
TMPDIR="$HOME/.cache/rocs-ci-tmp" ./scripts/ci/full.sh
uvx ruff==$(python -c 'import json; print(json.load(open("scripts/tool_versions.json"))["ruff"])') check .
git diff --check
```

### G1 — Pi host conformance

Faux-provider/test-callback gates prove:

- pre-factory loader-derived fixed identity, exactly-once registration, and monotonic handler index;
- exact terminal `input + contribution` apply with separator inside contribution;
- prepare/apply/assign/readback/witness/applied/record order;
- operation-derived span, including repeated contribution bytes;
- strict object validation without prototypes/accessors/symbols/cycles;
- private brand and `issued -> acknowledging -> consumed|invalid` closure;
- process-local lifecycle and generation/attempt/registration overflow;
- exact reload/abort/deadline order before callback/await/effect;
- all six entrypoint seams and every matching/absent/foreign/revoked/impossible-frame result;
- no provider/model operation before record commit;
- late settlement, stale API, empty prompt, duplicate registration, and same-run refresh behavior;
- grant re-enable/active rejection, immutable grant ID and attempt binding, per-grant counter reset versus process totals;
- expiry/disable in idle and active states, attempt exhaustion, exact over-contribution `aborted` error, and ordinary fallback;
- privacy-safe status shape, nearest-rank percentile calculation, exact error-rate population, atomic `rollbackRequired`, and auto-disable;
- no session JSONL/database authority.

The host harness executes all 16/13 schedules without using IDs or expected objects to choose behavior.

```bash
cd packages/coding-agent
npx tsx ../../node_modules/vitest/dist/cli.js --run test/extension-prompt-chain-insertion-evidence.test.ts
npx tsx ../../node_modules/vitest/dist/cli.js --run test/extension-host-capabilities.test.ts
npx tsx ../../node_modules/vitest/dist/cli.js --run test/extensions-runner.test.ts
npx tsx ../../node_modules/vitest/dist/cli.js --run test/suite/agent-session-model-extension.test.ts
npx tsx ../../node_modules/vitest/dist/cli.js --run test/agent-session-runtime-events.test.ts
npx tsx ../../node_modules/vitest/dist/cli.js --run test/agent-session-dynamic-tools.test.ts
cd ../..
npm run check
git diff --check
```

`npm run check` may rewrite files; run it only in the isolated candidate, inspect every diff, and reject paths outside task scope.

### G2 — Component conformance

The package proves:

- only fixed `pi-extensions` / `pi-ontology-workflows` / `@tryinget/pi-ontology-workflows` identity;
- complete separator-plus-rendering contribution bytes;
- Schema-3 return only from the exact applied callback;
- generation/attempt/index equality and exactly-once consumption;
- stale/clone/forge/delegate/foreign/timeout/throw/abort/reload/shutdown rejection;
- development/production grant bounds, expiry, disable, and default-off behavior;
- no predecessor delivery restoration or unrelated default change.

Component tests independently validate component-owned Schema-3/digest/callback behavior. They do not emulate the host fixture state machine and never branch on vector IDs/expected values.

```bash
cd packages/pi-ontology-workflows
npm run docs:list
node --import tsx --test tests/semantic-insertion-evidence.test.ts tests/semantic-preflight-lifecycle.test.ts
npm run quality:pre-push
npm run check
cd ../..
bash ./scripts/package-quality-gate.sh ci packages/pi-ontology-workflows
git diff --check
```

### G3 — Offline integrated matrix

Use disposable HOME/config/cache paths, a faux provider, and exact candidate artifacts.

- Both standalone validators execute full 16/13 closure.
- The host harness independently executes full 16/13 closure.
- The real component executes the 3 accepted cases plus component-owned identity, acknowledgement, grant, stale/reload, throw/timeout, and disable cases.
- Integration exercises every guard result, callback-boundary reload/abort/deadline, and terminal insertion bytes.
- No test harness derives behavior from ID/expected fields.
- Before/after hashing proves no source checkout or managed semantic `dist/` mutation.
- Disable/reload restores feature absence.

The receipt records versions, commands, hashes, counts, filesystem effects, and rollback. It is development evidence only.

### G4 — Named development canary

Workstation runtime-owner task D1 performs these operations after G0–G3:

1. run `python3 scripts/phasee/lane-op.py status current-posture`, `python3 scripts/phasee/lane-op.py status raw-backends`, and applicable service health; stop on degraded baseline/coexistence;
2. record a plan-only install/reload/rollback diff and obtain apply admission;
3. install exact candidates into one named disposable development Pi environment without changing baseline services;
4. start/reload one named process and verify capability/API versions;
5. enable a grant with `profile=development`, expiry <=10 minutes, max attempts <=32, and max contribution <=16 MiB;
6. run one explicit TUI insertion attempt;
7. inspect `getPromptChainInsertionEvidenceStatus()` for exact grant ID/generation/profile/limits, latest Schema-4 record, per-grant and process counts, durations, controls, and `rollbackRequired=false` without raw bytes;
8. disable/reload and prove absence;
9. restore prior runtime coordinates and recheck baseline health.

A faux provider is sufficient. If a real provider is used, its output is out-of-claim and the insertion record must already be committed before eligibility. D1 owns installation/reload/rollback; ROCS V1 only verifies its receipt.

### G5 — Owner releases and production canary

- PH1/PC1 owner release and supply-chain gates pass and bind exact commits/artifacts/API compatibility.
- Package publication is authorized by evidence `5583` but performed only by the two package release owners; engineering release notes use insertion-only wording. Editorial/steward publication is a separate owner handoff.
- PR1 first runs workstation status/admission and service-health surfaces, records a plan-only deployment/rollback diff, and stops on degraded baseline/coexistence.
- After apply admission, PR1 deploys both coordinates default-off and owns installation/reload/version rollback without changing baseline services.
- PR1 rehearses version and disable/reload rollback before enablement.
- PR1 enables one named process with exact `profile=production_canary`, <=30 minutes, <=10 attempts, and <=256 KiB contribution.
- Before and after every canary attempt, PR1 reads the privacy-safe status; host-side counters enforce time/attempt/size limits and auto-disable on exhaustion.

The host atomically sets `rollbackRequired=true` and disables future attempts for any protocol/hash disagreement, pre-record provider/model operation, stale-frame effect, unexpected prompt byte, capability/version mismatch, raw-prompt logging detection available to the host, or configured threshold breach. PR1 treats any unplanned closed error, `rollbackRequired`, or failed rollback probe as an immediate disable/reload/version-rollback trigger.

### G6 — Bounded production wave

Only PR1 performs the wave after G5 passes and a fresh workstation status/admission check. It enables at most 5 named processes, each with `profile=production_wave`, for at most 24 hours and at most 500 aggregate attempts. PR1 allocates per-process attempt ceilings whose sum is <=500 and records each immutable grant ID/generation/limits before enablement. Each grant is process-local/time-bound; there is no durable default-on switch.

The host status meter owns per-grant attempt/error counts, contribution lengths, record/control results, and integer-nanosecond duration samples; process totals are reported separately and excluded from thresholds. Nearest-rank percentiles sort accepted samples and select `ceil(p*n)-1`. Error rate uses current-grant `(all Schema-5 failures except private-cause operator_abort)/(accepted + all Schema-5 failures)` after denominator 100. The host evaluates thresholds at every record/failure linearization and atomically auto-disables plus marks that grant `rollbackRequired` on breach. PR1 polls after each canary attempt, at least every 25 wave attempts, and immediately on warning.

Thresholds for contributions up to 256 KiB:

- zero invariant/hash/identity/guard/byte disagreements;
- zero pre-record provider/model operations;
- zero stale-frame, unexpected reentry, or unexpected prompt-change effects;
- operational closed-error rate below 1% after the first 100 attempts, excluding operator aborts;
- insertion bookkeeping excluding component prepare callback: p95 <= 50 ms and p99 <= 250 ms;
- complete callback-to-record duration: p95 <= 1 second and every attempt below the fixed 5-second deadline;
- rollback probe succeeds on every named process before and after the wave.

Any host `rollbackRequired` flag or independently detected threshold breach makes PR1 stop all grants and perform immediate disable/reload plus version rollback when needed. PO1 only verifies PR1/release receipts and records AK evidence; it performs no runtime operation. Expansion beyond this 5-process/24-hour/500-attempt wave requires a fresh owner-reviewed rollout artifact even though the operator authorized production generally.

Never log raw prompt/contribution bytes by default. Digests/lengths are operational observations, not public authentication.

## Stop conditions

Stop and fail the active task if:

- Decision 85 is not exactly `unblocked` before implementation;
- frozen bytes/aggregates drift;
- exact schema/digest/event/state/precedence/guard behavior requires inference;
- schema count differs from six or forbidden predecessor machinery appears;
- IDs, expected values, generated artifacts, or another implementation become an oracle;
- identity cannot be fixed before factory execution;
- terminal apply/assignment/readback bytes diverge;
- any provider/model operation becomes eligible before record commit;
- reload/session replacement leaves an old frame/API/witness/controller effective;
- brand is reproducible from JSON/digests;
- dirty owner bytes would be overwritten or silently incorporated;
- a focused/full gate fails for a non-environmental reason;
- installation/publication/rollout exceeds its owner task or named stage;
- evidence claims semantic correctness, provider transmission, model input/influence, adoption, consent, or public authentication;
- any G5/G6 rollback trigger or threshold fires.

Environmental failures are recorded and retried only after correction; they are never passing proxies.

## Rollback

### ROCS

Revert only the new schema/validator/test and exact Node pin. Never edit/regenerate the five frozen files. No runtime state exists.

### Pi host

Disable, synchronously revoke frames/witnesses/controllers, reload/restart, and restore the prior reviewed package version. Prove ordinary prompt/provider policy resumes and the capability is absent. No recovery is attempted.

### Component

Disable, invalidate pending acknowledgement state, reload, and restore the prior package version. Never restore predecessor Decision-53 files. Existing semantic-preflight/search behavior must match baseline.

### Workstation runtime/production

D1/PR1 remove only named candidate installs/caches after recording exact paths, restore prior compatible coordinates, and prove one prompt path with capability absent and no record. ROCS V1/PO1 only verify receipts. No runtime task edits source checkouts to roll back.

### AK/history

Never delete decisions, ADRs, reviews, tasks, evidence, receipts, or failed attempts. Record failure, leave the task failed, and open a fresh reframed task if authorized. Architecture changes require a superseding decision.

## Completion evidence

Every task records exact base/head/paths; frozen hash checks; commands/outcomes; independent counts; filesystem/secret/network posture; no-oracle proof; rollback rehearsal; deferred stages; and precise insertion-only wording.
