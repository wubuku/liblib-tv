# Batch 538 — 导演台全景图/选择画幅比例 flyout

> 状态：`SCRIPT_RECORDED_PASS`（commit 本批）。2026-09-27 CDP 已存截图
> 转录（44-director-rail-25.png / 44-director-rail-26.png，无需新采样）。

## 源站实测（SOURCE_FACT）

- **全景图 flyout**：三项纵排菜单——本地上传 / 历史记录 / AI 生成
  （各带小图标）；
- **选择画幅比例 flyout**：2 列卡片网格，7 项——自适应（默认激活，
  描边高亮）/ 21:9 / 16:9 / 4:3 / 1:1 / 3:4 / 9:16，每卡含比例矩形
  示意图形 + 文字标签；
- AI 生成 / AI 识图导入 为付费 AI 动作（约束禁触发，未点击）。

## clone 合同

- rail 三 flyout（添加角色/全景图/选择画幅比例）互斥展开，切换条目时
  收起前一 flyout；
- 画幅比例单选本地草稿（自适应默认），卡片含比例矩形示意；
- AI 生成/AI 识图为纯可视入口，不触发任何付费动作；
- batch 536/537 全部合同保持（回归绿）。

## 内容

- `src/components/director/DirectorIconRail.tsx`（两 flyout 扩展）；
- `scripts/verify-liblib-batch538.py`（20 检查）；
- 回归：batch 536/70 全绿；lint 0 error；typecheck 净。
- `runtime-audit.json`：本目录。
