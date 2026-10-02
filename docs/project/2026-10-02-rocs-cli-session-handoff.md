---
summary: "Handoff of 2026-10-02: AK 6134 (hollow-layer report) and AK 6329 (strict ref binding) shipped to main, unreleased; open operator decisions and next candidates."
read_when:
  - "You continue rocs-cli work after the 2026-10-01/02 Claude session."
  - "You consider cutting rocs-cli 0.4.6 or touching strict workspace ref binding."
type: "reference"
task_id: 6454
---

# rocs-cli session handoff (2026-10-02)

Continue in `~/ai-society/core/rocs-cli`. Read `AGENTS.md` and `next_session_prompt.md` first. AK is the
authority for tasks, decisions and evidence; this note only routes you to it.

## Continuation routing (AK 6454)

The sections below preserve the original session snapshot, not current status. The operator's
continuation answers are recorded in AK evidence **12314**: authorize 0.4.6 subject to the full gate,
keep exact submodule-pin binding, and reuse AK **6135** for its existing 43 template targets without
lifting its execution hold. The separate softwareco/ontology company-placeholder follow-up is AK
**6462**. Read AK 6454 for release execution evidence; authorization alone is not a release proof.

## Done (on origin/main, not released)

Both changes sit under `## [Unreleased]` in `CHANGELOG.md`. Consumers that run this checkout through
`scripts/rocs.sh` (for example replay-fabric, issue-tracker, holdingco/contrib, holdingco/infra) already
have them. Consumers with a pinned or bundled runtime, such as ontology-kernel, get them only from a
release.

- **AK 6134, commit `66c1578`, evidence 11681:** `rocs lint` carries a warn-only hollow-layer report
  (`src/rocs_cli/hollow.py`): HOLLOW001 lists whole-value `<...>` placeholders in layer YAML, including
  `system4d.yaml`. HOLLOW002 flags YAML that does not parse. HOLLOW010 flags a layer with no
  concepts, relations or bridge mappings. HOLLOW020 flags a `system4d.yaml` byte-identical to the
  project template. Only the repo's own path layers are checked. Findings warn under `dev` and fail
  under `--ruleset strict` or `--fail-on-warn`. `validate`, `build` and the receipts are unchanged.
- **AK 6329, commit `3cec078`, evidence 12076:** strict ref binding reads a checkout in place only when
  the layer's manifest and `src/` hold no ignored entries and no nested `.git`; otherwise it reads a
  snapshot of the exact tree. A ref with no committed layer `src/` fails closed (`not_found`). A
  submodule at the ontology path is followed to its pinned commit, and the binding records
  `submodule_commit`. With no clone at the workspace path, the error now says to check the repo out.

## Consequences to keep in view

- `holdingco/contrib` and `holdingco/infra` use `<repo:holdingco@main>`. In strict mode they now fail
  closed until decision 168 folds the ontology into holdingco (AK 6274, which depended on 6329). This
  is what the decision 168 ADR asks for. Loose mode still works.
- softwareco pins `ontology` as a submodule (`b2e42da`). Strict now binds its real tree (`b908603`), and
  the 9 consumers of `<repo:softwareco@main>` keep resolving. Following the pin, instead of failing
  closed until decision 157's fold, was the session's call and has not been confirmed by the operator.

## Waiting on the operator (AK 6454; ask, do not assume)

1. **Cut 0.4.6?** It would ship both changes to pinned consumers. Use
   `uv run --frozen python -m rocs_cli release plan|apply --version 0.4.6`, then run the gate. Do not
   release without the operator's go.
2. **Submodule pins:** keep following them (current behavior), or fail closed for softwareco too?
3. **Fleet follow-up:** about 43 main checkouts carry the byte-identical template `system4d.yaml` (for
   example core/prompt-vault and softwareco/infra/{issue-tracker,workstation,provisioning}), and
   softwareco/ontology's company `system4d.yaml` has 14 placeholders. Should each get an AK task in
   its own repo? Nothing is filed yet.

## Next candidates in this repo (`ak task list -r . -s pending`)

- **5988 (P2):** warn-only vocabulary drift checks (ADR-0008 §10), the sibling of 6134. Keep it a
  separate rule family; do not fold the hollow report into it.
- **5903 (P2):** keep the tool version and absolute paths out of the tracked `ontology/dist` files.
- **6273 (P2):** looks settled by the ontology-kernel-de session (the repo went public on 2026-09-30
  and CI clones it without the deploy key). Leave it to that owner.
- **Not addressed by 6134:** `fleet_detection.py:253` still counts any manifest with a locator as
  having an ontology.

## Boundaries

- Claim with your own harness id (pi: `session-$PI_SESSION_ID`); release the claim when you stop.
- Edit only this repo. The untracked `.ontology/` predates these sessions; leave it alone.
- Another session has a staged, uncommitted rename `system4d.yaml -> system4d.yaml.j2` in
  core/tpl-template-repo. Do not touch it.
- Acceptance gate: `./scripts/ci/full.sh` (353 tests at `3cec078`). Commit to main and push to `origin`,
  which is the only remote.
