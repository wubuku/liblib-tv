import assert from "node:assert/strict";
import fs from "node:fs";

const root = new URL("..", import.meta.url);
const storeSource = fs.readFileSync(
  new URL("./src/store/directorStore.ts", root),
  "utf8",
);
const treeSource = fs.readFileSync(
  new URL("./src/components/director/DirectorObjectTree.tsx", root),
  "utf8",
);
const inspectorSource = fs.readFileSync(
  new URL("./src/components/director/DirectorInspector.tsx", root),
  "utf8",
);
const readmeSource = fs.readFileSync(
  new URL(
    "./docs/research/liblib-canvas-batch89-2026-08-29/README.md",
    root,
  ),
  "utf8",
);

const assertions = [
  [
    "state exposes explicit addDirectorCamera action",
    storeSource,
    /addDirectorCamera: \(\) => DirectorCommandResult/,
  ],
  [
    "new camera is created from an existing camera source",
    storeSource,
    /function createDirectorCameraFromSource\([\s\S]*source\.kind !== "camera"[\s\S]*source\.camera/,
  ],
  [
    "new camera clears follow/look-at object relationships",
    storeSource,
    /createDirectorCameraRelation\(\)/,
  ],
  [
    "new camera creates a camera track at the current time",
    storeSource,
    /const track = createTrackForObject\(camera, state\.timeline\.currentTime\)/,
  ],
  [
    "new camera becomes active and selected",
    storeSource,
    /activeCameraId: camera\.id,[\s\S]*selectedObjectId: camera\.id,[\s\S]*selectedTrackId: track\.id/,
  ],
  [
    "new camera uses one semantic history entry",
    storeSource,
    /commandKind: "ADD_CAMERA"[\s\S]*historyEntries: 1[\s\S]*createDirectorHistoryEntry/,
  ],
  [
    "new camera is persisted through active document authority",
    storeSource,
    /updateActiveDirectorDocument\(state, after, state\.captures\)/,
  ],
  [
    "object tree exposes add-camera affordance",
    treeSource,
    /data-director-add-camera[\s\S]*addDirectorCamera/,
  ],
  [
    "scene inspector exposes scene settings region",
    inspectorSource,
    /data-director-scene-settings[\s\S]*场景设置/,
  ],
  [
    "scene settings exposes ground color control",
    inspectorSource,
    /data-director-scene-ground-color[\s\S]*groundColor/,
  ],
  [
    "scene inspector exposes add-camera affordance",
    inspectorSource,
    /data-director-scene-camera-actions[\s\S]*data-director-add-camera/,
  ],
  [
    "source boundary rejects source-exact inference",
    readmeSource,
    /SOURCE_UNKNOWN[\s\S]*LibTV 原站 Director[\s\S]*\n[\s\S]*CLONE_DECISION/,
  ],
];

for (const [label, source, pattern] of assertions) {
  assert.match(source, pattern, label);
}

console.log(`Batch 89 pure/source verification passed (${assertions.length} assertions).`);
