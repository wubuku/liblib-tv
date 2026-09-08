# Batch 220 — 剧本预填完整内容采样（未完成，阻塞记录）

## 阻塞

- 空画布快捷芯片（故事脚本生成）依赖 Agent 抽屉开启后产生的会话状态；
  关闭抽屉并清理画布后芯片不再出现——**芯片出现条件=Agent 抽屉已开启
  且 Skill 卡已点过**。该前置在无头自动采样中难以可靠复现。
- 因此 text 节点的完整剧本 markdown 提取在本批未完成。

## 现有知识

- Batch 206 截图与 DOM 转储确认 text 节点预填内容以「剧本」开头。
- 渲染层 textContent 含 markdown-content CSS 类包裹。
- clone `createStoryScriptPair` 预填维持「剧本」单行（接近源站开头）。

## 后续

- 需在源站 Agent 抽屉可靠的开启窗口内重新执行：抽屉开→点 Skill 卡→
  发送→双击 text 节点→textarea.value 提取。建议合并到下一批 Agent
  表面采样一起做。
- 源站画布已清零。
