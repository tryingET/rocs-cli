---
summary: "Standalone consumer acceptance fixture."
read_when:
  - "When maintaining standalone consumer acceptance tests."
type: "reference"
---

# Standalone acceptance fixture

`tests/test_standalone_consumer.py` copies this directory, publishes the pinned
self-contained artifact into it, and runs the installed artifact with a sanitized
PATH and no sibling workspace. This fixture intentionally contains no workspace
locator or compatibility script.
