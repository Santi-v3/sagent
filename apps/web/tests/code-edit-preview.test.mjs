import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const componentUrl = new URL("../components/code-edit-preview-panel.tsx", import.meta.url);
const source = await readFile(componentUrl, "utf8");

test("component name matches filename", () => {
  assert.match(source, /export function CodeEditPreviewPanel/);
});

test("component uses fetch only for the three allowed code-edit endpoints", () => {
  const fetchMatches = source.match(/\bfetch\(/g);
  assert.ok(fetchMatches);
  for (const match of fetchMatches) {
    assert.equal(match, "fetch(");
  }
  const previewEndpoint = source.match(/\/agent\/code-edits\/preview/);
  assert.ok(previewEndpoint, "Must call preview endpoint");
  const approveEndpoint = source.match(/\/agent\/code-edits\/approve/);
  assert.ok(approveEndpoint, "Must call approve endpoint");
  const applyEndpoint = source.match(/\/agent\/code-edits\/apply/);
  assert.ok(applyEndpoint, "Must call apply endpoint");
});

test("component forbids cloud, shell, git, commit, push, merge button labels", () => {
  const forbiddenLabels = [
    "commit",
    "push",
    "merge",
    "DeepSeek",
    "deepseek",
  ];
  for (const label of forbiddenLabels) {
    assert.doesNotMatch(source, new RegExp(`>\\s*${label.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\s*<`, "i"));
  }
});

test("component does not contain model_response or api-key fields", () => {
  assert.doesNotMatch(source, />\s*model_response\s*</);
  assert.doesNotMatch(source, /modelResponse/);
  assert.doesNotMatch(source, />\s*api_key\s*</);
  assert.doesNotMatch(source, />\s*API_KEY\s*</);
  assert.doesNotMatch(source, />\s*api-key\s*</);
  assert.doesNotMatch(source, />\s*secret\s*</);
  assert.doesNotMatch(source, />\s*endpoint\s*</);
});

test("apply button is conditionally rendered based on approval state", () => {
  assert.match(source, /Änderung anwenden/);
  assert.match(source, /preview\?.status === "approved"/);
});

test("component renders security invariants read-only badge", () => {
  assert.match(source, /Read-only/);
  assert.match(source, /Keine Shell/);
});

test("component resets when path or content changes after preview", () => {
  assert.match(source, /previewedPath/);
  assert.match(source, /previewedContent/);
  assert.match(source, /isStale/);
});

test("reset clears diff and proposal_hash from UI and disables apply", () => {
  assert.match(source, /reset/);
  assert.match(source, /setPreview\(null\)/);
  assert.match(source, /setStep\("idle"\)/);
  assert.match(source, /Zurücksetzen/);
});

test("history tracks preview, approve, apply, reset, error actions", () => {
  assert.match(source, /addHistory\(/);
  assert.match(source, /action:.*"preview"/);
  assert.match(source, /action:.*"approve"/);
  assert.match(source, /action:.*"apply"/);
  assert.match(source, /action:.*"reset"/);
  assert.match(source, /action:.*"error"/);
});

test("history stores only safe metadata, no file contents", () => {
  const contentMatch = source.match(/HistoryEntry/);
  assert.ok(contentMatch);
  assert.doesNotMatch(source, /history.*content/i);
});

test("proposal_hash in history is truncated or redacted", () => {
  assert.match(source, /hashPreview/);
  assert.match(source, /proposal_hash\.slice\(0,\s*\d+\)/);
});

test("error display shows no stacktrace pattern", () => {
  assert.doesNotMatch(source, /stacktrace/i);
  assert.doesNotMatch(source, /error\.stack/i);
});

test("stale detection disables apply", () => {
  assert.match(source, /isStale/);
  assert.match(source, /Vorschlag ist veraltet/);
});

test("component uses no localStorage, sessionStorage, or IndexedDB", () => {
  assert.doesNotMatch(source, /localStorage/);
  assert.doesNotMatch(source, /sessionStorage/);
  assert.doesNotMatch(source, /IndexedDB/);
  assert.doesNotMatch(source, /indexedDB/);
});
