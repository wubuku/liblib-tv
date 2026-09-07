# Batch 200 — Agent 抽屉宽度规则破解 + Skill 卡芯片行为

## 源站事实（2026-09-08；CDP 视口覆盖三档采样，`source-drawer-widths.json` / 截图存档）

- **抽屉宽度规则破解**：容器在 1920 / 1680 / 1440 三档视口下均实测
  **400px 整**、右缘贴边——固定宽度，与视口无关。Batch 199 的「427」
  为 elementFromPoint 爬升取盒的测量伪影，更正。
- **Skill 卡点击行为**：点击 Skill 卡将该 Skill 名以**芯片插入输入区**
  （截图：输入区出现「皮克斯动画广告」芯片），抽屉保持打开；芯片可
  移除。抽屉并不关闭（Batch 200 首测的 asideLen=0 为测量伪影更正）。

## 实施

- `AgentDrawer` 宽度 `w-[340px]` → `w-[400px]`（三档视口直采）。
- Skill 卡点击后在输入区上方渲染 Skill 芯片
  （`data-agent-skill-chip`，可移除 `data-agent-skill-chip-remove`）；
  卡片选中态（`selectedSkillId`）保持。

## 验收

- `verify-liblib-batch200.py`：9 checks（抽屉 400 宽/卡点芯片出现/
  芯片文案/抽屉保持/芯片可移除/1200 视口下仍 400/0 page error）。
- 回归绿：22 / 107 / 121 / 172 / 185 / 196 / 197 / 198 / 199。
- `npm run check`：0 errors（8 warnings 基线）；docs check 通过。
- 不证明：芯片与提示词一同发送后的会话语义；Skill 卡再点取消选择的
  行为（源站未采样）；宽度在 <1200 视口的断点行为。
- 源站测试残留清理：采样节点已删（0 残留）。
