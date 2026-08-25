# Batch 26 Screenshot Analysis

## 1. Source Visual Reuse

本批没有重复识别既有整图。

复用事实：

- `docs/research/liblib-canvas-batch24-2026-08-25/SCREENSHOT_ANALYSIS.md` 已记录 ready video 顶部工具栏中存在 `智能续写`；
- Batch 9 已记录 video top/bottom overlay 的 node-relative anchor；
- Batch 23 已记录片段重拍截图，但明确排除 `智能续写` 的 source fidelity。

本批新增 selector 视觉合同来自当前线上 bundle，而不是再次依赖截图估计：

- `660px` width；
- `48px` timeline；
- `16px` handles；
- `4px` shell padding；
- `8px` flex gap；
- `8px` node margin；
- cyan continuation variant；
- two-decimal duration chip。

## 2. Re-inspection Rule

实施前不再打开片段重拍或 ready-video 整图。只有以下问题进入范围时才需要新的最小截图：

- 原站 selector 的实际 computed color/token 与 bundle class 不一致；
- continuation target visible prefix 的精确 DOM 垂直位置；
- 原站移动端另有 viewport clamping。

## 3. Clone Screenshot Ledger

本批截图由 `scripts/verify-liblib-batch26.py` 在 device scale factor 1 下生成：

| Screenshot | Viewport / state | Recorded result |
|---|---|---|
| `docs/design-references/liblib-clone-batch26-continuation-default-929-2026-08-25.png` | `929x874`, source selected, `0-30s` | selector 位于 node 下方，top toolbar、node、selector 三层没有重叠；cyan handles 包住完整 timeline，duration chip 居中 |
| `docs/design-references/liblib-clone-batch26-continuation-adjusted-929-2026-08-25.png` | `929x874`, handles + region adjusted | 未选区保留暗色 thumbnail，选区由 cyan 左右 handles、上下 outline 和半透明 fill 共同表达；`12.00 秒` chip 保持在 range 中心 |
| `docs/design-references/liblib-clone-batch26-continuation-target-929-2026-08-25.png` | `929x874`, target created + fit view | source 和 target 横向连接；target 使用 empty media body，Prompt panel 显示 source tile、能力提示、visible prefix、range 和 placeholder |
| `docs/design-references/liblib-clone-batch26-continuation-mobile-390-2026-08-25.png` | `390x844`, selector open | source node 与 `660px` selector 保持自然裁切；下方固定 toolbar 不被 selector 推动，document 无横向 overflow |
| `docs/design-references/liblib-clone-batch26-continuation-contact-sheet-2026-08-25.png` | four-state ledger | 2026-08-25 已进行一次完整视觉检查；后续优先读取本节，不重复识别整图 |

## 4. Visual Findings

### Direct clone screenshot facts

- selector 的 `56px` surface 紧凑承载 close、timeline、confirm，没有出现旧版 `316px` 重拍 editor。
- 默认全选与调整后选区的 handles 均清晰可见；duration 文本没有覆盖 close 或 confirm。
- target screenshot 中，连接 edge 终止于 empty target 左 handle；target 和 source 标题/分辨率位于各自节点上方。
- target Prompt panel 宽于当前 fit-view 后的 node，但保持以 target center 对齐，这是既有 inverse-scale 浮层合同。
- mobile 中 viewport 只显示 selector 中段，属于有意的 fixed-screen-width natural clipping，而不是 document overflow。

### Inference / clone-only

- timeline 使用循环本地缩略图，因此相邻 frame 并不代表真实 source video 的连续采样。
- target panel 的 source tile、能力说明和 visible prefix 层级符合 bundle 文案合同，但精确垂直位置仍是 clone 实现，不声明为 source DOM rect。
- contact sheet 的四宫格与英文标签仅用于测试账本，不属于产品 UI。

## 5. Re-inspection Rule

本 contact sheet 已完成一次视觉识别。除非组件实现或截图发生变化，后续 Batch 26 回归不得重新识别整张 contact sheet；需要调查时只检查最小相关 crop/state。
