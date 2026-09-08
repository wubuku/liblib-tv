# Batch 219 — clone TextNode 对齐为源站 markdown 展示块 + 按钮组

## 源站事实（Batch 218 直采）

- text 节点 350×350（源站视觉 759×759 是 zoom 后），
  `node-shell relative rounded-xl bg-[#171717]`
- 悬浮标题条（文档图标 +「文本节点」）
- 「尝试:」标签 + 5 操作按钮（自己编写内容/文生视频/图片反推提示词/
  文字生音乐/GVLM 3.1）
- markdown 展示区（无 textarea）

## 实施

- `TextNode.tsx` 重写：移除 textarea 编辑器，改为 350×350 卡片
  （悬浮标题条 + 尝试按钮组 + markdown 展示区）；
  `getDefaultNodeData("text")` 预填从「新文本节点」→「剧本」。

## 验收

- `npm run check`：0 errors（8 warnings 基线）
- 回归绿：22 / 102 / 172
- 不证明：markdown 渲染（当前为纯文本展示）；编辑入口（源站双击
  编辑器入口未采样）
