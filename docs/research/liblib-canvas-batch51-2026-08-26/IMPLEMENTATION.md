# Batch 51 实施记录

> 状态：已完成（2026-08-26）。本批将标准图片顶部工具条
> 从固定 `offset=16` 修正为源站 bundle/DOM 证据支持的 zoom-aware host
> 公式；动作集合和 active image tools 仍是后续独立任务。

## 进度

- [x] 计划与 source/clone/freshness 边界落档
- [x] `ImageToolbar` 接收 live React Flow `zoom`
- [x] top `NodeToolbar` 使用 `offset = 10 + 24 * zoom`
- [x] `ImageNode` 传递 viewport zoom
- [x] Batch 51 focused Playwright 与结构化 runtime audit
- [x] 两张 clone 截图和截图识别台账
- [x] 组件 spec、backlog、验证台账和索引同步
- [x] 跨批回归与 `npm run check`
- [x] closeout commit/push 与工作区清理

## 实施决定

### 已采用

React Flow v12 的 `NodeToolbar` 计算为：

```text
host left = node center in screen coordinates
host top = node top in screen coordinates - offset
transform = translate(-50%, -100%)
```

因此直接把 source host 的
`nodeTop - 24 * zoom - 10` 映射为：

```text
NodeToolbar offset = 10 + 24 * zoom
```

底部 `ImageEditPanel` 保持原有节点内 inverse-scale 结构，不与顶部 host
共用 gap 或 containing block。

### 明确未做

- 未把 toolbar 从旧的 `900.5px` action set 扩展到 source 的 `1092.5px`
  action set；
- 未将撤销/重做改名或伪装成源站标注/旋转/下载/预览；
- 未实现 preview、annotate、element edit、rotate 或 layer separation；
- 未修改视频、FrameOS、Director 或共享源站画布；
- 未增加 viewport clamp、自动避让或 page-level fixed portal；
- 未把并行留下的未引用 source JPEG 纳入本批 source 结论。

## Focused Verification

已运行：

```bash
python3 scripts/verify-liblib-batch51.py
```

结果：

```text
Batch 51 Playwright verification passed: source-confirmed image toolbar
top gap, node-centered bottom panel, zoom/pan follow, screen-size
preservation, and console.
```

## Closeout Verification

已于 2026-08-26 完成 closeout 前检查：

```text
python3 scripts/verify-docs.py
Documentation link check passed: 433 Markdown files, 1777 local targets.

git diff --check
passed

npm run check
passed: lint (0 errors, 9 existing warnings), typecheck and production build
```

跨批历史 verifier 产生的旧截图变更已恢复；Batch 51 新截图与
`runtime-audit.json` 保留。随后以独立 closeout commit 记录并 push，本批
完成后工作区应保持干净。

脚本覆盖：

- `929×874` 整理画布后的标准图片选中态；
- 约 `28%` 初始、一次放大到约 `38%`、固定 zoom 下 pan；
- toolbar/node center、`10 + 24 * zoom` top gap；
- panel/node center、`16 * zoom` bottom gap；
- toolbar `900.5×49px` 和 panel `660×274px` 屏幕尺寸；
- 无 console/page error；
- `runtime-audit.json` 结构化记录和两张 clone 截图。

完整 rect 见 [`runtime-audit.json`](runtime-audit.json)，截图台账见
[`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)。

## 结果判断

本批完成了用户指出的“上下浮层位置”中顶部纵向 host 的一个确定差异：

- toolbar 与 panel 仍共享 node center；
- toolbar gap 随 zoom 使用 source-confirmed 公式；
- panel gap 继续使用 source-confirmed `16 * zoom`；
- zoom/pan 不产生 page-level stale offset。

这不等于普通画布所有 UI 已完成。当前最重要的剩余差异是 source 的
`1092.5×49` 当前 action set 与 clone 旧 `900.5×49` action set，以及
active image tool 的替换状态机。

## 接力

下一批先读本目录、[`ImageNode.spec.md`](../components/ImageNode.spec.md)、
[`LibTVOverlayPositioning.contract.md`](../components/LibTVOverlayPositioning.contract.md)
和 [`LIBTV_IMAGE_ACTION_MATRIX.md`](../open-canvas-2026-08-26/LIBTV_IMAGE_ACTION_MATRIX.md)。
有头浏览器控制可用后，再按 source freshness runbook 重新复核源站；
不要用本批 clone 截图替代 source evidence，也不要重复识别本批截图。
