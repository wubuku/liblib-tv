# Batch 20 Screenshot Analysis

## 1. 原站 720° 全景点击态

### 文件

- 路径：`docs/design-references/liblib-original-image-action-panorama-2026-08-25.png`
- 来源：LibTV 登录态画布
- 采样日期：2026-08-25
- viewport：`929x874`
- zoom 文案：`28%`
- 交互状态：图片工具条点击“全景”后
- 识图次数：1

### Source fact

- 原图片节点仍在画布中。
- 右上方新增一个空图片节点，标题为 `720°全景图`。
- 新节点内部是深灰 placeholder 和居中的图片占位图标，不是源图片副本。
- 源节点右 handle 到新节点左 handle 有一条新 edge。
- 新节点下方有一个宽面板，面板水平中心与新节点近似一致；右侧自然超出 viewport 并被裁切。
- 面板顶部显示：
  - `+参考`
  - 一张编号 `1` 的源图缩略图
- 主输入区显示紫色 `720` 标识、`720全景` 和参数/设置图标。
- helper copy 可读部分为：`点击生成，直接将场景图像转为720全景图，支持文生/参考...`
- footer 可见：
  - `Lib Image`
  - `2:1 · 标准画质 · 2K · 1张`
  - 高级设置图标

### Geometry estimate

| Item | Screenshot estimate | Derived world estimate |
|---|---:|---:|
| panorama node | `~200x100px` | `~700x350` at 28% |
| source-to-node horizontal gap | `~34px` | `~120` |
| panorama top vs source top | `~-31px` | `~-110` |
| panel width | pattern-compatible `~660px` | screen-fixed |
| panel height | `~252px` | screen-fixed |
| node-to-panel gap | `~5px` | compatible with `16 * zoom` |

这些值是截图反推，不是原站 DOM computed style。

### Interaction model conclusion

“全景”是 **创建并进入一个专用派生生成节点**，不是对源图片立即执行本地滤镜，也不是直接复制一张完成图片。

### Unknown

- 没有保存点击生成后的 loading/result/error 状态。
- 面板右侧被 viewport 裁切，提交按钮和全部 footer 控件没有完整显示。
- 没有原站移动端 panorama 状态。
- 没有逐一采样多角度、打光、九宫格、高清、宫格切分。

### Re-inspection rule

除非需要确认 panorama 提交后的状态、被裁切的右侧控件或其他图片动作，不再重新打开此截图。后续先读本文件。

## 2. Clone verification

### 文件

- `docs/design-references/liblib-clone-batch20-panorama-desktop-929-2026-08-25.png`
- `docs/design-references/liblib-clone-batch20-panorama-mobile-390-2026-08-25.png`
- `docs/design-references/liblib-clone-batch20-panorama-contact-sheet-2026-08-25.png`
- 生成日期：2026-08-25
- 最终状态识图次数：1
- 同路径预检次数：1；预检发现 screenshot 中残留了无关的整理确认卡，随后把准备步骤从 `Alt+Shift+f` 改为 `Meta+0` 并重新生成最终证据

### Verified clone fact

- Desktop 使用 `929x874` viewport 和原生 fit-view `28%`，没有整理确认或其他无关 overlay。
- 新节点为深灰空媒体面，居中显示 muted image icon；源图片只出现在 panel 的编号 `1` reference 中。
- source-to-derived edge、cyan selected border、顶部图片工具条和底部专用 panel 同时可见。
- panel 沿新节点中心锚定，右侧超出 viewport 后自然裁切；没有移动到页面中心。
- Mobile 使用初始 `28%` viewport。`900.5px` 工具条和 `660px` panel 都按节点中心自然裁切，页面本身没有横向滚动。
- 最终截图中没有真实生成结果、上传态、后端任务 ID、账户资产或持久化反馈。

### DOM-backed geometry

| Item | Desktop `929x874` |
|---|---:|
| source node | `x=459.382, y=105.768, w=172.986, h=97.339` |
| panorama node | `x=665.741, y=75.176, w=194.679, h=97.339` |
| panorama panel | `x=433.080, y=176.965, w=660, h=252` |
| node/panel center | `763.080 / 763.080` |
| node-to-panel gap | `4.450px`, equal to `16 * zoom` within sub-pixel rounding |

Mobile assertions：

- panorama node: `x≈260.6, w=196`，右侧自然越过 `390px` viewport；
- panorama panel: `x≈28.6, w=660`，右侧自然裁切；
- `documentElement` 和 `body` 的 `scrollWidth == clientWidth == 390`。

### Visual conclusion

clone 已消除原先“立即复制一张完成图片”的错误模型，并复现原站证据支持的局部层级：source image、连接线、空 panorama 节点、单参考图专用 panel。`700x350`、`+120/-110` 和 `660x252` 仍属于截图反推后的 clone 参数，不应改写为原站 DOM fact。

### Re-inspection rule

除非实现或截图文件发生变化，后续不再打开这三张 clone 图；几何与行为问题优先运行 `scripts/verify-liblib-batch20.py`。
