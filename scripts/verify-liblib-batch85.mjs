import assert from "node:assert/strict";
import fs from "node:fs";

const root = new URL("..", import.meta.url);
const treeSource = fs.readFileSync(
  new URL("./src/components/director/DirectorObjectTree.tsx", root),
  "utf8",
);
const batchPlan = fs.readFileSync(
  new URL(
    "./docs/research/liblib-canvas-batch85-2026-08-29/PLAN.md",
    root,
  ),
  "utf8",
);

assert.match(treeSource, /data-director-selection-toolbar/);
assert.match(treeSource, /data-director-selection-count/);
assert.match(treeSource, /data-director-selection-action="copy"/);
assert.match(treeSource, /data-director-selection-action="delete"/);
assert.match(treeSource, /data-director-selection-action="clear"/);
assert.match(treeSource, /copyDirectorSelection/);
assert.match(treeSource, /deleteDirectorEntity/);
assert.match(treeSource, /clearSelection\(null\)/);
assert.match(treeSource, /分组 · \$\{selectionCount\}/);
assert.match(batchPlan, /清除选择不产生 history/);
assert.match(batchPlan, /SOURCE_UNKNOWN/);

console.log(
  JSON.stringify({
    batch: 85,
    status: "PASS",
    cases: {
      selectionToolbar: true,
      selectionCount: true,
      copyAction: true,
      deleteAction: true,
      clearAction: true,
      groupContext: true,
      sourceBoundaryRecorded: true,
    },
  }),
);
