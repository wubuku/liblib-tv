# LibTV 画布 Batch 8：视频组父子语义

> 建档日期：2026-08-25
> 状态：计划、实施、专项验证、跨批回归和完整工程检查已完成
> 目标：把原站视频组与失败视频从“视觉重叠”修正为 React Flow 的真实 parent-child 关系，并补齐受影响的图编辑事务。

## 为什么做这一批

当前 clone 的视频组和失败视频坐标看起来像包含关系，但 store 中两者都是顶层节点。结果是：

- 视频组 DOM 没有 `.parent`；
- 拖动视频组不会带动失败视频；
- 整理画布只能手工把两者放在相近位置；
- 复制、重新成组、删除和派生节点定位无法依赖真实层级。

保存的原站 DOM 与 xyflow v12 源码可以直接确认原站采用父子关系，而不是单纯视觉叠放。

## 文档导航

- [`PLAN.md`](PLAN.md)：缺口、价值、范围和验收标准
- [`VIDEO_GROUP_PARENTING.spec.md`](VIDEO_GROUP_PARENTING.spec.md)：证据链、数据关系与事务规格
- [`IMPLEMENTATION.md`](IMPLEMENTATION.md)：实施、验证、提交和接力记录

## 证据入口

- `docs/research/liblib-live-2026-08-25/full-canvas-audit.json`
- `docs/research/liblib-live-2026-08-25/canvas-audit.json`
- `node_modules/@xyflow/react/dist/esm/index.js`
- `node_modules/@xyflow/system/dist/esm/index.js`
- `src/store/canvasStore.ts`
- `src/lib/liblibOrganize.ts`

## 证据边界

原站 `.parent` class、组/视频绝对坐标和尺寸是直接证据；child 的相对 `(62,62)` 由两个直接坐标相减得到。级联删除、把已 parented child 重新成组、派生节点使用绝对坐标属于保持当前 clone 图模型一致性的实现决策，不描述为原站内部命令实现。

## 本批结果

- 初始失败视频改为视频组的真实 child，绝对画面位置不变；
- 视频组获得与原站一致的 `.parent` class，图片组保持空组；
- parent drag、child drag 和各自 undo/redo 均闭环；
- 复制 group 会带 child 并重映射 parentId；
- 单独复制 child 会得到可独立移动的顶层副本；
- parented child 仍可参与 Batch4 的重新成组；
- 删除 group 会级联 descendants 和相关 edges；
- Batch4-Batch8 与 `npm run check` 全部通过。

