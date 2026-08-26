# Batch 58 截图分析

> 状态：`RECORDED`（首次识别：2026-08-27）。截图识别成本高；本批优先使用
> DOM/store 状态断言，只有需要证明可见层级或视觉回归时才截图。

## 1. 复用原则

开始识别任何截图前，先读取：

- 本文件；
- Batch 52 的 [`SCREENSHOT_ANALYSIS.md`](../liblib-canvas-batch52-2026-08-26/SCREENSHOT_ANALYSIS.md)；
- Batch 53 的 [`SCREENSHOT_ANALYSIS.md`](../liblib-canvas-batch53-2026-08-26/SCREENSHOT_ANALYSIS.md)；
- Batch 54 的 [`SCREENSHOT_ANALYSIS.md`](../liblib-canvas-batch54-2026-08-26/SCREENSHOT_ANALYSIS.md)；
- Batch 35/46 的 Director 截图分析。

若截图文件、viewport、状态和问题未变化，不重复视觉识别。

## 2. 本批预期截图

| 文件 | 来源 | 状态 | 识别状态 |
|---|---|---|---|
| `liblib-clone-batch58-owner-preview-desktop-929-2026-08-27.png` | local clone | preview before invalidation | 已采集、已识别 |
| `liblib-clone-batch58-owner-cleanup-mobile-390-2026-08-27.png` | local clone | preview before invalidation；删除断言随后由 DOM/store 验证 | 已采集、已识别 |

## 3. 当前明确事实

- cleanup 的主要证据是 DOM detached、store owner null、graph/history unchanged；
- 不用截图证明 graph deletion 或 history；
- 不重新识别 Batch 52-54 已经记录过的 toolbar、preview media 和 edit panel 几何；
- 如果首次截图只显示既有 surface，没有新的视觉差异，记录为“视觉保持现状”。

## 4. 首次识别结果

### Desktop `929x874`

- 截图采集于本地 clone 的 `canvas-2` 图片节点预览打开后、删除 owner 前；
- 预览是覆盖全 viewport 的黑色半透明 page-level layer；
- 预览图片位于中央，底层画布、顶部导航、既有图片上下浮层和
  organize confirmation 仍可见但被遮罩压暗；
- 关闭按钮位于预览内容区域右上方；本批没有重新测量 Batch 52 已记录的
  media/close geometry；
- 该截图只证明 cleanup 前 surface 的可见层级，不证明源站删除语义。

### Mobile `390x844`

- 截图采集于本地 clone 的预览打开后、删除 owner 前；
- 预览 media 在窄视口内保持比例并居中，底部工具条和 organize confirmation
  仍位于被遮罩的底层 shell；
- 没有观察到新的 document/body 横向滚动；
- 该截图只证明当前 clone 的窄视口可见层级，不证明源站 responsive delete
  行为。

## 5. 证据分层

| 观察 | 类型 |
|---|---|
| preview overlay 覆盖 viewport、media 居中、底层 shell 被遮罩 | clone screenshot fact |
| owner delete/switch 后 DOM detached、UI owner null、graph/history 结果 | DOM/store-backed fact，见 `runtime-audit.json` |
| 删除/切换后必须关闭 owner | `CLONE_DECISION` / local runtime invariant |
| LibTV 源站是否执行相同 cleanup | 未确认，不写成 source fact |

本批后续 verifier 重跑不应重复识别这两张截图；若视觉代码、viewport 或研究问题
发生变化，才新增最小局部截图并更新本台账。
