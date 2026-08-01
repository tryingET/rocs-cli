---
summary: "Immutable preregistration for Decision 98 B0 deterministic semantic-relevance evaluation."
read_when:
  - "Executing or reviewing Decision 98 B0."
type: "experiment_preregistration"
status: "preregistered"
decision_id: 98
---
# Decision 98 B0 semantic-relevance preregistration

## Question and authority

B0 asks whether ROCS `rocs-lexical-v0` retrieves semantically relevant ontology concepts before any provider/model benefit claim is considered. ROCS owns execution and analysis. This evaluation uses no provider, model, DSPx authority, network, tool call, Pi installation, or normal Pi settings.

A B0 pass supports only deterministic retrieval relevance for this frozen corpus and gold set. It does not prove production generalization, prompt contribution survival, provider transmission, model input, or behavioral benefit. B1/B2 remain separate work.

## Frozen coordinates

- Runtime source: clean detached commit `c0cfb1297ba78f4ca1fe53f488bcb15ad79b7843` retained at exact isolated root `/data/agnt/tmp/rocs-cli-decision98-b0-runtime-c0cfb129`.
- Interpreter: the runtime checkout's `.venv/bin/python`, CPython `3.12.12`, SHA-256 `20341168c41f91f4328c68d1f1a8d563f5734d515e617ff80a8dcfce323218b7`; evaluator execution from any other interpreter fails closed.
- Base Python tree: `/home/tryinget/.local/share/uv/python/cpython-3.12.12-linux-x86_64-gnu`; 5,386-entry inventory digest `6f1b98a4f02813c21be383ac910dbe6a3acbe9cdc585382f3835a8ca3868c96a`.
- Native loader/runtime: exact SHA-256 values for the interpreter's resolved `libpthread`, `libdl`, `libutil`, `librt`, `libm`, `libc`, and `ld-linux` files are frozen in the machine-readable lock and rechecked before and after observation.
- Runtime lock: `uv.lock` SHA-256 `bdde23353d71df100b63fadcb9b35ddca54add02412276ee3395b11af33bda6b`.
- Virtual environment: `.venv/pyvenv.cfg` SHA-256 `b88c80de60f13be36bf53c717188e1dfa926730b9ef1102c3e169a3d1541c565`.
- Frozen dependencies: PyYAML `6.0.3`, rich `14.2.0`, markdown-it-py `4.0.0`, mdurl `0.1.2`, Pygments `2.19.2`.
- Complete runtime working-tree inventory: 1,053 non-`.git` entries; digest `21b12397aaaacf3d3a748242185d1f83b9728e960cee30f11940abf65ce04e9c`. This includes ignored `.venv` content, symlinks, modes, mtimes, sizes, and file digests.
- Algorithm/profile: `rocs-lexical-v0` / `review`.
- Index cache: disabled through request CLI and `ROCS_INDEX_CACHE=0`.
- Tool identity: `development_runtime`; manifest digest `sha256:21b12397aaaacf3d3a748242185d1f83b9728e960cee30f11940abf65ce04e9c`, derived from and reverified against the complete B0 runtime working-tree inventory above. This is B0 runtime identity, not the earlier R1b manifest.
- Dataset: `tests/fixtures/decision98-b0/prompts.json`; SHA-256 `e85b7bbebbdc355c4f33a3fa2b66b58b8c045c5d1a836fe05c1f96a0e11413a5`.
- Corpus root: `tests/fixtures/decision98-b0/corpus`; path-and-byte tree SHA-256 `021278da7cb1fe4ecb86857ae2510c934fe53172c952a7b1c05885c4f6d88d40`.
- Evaluator: `scripts/decision98_b0_evaluate.py`; SHA-256 `deb9b9b7c7ff06e0ff2b824773d165cde73c284dff72304638473fea6892c34f`.
- Evaluator support: `scripts/decision98_b0_support.py`; SHA-256 `9211015bb0c173377f4a91f3804c0d14c5d9a1be05ce082dc32dc98f0c87ebf8`.
- Machine-readable lock: `tests/fixtures/decision98-b0/preregistration-lock.json`. Its SHA-256 is recorded by the two preregistration reviews and AK evidence after the final commit; execution must supply that accepted digest through `--lock-sha256`.
- Output: exactly `docs/project/decision98-b0-semantic-relevance-report.json`; no output-path argument is accepted and the path must not exist before execution.

The machine-readable lock binds the evaluator, this document, dataset, corpus, runtime, environment, limits, floors, and exact output path. The evaluator verifies its own bytes and this document against the lock. The execution command additionally binds the accepted detached preregistration commit and accepted lock digest, avoiding a circular self-hash inside the commit.

Any coordinate, digest, checkout, environment, dependency, inventory, or output mismatch fails closed. The accepted preregistration commit is immutable; corrections require a new preregistration revision and task before execution.

## Dataset and annotation

The corpus contains ten synthetic but contract-valid concept documents representing Decision-98-adjacent semantic boundaries. The dataset contains 50 prompts, balanced as ten per named stratum:

1. `exact_terminology`;
2. `paraphrase_synonym`;
3. `multi_concept`;
4. `ambiguity_distractor`;
5. `null_out_of_domain`.

Forty prompts are applicable and ten are null. Every concept appears in exact/paraphrase coverage; multi-concept prompts have two complete relevant IDs.

Gold labels were assigned without retrieval execution by two independent annotators. Exact, multi-concept, and ambiguity prompts retain:

- annotator A: `dispatch-1785590736088`;
- annotator B: `dispatch-1785590736088-1`.

After preregistration review strengthened paraphrases and lexical near-miss nulls, all revised paraphrase and null prompts were independently annotated by:

- annotator A: `dispatch-1785591508417`;
- annotator B: `dispatch-1785591508418`.

Across the final 50 prompts, the annotators agree on 49/50 complete sets. A09 was adjudicated by `dispatch-1785590829110` under the frozen policy: include direct answers plus concepts providing an essential evidentiary qualification. The dataset preserves both annotations and the adjudicated gold.

## Invocation and mutation contract

The one allowed execution command has this shape, with the exact accepted preregistration commit, lock digest, and isolated runtime path substituted by the execution task:

```bash
env -i \
  TMPDIR=/home/tryinget/.local/state/pi-quests/tmp \
  HOME=/home/tryinget/.local/state/pi-quests/tmp \
  PATH=/usr/bin:/bin LANG=C.UTF-8 LC_ALL=C.UTF-8 \
  /data/agnt/tmp/rocs-cli-decision98-b0-runtime-c0cfb129/.venv/bin/python \
  -I -S -B scripts/decision98_b0_evaluate.py \
  --runtime-root /data/agnt/tmp/rocs-cli-decision98-b0-runtime-c0cfb129 \
  --prereg-commit <accepted-40-hex-preregistration-commit> \
  --lock-sha256 <accepted-lock-sha256>
```

Before discovery, the evaluator requires:

- detached, clean source and runtime checkouts at the supplied preregistration commit and frozen runtime commit;
- the exact evaluator, support module, preregistration, dataset, corpus, lock, `uv.lock`, interpreter, base Python tree, native libraries, `pyvenv.cfg`, and dependency identities;
- isolated `-I -S -B` startup, which ignores inherited Python configuration, disables `site`/`sitecustomize`, and prevents bytecode mutation;
- an absent reserved report path and absent fixed private-home path;
- a private mode-0700 `TMPDIR` isolated from both checkouts.

For each prompt, the evaluator launches a fresh exact-runtime Python process twice with a closed environment, request schema, limits, no env file, and no index cache. It independently verifies result schema, request correlation, algorithm, effective limits, tool identity and digest, result digest, candidate IDs/ranks/integer scores, and classification before scoring. The first is the logical-cold observation; the immediate repeat is logical-warm. OS page caches are not cleared or claimed. Each invocation has a 2.0-second timeout.

The only transient mutation is `${TMPDIR}/decision98-b0-private-home`, created mode 0700 and removed on all ordinary evaluator exits through `finally`; an abrupt process kill is indeterminate and requires the execution controller's mandatory rollback check. The only retained mutation is the exact report path. The evaluator inventories all source, corpus, and runtime working-tree entries, including directories, files, symlinks, modes, mtimes, sizes, and file digests, while excluding owner-managed `.git` metadata. The runtime inventory is also compared with the preregistered digest, so ignored virtual-environment content is not merely baselined. The source checkout must contain no ignored content. The evaluator rechecks inventories, clean detached checkouts, locked sources, runtime, environment, dependencies, and private-home absence after observation and before report creation.

The execution controller must provide an exclusive no-concurrent-mutation window for both checkouts and the corpus. The inventories detect accidental or persistent drift; they are not claimed as a security boundary against a malicious same-UID process that temporarily replaces and byte-for-byte restores files. Any observed concurrency makes the run indeterminate.

The report is created only after all operational checks pass, using an exclusive atomic create at its existing parent; parent directories are never created by the evaluator. A preflight or racing collision fails closed. A timeout is censored at 2000 ms and counts as a failed timeout gate; protocol, exit, parse, mutation, cleanup, or identity failures abort without a report. No prompt is excluded after execution starts.

## Metrics

For applicable prompts:

- recall@3 uses the complete adjudicated gold set;
- reciprocal rank uses the first relevant returned concept;
- macro recall@3 is computed independently for each applicable stratum.

For null prompts, null rejection requires an empty candidate list. Deterministic repeat requires byte-identical cold/warm JSON results. Latency uses nearest-rank p95 across all 50 prompts for each pass.

## Numerical floors

All gates must pass:

| Gate | Floor |
|---|---:|
| Mean applicable recall@3 | `>= 0.90` |
| Mean reciprocal rank | `>= 0.85` |
| Each applicable stratum mean recall@3 | `>= 0.80` |
| Null rejection rate | `>= 0.90` |
| Byte-identical repeat rate | `= 1.00` |
| Timeout rate | `= 0.00` |
| Logical-cold p95 | `<= 750 ms` |
| Logical-warm p95 | `<= 500 ms` |

The report's top-level `passed` is the conjunction of all gates. No averaging may hide a failed stratum or operational gate.

## Decision rule and stop conditions

- **Pass:** record the immutable report, exact command, identities, metrics, and independent review in AK. B0 then supports Decision-98 completion/KES work but not B1/B2 claims.
- **Fail:** retain the report and stop; do not tune corpus, prompts, gold, limits, or floors in the same task. Any revised hypothesis requires a new preregistration.
- **Indeterminate:** whole-evaluator/controller timeout, source/digest drift, output collision, corpus/runtime/source mutation, runtime dirt, cleanup failure, malformed output, or concurrent mutation stops all forward work. Do not retry mechanically. A per-invocation 2.0-second timeout is instead retained as a failed report row and necessarily fails the timeout gate.

No B1 provider/model task may be opened from B0 unless every floor passes and independent review accepts the report.
