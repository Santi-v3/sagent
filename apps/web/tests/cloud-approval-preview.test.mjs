import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const metadataUrl = new URL("../data/cloud-approval-preview.json", import.meta.url);
const componentUrl = new URL("../components/cloud-approval-preview.tsx", import.meta.url);
const shellUrl = new URL("../components/sagent-shell.tsx", import.meta.url);
const metadata = JSON.parse(await readFile(metadataUrl, "utf8"));
const componentSource = await readFile(componentUrl, "utf8");
const shellSource = await readFile(shellUrl, "utf8");

test("cloud approval preview shows provider and metadata", () => {
  assert.equal(metadata.providerId, "deepseek-cloud");
  assert.equal(metadata.purpose, "coding");
  assert.equal(metadata.scope, "one_run_only");
  assert.equal(metadata.cloudExecution, "No");
  assert.equal(metadata.previewType, "Local metadata only");
});

test("cloud approval preview shows denied defaults", () => {
  assert.equal(metadata.approvalStatus, "no_decision");
  assert.equal(metadata.isValid, false);
  assert.equal(metadata.isApproved, false);
  assert.equal(metadata.explicitConfirmed, false);
});

test("cloud approval preview shows secrets excluded and repo dump blocked", () => {
  assert.equal(metadata.secretsExcluded, true);
  assert.equal(metadata.fullRepoDumpBlocked, true);
});

test("cloud approval preview component has no cloud execution button", () => {
  assert.doesNotMatch(componentSource, /Cloud ausführen/);
  assert.doesNotMatch(componentSource, /Cloud starten/);
  assert.doesNotMatch(componentSource, /onClick|onSubmit|action=/);
});

test("cloud approval preview component has no API key or endpoint fields", () => {
  const forbidden = ["api_key", "apiKey", "endpoint", "api-key", "secret", "token"];
  for (const term of forbidden) {
    assert.equal(metadata[term], undefined, `metadata should not contain ${term}`);
  }
});

test("cloud approval preview calls only the local preview route", () => {
  assert.equal(componentSource.match(/\bfetch\(/g)?.length, 1);
  assert.match(componentSource, /fetch\(`\$\{apiUrl\}\/cloud\/approval-preview`/);
  assert.match(componentSource, /method: "POST"/);
  assert.match(shellSource, /<CloudApprovalPreview apiUrl=\{API_URL\} \/>/);
  assert.doesNotMatch(componentSource, /https?:\/\/|wss?:\/\//);
  assert.doesNotMatch(componentSource, /\b(XMLHttpRequest|WebSocket|EventSource)\b/);
});

test("cloud approval preview sends denied metadata only", () => {
  assert.match(componentSource, /provider_id: previewData\.providerId/);
  assert.match(componentSource, /purpose: previewData\.purpose/);
  assert.match(componentSource, /approved: false/);
  assert.match(componentSource, /explicit_confirmed: false/);
  assert.match(componentSource, /repo_context_included: false/);
  assert.match(componentSource, /diffs_included: false/);
  assert.match(componentSource, /files_included: false/);
  assert.match(componentSource, /bytes_estimate: 0/);
  assert.doesNotMatch(
    componentSource,
    /\b(prompt|file_content|diff_content|api_key|token|endpoint|model_response)\b/i,
  );
});

test("cloud approval preview falls back to static offline metadata", () => {
  assert.match(componentSource, /useState\(previewData\)/);
  assert.match(componentSource, /setPreview\(previewData\)/);
  assert.match(componentSource, /Statische Offline-Fallback-Vorschau aktiv/);
});

test("cloud approval preview component contains no DeepSeek execution", () => {
  assert.doesNotMatch(componentSource, /deepseek.*(run|call|execute|complete|start)/i);
  assert.doesNotMatch(componentSource, /model.*(run|call|execute|start)/i);
  assert.doesNotMatch(componentSource, /remote_http/);
  assert.doesNotMatch(componentSource, /node:fs|readFile|writeFile/);
});

test("cloud approval preview component contains no model input fields", () => {
  assert.doesNotMatch(componentSource, /prompt|modelSelect|model.*input/i);
});

test("cloud approval preview component has readonly badge", () => {
  assert.match(componentSource, /Preview only/);
  assert.match(componentSource, /read-only/);
});
