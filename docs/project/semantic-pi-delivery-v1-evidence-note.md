---
summary: "Evidence establishing the Decision 53 Pi identity defect, current host-witness gap, and remaining live-owner blockers."
read_when:
  - "Reviewing evidence for the semantic Pi delivery v1 successor."
system4d:
  container: "Evidence boundary for the Decision 53 successor."
  compass: "Use owner-issued identity and observed host behavior without turning fixtures or implementation into authority."
  engine: "Trace origin -> retrieve owner decision -> inspect host application seam -> classify legal next move."
  fog: "Passing tests or current implementation may be mistaken for accepted identity, insertion proof, or production authorization."
type: "evidence"
status: "proposed"
---

# Evidence note — semantic Pi delivery v1

## Owner-issued identity

Pi-owner task `4108` is complete with AK evidence `5030` and `5031`. Its accepted artifact is:

- repository: `pi-extensions`;
- canonical source: `git+https://github.com/tryingET/pi-extensions.git`;
- workspace projection: `local://softwareco/owned/pi-extensions`;
- component: `packages/pi-ontology-workflows` / `pi-ontology-workflows`;
- package: `@tryinget/pi-ontology-workflows`;
- protocol role: `semantic_pi_delivery_attestor`;
- exact accepted commit: `63d1e9f5c271007b48c45818d1f419a228de1561`.

The artifact rejects a standalone `pi-adapter`, distinguishes governance ownership from repository identity, and grants no implementation, dogfood, or live authority.

## Origin of the defect

Repository history and a dedicated scout found that `pi-adapter` began as a fixture issuer label and was later hardened into an exact repository tuple. It has no product charter, repository, package, capability-map identity, release surface, or independent owner lifecycle. The v0 owner-identity gate correctly refused to substitute an implementation path for that missing owner fact.

## Current implementation behavior

The default-off v0 Pi implementation exists in `pi-ontology-workflows`. Its `SemanticReleaseDeliveryGate` can emit `delivered` when constructed with `isolatedDogfood: true` after checking cancellation, deadline, activation-head equality, generation receipt shape, and receipt digest. This is verified fixture behavior, not post-application evidence.

V0 remains historically valid as the accepted experiment. The successor must not edit its packet or alias its issuer. Runtime acceptance may deliberately reject v0 after v1 lands.

## Pi host observation

Current Pi host behavior chains `before_agent_start` handlers and later assigns the final system prompt to agent state. The extension callback return occurs before that assignment. Existing `ctx.hostCapabilities` provides immutable host package/version, extension API version, and static capability tokens, but it does not provide:

- a host-owned loaded-component manifest digest;
- a fresh extension runtime generation;
- a prompt-run attempt identity;
- post-assignment acknowledgement;
- an immutable application witness.

Therefore a callback return, prepared bytes, fixture output, path, package manifest, or static capability token cannot establish `delivered`.

## Live owner posture

No owner-issued artifact currently establishes all of:

- a real production consumer for this protocol;
- consumer consent;
- one operator-named canary through that consumer owner;
- an independently owned recovery controller outside replaceable semantic and runtime roots.

`live_acquisition_implemented=false` remains mandatory. Publication, adoption, activation, defaults, startup behavior, fleet rollout, and production D2E remain blocked.

## Process evidence

The accepted v0 ADR requires expansion through a later decision and superseding ADR. The governance lifecycle requires problem/evidence framing, RFC, immutable exact-artifact reviews, controlling synthesis, ADR, post-ADR implementation/validation plans, owner-scoped tasks, evidence, and learning.

## R21 implementation blocker

Post-ADR task `4230` independently verified the three pinned Unicode-15 input identities. The exact 1,913,704-byte `UnicodeData.txt` with SHA-256 `806e9aed65037197f1ec85e12be6e8cd870fc5608b4de0fffd990f689f376a73` contains six required surrogate range-sentinel source rows at lines 15253–15258: `D800`, `DB7F`, `DB80`, `DBFF`, `DC00`, and `DFFF`, all General_Category `Cs`. R21 simultaneously required parsing every field-0 source and rejecting every non-scalar token, with no sentinel branch. Machine-contract fail-closed rules therefore prohibited packet generation. AK evidence `5325` records the reproduced hashes, rows, no generated packet, and unchanged frozen sources.

R22 may resolve only this contradiction by recognizing the six exact pinned rows as non-emitting source metadata while retaining scalar-only mappings and outputs. Tests or implementation inference cannot repair r21 without a new exact-byte review and superseding ADR.

## R22 review blockers

The exact r22 review at commit `b834dc2e3b450483a7f0bfabf8fa88a910d9beb8`, aggregate `4c874dbbc016b09c5e2ba7b5c17dce20a9f4133ec8e7380a6b421e534eefec4f`, returned `revise_rfc`. CaseFolding contains six and CompositionExclusions four non-ASCII UTF-8 bytes in comment suffixes, while r22 did not order comment removal before ASCII syntax validation. Governance also found corrected runtime authority still bound to Decision 71 and required explicit sentinel-branch conformance obligations. The controlling record is `semantic-pi-delivery-v1-review-synthesis-r22.md`.

R23 must fix raw-byte preprocessing, bind all corrected authority to Decision 80 conditionally on its accepted superseding ADR, and require independent exact-six/negative/emission conformance while preserving the existing protocol fixture counts.

## Evidence conclusion

The lawful next move is a new cross-repo Tier-1 RFC for a default-off v1 receipt and host witness. It may authorize later isolated implementation and a separately authorized one-shot proof; it cannot authorize live adoption.
