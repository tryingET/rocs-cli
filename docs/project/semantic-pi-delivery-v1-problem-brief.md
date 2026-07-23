---
summary: "Problem brief for replacing Decision 53's fictional Pi adapter identity and unverifiable delivered claim with a real component identity and host-witnessed v1 receipt."
read_when:
  - "Reviewing or implementing the Decision 53 Pi delivery successor."
system4d:
  container: "Decision 53 successor problem boundary."
  compass: "Make Pi delivery identity and evidence truthful without widening semantic or production authority."
  engine: "Owner identity -> reviewed v1 protocol -> default-off implementation -> separately authorized isolated proof."
  fog: "A fixture issuer, callback return, or package path may be mistaken for a product identity or post-application witness."
type: "problem_brief"
status: "proposed"
---

# Problem brief — semantic Pi delivery v1

## Trigger

Decision 53 protocol v0 and its default-off Pi implementation use `pi-adapter` as a repository and receipt issuer. No such repository, package, product charter, capability-map entry, or independent lifecycle exists. The accepted Pi-owner identity artifact at commit `63d1e9f5c271007b48c45818d1f419a228de1561` instead establishes the existing `pi-extensions` repository and `pi-ontology-workflows` component as the Pi-side semantic-delivery attester, while keeping Pi host identity separate.

V0 also permits an isolated constructor flag to emit `delivered` after local checks. Pi currently supplies immutable host context but no host-issued acknowledgement after the completed prompt chain has been installed. Prepared bytes, callback return, package paths, fixtures, and local flags therefore cannot truthfully prove delivery.

## Why this is Tier 1

The correction changes a cross-repo protocol schema, digest domain, issuer model, runtime acceptance rules, Pi extension API, and evidence boundary. It affects ROCS, `pi-ontology-workflows`, and the Pi host. It requires a successor decision and cannot be repaired by editing accepted v0 history or silently aliasing identities.

## Required outcome

A successor must:

1. preserve `docs/project/semantic-release-v0/**` and the accepted v0 ADR as history;
2. introduce `semantic-pi-delivery-receipt.v1` with digest domain `semantic-release.pi-delivery.v1`;
3. bind governance role, repository provenance, component, package artifact, protocol issuer, host, loaded artifact, runtime generation, and prompt-run attempt as separate axes;
4. require a separately issued Pi-host post-application witness before `delivered`;
5. keep delivery default-off, keep `live_acquisition_implemented=false`, and reject v0 receipts in the successor runtime;
6. permit no compatibility alias from `pi-adapter`;
7. keep production/live gates closed until a real consumer, consent, one operator-named canary, and an independent recovery controller exist.

## Non-goals

This decision does not establish a consumer, name a canary, appoint recovery ownership, authorize publication/adoption/activation, enable startup/default/fleet behavior, or prove provider transmission or model influence.

## Stop condition

No v1 implementation or executable dogfood begins before exact-byte review closure, successor ADR acceptance, post-ADR plans, owner-scoped tasks, and explicit task reevaluation.
