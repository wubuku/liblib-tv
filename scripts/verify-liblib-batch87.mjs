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
    // ★★ Batch 855：这条断言的**前提**已变 ⟹ ⟹ 判据随之迁移。
    //
    // ★ 旧写法（batch 87～854）：`selectedGroup.characterIds.filter(...)`
    //   —— 它假定「组里只有角色」⟹ ⟹ `characterIds` 就是权威成员列表。
    // ★ ★ 但 batch 854 已把 `characterIds` **降为派生量**（源站逐字
    //   `function U(e){return O(e).filter(角色).map(id)}`），
    //   权威成员列表是 `O(e)`（`members` 优先／`characterIds` 兜底／去重）；
    //   batch 855 更把选择态**按全部成员**算（源站逐字 `lQ(n)`
    //   ＝ `selectedSceneMembers`＝全部成员，任意类别）。
    //   ⟹ ⟹ 于是「按角色过滤」既**漏**了非角色成员、又与源站不符。
    // ★ ★ 所以本断言改成：**按权威成员列表解析出的成员**逐个过滤存在性。
    //   （源码里 `resolveGroupMemberRefs(selectedGroup)` 是 store 侧那份实现，
    //   与 `directorGroupMath.ts`／`directorProjectDocument.ts` 的两份独立实现
    //   一起被 batch 855 的门禁 S9 **三向交叉验证**。）
    "selection repair validates group membership",
    storeSource,
    /resolveGroupMemberRefs\(selectedGroup\)\s*\.map\(\(member\) =>\s*member\.id\s*\)\s*\.filter\(\(objectId\) =>\s*objectIds\.has\(objectId\)/s,
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

// ★★ Batch 855：迁移后的判据**不能**被「两条都写」蒙混过关 ⟹ ⟹
//   显式断言旧写法（「按角色过滤」）在 store 里**已清零**。
// ★ 这条是**负向**断言 ⟹ ⟹ 它保证本文件上面的正向断言不是被「双写」放宽出来的。
assert.doesNotMatch(
  storeSource,
  /selectedGroup\.characterIds\.filter\(/,
  "legacy character-only group selection filter must be gone (Batch 855)",
);

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

