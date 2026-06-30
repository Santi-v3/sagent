import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const metadataUrl = new URL("../data/benchmark-status.json", import.meta.url);
const componentUrl = new URL("../components/benchmark-status.tsx", import.meta.url);
const metadata = JSON.parse(await readFile(metadataUrl, "utf8"));
const componentSource = await readFile(componentUrl, "utf8");

test("benchmark metadata exposes only the two approved loopback providers", () => {
  assert.deepEqual(metadata.providers, [
    { name: "LM Studio", endpoint: "127.0.0.1:1234" },
    { name: "Ollama", endpoint: "127.0.0.1:11434" },
  ]);
  assert.equal(JSON.stringify(metadata).includes("remote_http"), false);
  assert.equal(JSON.stringify(metadata).includes("https://"), false);
});

test("benchmark metadata uses the fixed synthetic task catalog", () => {
  assert.deepEqual(
    metadata.tasks.map((task) => task.taskId),
    ["safe-refactor-plan", "deterministic-test-cases", "cancellation-probe"],
  );
});

test("example command remains confirmation-required and cannot run a benchmark", () => {
  assert.equal(metadata.confirmationState, "confirmation_required");
  assert.equal(metadata.safeCommand.includes("--confirmed"), false);
  assert.match(metadata.safeCommand, /sagent_agent_api\.benchmark_cli$/);
});

test("UI contract contains no result text fields or automatic execution path", () => {
  const forbiddenKeys = new Set(["prompt", "response", "modelText", "resultText"]);
  const collectKeys = (value) => {
    if (Array.isArray(value)) return value.flatMap(collectKeys);
    if (value && typeof value === "object") {
      return Object.entries(value).flatMap(([key, child]) => [key, ...collectKeys(child)]);
    }
    return [];
  };

  assert.equal(collectKeys(metadata).some((key) => forbiddenKeys.has(key)), false);
  assert.match(componentSource, /<button[\s\S]*?disabled[\s\S]*?>[\s\S]*?Benchmark starten/);
  assert.doesNotMatch(componentSource, /\b(fetch|XMLHttpRequest|WebSocket)\b/);
});
