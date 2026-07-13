---
summary: "Decision:53 revision-v9 Many-of-the-Greats decision selecting contextual dominance for owner-authenticated authority proofs."
read_when: ["Implementing or reviewing semantic-release revision v9."]
type: "conflict_resolution"
status: "proposed"
decision: "53"
rfc_revision: "semantic-release-revision-v9"
method: "many-of-the-greats"
---
# Decision 53 — Many of the Greats Resolution v9

## QUESTION

How must revision v9 divide authority between owner-issued observations, deterministic ROCS verification, canonical state machines, and finite differential evidence so that no caller becomes an ambient cross-owner oracle?

## MODE 1 — MANY OF THE GREATS

### School 1: Least-Authority Capability Security
- **Core claim:** Each owner surface alone issues its facts through a pinned read capability; assemblers only transport them.
- **Premises:** Labels and self-digests establish identity, not provenance. Cross-owner minting is authority substitution.
- **Strongest case:** Revision v8 permitted category reassignment and coherent fabrication because the snapshot assembler effectively issued all observations.
- **What it sees that others miss:** Correct graph structure cannot repair an unlawful issuer.

### School 2: Closed-World Proof Graphs
- **Core claim:** After lawful owner facts enter, every derived conclusion must follow from a complete closed graph with no surplus nodes, defaults, or unregistered edges.
- **Premises:** Omitted joins create false accepts; generic context recreates ambient authority.
- **Strongest case:** A normative role manifest and exact bundle closure turn review from open-ended probing into finite edge verification.
- **What it sees that others miss:** Provenance alone does not prove relational legality.

### School 3: Canonical Transactional State
- **Core claim:** Currentness requires an owner-store read at a pinned head/revision plus action-time freshness or CAS token.
- **Premises:** Immutable facts may remain historically valid while stale for authorization.
- **Strongest case:** Publication, activation, task, trust, and rollback decisions all require exact current pointers.
- **What it sees that others miss:** A correctly issued receipt can still be obsolete or forked.

### School 4: Explicit Trust-Boundary Engineering
- **Core claim:** Finite proof must terminate in named exogenous local capabilities whose distribution digests and scopes are pinned by verifier configuration.
- **Premises:** Infinite recursive proof is impossible; hidden ambient trust is worse than explicit bounded trust.
- **Strongest case:** Owner-store acquisition cannot be proven solely by candidate JSON. The architecture must specify exactly what the verifier trusts and what later implementation must demonstrate.
- **What it sees that others miss:** Formal closure without terminal axioms is either dishonest or non-terminating.

### School 5: Independent Differential Conformance
- **Core claim:** Python and Node must independently verify the same normative rule-role-edge manifest and derive mutation evidence rather than trusting fixture labels.
- **Premises:** Self-declared inventories and drift counts prove only themselves.
- **Strongest case:** Revision v8 claimed parity while Node ignored the registry.
- **What it sees that others miss:** Governance closure requires executable agreement about completeness evidence.

## MODE 2 — CONFRONTATION

### Clash 1: Least Authority vs Explicit Trust Anchors
- **Fundamental contradiction:** A terminal pin is trusted, but no cross-owner caller may inherit the pinned owner's issuance power.
- **Resolution:** Pins are owner-specific acquisition capabilities. A collator may carry owner-issued read receipts but cannot construct them. Role→owner→repository→capability is fixed normatively.

### Clash 2: Closed Graph vs Live Currentness
- **Fundamental contradiction:** An offline graph is immutable while current heads advance.
- **Resolution:** Graph validity is historical; authorization additionally requires each read receipt's CAS/freshness token to satisfy an externally configured action-time floor. The two predicates remain separate.

### Clash 3: Finite Edge Registry vs Open-Ended Review
- **Fundamental contradiction:** Review can imagine unlimited mutations, while decisions need finite closure.
- **Resolution:** A normative rule manifest enumerates every authority-bearing rule, role, anchor, node, owner, repository, and edge. Validators enforce a bijection between manifest and registry. Review may challenge manifest completeness, but missing listed coverage is machine failure.

## MODE 3 — INTEGRATION OR DECISION

- **Chosen path:** Contextual Dominance
- **Result:**
  - Least-authority capability security dominates fact issuance.
  - Canonical transactional state dominates current authorization.
  - Closed-world proof graphs dominate deterministic derivation.
  - Explicit trust-boundary engineering terminates proof recursion.
  - Differential conformance dominates claims of executable parity.
- **Why justified:** These schools govern different layers and cannot lawfully be collapsed into one universal snapshot authority.
- **What remains unresolved:** Live capability provisioning, read-receipt acquisition, and action-time freshness are later owner-authorized implementation work; revision v9 specifies their closed contract and refuses to claim operation.

## PRACTICAL CONSEQUENCE

Revision v9 must replace generic observations with owner-issued store-read receipts bound to externally configured owner-specific acquisition pins; bind receipt fact to exact head/revision and freshness/CAS token; enforce exact snapshot/role closure; complete the authority-rule manifest across every authority-bearing rule; make both validators enforce identical registry owner/cardinality/linkage rules; derive direct mutation evidence mechanically; and keep production authorization blocked until live acquisition evidence exists.
