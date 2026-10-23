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

// ★★ Batch 856 判据迁移：组 gizmo（源站**没有**）已删除 ⟹ ⟹ gizmo 挂点数
//   从 3 变 2、`onLostPointerCapture` 从 2 变 1 ⟹ ⟹ 「写死个数」的前提过期
//   （写死的个数只要少一个 gizmo 就会假红，而多一个 gizmo 又照样绿）。
// ★★ 改成**结构性**断言：
//   ① 每个 `<TransformControls>` 挂点都**必须**带 `onPointerCancel={cancelTransform}`；
//   ② `onPointerCancel` 的数量 == gizmo 挂点数（不多不少）；
//   ③ 主变换 gizmo（`mode={transformMode}`）**唯一**，且额外带
//      `onLostPointerCapture={cancelTransform}`；
//   ④ 路径控制点 gizmo（`mode="translate"`）**唯一**。
// ★★ 负向断言：**组**的 rig 组件里**不允许**出现 `<TransformControls>`
//   （源站没有组 gizmo ⟹ 见 batch 856 的 README 与 raw/source-856-groupgizmo.json）。
const liveViewport = viewportSource
  .replace(/\/\*[\s\S]*?\*\//g, "")
  .replace(/(^|[^:])\/\/.*$/gm, "$1");
// ★ ★ 每个挂点的范围＝「它自己的 `/>`」与「下一个挂点的开头」**取先到者**
//   ⟹ ⟹ 一个自成一体的 gizmo 不会被并进前一块 ⟹ ⟹ 逐挂点断言才有分辨力；
//   ⟹ ⟹ 嵌套在前一个挂点属性里的 gizmo 也**不会**被漏掉。
const TC = "<TransformControls";
const gizmoBlocks = [];
let gizmoAt = liveViewport.indexOf(TC);
while (gizmoAt !== -1) {
  const closeAt = liveViewport.indexOf("/>", gizmoAt);
  const nextAt = liveViewport.indexOf(TC, gizmoAt + TC.length);
  const end =
    nextAt !== -1 && (closeAt === -1 || nextAt < closeAt) ? nextAt : closeAt;
  gizmoBlocks.push(liveViewport.slice(gizmoAt, end === -1 ? undefined : end));
  gizmoAt = nextAt;
}
assert.ok(gizmoBlocks.length >= 1, "视口里必须至少有一个 TransformControls 挂点");
for (const block of gizmoBlocks) {
  assert.match(
    block,
    /onPointerCancel=\{cancelTransform\}/,
    "每个 TransformControls 挂点都必须带 pointer cancel 保护",
  );
}
assert.equal(
  (liveViewport.match(/onPointerCancel=\{cancelTransform\}/g) ?? []).length,
  gizmoBlocks.length,
);
const mainGizmos = gizmoBlocks.filter((block) => /mode=\{transformMode\}/.test(block));
assert.equal(mainGizmos.length, 1, "主变换 gizmo 必须唯一");
assert.match(mainGizmos[0], /onLostPointerCapture=\{cancelTransform\}/);
const pathGizmos = gizmoBlocks.filter((block) => /mode="translate"/.test(block));
assert.equal(pathGizmos.length, 1, "路径控制点 gizmo 必须唯一");
const groupRig = liveViewport.match(
  /function DirectorGroupTransformRig\([\s\S]*?\n\}/,
);
assert.ok(groupRig, "必须能找到组 rig 组件");
assert.doesNotMatch(
  groupRig[0],
  /<TransformControls/,
  "组 rig 组件不允许有 gizmo（源站没有组 gizmo）",
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
