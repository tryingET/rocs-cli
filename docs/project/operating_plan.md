---
summary: "Active operating slices for the current rocs-cli tactical wave."
read_when:
  - "You need the next executable slices for the active tactical goal"
  - "You are checking whether live AK tasks still cover the active wave"
type: "reference"
---

# Operating plan

Active tactical goal: **Tactical Goal 2 — remove the remaining bootstrap/audit helper drift with shared, directly tested seams**.

## Operating slices

| Slice | AK coverage | Deliverable | Current state |
|---|---|---|---|
| OP1 | `#363` | Modularize bootstrap CI-include remediation into directly unit-tested Python helpers without losing current YAML/reference-tag behavior | Ready in AK |
| OP2 | `#364` | Extract shared FCOS gate contract helpers so bootstrap/audit stop carrying parallel drift-prone logic | Ready in AK |
| OP3 | `#363` + `#364` | Re-run repo validation plus fresh-bootstrap/rerun-on-existing convergence checks on the touched surfaces before closing the tactical goal | Acceptance slice attached to the active pair |

## HTN
- `G0`: keep downstream fleet helper surfaces deterministic and low-drift
  - strategic goal: eliminate contract drift in downstream fleet helper surfaces
    - tactical goal: remove remaining bootstrap/audit helper drift with shared, directly tested seams
      - operating slice OP1 -> AK `#363` -> helper extraction + unit tests
      - operating slice OP2 -> AK `#364` -> shared gate helper extraction + caller rewiring
      - operating slice OP3 -> AK `#363` + `#364` -> validation and convergence proof

## Materialization rule for this wave
- Use the existing authoritative AK tasks `#363` and `#364`.
- Do **not** create separate docs/operator tasks until this tactical goal is materially complete.
- Close stale prior-wave task `#329` instead of treating it as active backlog.
