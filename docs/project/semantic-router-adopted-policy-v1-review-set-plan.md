---
summary: "Strict three-lane review plan for Decision 103 adopted routing-policy protocol."
read_when:
  - "Opening or synthesizing Decision 103 review."
type: "review_set_plan"
status: "proposed"
decision_id: 103
---
# Review-set plan — adopted semantic-routing policy v1

## Reviewed packet

Review exactly the paths listed and hashed by [`semantic-router-adopted-policy-v1/packet-manifest.json`](semantic-router-adopted-policy-v1/packet-manifest.json). Any byte change retires all reviews against the prior aggregate.

## Closure mode

Decision 103 uses `multi_lane_requires_synthesis`. All three lanes are mandatory. Each lane returns `accept | revise | reject` with evidence. A designated synthesis cites all final lane reviews and alone may recommend `ready_for_adr`.

## Lane A — semantic authority and publication

Reviewer must be independent of packet authorship and assess:

- `softwareco/ontology` is the only first-policy semantic owner;
- canonical `co.software.*` identifiers are accepted only when present in the exact frozen owner inventory, and the parsed digest-bound Decision 102 policy/provenance manifest and every provenance-record source owner, concept IDs, joint-route IDs, and later selected IDs all remain bound to it; prefix inference and core relabeling fail;
- core-owned meaning is not copied, relabeled, or selected by convenience;
- owner publication, withdrawal, and revocation remain owner-issued;
- ROCS and AK do not acquire semantic authority;
- publication and consumer adoption remain separate;
- later owner paths and approval remain explicit gates.

Reject on ambiguous namespace ownership, mutable-latest semantics, inferred approval, or publication without withdrawal/currentness handling.

## Lane B — protocol, security, and rollback

Reviewer assesses:

- closed JSON shapes, canonical I-JSON and digest domains;
- append-only event chain, authenticated monotonic checkpoint, authoritative ref, and reserved terminal-event capacity;
- no-follow, local-only, bounded acquisition expectations with closed issuer/approval/channel/store trust;
- fresh single-use caller challenge/action binding, separate caller verification request, approved Ed25519 key/signature with non-circular attestation body, and authenticated challenge-consumption body/receipt whose issuer trust, store, key, and digest are externally pinned;
- unidirectional checkpoint→head commitment plus a contiguous monotonic checkpoint chain from the caller pin;
- exact equality joins across policy binding, candidate, verdict, envelope, attempt, non-circular verdict/publication approval subjects, signed approval attestation bodies, event, history, head, checkpoint, receipt, commit/tree, and proof;
- the external request pins exact custodian, reviewer, and semantic-owner authority coordinates, separate non-circular authority credentials, signed approval digests, trust roots, and canonical raw-32-byte Ed25519 public keys; repository strings or self-digests cannot issue authority;
- the signed receipt body authenticates descriptor-anchored no-follow capture, closed-environment, no-network, and stable-final-recheck guarantees as well as identity, challenge, checkpoint, and time;
- stale H1 replay after H2, forked, absent, withdrawn, revoked, or mismatched heads fail closed;
- rollback disables invocation or returns to a separately current prior release without rewriting history;
- no network, live signing/key provisioning, provider/model, or live capability is implied.

Reject on digest ambiguity/cycle, repository-string or opaque-ref authority, self-issued/redatable/replayable currentness, invalid/unapproved signing key, proof-nested values masquerading as caller pins, missing challenge consumption, rollbackable/broken checkpoint chain, non-atomic head semantics, incoherent proof/history size bounds, exhausted withdraw/revoke reserve, unsafe error disclosure, or rollback that erases history.

## Lane C — empirical custody and falsification

Reviewer must be independent of policy authorship and assess:

- closed canonical B0 deny coordinates and complete no-reuse coverage including O/evaluator/fixtures/floors/regressions/execution, with each coverage source digest joined to the actual artifact coordinate;
- owner-issued custody policy established before data creation, including exact source/license/consent evidence, complete prohibited-content set, privacy/ACL/retention/backups/all deletion triggers/incidents;
- exact canonical role cardinalities, twelve pairwise-distinct authenticated principals, nested exposure evidence and append-only access history, custodian/reviewer distinction, implementer binding, and mechanical D/U/O-author/annotator/adjudicator/evaluator separation;
- exact unique B0 surface bijection and canonical commit coordinates;
- inspectable preregistered attempt envelope with closed environment and nested reservation/rollback, anti-overlap, one process invocation with two fixed internal passes, and outcome precedence;
- policy quality gates prevent both false routing and trivial abstention;
- raw protected rows remain outside ROCS, Git, and AK;
- failed or indeterminate evidence is retained without mechanical retry.

Reject on reusable or incompletely covered B0 coordinates, opaque custody, role conflict, exposed acceptance data, post-observation floor changes, extra invocation/pass/retry/rerun, or execution without sealed identities.

## Synthesis checklist

Synthesis must state:

1. packet aggregate and manifest SHA-256;
2. exact review dispatch/session identifiers;
3. every lane outcome and unresolved minority finding;
4. whether protocol design may proceed to ADR;
5. that no real policy, evaluation, publication, consumer, or Pi action is authorized;
6. whether a superseding packet revision is required.

## Independence disclosure

Every reviewer records repository paths read, B0 exposure, authorship conflicts, and whether they observed any proposed D/U/O content. A reviewer with U/O access cannot review policy authorship; a policy author cannot review U/O custody or verdict correctness.
