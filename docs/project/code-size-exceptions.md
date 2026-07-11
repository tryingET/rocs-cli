---
summary: "Resolved brownfield readability exceptions after the Wave 8 RefactorOps decomposition."
read_when:
  - "Reviewing the Wave 8 CLI decomposition."
type: "reference"
---

# Code-size exceptions

Wave 8 closed both prior exceptions without changing CLI behavior. `src/rocs_cli/cli.py` now retains parser assembly, `main`, compatibility re-exports, and the shared console seam below 500 LOC. Focused platform/membrane, ontology lifecycle, ontology utility, support, and validation modules are each below 500 LOC.

The former `tests/test_cli.py` compatibility oracle is mechanically split by concern. Shared fixtures live in `tests/_cli_support.py`; every discovered test remains present in focused files below 1000 LOC. No active code-size exceptions remain.
