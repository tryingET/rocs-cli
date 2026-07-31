---
summary: "Evidence and predecessor disposition for Decision 89 extension-local handler observation."
read_when:
  - "Checking why Decision 89 excludes Pi-host insertion claims."
type: "evidence_note"
status: "proposed"
---
# Evidence note — extension-local prompt-chain handler observation v0

## Predecessor facts

- Decision 85 ADR and frozen RFC/vectors remain accepted architecture history.
- Task `4331` failed cleanly on an impossible repository-wide Ruff gate; evidence `5590`.
- Corrected R1b task `4342` completed the six-schema/eight-domain 16-case/13-fixture substrate; evidence `5600`.
- Host task `4343` produced no commit. Independent review remained controlling `REJECT/FAIL`; evidence `5665` records the stopped candidate and operator decision.
- Shared `pi-mono` stayed at `5be4473cc156eb03d0069cc6770f1b95ea9eac97` with no H1 mutation.
- The temporary H1 candidate was removed after recording its manifest.

## Lessons binding Decision 89

1. A package cannot prove host assignment/readback, universal dispatch exclusion, stale-host isolation, or provider/model behavior from an extension callback.
2. Host compatibility identity is not insertion evidence.
3. Self-produced digests are local integrity aids, not public authentication.
4. A test must run producer then observer sequentially. `Promise.all` cannot prove adjacency or ordering.
5. The runtime-record claim must stop at package-local return-value preparation before the source-level return statement; it cannot prove that execution reached or crossed that statement, callback return/promise settlement, or host consumption.
6. Pi session lifecycle events may reset one existing package runtime; reload/new/resume/fork must not be modeled as proof of host re-instantiation.
7. Existing semantic-preflight framing replacement and disabled-mode hints cannot be silently re-described as universal exact append or no modification.
8. Operational supersession must use AK's supported terminal `superseded` decision state; already-resolved post-ADR link reevaluations cannot be retroactively rewritten after an unblocked decision.

## Prospective evidence target

A future package task may prove:

- exact callback input string received by the package;
- exact contribution and append candidate produced locally;
- outer package wrapper observed the inner producer's resolved output;
- exact return object was constructed and one bounded diagnostic-slot assignment was the final package operation before the source-level return statement;
- a separate package harness observed ordinary callback resolution without promoting that fact into each runtime record;
- deterministic single-slot record construction, replacement/clearing, and failure behavior;
- default-off lifecycle and same-runtime grant invalidation without a second lineage state machine;
- non-append replacement behavior and disabled-mode hints remained outside the positive record.

No implementation is authorized by this note or Decision 89. Strict review and an accepted ADR are necessary but not sufficient: code or tests require a fresh owner-scoped package task, and installation, reload, dogfood, publication, activation, provider/model use, live acquisition, or production each require later owner authority.
