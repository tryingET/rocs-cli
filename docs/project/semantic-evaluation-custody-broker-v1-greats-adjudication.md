---
summary: "Many-of-the-Greats adjudication selecting owner-local machines joined by evidence contracts rather than one cross-owner state machine."
read_when:
  - "Reviewing the decomposition of Decision 104."
type: "evidence"
status: "proposed"
decision_id: 104
prompt_template: "many-of-the-greats"
prompt_version: 3
---
# Many-of-the-Greats adjudication — Decision 104 decomposition

## QUESTION

What architecture should replace Decision 103's rejected combined proof graph when semantic truth, execution custody, evaluation, and publication belong to different authorities?

## MODE 1 — MANY OF THE GREATS

### School 1: State-machine formalism

- **Core claim:** Safety comes from one explicit transition relation whose legal states, guards, crash outcomes, and invariants can be explored rather than inferred from prose.
- **Premises:** Distributed effects are unsafe when replay, linearization, and terminal states are implicit. A machine-readable model is the most reliable way to expose missing branches.
- **Strongest case:** The rejected R2 implementation passed 347 tests while independent review still found forgeable authority and incomplete joins. Executable state semantics would have exposed those gaps earlier.
- **What it sees that others miss:** Informal modularity can hide unsafe compositions and ambiguous recovery behavior.

### School 2: Security-kernel and capability discipline

- **Core claim:** A fact is trustworthy only when the component controlling the protected resource enforces it; signatures and semantic validators cannot substitute for mediation at the effect boundary.
- **Premises:** Authority must be minimal, explicit, and non-forgeable. Receipts describe committed effects but do not cause them.
- **Strongest case:** Dataset custody, process start, protected reads, revocation, and cleanup can only be established by the runtime that controls those effects. ROCS cannot prove those facts from caller-authored JSON.
- **What it sees that others miss:** A complete abstract model remains fiction if it is not co-located with the enforcement mechanism.

### School 3: Information hiding and end-to-end composition

- **Core claim:** Each owner must define its own state and expose a small stable contract; a cross-owner mega-machine duplicates hidden implementation state and becomes a second, false authority.
- **Premises:** Modules are reliable when design decisions are localized. Cross-system correctness should be established at interfaces, not by centralizing every internal transition.
- **Strongest case:** The 271 KB Decision 104 packet had to model global allocation, custody, spawning, read spooling, approval, evaluation, verdict storage, and publication joins. Every repair expanded the model while making ownership less legible.
- **What it sees that others miss:** Global formal completeness can destroy source-owner truth and evolvability.

### School 4: Evolutionary and socio-technical architecture

- **Core claim:** Decisions should align with systems and teams that can implement, test, operate, and revise them independently.
- **Premises:** Cross-owner designs fail when one repository specifies another owner's runtime in implementation detail. Small reversible decisions expose integration risk sooner.
- **Strongest case:** DSPx already owns execution episodes and receipt-backed empirical evidence; the semantic owner owns immutable policy meaning; ROCS owns deterministic evaluation under that meaning; Decision 53 already owns publication/currentness. Separate decisions let each owner accept its actual obligations.
- **What it sees that others miss:** Architectural review is not credible when the named owner has not accepted the machinery attributed to it.

## MODE 2 — CONFRONTATION

### Clash 1: State-machine formalism vs information hiding

- **Fundamental contradiction:** One school seeks a globally closed transition system; the other rejects any global model that reproduces owner-private state.
- **Incompatible assumptions:** A central model assumes one specification authority can truthfully enumerate all transitions. Information hiding assumes each owner must retain authority over internal semantics.
- **What formalism explains better:** Replay races, crash ambiguity, unreachable states, and missing terminal branches inside one runtime.
- **What information hiding explains better:** Why the global packet grew without converging and why its joins repeatedly invented authority.
- **Residual tension:** Cross-owner behavior still needs testable composition, but composition proof need not expose every internal state.

### Clash 2: Security kernel vs semantic proof

- **Fundamental contradiction:** Runtime enforcement establishes what happened; semantic proof establishes what the bytes mean. Neither can derive the other's authority.
- **Incompatible assumptions:** A semantic verifier cannot become a custody broker, and a custody broker cannot decide ontology or policy meaning.
- **What the security kernel explains better:** Single start, protected access, revocation, cleanup, and crash recovery.
- **What semantic proof explains better:** Canonical policy identity, deterministic evaluation rules, and verdict derivation from accepted evidence.
- **Residual tension:** The interface must reject unverifiable evidence without letting either side redefine the other.

### Clash 3: New publication integration vs Decision 53 reuse

- **Fundamental contradiction:** A new global protocol wants publication to be its final state; Decision 53 already owns publication/currentness independently.
- **Incompatible assumptions:** Publication cannot simultaneously be an internal transition of the evaluation machine and an external owner-authorized protocol.
- **What a global protocol explains better:** A visually complete end-to-end diagram.
- **What Decision 53 explains better:** Existing accepted authority, currentness, adoption, and rollback semantics.
- **Residual tension:** Compatibility requires a bounded adapter contract, not a second publication authority.

## MODE 3 — INTEGRATION OR DECISION

- **Chosen path:** Contextual Dominance
- **Result:**
  1. State-machine formalism dominates **inside one owner's enforcement or semantic boundary**.
  2. Security-kernel discipline dominates **where real process, dataset, handle, lease, and cleanup effects occur**.
  3. Information hiding dominates **between DSPx, ROCS, and the Decision 53 publication authority**.
  4. Evolutionary architecture dominates **decision sequencing**: each owner receives a separate reviewable decision before implementation.
- **Why this path is justified:** The schools do not combine into one global machine without contradiction. Their strengths apply at different boundaries. Owner-local executable machines can be joined through immutable, versioned evidence contracts and adversarial conformance vectors without creating a new central authority.
- **What remains unresolved:** Exact DSPx custody mechanics, exact ROCS evaluation semantics, and the minimal Decision 53 compatibility contract remain later decisions. No present document authorizes their implementation.

## PRACTICAL CONSEQUENCE

Decision 104 should specify only ownership, cross-owner invariants, evidence direction, and non-goals. The rejected global `state-machine.json` must not remain normative. Separate later decisions must be reviewed by the actual owners for DSPx custody/execution, ROCS evaluation, and a non-authoritative Decision 53 compatibility adapter. End-to-end proof should test interface traces generated from those accepted owner contracts rather than recreate their internal states in one graph.
