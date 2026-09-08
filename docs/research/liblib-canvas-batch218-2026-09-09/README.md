# Batch 218 — text 节点编辑态采样（证据批）

## 源站事实（`source-text-node-shell.json` / 截图存档）

- text 节点结构（759×759，`node-shell relative overflow:visible width:fit-content`）：
  1. **悬浮标题条**（759×24）：文档图标 +「文本节点 2」（zoom 补偿）
  2. **STYLE 元素**：markdown-content CSS（p/h1/h2/h3 样式规则）
  3. **主内容区**（`group overflow-visible rounded-xl` 759×759）：
     - 「尝试:」标签
     - **5 个操作按钮**：自己编写内容 / 文生视频 / 图片反推提示词 / 文字生音乐 / GVLM 3.1
     - markdown 渲染内容
- **无 textarea**：text 节点为 markdown 展示块 + 操作按钮，不是 textarea 编辑器
- 无连线

## 与 clone 对照

- clone TextNode 需对齐为：markdown 展示块 + 尝试区按钮组
- 关键差异：源站 text 节点是 **markdown 渲染 + 按钮组**，非编辑器
- 「尝试:」按钮组含 AI 功能入口（文生视频/图片反推/文字生音乐/GVLM 3.1）

## 处置

- 证据批：text 节点结构已完整采样（JSON + 截图），clone 实装另立批次
  （需要 markdown 渲染 + 尝试按钮组实装）。
- 源站画布已清零。
