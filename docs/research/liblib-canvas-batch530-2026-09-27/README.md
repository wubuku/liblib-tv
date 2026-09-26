# Batch 530 — 图片节点模型触发菜单

> 状态：`SCRIPT_RECORDED_PASS`（commit 本批）。第一轮源站采样实测可开
> （liblib-source-exploration-2026-09-25 NOTES §3 + 截图 03b）——图片
> 编辑器参数条的模型触发芯片可打开 7 行模型菜单。此前 clone 的芯片为
> 静态「Lib Image」文本（batch 10/20 时代采样）。

## 行为合同

- 标准图片编辑器参数条芯片：闭合态显示当前模型名，默认
  「Lib Image 2.5 Pro」（截图 03b 当前源站合同；旧「Lib Image」静态
  文案仅保留在 panorama 变体，batch 20 合同不变）；
- 点击芯片 → 菜单锚定在芯片上方（`data-image-model-menu`，440px 圆角
  浮层）：7 行模型 = Lib Image 2.5 Pro(30s) / Lib Image 2.5 Fast(20s) /
  Lib Image(60s) / General image Pro(50s) / General image V2(25s) /
  Seedream 5.0 Pro(20s) / Qwen image 3.0(60s，上新徽标)；
- 选中行高亮并显示描述（其余行仅名称——源站截图非选中行无描述，
  hover 行为 SOURCE_UNCERTAIN）；时长胶囊右侧对齐；
- 选择 → 菜单关闭 + 芯片名同步；再点芯片开合（clone 决策：无遮罩
  点击关闭，菜单 UX 惯例）；
- 选择仅更新本地草稿状态，不触发生成（与全站禁真实生成约束一致）。

## SOURCE / CLONE 边界

- 模型名/时长/上新徽标：SOURCE_FACT（截图 03b + NOTES §3）；
- Seedream 5.0 Pro 描述在菜单内被截断，取 AgentDrawer 模型目录
  （batch 234 采样）同名条目完整文案（evidence-backed cross-reference）；
- Qwen image 3.0 行无描述采样，留空；
- 行首小图标为近似（Flower2/Asterisk/BarChart2/RefreshCw，
  SOURCE_UNCERTAIN——源站图标在截图中过小）。

## 内容

- `src/components/ImageModelMenu.tsx`（新组件：目录数据 + 菜单）；
- `src/components/ImageEditPanel.tsx`（标准变体芯片接线：本地模型状态、
  aria-expanded、chevron 翻转；panorama 不动）；
- `scripts/verify-liblib-batch530.py`（23 检查）；
- 回归：batch 10（几何 32px 芯片高）/20（panorama 旧文案）全绿；
  `npm run lint` 0 error；typecheck 仅并行开发者 JimengGenPanel WIP 错误。
- `runtime-audit.json`：本目录。
