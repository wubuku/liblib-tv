# Batch 56 计划：图片旋转入口的最小派生节点复刻

> 建档日期：2026-08-26
> 对应 backlog：`LIBTV-PAR-002`
> 风险等级：中高。入口已被源站观察证明可能改变 graph。

## 1. 缺口与价值

| 项目 | 当前 clone | 已有源站证据 | 价值 | 本批决策 |
|---|---|---|---:|---|
| 旋转入口 | `32x32` disabled placeholder | 点击后新增并选中 `旋转与镜像` 节点 | 5 | 启用最小 graph slice |
| source edge | 无 | 源节点与新节点形成派生关系的现场 graph 结果 | 5 | 使用现有 derived-node transaction |
| selection | 无动作 | 新派生节点被选中 | 5 | 保持 `addDerivedNode` 选择语义 |
| undo | 入口不可用 | 一次 `Meta+Z` 撤销新增节点 | 5 | 复用现有 atomic history |
| rotate editor | 无 | bundle 有角度/镜像状态，但本轮未安全进入 | 4 | 不做 |
| dirty/save/upload | 无 | bundle 有潜在保存上传路径，未 live 验证 | 5 | fixture-gated，不做 |

## 2. Source fact / Inference / Clone decision

### Source fact

- 当前源站图片工具条存在 `旋转` 图标入口；
- 共享登录态画布上的一次点击实际产生了新节点；
- 新节点名称为 `旋转与镜像`；
- 新节点在点击后处于选中态；
- 单次 `Meta+Z` 可恢复到点击前的 graph；
- 该次观察没有证明最终 bitmap、尺寸、角度、镜像状态或保存路径。

### Inference

- 旋转入口至少存在一个会产生 graph-visible artifact 的实现路径；
- node + edge + selection 应作为一个 clone transaction 处理；
- 不能因为 bundle 中出现 local rotate state，就把入口强行改为只读 local editor。

### Clone-only decision

- 在本地使用 `addDerivedNode`，保证节点、source edge、selection 和 history
  的现有原子边界；
- 派生节点仍是 `image`，名称固定为 `旋转与镜像`；
- 为保持本地画布可见性，clone prototype 复用 source image URL；这是本地
  可视化决策，不是源站处理结果证据；
- `rotateMirror` metadata 仅保存 source node ID、source filename 和
  `prototype=true`；
- 不让入口触发 CSS rotation 或伪造角度值。

## 3. 实施步骤

1. 在 `ImageNodeData` 增加 typed `rotateMirror` metadata；
2. 在 `ImageNode` 增加 `旋转` 的独立 action 分支；
3. 将 `image-toolbar-rotate` 改为仅对有源媒体的图片节点可用；
4. 使用 `addDerivedNode` 创建 `旋转与镜像` 图片节点；
5. 记录本地 prototype 反馈，避免将派生节点误读成真实 bitmap 处理完成；
6. 编写 Batch 56 focused Playwright verifier，覆盖 desktop/mobile、node/edge/
   selection、source relationship、undo/redo、no-media no-op 和 overflow；
7. 保存 clone 截图并完成一次 `SCREENSHOT_ANALYSIS.md`；
8. 更新组件规格、研究索引、backlog、verification ledger、Harness 和
   changelog；
9. 运行专项验证、相邻图片批次、`npm run check`、docs check 和 diff check。

## 4. 验收标准

### Desktop / mobile

- 初始图片工具条仍显示 `旋转`，且有媒体时不再 disabled；
- 点击后节点数增加 1，边数增加 1；
- 新节点文本包含 `旋转与镜像`；
- 新节点具有 `data-rotate-mirror`、source ID、source filename 和
  `prototype=true`；
- 新节点被唯一选中，原节点不再是唯一选中节点；
- 新 edge 为 source -> derived；
- 派生节点有本地图片可见，但不显示角度/镜像结果承诺；
- 一次 undo 恢复到点击前 node/edge/selection，redo 恢复派生节点；
- 窄 viewport 不产生 document/body 横向滚动。

### No-media boundary

- 没有 `imageUrl` 的图片节点不触发派生节点创建；
- disabled/no-op 边界由本地 fixture 验证，不推断源站所有权限状态。

### Repository

- Batch 56 focused verifier 通过；
- Batch 52/54 相邻回归通过；
- `npm run check`、`python3 scripts/verify-docs.py`、`git diff --check` 通过；
- 实施文档、截图台账和提交历史完整；
- 工作区干净且 checkpoint 已 push。

## 5. 停止条件

如果实施过程中发现必须决定源站最终 bitmap、dirty modal、保存上传或真实
provider 才能满足当前证据，则停止扩边，将该未知写回本批文档并保持本地最小
graph slice。
