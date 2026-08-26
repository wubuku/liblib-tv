# Batch 51 截图与测量台账

## 识别策略

本批没有重新进行截图视觉识别。两张截图只作为 clone runtime evidence
保存；所有几何结论来自同一轮 Playwright DOM `bounding_box()` 结果和
`runtime-audit.json`。这样可以避免后续为了恢复记忆重复识别同一批图片。

## Evidence

| 文件 | 来源 | viewport | 状态 | 分析方式 |
|---|---|---:|---|---|
| [`liblib-clone-batch51-image-toolbar-source-gap-28-2026-08-26.png`](../../design-references/liblib-clone-batch51-image-toolbar-source-gap-28-2026-08-26.png) | 当前 clone | `929×874` | 整理画布、选中 `i-YDfWhFlthe`、约 28% | DOM/JSON，不做视觉重识别 |
| [`liblib-clone-batch51-image-toolbar-source-gap-zoom-pan-2026-08-26.png`](../../design-references/liblib-clone-batch51-image-toolbar-source-gap-zoom-pan-2026-08-26.png) | 当前 clone | `929×874` | 放大到约 38%，再 pan | DOM/JSON，不做视觉重识别 |

## 可复核结果

- 初始节点屏幕宽度 `176.534px`，由 `622` flow units 推出 zoom
  `0.283816`；顶部工具条为 `900.5×49px`；
- 初始 toolbar gap 为约 `16.812px`，等于
  `10 + 24 × 0.283816`；底部 panel gap 为约 `4.541px`，等于
  `16 × 0.283816`；
- 放大后 zoom 为 `0.383816`，toolbar gap 为约 `19.212px`，等于
  `10 + 24 × 0.383816`；bottom panel gap 为约 `6.141px`；
- 放大后 toolbar 仍为 `900.5×49px`，bottom panel 仍为
  `660×274px`；
- pan 后 toolbar、panel 与 node 的相对中心和垂直关系继续满足合同；
- 没有观察到 graph node/edge 变化、console error 或 page error。

## 边界

这些是 clone-owned measurements，不是新的 LibTV source screenshot。当前
source action set 仍记录为 `1092.5×49px`、9 个文字动作加 4 个图标动作；
本批只修正 top host 几何，没有把旧 clone action set 冒充为 source parity。
