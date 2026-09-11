# Batch 386 — /project 顶部促销横幅实装（`SOURCE_FACT` + `IMPLEMENTED`）

> 状态：源站 2026-09-12 直采的顶部促销横幅实装；batch 168 促销
> 断言迁移；**三连跑通过**。liblib.tv 画布页恢复重测：
> `RECOVERY: still-broken` 维持。

## 源站事实（`SOURCE_FACT`，2026-09-12 /project 直采）

顶部促销横幅：`💥 Seedance 2.5 720P 年会员生成限时5折起，低至
0.39 元/秒｜年会员最低 4.5 折 限时抢购`（全宽条，页面首元素）；
侧栏促销为单行「积分超市限时抢购」（SD2.5 畅享卡行已不在源站）。

## Clone 变更

- `project/page.tsx` 新增顶部横幅（`data-project-top-banner`，
  💥 + 文案 + 「年会员最低 4.5 折 限时抢购」芯片，amber 色调）；
- 侧栏促销改单行「积分超市限时抢购」（SD2.5 畅享卡行移除——
  源站已无）；
- batch 168 验证器迁移：sidebar 促销单行断言 + 顶部横幅存在性与
  文案断言（Seedance 2.5 720P / 0.39 元/秒）。

## 验收

- batch 168 全绿（迁移后）；typecheck 0 错误；
- `npm run check` 0 errors / 0 warnings；docs check 941 文件通过。

## 后续候选

- liblib.tv 画布页恢复重测 → BLOCKED_SOURCE 三项与 CLONE_DECISION
  替换；
- jimeng batch 5-8 源站级深化对照（随并行路线节奏）。
