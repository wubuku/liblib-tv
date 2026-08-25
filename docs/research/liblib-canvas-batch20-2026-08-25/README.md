# Batch 20：720° 全景派生节点

> 状态：原站交互截图已审计，计划与组件合同已落档。

## 当前缺口

当前 clone 将图片工具条的“全景”与其他动作一样处理为“复制当前图片并填入通用 Prompt”。原站截图显示的真实交互不同：点击“全景”会创建并选中一个连接到源图片的空 `720°全景图` 节点，下方出现带源图参考和专用参数的生成面板。

## 本批范围

- 只修复有直接原站证据的“全景”动作；
- 创建空的 `720°全景图` 派生节点和一条 source-to-derived edge；
- 复刻单参考图、`720全景` 专用提示和 `2:1 · 标准画质 · 2K · 1张` 参数；
- 保留本地生成状态，不调用真实图片或 720° 服务；
- 不推断多角度、打光、九宫格、高清、宫格切分的具体原站流程。

## 阅读顺序

1. [`PLAN.md`](PLAN.md)
2. [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)
3. [`PANORAMA_DERIVATION.spec.md`](PANORAMA_DERIVATION.spec.md)
4. [`IMPLEMENTATION.md`](IMPLEMENTATION.md)

## 证据

- 原站截图：[liblib-original-image-action-panorama-2026-08-25.png](../../design-references/liblib-original-image-action-panorama-2026-08-25.png)
- 图片状态审计：[image-node-state-audit.json](../liblib-live-2026-08-25/image-node-state-audit.json)
- 原站 bundle 文案：[`nodeTypeSpaceScene720`](../liblib-seedance-2.5-2026-08-25/live-script-string-evidence.json)

