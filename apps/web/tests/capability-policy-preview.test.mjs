import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const metadataUrl = new URL("../data/capability-policy-preview.json", import.meta.url);
const componentUrl = new URL("../components/capability-policy-preview.tsx", import.meta.url);
const shellUrl = new URL("../components/sagent-shell.tsx", import.meta.url);
const metadata = JSON.parse(await readFile(metadataUrl, "utf8"));
const componentSource = await readFile(componentUrl, "utf8");
const shellSource = await readFile(shellUrl, "utf8");

test("capability policy preview shows all 12 capabilities in metadata", () => {
  assert.equal(metadata.capabilities.length, 12);
  const names = metadata.capabilities.map((c) => c.name);
  assert.deepEqual(names, [
    "read_workspace",
    "preview_file_edits",
    "apply_single_file_edit",
    "apply_multi_file_edit",
    "run_tests",
    "run_shell_command",
    "git_status",
    "git_commit",
    "git_push",
    "change_dependencies",
    "use_local_model",
    "use_cloud_model",
  ]);
});

test("capability policy preview shows correct default modes in metadata", () => {
  const find = (name) => metadata.capabilities.find((c) => c.name === name);
  assert.equal(find("preview_file_edits").mode, "allowed");
  assert.equal(find("git_status").mode, "allowed");
  assert.equal(find("apply_single_file_edit").mode, "approval_required");
  assert.equal(find("use_cloud_model").mode, "disabled");
  assert.equal(find("read_workspace").mode, "preview_only");
});

test("capability policy preview has safety flags false in metadata", () => {
  assert.equal(metadata.shellExecuted, false);
  assert.equal(metadata.gitExecuted, false);
  assert.equal(metadata.networkUsed, false);
  assert.equal(metadata.cloudUsed, false);
  assert.equal(metadata.modelCalled, false);
  assert.equal(metadata.runtimeActivated, false);
});

test("capability policy preview component is integrated into shell", () => {
  assert.match(shellSource, /<CapabilityPolicyPreview apiUrl=\{API_URL\} \/>/);
});

test("capability policy preview component fetches only from /capabilities/preview", () => {
  const fetches = componentSource.match(/\bfetch\(/g);
  assert.equal(fetches?.length, 1);
  assert.match(componentSource, /fetch\(`\$\{apiUrl\}\/capabilities\/preview`/);
  assert.doesNotMatch(componentSource, /https?:\/\/|wss?:\/\//);
  assert.doesNotMatch(componentSource, /\b(XMLHttpRequest|WebSocket|EventSource)\b/);
});

test("capability policy preview has no toggle, enable, or run buttons", () => {
  assert.doesNotMatch(componentSource, /<\s*input/);
  assert.doesNotMatch(componentSource, /<\s*select/);
  assert.doesNotMatch(componentSource, /<\s*textarea/);
  assert.doesNotMatch(componentSource, /onSubmit|action=/);
  assert.doesNotMatch(componentSource, /toggle|run\s|start\s/i);
  assert.doesNotMatch(componentSource, /onClick|onSubmit|action=/);
});

test("capability policy preview has no shell, git, commit, push, merge buttons", () => {
  assert.doesNotMatch(componentSource, /<button.*Shell|<button.*Git.*run|<button.*Commit|<button.*Push|<button.*Merge/i);
});

test("capability policy preview has no cloud, deepseek, remote_http controls", () => {
  assert.doesNotMatch(componentSource, /Cloud.*(run|execute|start)/i);
  assert.doesNotMatch(componentSource, /DeepSeek|deepseek/i);
  assert.doesNotMatch(componentSource, /remote_http|remoteHttp/i);
});

test("capability policy preview has no API key, endpoint, or secret fields", () => {
  assert.doesNotMatch(componentSource, /api_key|apiKey|endpoint|api-key|secret|token/);
});

test("capability policy preview has no model_response input", () => {
  assert.doesNotMatch(componentSource, /model_response|modelResponse/);
});

test("capability policy preview shows readonly badge", () => {
  assert.match(componentSource, /Read-only preview/);
  assert.match(componentSource, /read-only/);
});

test("capability policy preview shows no runtime actions message", () => {
  assert.match(componentSource, /No runtime actions/);
  assert.match(componentSource, /no shell, git, network, cloud, or model/);
});

test("capability policy preview falls back to static offline metadata", () => {
  assert.match(componentSource, /fallbackEntries/);
  assert.match(componentSource, /Statische Offline-Fallback-Vorschau aktiv/);
});

test("capability policy preview has no localStorage, sessionStorage, or IndexedDB", () => {
  assert.doesNotMatch(componentSource, /localStorage|sessionStorage|IndexedDB/);
});

test("capability policy preview metadata contains no endpoints or secrets", () => {
  const forbidden = ["api_key", "apiKey", "endpoint", "secret", "token", "url", "host", "port"];
  const text = JSON.stringify(metadata);
  for (const term of forbidden) {
    assert.equal(text.includes(term), false, `metadata should not contain ${term}`);
  }
});
