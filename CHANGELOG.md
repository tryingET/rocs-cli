---
summary: "Changelog for rocs-cli."
read_when:
  - "Preparing a release or reviewing user-visible changes."
---

# Changelog

## [Unreleased]

### Changed
- Hardened ROCS manifest layer parsing so each layer must declare exactly one of `path` or `ref`.
- Made bootstrap CI include wiring structural: `.gitlab-ci.yml` is now merged as YAML and invalid CI YAML fails closed instead of being text-spliced.
- Made fleet CI-gate auditing semantic: parsed CI YAML/script nodes are inspected, comment-only markers no longer count as contract evidence, and `ROCS_CI_PROFILE` must be bound in the same script context as the wrapper call.
- Switched GitLab ref-cache keys to an injective encoding while preserving reads from complete legacy cache entries.

### Fixed
- `scripts/vendor-to.sh` now rejects vendoring targets that overlap the source package tree, preventing recursive self-copy behavior.
- Authority receipt lock handling no longer triggers a `return`-in-`finally` warning during compilation.
