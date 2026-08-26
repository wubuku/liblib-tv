# Batch 53 计划：图片空标注替换态

> 建档日期：2026-08-26
> 对应 backlog：`LIBTV-PAR-002` Annotate empty

## 1. 缺口与价值

| 项目 | 当前 clone | 当前源站合同 | 价值 | 本批决策 |
|---|---|---|---:|---|
| 标注入口 | 当前按钮身份存在但 disabled | 当前图片 toolbar 有 `标注` | 5 | 启用并进入专用状态 |
| toolbar 替换 | 无 active image tool state | 标准 `1092.5x49` 被 `536x49` 专用条替换 | 5 | 实施 |
| generation panel | 标准 `660px` 面板仍会存在 | active annotate 下标准 bottom panel 不存在 | 5 | 实施 |
| 绘制 surface | 无 canvas | 节点上覆盖 CSS canvas，backing size 为 CSS rect × DPR2 | 5 | 实施空态 |
| 退出 | 只有全局 Escape 清 selection | Escape 可恢复标准双浮层 | 5 | 实施 |
| 保存/绘制结果 | 无 | 保存语义本轮未执行，空态无写入 | 3 | 明确不实现 |

## 2. Source Fact / Inference / Clone Decision

### Source fact

- 标注入口进入 `ElementTool.Annotate`；
- 专用工具条尺寸为 `536x49`，与 selected node center 对齐；
- 空标注态显示 8 个按钮，文字入口包含 `标注` 和 `保存`；
- 空态 undo/redo disabled；
- 绘制 canvas 覆盖图片节点，CSS rect 为
  `194.117x97`，backing size 为 `388x194`，对应 DPR2；
- 标准底部生成面板卸载；
- Escape 后专用 toolbar/canvas 卸载，标准 toolbar/panel 恢复；
- 本轮源站未绘制、未保存、未上传、未生成。

### Inference

- active tool state 由 page/UI 层持有 node identity，不能写进 graph data；
- canvas 应随节点 transform 走，不能变成 page-level modal；
- 空态退出必须保留 selection、graph、Prompt、viewport 和 history；
- 标注 toolbar 应使用独立 selector/owner，不能复用 standard
  `data-image-toolbar`。

### Clone-only decision

- `uiStore.imageAnnotate` 保存 `{ nodeId, imageUrl, width, height }`；
- `ImageNode` 根据 node id 替换 standard toolbar/panel；
- canvas backing ratio 固定为 `2`，以便在当前 device scale factor=1 的本地
  verifier 中仍明确复现源站 DPR2 合同；
- 专用工具条未获证据的图标只作为空态视觉壳层，不绑定绘制或保存副作用；
- `保存` 在空态保持 enabled，但本批不实现保存副作用；仅空态 `撤销`/`重做` 为 disabled；
- Escape、关闭按钮和节点切换都只退出 active state，不产生 graph transaction。

## 3. 实施步骤

1. 为 `uiStore` 增加 typed `ImageAnnotateState` 和 open/close actions；
2. 在 `ImageToolbar` 启用 `标注` action，dispatch annotate state；
3. 新增 `ImageAnnotateToolbar`，保持 `536x49` 和 node-centered top host；
4. 新增 `ImageAnnotateSurface`，覆盖图片、阻止节点拖拽，并把 backing
   width/height 设为 CSS rect × 2；
5. 在 `ImageNode` active annotate 时隐藏 standard toolbar/panel；
6. 在 page keyboard boundary 中优先处理 annotate Escape，阻断底层快捷键；
7. 增加 Batch 53 focused Playwright、runtime audit 和 desktop/mobile 截图；
8. 更新组件合同、Big Picture、backlog、verification ledger、Harness 和
   changelog。

## 4. 验收标准

### Desktop

- 选中图片时仍只有 standard toolbar + bottom panel；
- 点击 `标注` 后 standard toolbar 和 `data-image-edit-panel` 均卸载；
- 出现一个 `536x49` 的 `data-image-annotate-toolbar`；
- toolbar center 与 node center 在 1px 内；
- 出现一个覆盖 node image 的 canvas，CSS rect 等于 node image rect；
- canvas backing width/height 为 CSS rect 的约 2 倍；
- `标注`、`保存` 可访问名称可读，空态 `撤销`/`重做` disabled，`保存` enabled；
- nodes、edges、selected node、Prompt、viewport、history 不变；
- Escape 和 close button 恢复 standard toolbar/panel。

### Mobile

- active annotate 不导致 document 横向溢出；
- 专用 toolbar 遵循节点锚定和自然裁切，不被 page center/clamp 重定位；
- canvas 仍覆盖节点图片，backing ratio 约为 2；
- Escape 后 standard state 恢复。

### Repository

- 专项 verifier 通过；
- Batch 10/11/52 与 `npm run check` 通过；
- `verify-docs.py`、`git diff --check` 通过；
- 截图先形成 `SCREENSHOT_ANALYSIS.md`，再提交；
- 关键代码、文档 closeout 分别 commit/push，工作区最终干净。

## 5. 不做事项

- 不实现真实 stroke/path/eraser；
- 不实现真实保存，不上传标注图片；保留源站可见的 enabled `保存` 控件，但点击不产生副作用；
- 不创建结果 image node，不修改当前 image node；
- 不实现旋转、元素编辑、图层分离或下载；
- 不把 source 未确认的 8 个按钮逐一解释成真实业务能力。

## 6. Closeout

本计划已实施完成。代码、验证、问题修复、截图和 commit/push 历史见
[`IMPLEMENTATION.md`](IMPLEMENTATION.md)；后续先读
[`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)，不要重复识别本批截图。
