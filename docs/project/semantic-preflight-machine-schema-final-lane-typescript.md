---
summary: "Decision:52 final TypeScript/Pi independent machine-schema verifier lane."
read_when: ["Checking decision:52 final verifier review."]
type: "review_memo"
decision_id: 52
review_outcome: "ready_for_adr"
---
# Final Machine-Schema Lane — TypeScript / Pi

Reviewed ROCS `df64a18` and Pi `c98c0a9c` under peer run `scoutpeer-mrhs68o3-b6745d78` using Node/Ajv with no Python imports or producer calls.

Independent checks confirmed:

- unknown-field failure tuple exactly matches the portable fixture;
- negative pack has two documents, differs from golden, passes Draft 2020-12 structure, recomputes digest `sha256:032016c3c2c25d267d2ab6a0916c93700c3f7de44d9c58d830141309606025d5`, and fails root-first as intended;
- the exact Pi prepared-runtime corpus parses;
- no remaining material verifier ambiguity exists.

```text
review_outcome = ready_for_adr
```
