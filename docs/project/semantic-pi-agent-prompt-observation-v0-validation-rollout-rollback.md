---
summary: "Validation, rollout, stop, and rollback contract for Decision 98."
read_when:
  - "Validating or dogfooding Decision 98."
type: "validation_rollout_rollback"
status: "proposed"
decision_id: 98
---
# Validation, rollout, and rollback — correlated Pi agent-prompt observation v0

## Global stop rule

Any indeterminate provenance, build, load, prompt mismatch, attempted second provider request, provider result, or restoration means: stop forward work, preserve sanitized evidence, disable if safe, execute rollback after any start/mutation, and create a separate investigation task. Never retry mechanically.

Use managed private mode-0700 scratch and the workstation heavy-job wrapper. Raw profiles/settings never enter AK. Preserve unrelated dirty and `.ontology/` paths.

## H−1 gates

- current owner-main parent and `b4bbbc080` evidence recorded;
- exact five capabilities including confirm countdown behavior;
- current trust/context/stale/shutdown semantics;
- changelog/docs/exports;
- new focused tests, touched-file LOC/byte report, brownfield exceptions;
- exact focused command from finalized test paths, root `npm run check`, root `./test.sh`, `git diff --check <parent>..<candidate>`, clean status;
- two reviews;
- disposable revert tree equals parent and passes named gates.

## H0 gates

- concurrent token uniqueness and correct pair under reversed overlap;
- shallow-frozen pre-start outer envelope and ready envelope;
- immutable primitive snapshots while nested options retain existing shared mutability;
- exact chain/assignment/ready/preflightResult/provider order;
- old extension/error compatibility and same-process replacement non-reuse;
- passive extension proves no automatic host-owned token copying;
- capability object contains identifier only;
- docs/types/exports/changelog;
- new focused tests and brownfield exceptions;
- exact commands specified in the accepted implementation plan;
- two reviews and revert-to-H−1 tree equality/gates.

## P0 gates

- Decision-89 behavior remains;
- unsupported host preserves ordinary behavior;
- match/mismatch/latest-slot/overlap/nonmatching/repeated semantics;
- malformed rules:
  - missing/non-string/nonmatching token ignores without prompt access;
  - matching token plus missing/non-string/invalid-Unicode prompt clears with no record/error/log leakage;
  - malformed after terminal does not rewrite;
- all lifecycle/request/grant clearing paths;
- literal outputs/precedence;
- token absent from public keys/digest inputs/errors/readback/log/session/evidence and token-only invariance;
- one pre-start plus one ready registration;
- zero growth of existing lifecycle test;
- exact hard touched-file command:

```bash
for f in <touched-code>; do test "$(wc -l <"$f")" -le 500 && test "$(wc -c <"$f")" -le 51200; done
for f in <touched-tests>; do test "$(wc -l <"$f")" -le 1000 && test "$(wc -c <"$f")" -le 81920; done
```

- current manifests/lock/version/entrypoint/release/semantic-delivery unchanged;
- focused/quality/full/package/release/AST/diff/clean gates;
- two reviews and revert-to-parent equality/gates.

## R1a gates

- accepted R1a parent equals H0 and delta is exactly the named one test file;
- required P0 root/commit/tree env values verified before loader use;
- `DefaultResourceLoader` `additionalExtensionPaths` loads exact entrypoint with discovered extensions disabled;
- fixed faux-provider identity/clock/chunks/tokens;
- exact command from the plan;
- expected order `pre-start -> assignment -> ready -> terminal -> faux-provider start`;
- overlap/malformed/mismatch/lifecycle/literal-output cases;
- no settings/install/network/real model;
- independent review.

## R1b preparation

Fail closed unless recorded:

- H0/P0/R1b-canary source commits/trees/reviews and current-line ancestry;
- Node/npm versions, lock hashes, `npm ci --ignore-scripts`, explicit offline build, artifact hashes;
- exact CLI argv, cwd, environment variable names (never credential values), private profile path/mode/ownership;
- profile settings: retry disabled, provider max retries zero, compaction disabled, no queued state;
- `--no-extensions --no-approve --no-tools` plus only explicit P0 and reviewed canary `-e` paths;
- canary provider has no network and hard-fails invocation two before any transport;
- process termination independent of candidate extension;
- normal settings/executable hash inventory proving no mutation;
- sanitized evidence destination and rollback authority.

## R1b live gates

Same TUI process must report exact argv/environment allowlist, loaded P0/canary realpaths, one unsuffixed ontology command source, absence of other ontology sources, fixed protocol, and request count.

Sequence:

1. default-off disabled;
2. one fresh confirmed grant and enabled-none;
3. one semantic prompt to deterministic local provider;
4. exactly one provider invocation;
5. literal terminal match/mismatch;
6. no tool/retry/compaction/follow-up/second request;
7. disable/reset;
8. immediate rollback after success or stop.

Mismatch is observed evidence but fails success closure; no same-task investigation.

## Isolated runtime rollback

Disable if safe; terminate and prove process absence; prove normal settings/executable hashes unchanged; prove no candidate process/RPC endpoint; preserve sanitized receipts; remove only owned scratch after liveness/ownership checks or retain with owner note. Partial rollback stops all work.

Pi-source revert dependency order is R1b canary source -> R1a harness -> H0 -> H−1. P0 reverts independently in `pi-extensions` and must be absent from later integration/runtime verification. H0 never reverts while its R1a/R1b descendants remain. Verification occurs in disposable worktrees, requires resulting tree equality to each recorded parent and named gates, and never resets branches.

## B0 preregistration and gates

Commit/review an immutable preregistration with at least 40 dual-annotated prompts balanced across named strata, dataset/gold digest, adjudicator, exact runtime/semantic coordinates, metrics, numerical floors, exclusions, cold/warm treatment, and timeout censoring. ROCS owns execution/analysis; no provider/model. No B1 task unless floors pass.

## Evidence and KES closure

AK records exact stage identities/commands/counts/reviews, same-process R1b provenance, one-invocation receipt, rollback receipt, and B0 prereg/report. A KES-owner task promotes reviewed learnings and returns an accepted artifact/knowledge ID. Final closure requires reviews for H−1, H0, P0, R1a, R1b, rollback, B0, and KES.
