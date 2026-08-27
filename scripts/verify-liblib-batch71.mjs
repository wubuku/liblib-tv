import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const storeSource = fs.readFileSync(
  path.join(root, "src/store/directorStore.ts"),
  "utf8",
);
const inspectorSource = fs.readFileSync(
  path.join(root, "src/components/director/DirectorInspector.tsx"),
  "utf8",
);
const timelineSource = fs.readFileSync(
  path.join(root, "src/components/director/DirectorTimeline.tsx"),
  "utf8",
);
const viewportSource = fs.readFileSync(
  path.join(root, "src/components/director/DirectorViewport.tsx"),
  "utf8",
);
const gestureSource = fs.readFileSync(
  path.join(root, "src/components/director/useDirectorGestureBoundary.ts"),
  "utf8",
);

const staticAssertions = [
  ["gesture helper is typed", gestureSource, /DirectorGestureBoundaryHandlers/],
  ["gesture helper begins from focus/pointer", gestureSource, /onFocus: begin/],
  ["gesture helper commits on blur", gestureSource, /onBlur: commit/],
  ["number inputs stay active through pointerup", gestureSource, /type === "number"/],
  ["range keyboard interaction begins a gesture", gestureSource, /event\.key !== "Tab"/],
  ["gesture helper handles pointercancel", gestureSource, /onPointerCancel: cancel/],
  ["external gesture cancellation clears local ref", gestureSource, /activeRef\.current = false/],
  ["Inspector uses the gesture helper", inspectorSource, /useDirectorGestureBoundary/],
  ["pose control has a gesture scope", inspectorSource, /commandKind: "pose-control"/],
  ["camera FOV has a gesture scope", inspectorSource, /commandKind: "camera-fov"/],
  ["path fields have gesture scopes", inspectorSource, /path-anchor-position/],
  ["path transform has a gesture scope", inspectorSource, /commandKind: "path-transform"/],
  ["path drawing begins a gesture", timelineSource, /commandKind: "path-draw"/],
  ["path drawing commits from the pen completion UI", viewportSource, /data-director-path-drawing-complete[\s\S]{0,500}commitDirectorGesture/s],
  ["path drawing cancel clears both draft and gesture", viewportSource, /data-director-path-drawing-cancel[\s\S]{0,500}cancelDirectorGesture/s],
  ["path anchor handle transform commits history", viewportSource, /updateMotionPathAnchorWorldHandle[\s\S]{0,260}commitDirectorGesture/s],
  ["path controls have a window cancel fallback", viewportSource, /window\.addEventListener\("pointercancel"/],
  ["drawing surface has a window cancel fallback", viewportSource, /cancelMotionPathDrawing\(\);\s*cancelDirectorGesture\(\)/s],
  ["store has path drawing lifecycle", storeSource, /startMotionPathDrawing:[\s\S]{0,600}finishMotionPathDrawing:[\s\S]{0,300}cancelMotionPathDrawing:/s],
];

for (const [label, source, pattern] of staticAssertions) {
  const passed = pattern instanceof RegExp ? pattern.test(source) : pattern.test(source);
  assert.equal(passed, true, label);
}

const result = {
  status: "PASS",
  batch: 71,
  staticAssertions: staticAssertions.map(([label]) => label),
  gestureBoundary: "focus-pointer-update-commit-cancel",
  coveredInputs: ["number", "range", "path-anchor", "path-transform", "path-draw"],
};

console.log(JSON.stringify(result));
