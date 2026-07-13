---
summary: "Controlling Decision:53 synthesis after semantic-release revision-v12 rereview."
read_when: ["Checking Decision:53 closure after revision v12."]
type: "review_synthesis"
status: "complete"
review_outcome: "revise_rfc"
---
# Decision 53 Rereview Synthesis v12

## Outcome

`revise_rfc`

Revision v13 must:

1. bind the complete approved action into the publication transaction and derive recovery authority from operation, transaction, prior state and result—no expected-action parameter;
2. model recovery-start state correctly: pre-linearization sees the prior head, post-linearization sees the result head;
3. carry exact consumer repository and canary scope through request, generation and every Pi delivery variant;
4. pin tombstone genesis through an external semantic-owner receipt and require each delta authorization digest to equal its resulting lifecycle/removal head;
5. replace the oversized differential artifact with a hash-complete deterministic shard manifest whose manifest and every shard are under 16 MiB; enforce byte and depth limits in Python and Node.

Decision `53` remains `review_pending`; no production gate is open.
