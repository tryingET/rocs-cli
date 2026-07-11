---
summary: "Wave 3 deterministic semantic-transaction behavior coverage."
read_when:
  - "Reviewing or changing semantic transaction behavior."
---

# Wave 3 transaction coverage

| Contract | Evidence |
|---|---|
| Strict transaction identity, plan/capsule/base digests, semantic effects, IDs, blast radius, obligations, owner partitions, preimages, gates, rollback, digest | `tests/test_semantic_transactions.py::test_full_lifecycle_and_content_addressed_receipt`; Wave 2 strict-schema tests remain active. |
| Prepare and simulate do not mutate ontology bytes | `test_full_lifecycle_and_content_addressed_receipt`. |
| Apply-only mutation, distinct operator approval, same-filesystem staging, deterministic verifier, content-addressed receipt | `test_full_lifecycle_and_content_addressed_receipt`, `test_stale_approval_verifier_and_publication_fail_closed`. |
| Stale base, approval mismatch/model approval, verifier failure, injected publication failure restore exact preimages | `test_stale_approval_verifier_and_publication_fail_closed`. |
| Ref-layer and cross-owner writes fail closed | `test_owner_and_ref_crossing_rejected`. |
| Verify and rollback reject receipt/postimage drift and restore preimage bytes | Lifecycle test plus strict digest checks in `transactions.py`; additional drift branches are direct fail-closed guards. |
| Waves 0–2 regression | Full `unittest discover` includes Wave 0 safety, Wave 1 contracts, and Wave 2 membrane suites; report the count from the current run rather than pinning a stale number here. |

The tests use disposable temporary ontology/artifact roots. Transaction code invokes no shell, model, or network execution. The hidden `--inject-failure` option is test-only and not part of the public contract.
