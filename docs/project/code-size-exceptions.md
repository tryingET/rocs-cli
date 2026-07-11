---
summary: "Brownfield readability exceptions for the ROCS CLI parser and legacy monolithic CLI test suite."
read_when:
  - "Adding another command family to src/rocs_cli/cli.py."
  - "Adding tests to tests/test_cli.py."
type: "reference"
---

# Code-size exceptions

The Wave 0–4 implementation split new fleet and transaction logic into modules below the workspace 500-LOC code budget. Two pre-existing brownfield aggregation surfaces remain over their readability budgets:

| Path | Current LOC | Owner | Reason retained for this wave | Reopen trigger |
|---|---:|---|---|---|
| `src/rocs_cli/cli.py` | 1473 | `core/rocs-cli` | It remains the established argparse assembly and error-normalization boundary. Splitting parser registration while simultaneously replacing every script and adding four governed protocol families would have mixed a broad mechanical refactor into an authority-sensitive feature migration. | Before adding another top-level command family, extract command-family registration/handlers into importable modules while preserving the exact `rocs contracts` ↔ parser test. |
| `tests/test_cli.py` | 1326 | `core/rocs-cli` | Existing CLI behavior tests remain a shared compatibility oracle; Wave tests were otherwise placed in dedicated files. | Before adding another CLI test class, extract existing concern groups and shared fixtures under RefactorOps, preserving full discovery behavior. |

These are readability exceptions only. They do not relax deterministic output, safety, coverage, or file-size rules for new modules. Newly added `fleet*`, `transaction*`, intelligence, and constitution modules remain below 500 LOC.
