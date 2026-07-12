#!/usr/bin/env node
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { mkdir, mkdtemp, readFile, readdir, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { pathToFileURL } from "node:url";

function parseArgs(argv) {
  const values = new Map();
  for (let index = 0; index < argv.length; index += 2) {
    const key = argv[index];
    const value = argv[index + 1];
    if (!key?.startsWith("--") || !value) throw new Error("expected --name value arguments");
    values.set(key.slice(2), path.resolve(value));
  }
  for (const required of ["runtime-root", "package-root", "output"])
    if (!values.has(required)) throw new Error(`missing --${required}`);
  return Object.fromEntries(values);
}

const args = parseArgs(process.argv.slice(2));
const moduleAt = (relative) => import(pathToFileURL(path.join(args["package-root"], relative)).href);
const [
  { createSemanticPreflightRuntime },
  { inspectOntology },
  { createFilesystemPort },
  prepared,
  runner,
] = await Promise.all([
  moduleAt("src/semantic/preflight-runtime.ts"),
  moduleAt("src/core/inspect.ts"),
  moduleAt("src/adapters/filesystem.ts"),
  moduleAt("src/semantic/prepared-runtime.ts"),
  moduleAt("src/semantic/runner.ts"),
]);

assert.equal(process.env.PYTHONPATH, undefined, "proof environment must not expose PYTHONPATH");
assert.equal(process.env.PI_ONTOLOGY_ROCS_BIN, undefined, "proof environment must not expose runner overrides");
assert.equal(process.env.ROCS_BIN, undefined, "proof environment must not expose runner overrides");

const location = Object.freeze({
  root: args["runtime-root"],
  manifestPath: path.join(args["runtime-root"], "manifest.json"),
  dependencyLockPath: path.join(args["runtime-root"], "uv.lock"),
  entrypointPath: path.join(args["runtime-root"], "entrypoint.txt"),
});
const manifest = await prepared.verifyPreparedRuntime(location);
const sandbox = await mkdtemp(path.join(tmpdir(), "decision52-i7-"));
const repo = path.join(sandbox, "consumer");
const ontology = path.join(repo, "ontology");
const conceptPath = path.join(ontology, "src", "reference", "concepts", "core.Agent.md");
await mkdir(path.dirname(conceptPath), { recursive: true });
await writeFile(
  path.join(ontology, "manifest.yaml"),
  [
    "rocs:",
    "  layers:",
    "    - name: core",
    "      path: ontology/src",
    "  profiles:",
    "    default: review",
    "    review:",
    "      include_layers: [core]",
    "",
  ].join("\n"),
);
await writeFile(
  conceptPath,
  [
    "---",
    "ont:",
    "  id: core.Agent",
    "  type: concept",
    "  labels: [Agent]",
    "  description: Agent authority.",
    "  examples: [agent]",
    "  anti_examples: []",
    "---",
    "# Agent",
    "",
    "Untrusted semantic prose for explicit pack only.",
    "",
  ].join("\n"),
);

async function snapshot(root) {
  const output = {};
  async function walk(current) {
    for (const entry of (await readdir(current, { withFileTypes: true })).sort((a, b) => a.name.localeCompare(b.name))) {
      const absolute = path.join(current, entry.name);
      if (entry.isDirectory()) await walk(absolute);
      else if (entry.isFile()) {
        const bytes = await readFile(absolute);
        output[path.relative(root, absolute)] = `sha256:${createHash("sha256").update(bytes).digest("hex")}`;
      }
    }
  }
  await walk(root);
  return output;
}

const before = await snapshot(repo);
const target = {
  scope: "repo",
  repoPath: repo,
  repoKind: "repo",
  workspaceRoot: sandbox,
  workspaceRefMode: "strict",
  reasons: ["isolated decision-52 proof fixture"],
  externalToCurrentRepo: false,
};
const workspace = {
  async detect(cwd) {
    return {
      cwd,
      workspaceRoot: sandbox,
      workspaceRefMode: "strict",
      currentRepoPath: repo,
      currentRepoDetectedFromGit: true,
      currentRepoHasOntology: true,
      currentRepoKind: "repo",
      currentCompany: "softwareco",
    };
  },
  async resolveTarget() {
    return target;
  },
};
const never = async () => {
  throw new Error("legacy ROCS path must not run during the verified vertical slice");
};
const legacyRocs = { summary: never, validate: never, build: never, pack: never };
let proofDiscoveries = 0;
const runtime = createSemanticPreflightRuntime({
  workspace,
  legacyRocs,
  async prepare() {
    return { location, manifest, cacheRoot: path.dirname(args["runtime-root"]), published: false };
  },
  async activate(preparedRuntime) {
    const descriptor = await runner.createDevelopmentRocsRunnerDescriptor(preparedRuntime.location);
    const port = await runner.createVerifiedDevelopmentRocsPort(descriptor);
    const discover = port.discover.bind(port);
    return {
      descriptor,
      port: Object.freeze({
        ...port,
        async discover(...parameters) {
          proofDiscoveries++;
          return discover(...parameters);
        },
      }),
    };
  },
});
const commands = new Map();
const events = new Map();
runtime.register({
  registerCommand(name, definition) {
    commands.set(name, definition.handler);
  },
  on(name, handler) {
    const handlers = events.get(name) ?? [];
    handlers.push(handler);
    events.set(name, handlers);
  },
});
const notifications = [];
const statuses = [];
const hostCapabilities = Object.freeze({
  host_package: "@earendil-works/pi-coding-agent",
  host_version: "0.74.0",
  extension_api_version: "1.0.0",
  capabilities: Object.freeze([
    "prompt.system.chain.v1",
    "session.lifecycle.reason.v1",
    "ui.mode.v1",
    "ui.confirm.timeout.v1",
    "session.shutdown.v1",
  ]),
});
const ctx = {
  cwd: repo,
  mode: "tui",
  hasUI: true,
  hostCapabilities,
  isIdle: () => true,
  ui: {
    async confirm(_title, _message, options) {
      assert.deepEqual(options, { timeout: 30_000 });
      return true;
    },
    notify(message, level) {
      notifications.push({ message, level });
    },
    setStatus(_id, value) {
      statuses.push(value ?? "");
    },
  },
};
const emit = async (name, event = {}) =>
  Promise.all((events.get(name) ?? []).map((handler) => handler(event, ctx)));

await emit("session_start", { reason: "startup" });
await commands.get("ontology-preflight")("enable-development", ctx);
assert.equal(runtime.snapshot().grant, true, "explicit TUI confirmation must enable only this generation");
const [preflightRaw] = await emit("before_agent_start", {
  prompt: "agent authority",
  systemPrompt: "ISOLATED_BASE_PROMPT",
});
assert.ok(preflightRaw && typeof preflightRaw.systemPrompt === "string");
const systemPrompt = preflightRaw.systemPrompt;
assert.equal(proofDiscoveries, 1, "one prompt run must perform exactly one discovery");
if (!/outcome=matched/.test(systemPrompt))
  throw new Error(`preflight did not match: ${JSON.stringify({ notifications, statuses, systemPrompt })}`);
assert.match(systemPrompt, /"ont_id":"core.Agent"/);
assert.doesNotMatch(systemPrompt, /Untrusted semantic prose|Agent authority\./);
assert.equal(runtime.snapshot().promptBindings, 1);

const access = runtime.inspectAccess(ctx, { kind: "pack", ontId: "core.Agent" });
assert.equal(access.bound, true, "pack must use the prompt-local exact-ID binding");
const pack = await inspectOntology(
  { kind: "pack", ontId: "core.Agent" },
  access.runtime,
  { files: createFilesystemPort(), rocs: access.rocs, workspace },
);
assert.equal(access.isCurrent(), true);
assert.match(pack.pack?.text ?? "", /Untrusted semantic prose for explicit pack only/);
runtime.noteInspect(ctx, { kind: "pack", ontId: "core.Agent" }, true);
const after = await snapshot(repo);
assert.deepEqual(after, before, "discovery and bound pack must not mutate the consumer tree");
assert.equal(await readdir(ontology).then((names) => names.includes("dist")), false);

const candidateLine = systemPrompt.split("\n").find((line) => line.startsWith("candidates="));
const receipt = {
  schema: "decision52-semantic-preflight-vertical-proof.v0",
  development_only: true,
  adopted_runtime: false,
  automatic_modes: ["tui"],
  sanitized_environment: {
    inherited_pythonpath: false,
    inherited_runner_override: false,
    shell_invoked: false,
    network_required: false,
    sibling_runner_discovery: false,
  },
  implementation: {
    rocs_cli: "ddbfa70b29c5805c859d32abc3265278cc6ce0d2",
    pi_host: "5be4473cc156eb03d0069cc6770f1b95ea9eac97",
    pi_ontology_workflows: "5719669cf4476f5f33cc9ac082b2de3af6940dd2",
  },
  runtime: {
    rocs_commit: manifest.rocs_commit,
    manifest_digest: manifest.manifest_digest,
    file_count: manifest.files.length,
  },
  preflight: {
    outcome: "matched",
    prompt_block_digest: `sha256:${createHash("sha256").update(systemPrompt).digest("hex")}`,
    candidates_digest: `sha256:${createHash("sha256").update(candidateLine ?? "").digest("hex")}`,
    candidate_count: 1,
    ontology_prose_in_system_role: false,
  },
  pack: {
    bound: true,
    ont_id: "core.Agent",
    text_digest: `sha256:${createHash("sha256").update(pack.pack?.text ?? "").digest("hex")}`,
  },
  consumer_tree_unchanged: true,
  managed_dist_absent: true,
  lifecycle_status_tail: statuses.slice(-2),
  notification_levels: notifications.map((item) => item.level ?? "info"),
};
await mkdir(path.dirname(args.output), { recursive: true });
await writeFile(args.output, `${JSON.stringify(receipt, null, 2)}\n`);
await emit("session_shutdown", { reason: "quit" });
assert.equal(runtime.snapshot().grant, false);
await rm(sandbox, { recursive: true, force: true });
console.log(JSON.stringify(receipt));
