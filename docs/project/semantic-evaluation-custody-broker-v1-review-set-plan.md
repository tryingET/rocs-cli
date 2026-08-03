---
summary: "Strict review-set plan for Decision 104's policy/broker/state-machine separation."
read_when:
  - "Launching or synthesizing Decision 104 review."
type: "review_set_plan"
status: "proposed"
decision_id: 104
---
# Review-set plan — semantic evaluation custody broker v1

## Reviewed object

Review the exact packet frozen by `semantic-evaluation-custody-broker-v1/packet-manifest.json`. Reviewers must cite the packet aggregate and manifest SHA-256. A review of a path, branch name, summary, or earlier bytes is non-controlling.

## Required independent lanes

### Lane A — constructibility and single-source semantics

Questions:

- Is `state-machine.json` sufficient to enumerate every legal/illegal transition and all eight evidence branches?
- Does any prose, schema proposal, or receipt imply behavior absent from the machine?
- Are branch predicates exclusive and complete?
- Does every path reach `closed` before `verdict_fixed`?
- Can generated Python/Node/fixture vectors remain independent while sharing the model as normative data?

Reject on any prose-only transition, ambiguous branch, hidden retry/reopen path, or representation that becomes an independent behavioral source.

### Lane B — broker security, linearizability, and lifecycle

Questions:

- Are every mutation's owner, expected generation, linearization point, crash disposition, and idempotency semantics explicit?
- Can any valid signature exist without matching committed state and still be accepted?
- Can concurrent or replayed commands start twice?
- Can an expired/revoked/closed handle still read?
- Can verdict fixation occur with an unreaped process, live handle, readable lease, or ambiguous store head?
- Is actual actor/channel authentication distinct from declared identity?

Reject if runtime behavior remains a signed assertion, if raw descriptors transfer, or if any crash path lacks a fail-closed authoritative disposition.

### Lane C — authority, scope, and supersession

Questions:

- Are semantic owner, broker owner, independent reviewer, ROCS, AK, publication owner, consumer, and Pi facts non-interchangeable?
- Does the immutable policy coordinate exclude runtime and publication semantics?
- Does publication/currentness genuinely reuse Decision 53 rather than shadowing it?
- Are Decision 103 history, R0/R1 carry-forward, rejected R2 evidence, and Decision 98 B0 handled without retroactive authority?
- Are all live effects blocked pending separately owned decisions/tasks?

Reject on inferred owner authority, fixture promotion, history rewriting, premature live gates, or scope that one repository cannot own.

### Lane D — simplicity, multi-order effects, validation, and rollback

Apply Prompt Vault's `100x-mindset` and `compound-check` lenses:

- Does the successor delete more concepts/joins than it adds?
- Is the next change easier because one model generates/checks vectors?
- Can a newcomer explain each subsystem independently?
- Are operational/review costs reduced rather than displaced?
- Do fault injection, independent parity, dogfood, and rollback test reality rather than documents?

Reject if the new architecture merely renames the combined graph, adds an adapter layer without deleting duplicate authority, or requires the same cross-product review loop.

## Adversarial probes required in synthesis

The controlling synthesis must explicitly answer:

1. valid signature with absent broker transition;
2. changed outer verdict with old valid approval;
3. concurrent start CAS race;
4. crash after start commit but before process observation/receipt delivery;
5. copied opaque handle after revoke/expiry/close;
6. actor-coordinate substitution with the same principal text;
7. caller-invented contamination digest;
8. map insertion-order permutation;
9. malformed hostile input escaping the safe error model;
10. completed verdict with retained process/handle;
11. publication/currentness object inserted back into evaluation;
12. Decision 98 B0 material hidden in synthetic fixtures;
13. a self-consistent attacker owner/store/descriptor/local-head world against independently supplied caller pins;
14. allocation A's atomic record followed by allocation B before A readback, proving that only A's current memberships renew;
15. exact numeric max/max+1 and every used operator/failure against the closed registries;
16. crash after spawn-intent claim before or after the sole spawn syscall, with no retry and containment emptiness before closure;
17. crash before/after protected-read spool persistence and acknowledgement, proving no second protected-store read;
18. crash across journal/verdict-register fixation, attacker-selected register authority, and identity-overlapping or stale approvals;
19. max-read delta trace growth, proving no copied prior-state quadratic expansion.

## Closure rule

All four lanes must return `accept` on identical bytes. A designated synthesizer must cite every lane, resolve rather than average conflicts, and return `ready_for_adr` only with no blocking finding. Timeout, silence, usage-limit failure, or review of drifted bytes is not acceptance.

The ADR is a separate artifact and may be written only after AK records legal strict-convergence closure. Implementation planning is separately reviewed after the ADR.
