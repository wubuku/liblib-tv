import assert from "node:assert/strict";
import fs from "node:fs";

const root = new URL("..", import.meta.url);
const viewportSource = fs.readFileSync(
  new URL("./src/components/director/DirectorViewport.tsx", root),
  "utf8",
);
const storeSource = fs.readFileSync(
  new URL("./src/store/directorStore.ts", root),
  "utf8",
);
const planSource = fs.readFileSync(
  new URL(
    "./docs/research/liblib-canvas-batch86-2026-08-29/PLAN.md",
    root,
  ),
  "utf8",
);

assert.match(viewportSource, /data-director-transform-context/);
assert.match(viewportSource, /data-director-transform-context-kind/);
assert.match(viewportSource, /data-director-transform-context-state/);
assert.match(viewportSource, /data-director-transform-context-target/);
assert.equal(
  (viewportSource.match(/onPointerCancel=\{cancelTransform\}/g) ?? []).length,
  3,
);
assert.equal(
  (viewportSource.match(/onLostPointerCapture=\{cancelTransform\}/g) ?? [])
    .length,
  2,
);
assert.match(storeSource, /DIRECTOR_TARGET_LOCKED/);
assert.match(storeSource, /authoredObjects/);
assert.match(storeSource, /objects/);
assert.match(storeSource, /historyEntries: 1/);
assert.match(planSource, /clone-owned/);
assert.match(planSource, /SOURCE_UNKNOWN/);
assert.match(planSource, /pointer cancel/);

console.log(
  JSON.stringify({
    batch: 86,
    status: "PASS",
    cases: {
      transformContextSelectors: true,
      objectAndGroupPointerCancel: true,
      objectAndGroupLostPointerCapture: true,
      authoredRuntimeAuthorityPresent: true,
      lockedReasonBoundaryPresent: true,
      sourceBoundaryRecorded: true,
    },
  }),
);
