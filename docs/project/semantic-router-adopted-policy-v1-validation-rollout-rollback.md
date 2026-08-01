---
summary: "Validation, staged rollout, evidence custody, and rollback plan for Decision 103 adopted routing-policy protocol."
read_when:
  - "Planning implementation or any owner/empirical action after Decision 103."
type: "validation_rollout_rollback"
status: "proposed"
decision_id: 103
---
# Validation, rollout, and rollback — adopted semantic-routing policy v1

## Governing posture

Decision 103 is protocol design only. Passing this packet's review does not authorize the phases below. Each phase opens only under a separate scoped task with accepted predecessor evidence.

```text
P0 protocol review
→ P1 offline verifier implementation
→ P2 semantic-owner path/publication implementation
→ P3 fresh custody and preregistration
→ P4 D policy authoring
→ P5 one-shot U/O execution
→ P6 owner publication
→ separate consumer decision(s)
```

## P0 — protocol review

Required:

- packet hashes and aggregate exact;
- JSON schema parses and is closed;
- three mandatory review lanes accept;
- synthesis recommends `ready_for_adr`;
- Decision 103 passport is internally consistent;
- no code, policy, dataset, publication, or runtime mutation.

Rollback: replace the proposal with a new packet aggregate; preserve rejected reviews.

## P1 — ROCS offline verifier

Authorized only after accepted ADR and implementation plan. Implement schema embedding, strict I-JSON/JCS, all seven digest domains, object/invariant/complete-history validation, safe errors, fixtures, independent Node oracle, and explicit-local-file CLI verification.

Gates:

- Python and Node byte agreement;
- malformed, duplicate, noncanonical, over-budget, stale/forked history matrices;
- publish-without-pass, withdrawal, revocation, head fork/regression, identity drift, and proof-age failures;
- existing Decision 102 route/discovery compatibility unchanged;
- complete repository gate and reverse rollback rehearsal;
- `live_acquisition_implemented=false` mechanically observable.

Fixtures remain conspicuously synthetic. No real policy or owner path is touched.

## P2 — semantic-owner storage mechanics

Softwareco ontology owner separately accepts exact paths and implements append-only/CAS candidate/publication storage. This phase may use synthetic fixtures only.

Gates:

- owner-local task and review;
- no-follow, atomic, crash-safe append/head update;
- full history reconstruction;
- concurrent writer/fork rejection;
- withdraw/revoke and failed-update rehearsal;
- ROCS verifies but cannot write or approve;
- external recovery preserves prior head and immutable events.

No live publication occurs in P2.

## P3 — fresh custody and preregistration

Before D disclosure:

1. semantic owner freezes Softwareco-owned concept inventory and source snapshot;
2. DSPx or another named independent owner accepts custody, privacy, licensing, retention, deletion, and access controls;
3. B0-unexposed U/O authors create and seal U=600 and O=96;
4. independent annotators/adjudicator complete readiness;
5. D authors independently create D=360;
6. contamination checks bind B0, D, U, policy-source eligibility, and templates;
7. evaluator, metrics, floors, identities, command, and rollback are preregistered.

Raw U/O stays outside Git/AK/ROCS/Pi. The controller receives only digests and readiness receipts.

Stop permanently for the affected set on leakage, B0 derivation, role conflict, unlicensed/private content, annotation unreadiness, digest drift, or custody uncertainty.

## P4 — visible policy authoring

Policy authors use only the frozen Softwareco ontology sources and D. Every clause alternative has exact owner provenance and contamination review. Selected IDs remain Softwareco-owned.

Gates:

- D behavior and operational dry-runs under the P1 verifier;
- policy/provenance/candidate digest freeze;
- no U/O access;
- independent semantic-owner review;
- rollback by candidate supersession before U/O execution, never by rewriting D history.

D results are development evidence only.

## P5 — one-shot U/O execution

Custodian executes the exact preregistered command once against sealed U/O and frozen candidate. Policy authors/implementers receive no row outputs before immutable verdict publication.

Evidence-validity precedence:

1. integrity/execution invalidity → `indeterminate`, stop without retry;
2. otherwise any frozen gate failure → `fail`, stop without same-candidate change;
3. otherwise all gates and independent review pass → `pass`.

Required safety/utility floors are those in Decision 102's accepted validation contract: zero false routes on 300 U null rows, zero unexpected U errors, exact O oracles, point and Wilson precision floors, at least 80% overall applicable correct-route coverage, per-stratum and holdout floors, and byte-identical repeat. Report full-precision gates and aggregate confusion matrices. A pass requires independent custody and verdict review.

A failed policy may produce a new candidate only under a new task and fresh acceptance set when required by exposure rules. The failed report remains immutable.

## P6 — semantic-owner publication

Only a reviewed `pass` verdict permits the owner to append `publish`. Publication captures a fresh owner commit/tree and terminal head. ROCS independently validates complete history and produces a currentness proof. Publication evidence does not create consumer adoption.

Withdrawal/revocation rehearsal occurs before first publish. A live owner capability remains blocked until separately implemented and reviewed; explicit local owner files may support an offline publication rehearsal but not production currentness claims.

## Consumer gates (outside Decision 103)

After P6, separate exact-consumer decisions may authorize:

### C1 no-injection shadow

- clean current owner branches and installed artifacts;
- explicit consumer consent and opt-in;
- command-only or deterministic faux-provider harness first;
- observe route/currentness and record suppression without changing prompt content;
- no added provider/model request;
- exact disable rollback and live reload proof.

### C2 prompt-projection canary

Only after C1 acceptance and recovery rehearsal. Requires separate prompt-custody, provider, cost, retry, compaction, and delivery evidence. One named canary; default off.

### C3 automatic preflight

Last and separately decided. Requires accepted semantic quality, publication currentness, consumer benefit/safety evidence, independent recovery controller, action-time owner proof, provider/model authorization, and tested startup/default rollback. A single canary cannot imply fleet rollout.

## Dogfood meanings

| Dogfood | Lawful claim |
|---|---|
| P1 synthetic verifier | protocol implementation works on synthetic fixtures |
| P2 owner-storage rehearsal | append/head/rollback mechanics work on synthetic owner data |
| P4 D run | visible development policy behavior only |
| P5 U/O | frozen offline acceptance verdict only |
| P6 publication rehearsal | owner publication/currentness mechanics only |
| C1 faux-provider shadow | operational no-injection integration only |
| C2 canary | bounded delivery/behavior under named authorization |
| C3 automatic | only the exact accepted activation scope |

No dogfood level may claim a later evidence dimension.

## Global stop conditions

Stop on protected Decision 102 drift, B0 reuse, cross-owner meaning, U/O exposure, unreviewed floor change, malformed or incomplete verdict, non-pass publication, stale/forked owner head, network or provider/model surprise, dirty owner worktree used as authority, missing recovery owner, consumer substitution, automatic enablement, or restoration uncertainty.

## Evidence retention

Preserve rejected packets, failed/indeterminate reports, immutable owner events, rollback receipts, and independent reviews. Session logs and intercom are not owner authority. AK stores links/digests, never raw protected data or synthesized owner facts.
