# Batch 533 — 脚本 V2 进度卡卡体与编辑器重入

> 状态：`SCRIPT_RECORDED_PASS`（commit 本批）。2026-09-27 CDP 补采
> （截图 39 + 节点 DOM 文本采样）：分镜编辑器会话后，画布上的脚本 V2
> 节点（b-007xQ4Z8ZW）卡内为进度卡形态——DOM 文本序
> 「脚本 V2 1 | 1 | 确认镜头 | 2 | 准备资产 | 3 | 合成提示词 | 打开脚本节点 →」，
> 截图中三圆圈横排、连线相连、标签在下。

## 合同

- script-v2 卡体（350×350，浮动标题条保持 batch 207 的「脚本生成器」
  默认——该合同断言保留）：三步进度 ①确认镜头（激活态浅底）—
  ②准备资产—③合成提示词（圆圈+连线+下方标签）；
- 底部「打开脚本节点 →」按钮（`data-script-v2-open`）→ 打开全屏分镜
  脚本编辑器（batch 531/532 合同），ESC/✕ 关闭后可再次打开；
- 新建态内部从未被采样（207 仅断言标题），进度卡是唯一实证内部形态，
  clone 以其为卡体（SOURCE_PARTIAL 注记在组件头）；
- 不触发任何生成动作。

## 内容

- `src/components/nodes/ScriptV2Node.tsx`（占位卡体 → 进度卡）；
- `scripts/verify-liblib-batch533.py`（14 检查：createStoryScriptPair
  建卡 → 步进内容断言 → 打开/ESC/✕ 往返）；
- 回归：batch 207（成对创建 + 标题合同）绿；lint 0 error。
- `runtime-audit.json`：本目录。
