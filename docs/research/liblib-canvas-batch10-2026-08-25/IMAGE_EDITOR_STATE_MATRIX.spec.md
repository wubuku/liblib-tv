# Image Editor Five-State Matrix Spec

## 1. 原站直接事实

来源：`docs/research/liblib-live-2026-08-25/image-node-state-audit.json`。

| 节点 | panel h | Prompt | refs | 顶部直接入口 | generation settings |
|---|---:|---:|---:|---|---|
| 男性 `i-1FQ9tErTcC` | 191 | 0 字 | 0 | 标记 / 风格 | 16:9 · 标准画质 · 2K · 1张 |
| 女性 `i-lBzmo67AHv` | 191 | 0 字 | 0 | 标记 / 风格 | 16:9 · 标准画质 · 2K · 1张 |
| 咖啡 `i-dnwoZQ7jsG` | 211 | 602 字 | 0 | 标记 / 风格 | 2:1 · 低画质 · 1K · 1张 |
| 咖啡馆 `i-vxeeCnxySa` | 191 | 7 字 | 0 | 标记 / 风格 | 2:1 · 低画质 · 1K · 1张 |
| 分镜 `i-YDfWhFlthe` | 273.797 | 204 字 | 2 | 参考 / 标记 / 风格 | 16:9 · 低画质 · 1K · 1张 |

统一 placeholder：

```text
可直接文字生图，或上传图片输入文字指令对图片进行编辑，如：将背景改为雪夜
```

控件矩形：

- 顶部“参考 / 标记 / 风格”：`54x26`；
- footer 模型按钮：高 `32px`；
- footer generation settings 按钮：高 `32px`；
- footer icon buttons：`32x32`；
- 右上展开按钮：`28x28`；
- 分镜参考图：`47x47`，水平间距 `9px`。

五个 panel 的 textContent 都含“高级设置智能引用 AutoLink”，但 DOM 审计的顶部文字按钮集合中没有 AutoLink pill。因此：

- “顶部不应显示 AutoLink 文字 pill”是直接证据支持的负向合同；
- AutoLink 的准确图标路径、按钮次序和打开后弹层不在当前 JSON 中，不能声称已逐像素确认。

## 2. 关键反例

`咖啡馆` 同时满足：

```text
prompt length = 7
references = 0
panel height = 191
```

因此以下推断是错误的：

```text
has prompt => panel height 211
```

clone 必须让已知节点显式携带 `editorHeight`。`editorVariant` 可以继续表达内容类别或派生工具状态，但不能作为五个原站状态的唯一高度来源。

同理，“有 Prompt”不代表显示“参考”入口。当前五节点样本中，只有 `references.length > 0` 的分镜节点显示“参考”。

## 3. Clone 数据合同

```ts
type ImageEditorHeight = 191 | 211 | 274;

interface ImageNodeData {
  editorVariant?: "empty" | "prompt" | "referenced" | "tool";
  editorHeight?: ImageEditorHeight;
  prompt?: string;
  references?: string[];
  generationSettings?: string;
}
```

规则：

- 初始五节点必须显式写 `editorHeight`；
- 新建空白图片默认 `191`；
- 图片工具条产生的派生节点默认 `274`；
- 没有显式高度的兼容数据才回退到旧 variant 映射；
- “参考”入口由当前 references 数量控制；
- Prompt 和 references 在面板内变化时不自动改变高度，避免交互过程中无证据跳动。

## 4. Clone 交互边界

### 原站支持

- 顶部无 AutoLink 文字 pill；
- footer 存在与“智能引用 AutoLink”相关的控件文本；
- footer 控件为图标化 `32px` 控件。

### Clone 保留

现有原型已经实现：

1. 有 Prompt 且无引用时发现两个候选素材；
2. 用户点击入口后查看建议；
3. 用户确认后写入两张 references 和 Prompt token。

本批保留这个闭环，但入口移动到 footer 的链形图标按钮。该弹层的样式和确认逻辑属于 clone 原型能力，不写成原站完整交互事实。

## 5. 稳定测试接口

```text
data-image-edit-panel
data-image-editor-top-controls
data-image-editor-control="参考|标记|风格"
data-image-editor-model
data-image-editor-settings
data-image-editor-footer-icon
data-image-editor-autolink
data-image-editor-autolink-popover
data-image-editor-reference
```

这些 attribute 仅用于回归，不改变视觉。

## 6. Prompt 数据

`咖啡` 必须使用审计 JSON 中完整 602 字字符串。测试以文本长度和首尾关键片段共同校验，避免只靠硬编码长度掩盖内容替换。

`分镜 #2` 使用审计 JSON 中的 204 字文本，其中“孤立感。”与 `[视觉风格` 之间保留一个空格。

