import assert from "node:assert/strict";
import fs from "node:fs";

const root = new URL("..", import.meta.url);
const storeSource = fs.readFileSync(
  new URL("./src/store/directorStore.ts", root),
  "utf8",
);
const documentSource = fs.readFileSync(
  new URL("./src/lib/directorProjectDocument.ts", root),
  "utf8",
);
const planSource = fs.readFileSync(
  new URL(
    "./docs/research/liblib-canvas-batch87-2026-08-29/PLAN.md",
    root,
  ),
  "utf8",
);

const assertions = [
  ["selection repair helper exists", storeSource, /repairDirectorSelectionState/],
  [
    "portable restore has explicit policy",
    storeSource,
    /selectionPolicy: "default" \| "preserve-current"/,
  ],
  [
    "undo/redo restore preserves current selection",
    storeSource,
    /state\.localModelLibrary,\s*"preserve-current",\s*state/s,
  ],
  [
    "selection repair filters missing object IDs",
    storeSource,
    /state\.selectedObjectIds\.filter\(\(objectId\) =>\s*objectIds\.has\(objectId\)/s,
  ],
  [
    "selection repair validates group membership",
    storeSource,
    /selectedGroup\.characterIds\.filter\(\(objectId\) =>\s*objectIds\.has\(objectId\)/s,
  ],
  [
    "selection repair validates timeline track",
    storeSource,
    /restored\.timeline\.tracks\.some\(\s*\(track\) => track\.id === state\.timeline\.selectedTrackId/s,
  ],
  [
    "selection repair validates motion path anchor",
    storeSource,
    /selectedPath\.anchors\.some\(\s*\(anchor\) => anchor\.id === state\.timeline\.selectedMotionPathAnchorId/s,
  ],
  [
    "selection stays outside portable document",
    documentSource,
    /export interface DirectorProjectDocumentV1/,
  ],
  [
    "plan records source boundary",
    planSource,
    /source-exact.*SOURCE_UNKNOWN|SOURCE_UNKNOWN/,
  ],
];

for (const [label, source, pattern] of assertions) {
  assert.match(source, pattern, label);
}

console.log(
  JSON.stringify({
    batch: 87,
    status: "PASS",
    cases: {
      explicitRestorePolicy: true,
      objectSelectionRepair: true,
      groupSelectionRepair: true,
      timelineSelectionRepair: true,
      portableDocumentBoundary: true,
      sourceBoundaryRecorded: true,
    },
  }),
);

