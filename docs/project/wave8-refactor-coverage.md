---
summary: "Wave 8 behavior-preserving CLI decomposition coverage."
read_when:
  - "Reviewing Wave 8 RefactorOps evidence."
type: "reference"
---

# Wave 8 RefactorOps coverage

Wave 8 mechanically decomposes CLI handlers and tests. It adds no command, schema, dependency, output, exit, or filesystem behavior. The parser and global error boundary remain in `rocs_cli.cli`; `_schema_validation_result` is re-exported there while transaction persistence imports its dependency-neutral owner directly. All handler output resolves `rocs_cli.cli.console` at runtime, preserving caller replacement of that seam.

The baseline and post-split suites each discover 153 tests. Focused CLI test modules preserve all test method names and assertions; only intentional module qualification changes. Verification includes the full unit suite, CI gate, compilation, strict docs, CLI signature/contracts, and disposable module CLI execution.
