import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const storeSource = fs.readFileSync(
  path.join(root, "src/store/directorStore.ts"),
  "utf8",
);

const staticAssertions = [
  ["authored state is part of DirectorState", /authoredObjects: DirectorObject\[\]/],
  ["authored state is initialized", /authoredObjects: cloneObjects\(\)/],
  ["snapshot uses authored state", /objects: state\.authoredObjects/],
  ["restore creates authored state", /const authoredObjects = restored\.objects/],
  ["runtime projection helper exists", /function projectDirectorRuntimeObjects/],
  ["timeline projection never samples runtime objects", {
    test: () => !/applyTimelineAtTime\(\s*state\.objects/.test(storeSource),
  }],
  ["path projection never samples runtime objects", {
    test: () => !/sampleTimelineObjectsAtTime\(\s*state\.objects/.test(storeSource),
  }],
  ["phone preview remains runtime-only", {
    test: () =>
      (storeSource.match(/objects: state\.objects\.map/g) ?? []).length >= 2,
  }],
];

for (const [label, pattern] of staticAssertions) {
  const passed =
    pattern instanceof RegExp ? pattern.test(storeSource) : pattern.test();
  assert.equal(passed, true, label);
}

const result = {
  status: "PASS",
  batch: 69,
  staticAssertions: staticAssertions.map(([label]) => label),
  forbiddenRuntimeProjectionCalls: 0,
  authoredRuntimeState: "discoverable",
};

console.log(JSON.stringify(result));
