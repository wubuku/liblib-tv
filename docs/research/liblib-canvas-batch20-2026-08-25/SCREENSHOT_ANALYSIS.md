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

