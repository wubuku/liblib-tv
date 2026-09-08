# Batch 214 — 运镜菜单为纯启动器（无选中标记）

## 源站事实（窗口 rAF ~31fps；`source-yunjing-selected-cards.json` / 截图存档）

- 选中与未选中的运镜卡片**类名与标记完全相同**（无勾选标记、无描边、
  无 aria-pressed）——菜单内不展示选中态。
- 点卡后菜单关闭，pill 文案保持「运镜」不变，提示词不注入（Batch 213
  采样中点卡后 prompt 亦为 null）——**菜单是纯启动器**。
- 推论：选中态在生成时注入（格式未采样），或仅由后端会话记录。

## 实施

- `VideoGenerationPanel`：移除运镜卡片的「✓ 已选」标记渲染
  （`yunjingSelection` 内部状态保留供生成语义，菜单内无任何选中
  视觉）——对齐源站纯启动器行为。

## 验收

- `verify-liblib-batch214.py`：6 checks（菜单 23 卡/无选中标记/点卡
  关菜单/pill 文案不变/0 console error）。
- 回归绿：213 / 146 / 22 / 172。
- `npm run check`：0 errors（8 warnings 基线）；docs check 通过。
- 不证明：选中态注入到生成的格式；卡片二次点击的取消行为。
- 源站测试残留清理：采样节点已删（0 残留）。
