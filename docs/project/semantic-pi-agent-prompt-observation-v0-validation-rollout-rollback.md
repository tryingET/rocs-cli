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

An indeterminate provenance, dependency preparation, build, load, reload/start, prompt mismatch, attempted second provider request, provider result, or restoration result means:

1. cease forward actions;
2. preserve sanitized evidence;
3. disable if safely available;
4. execute preauthorized rollback immediately after any mutation/start;
5. create a separate investigation task.

Never retry mechanically. Use managed `TMPDIR`, private mode-0700 scratch, and the workstation heavy-job wrapper for large npm work. Raw settings/profile bytes never enter AK; only sanitized hashes/receipts do. Preserve unrelated dirty files and `.ontology/` paths.

## H−1 gates

- exact current owner-main parent and local evidence commit recorded;
- capability identifiers/contexts rederived, not cherry-picked blindly;
- stale-context, trust, shortcut, RPC/print/shutdown, docs/export tests;
- focused/full owner commands pass;
- two reviews;
- `git revert <H−1>` applies cleanly to its parent and full required gates pass in a disposable verification worktree.

## H0 gates

1. unique token per concurrently alive execution inside one process/runtime generation;
2. correct token across paired pre-start/ready events under reversed overlap;
3. fresh pre-start envelopes; immutable token/system-prompt snapshots; existing nested options mutability preserved;
4. shallow-frozen ready envelope and mutation attempts cannot affect later handlers/host state;
5. complete chain before assignment; ready after assignment; ready before `preflightResult(true)` and provider start;
6. old extension/error compatibility;
7. token not reused across replacement generations in the same process;
8. passive extension proves the host does not automatically copy token into host-owned messages/entries/provider payload/log/error surfaces;
9. immutable capability object contains the capability identifier—not any run token—only on supporting hosts;
10. docs/types/exports/changelog and full coding-agent gates pass.

Use new focused tests and record exceptions for unavoidable brownfield over-budget host files. Required commands are focused Vitest, root `npm run check`, root `./test.sh`, `git diff --check`, and clean status. H0 revert validation returns to H−1, not pre-substrate owner main.

## P0 gates

1. all Decision-89 exact-append/digest/source-order cases remain;
2. unsupported-host precedence and old-host ordinary behavior;
3. prepared state with private token;
4. whole-prompt exact match/mismatch vectors and unknown contribution survival;
5. latest preparation wins; nonmatching/repeated ready events no-op; overlap never misattributes;
6. every reset/disable/expiry/grant/mode/generation/request/cwd/compatibility/producer/validation/non-append clearing path;
7. literal six-state output and precedence;
8. token absent from public record keys, command output, record digest inputs, errors, logs, session/evidence snapshots;
9. changing only the token leaves public record bytes and `record_digest` identical;
10. malformed ready input clears or ignores exactly as the state contract declares;
11. exactly one pre-start and one ready registration;
12. `preflight-runtime.ts <= 500` LOC; new code <=500; new tests <=1000; hard touched-file audit;
13. then-current package manifest, lock, version, entrypoint, release metadata, semantic-delivery files/tests unchanged;
14. focused, quality, full, package/release, AST, diff, and clean-status gates pass;
15. two reviews and disposable `git revert <P0>` validation.

## R1a gates

The exact committed Pi test path and command are recorded. It verifies H0/P0 Git identities before loading P0 through the real extension loader. Faux provider inputs and clock/random sources are fixed. Expected order:

```text
pre-start(token)
-> host assignment
-> ready(token, assigned prompt)
-> terminal observation
-> faux-provider request start
```

Negative overlap/mismatch cases prove omission rather than misattribution. No settings, installation, external network, or real model.

## R1b preparation

Fail closed unless recorded:

- exact H0/P0 commits, trees, artifact/lock hashes, current-line ancestry and reviews;
- Node/npm versions and successful lock-frozen dependency preparation;
- source-local built Pi argv and artifact hashes;
- absolute P0 package root and dependency availability;
- private isolated `PI_CODING_AGENT_DIR`, original absence/symlink state, mode, and ownership;
- byte/hash inventory proving normal global/project settings and executable remain unchanged;
- no-provider RPC/SDK command and tool `sourceInfo` provenance from the same candidates;
- pinned provider/model identity and authority for exactly one provider request;
- request-start counter/abort control;
- process termination and scratch cleanup commands independent of candidate extension;
- rollback authority and sanitized evidence destination.

## R1b live gates

- candidate protocol responds and provenance identifies one temporary candidate extension;
- default-off `disabled` then fresh confirmed grant and `enabled outcome=none`;
- tools disabled;
- exactly one provider-request start;
- one terminal exact-match or mismatch readback, recorded literally;
- no tool call, retry, compaction continuation, follow-up, second request, pack, publication, or default change;
- immediate disable/reset;
- immediate rollback after success or any stop condition.

Mismatch is a valid observed result but fails success closure; no additional live investigation occurs in the same task.

## Isolated runtime rollback

1. disable if safely available;
2. terminate candidate Pi and verify process absence;
3. prove normal settings/executable hashes remain equal to preflight inventory;
4. verify no candidate-loaded process or isolated RPC endpoint remains;
5. preserve sanitized candidate receipts;
6. remove only owned isolated profile/build scratch after liveness and ownership checks, or retain it with explicit owner note;
7. report any incomplete restoration as partial rollback and stop.

H−1/H0/P0 source rollback uses reviewed `git revert` commits in disposable verification worktrees; never reset owner lines.

## B0 preregistration and gates

Before execution, commit and independently review a B0 preregistration with immutable dataset/gold digest, exact strata and balance, dual annotators/adjudicator, runtime/semantic coordinates, recall/false-match/ambiguity/no-match/size/latency/timeout metrics, numerical floors, exclusions, cold/warm policy, and timeout censoring. ROCS owns execution and analysis. No provider/model use.

No B1 task is created unless B0 floors pass.

## Evidence and KES closure

AK records exact stage commits/trees/commands/counts/reviews, R1b sanitized before/candidate/rollback receipts and one-request count, and B0 prereg/report identities. A KES-owner task then promotes reviewed learnings and returns an accepted artifact/knowledge ID. Final Decision-98 closure requires reviews for H−1, H0, P0, R1a, R1b, rollback, B0, and KES.
