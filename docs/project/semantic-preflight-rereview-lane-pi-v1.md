---
summary: "Decision:52 attempt-2 Pi runtime re-review lane."
read_when:
  - "Reviewing decision:52 attempt-2 Pi findings."
type: "review_memo"
decision_id: 52
review_outcome: "revise_rfc"
---
# Re-review Lane — Pi Runtime v1

Reviewed `semantic-discovery-protocol-v0.md@c9591ba` and companion `semantic-preflight-adapter-v0.md@45fb944f` under Prompt Vault `review-rfc-multi` and installed Pi 0.80.6 evidence.

## Closed
Prompt-run scope, unauthenticated markers, TUI-only development direction, timeout-only Linux posture, generation invalidation, and separate output caps are materially improved.

## Remaining strict blockers

1. Prepared-runtime manifest, atomic publication, dependency/interpreter closure, permissions, and symlink-safe cache verification are unspecified.
2. Startup readiness versus prompt invocation is racy.
3. The 750/100/250 ms bounds do not form one end-to-end deadline, including post-KILL reaping.
4. Invalid UTF-8/truncated JSON has two possible classifications.
5. No trustworthy host-version/capability source is named.
6. TUI confirmation lacks idle requirement, timeout, and expiry.
7. Success/ambiguity/no-match lack operator-visible readback.

Exactly three lenses were applied: prompt/runner trust; lifecycle/process/output closure; consent/compatibility/UX.

```text
review_outcome = revise_rfc
```
