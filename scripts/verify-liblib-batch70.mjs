import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const storeSource = fs.readFileSync(
  path.join(root, "src/store/directorStore.ts"),
  "utf8",
);
const deskSource = fs.readFileSync(
  path.join(root, "src/components/director/DirectorDesk.tsx"),
  "utf8",
);
const viewportSource = fs.readFileSync(
  path.join(root, "src/components/director/DirectorViewport.tsx"),
  "utf8",
);
const curveSource = fs.readFileSync(
  path.join(root, "src/components/director/DirectorCurveEditor.tsx"),
  "utf8",
);
const kernelSource = fs.readFileSync(
  path.join(root, "src/lib/directorCommandKernel.ts"),
  "utf8",
);

const staticAssertions = [
  ["typed history state exists", kernelSource, /export interface DirectorHistoryState/],
  ["typed command result exists", kernelSource, /export interface DirectorCommandResult/],
  ["history uses before and after documents", kernelSource, /before: DirectorProjectDocumentV1/],
  ["bounded history exists", kernelSource, /createDirectorHistoryState\(\s*limit = 50/],
  ["store exposes history", storeSource, /history: DirectorHistoryState/],
  ["store exposes undo and redo", storeSource, /undoDirector: \(\) => DirectorCommandResult/],
  ["store observes document mutations", storeSource, /useDirectorStore\.subscribe/],
  ["transform command exposes no-op reason", storeSource, /reason: "DIRECTOR_COMMAND_NO_CHANGE"/],
  ["transform command exposes invalid-value reason", storeSource, /reason: "DIRECTOR_INVALID_VALUE"/],
  ["transform command exposes missing-target reason", storeSource, /reason: "DIRECTOR_TARGET_MISSING"/],
  ["gesture begin is explicit", storeSource, /beginDirectorGesture/],
  ["gesture commit is explicit", storeSource, /commitDirectorGesture/],
  ["gesture cancel is explicit", storeSource, /cancelDirectorGesture/],
  ["workspace routes undo", deskSource, /if \(event\.shiftKey\) redoDirector\(\);\s*else undoDirector\(\)/s],
  ["object transform starts a gesture", viewportSource, /commandKind: "object-transform"/],
  ["curve editing starts a gesture", curveSource, /commandKind: "speed-curve"/],
  ["graph history is not called", storeSource, {
    test: (source) =>
      !/undoDirector[\s\S]{0,180}canvasStore\.undo/.test(source) &&
      !/redoDirector[\s\S]{0,180}canvasStore\.redo/.test(source),
  }],
];

for (const [label, source, pattern] of staticAssertions) {
  const passed = pattern instanceof RegExp ? pattern.test(source) : pattern.test(source);
  assert.equal(passed, true, label);
}

const result = {
  status: "PASS",
  batch: 70,
  staticAssertions: staticAssertions.map(([label]) => label),
  historyBoundary: "discoverable",
  gestureBoundary: "discoverable",
};

console.log(JSON.stringify(result));
