---
summary: "Resolved brownfield readability exceptions after the Wave 8 RefactorOps decomposition."
read_when:
  - "Reviewing the Wave 8 CLI decomposition."
type: "reference"
---

# Code-size exceptions

Wave 8 closed both prior exceptions without changing CLI behavior. `src/rocs_cli/cli.py` now retains parser assembly, `main`, compatibility re-exports, and the shared console seam below 500 LOC. Focused platform/membrane, ontology lifecycle, ontology utility, support, and validation modules are each below 500 LOC.

The former `tests/test_cli.py` compatibility oracle is mechanically split by concern. Shared fixtures live in `tests/_cli_support.py`; every discovered test remains present in focused files below 1000 LOC.

One active bounded exception exists: `src/rocs_cli/source_contract.py` is 526 LOC / under 26 KB. Decision 110 requires one shared parser/dispatcher rather than behaviorally drifting admission modules, and the file keeps byte/YAML/schema/path/corpus-reference phases together so their precedence remains reviewable. The focused test remains below 1000 LOC. Split only if a later contract revision can preserve one dispatch and one precedence implementation without duplication.
