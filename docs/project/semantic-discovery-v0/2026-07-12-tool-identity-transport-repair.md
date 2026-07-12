---
summary: "Operator-authorized explicit CLI transport for Pi-prepared ROCS tool identity under decision 52."
read_when:
  - "Implementing or auditing semantic discovery invocation identity."
type: "protocol_repair"
status: "accepted_repair"
decision_id: 52
---
# Semantic Discovery v0 — Tool-Identity Transport Repair

## Defect

Task `3818` found that ROCS must bind Pi's prepared-runtime `manifest_digest` into `tool_identity`, but the accepted closed request, exact argv, and environment supplied no channel for that opaque value. Inferring it from paths, cache names, repository files, or ambient environment would violate the accepted trust boundary.

## Operator-selected resolution

The operator selected **explicit CLI metadata flags** on 2026-07-12:

```text
--tool-kind development_runtime
--tool-manifest-digest sha256:<64 lowercase hex>
```

These flags are mandatory for `discover` v0. They are invocation metadata rather than caller-request or corpus identity. Pi computes and verifies the prepared-runtime manifest digest, then supplies it unchanged. ROCS validates the closed fields and binds them into `tool_identity`, `effective_execution_digest`, and `result_digest`.

No environment variable, implicit descriptor lookup, path inference, repository launcher, or output post-processing may supply or replace the identity. The parser may recognize `adopted_runtime`, but execution remains rejected as `unsupported_identity` until decision `53` authorizes production runtime adoption.

Bound pack follow-up also carries the discovery request's explicit effective profile so its fresh snapshot can reproduce the same corpus identity.
