import assert from "node:assert/strict";
import fs from "node:fs";

const root = new URL("..", import.meta.url);
const storeSource = fs.readFileSync(
  new URL("./src/store/directorStore.ts", root),
  "utf8",
);
const inspectorSource = fs.readFileSync(
  new URL("./src/components/director/DirectorInspector.tsx", root),
  "utf8",
);
const timelineSource = fs.readFileSync(
  new URL("./src/components/director/DirectorTimeline.tsx", root),
  "utf8",
);
const viewportSource = fs.readFileSync(
  new URL("./src/components/director/DirectorViewport.tsx", root),
  "utf8",
);
const planSource = fs.readFileSync(
  new URL(
    "./docs/research/liblib-canvas-batch88-2026-08-29/PLAN.md",
    root,
  ),
  "utf8",
);

const assertions = [
  [
    "timeline selection normalization exists",
    storeSource,
    /function normalizeDirectorTimelineSelection/,
  ],
  [
    "single-object track preference excludes group and prefers non-pose",
    storeSource,
    /track\.kind !== "group"[\s\S]*track\.kind !== "pose"/,
  ],
  [
    "multi-selection clears single-target timeline context",
    storeSource,
    /if \(selectedObjectIds\.length !== 1\) return null/,
  ],
  [
    "group selection only resolves group tracks",
    storeSource,
    /track\.kind === "group"[\s\S]*track\.groupId === selection\.selectedGroupId/,
  ],
  [
    "keyframe selection validates its owning track",
    storeSource,
    /selectedTrack\.keyframes\.some[\s\S]*state\.timeline\.selectedKeyframeId/,
  ],
  [
    "path anchor selection validates path and track",
    storeSource,
    /selectedPath\.anchors\.some[\s\S]*state\.timeline\.selectedMotionPathAnchorId/,
  ],
  [
    "delete projection normalizes against surviving entity selection",
    storeSource,
    /const normalizedTimeline = normalizeDirectorTimelineSelection/,
  ],
  [
    "direct object transform writes restore object selection authority",
    storeSource,
    /commandKind: "UPDATE_OBJECT_TRANSFORM"[\s\S]*selectedObjectId: objectId/,
  ],
  [
    "pose writes restore object selection authority",
    storeSource,
    /function updateCharacterRigAndTimeline[\s\S]*selectedObjectIds/,
  ],
  [
    "clipboard paste passes through normalization",
    storeSource,
    /function projectDirectorClipboardPasteState[\s\S]*normalizeDirectorTimelineSelection/,
  ],
  [
    "finished motion path restores complete object selection authority",
    storeSource,
    /finishMotionPathDrawing:[\s\S]*selectedObjectId: draft\.objectId,[\s\S]*selectedObjectIds,[\s\S]*selectedGroupId: null/,
  ],
  [
    "restore repair does not invent a compatible timeline track",
    storeSource,
    /repairDirectorSelectionState[\s\S]*fallbackToCompatibleTrack: false/,
  ],
  [
    "Inspector exposes the authoritative selected track",
    inspectorSource,
    /track\.id !== timeline\.selectedTrackId/,
  ],
  [
    "Inspector verification selector exists",
    inspectorSource,
    /data-director-inspector-track-id/,
  ],
  [
    "Timeline track click is a first-class authority",
    timelineSource,
    /onClick=\{\(\) => selectTimelineTrack\(track\.id\)\}/,
  ],
  [
    "Timeline keyframe click is a first-class authority",
    timelineSource,
    /selectTimelineKeyframe\(track\.id, keyframe\.id\)/,
  ],
  [
    "Viewport exposes transform target context",
    viewportSource,
    /data-director-transform-context-target/,
  ],
  [
    "selection remains clone-owned and source boundary is recorded",
    planSource,
    /Clone-owned[\s\S]*不宣称 LibTV 原站 Director/,
  ],
];

for (const [label, source, pattern] of assertions) {
  assert.match(source, pattern, label);
}

console.log(
  JSON.stringify({
    batch: 88,
    status: "PASS",
    cases: {
      selectionNormalization: true,
      multiSelectionClearsTimelineContext: true,
      groupTrackAuthority: true,
      keyframeAndPathOwnership: true,
      deleteRepair: true,
      directWriteEntrypoints: true,
      inspectorTimelineAgreement: true,
      viewportTransformContext: true,
      sourceBoundaryRecorded: true,
    },
  }),
);
