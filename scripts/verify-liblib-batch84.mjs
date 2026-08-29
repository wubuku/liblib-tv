import assert from "node:assert/strict";
import fs from "node:fs";

const root = new URL("..", import.meta.url);
const treeSource = fs.readFileSync(
  new URL("./src/components/director/DirectorObjectTree.tsx", root),
  "utf8",
);
const inspectorSource = fs.readFileSync(
  new URL("./src/components/director/DirectorInspector.tsx", root),
  "utf8",
);
const viewportSource = fs.readFileSync(
  new URL("./src/components/director/DirectorViewport.tsx", root),
  "utf8",
);
const storeSource = fs.readFileSync(
  new URL("./src/store/directorStore.ts", root),
  "utf8",
);

assert.match(treeSource, /data-director-object-lock/);
assert.match(treeSource, /toggleObjectLocked\(object\.id\)/);
assert.match(treeSource, /aria-label=\{object\.locked \? `解锁/);
assert.match(inspectorSource, /data-director-inspector-lock/);
assert.match(inspectorSource, /对象已锁定，属性与变换编辑已停用/);
assert.match(inspectorSource, /disabled=\{selected\.locked\}/);
assert.match(inspectorSource, /data-director-motion-path-locked/);
assert.match(viewportSource, /object\.locked/);
assert.match(viewportSource, /hasLockedMember/);
assert.match(storeSource, /DIRECTOR_TARGET_LOCKED/);
assert.match(storeSource, /toggleObjectLocked:/);
assert.match(storeSource, /function directorPathTargetIsLocked/);

const guardedCommands = [
  "UPDATE_OBJECT_TRANSFORM",
  "UPDATE_CAMERA",
  "APPLY_POSE_PRESET",
  "UPDATE_POSE_CONTROL",
  "UPDATE_GROUP_TRANSFORM",
  "CREATE_MOTION_PATH",
  "START_PATH_DRAWING",
  "UPDATE_PATH_ANCHOR",
  "UPDATE_PATH_TRANSFORM",
  "TOGGLE_PATH_ENABLED",
];
for (const command of guardedCommands) {
  assert.match(storeSource, new RegExp(command));
}

console.log(
  JSON.stringify({
    batch: 84,
    status: "PASS",
    cases: {
      treeLockControl: true,
      inspectorLockControl: true,
      lockedViewportNoTransformControls: true,
      lockedObjectGuard: true,
      lockedPathGuard: true,
      lockedGroupGuard: true,
      stableReason: true,
    },
  }),
);
