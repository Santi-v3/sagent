import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const metadataUrl = new URL("../data/cloud-approval-preview.json", import.meta.url);
const componentUrl = new URL("../components/cloud-approval-preview.tsx", import.meta.url);
const metadata = JSON.parse(await readFile(metadataUrl, "utf8"));
const componentSource = await readFile(componentUrl, "utf8");

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

test("cloud approval preview component uses no direct network calls", () => {
  assert.doesNotMatch(componentSource, /\b(fetch|XMLHttpRequest|WebSocket|EventSource)\b/);
});

test("cloud approval preview component contains no DeepSeek execution", () => {
  assert.doesNotMatch(componentSource, /deepseek.*(run|call|execute|complete|start)/i);
  assert.doesNotMatch(componentSource, /model.*(run|call|execute|start)/i);
});

test("cloud approval preview component contains no model input fields", () => {
  assert.doesNotMatch(componentSource, /prompt|modelSelect|model.*input/i);
});

test("cloud approval preview component has readonly badge", () => {
  assert.match(componentSource, /Preview only/);
  assert.match(componentSource, /read-only/);
});
