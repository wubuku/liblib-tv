# Batch 385 — /project 列表页新鲜度采样：侧栏三条新条目实装（`SOURCE_FACT` + `IMPLEMENTED`）

> 状态：liblib.tv 画布页劣化 ≠ 全站劣化——**/project 列表页健康可采样**，
> 采得侧栏三条新条目并实装；batch 168 验证器同步迁移；typecheck 0 错误。
> 源站画布页（BLOCKED_SOURCE 三项 + 故事板 CLONE_DECISION）维持阻塞。

## 源站事实（`SOURCE_FACT`，2026-09-12 /project 页直采）

- 顶部促销横幅：`Seedance 2.5 720P 年会员生成限时5折起，低至0.39
  元/秒｜年会员最低 4.5 折 限时抢购`；
- 侧栏导航新增三条目（batch 168 时代仅 4 条）：
  **Blender 插件 / LibTV Plugin / 百万积分大包上线**（导航序列
  首页/项目/LibTV Agent/创作者挑战赛 + 三新条目）；
- 页面其余结构：回收站、新建文件夹、开始创建、创建新的视频项目、
  5 张画布卡（未命名 + 日期 2026-09-07/09-06×3/09-05）、没有更多了；
- 促销文案确认：SD2.5 畅享卡/积分超市限时抢购 侧栏促销仍在。

## Clone 变更

- `project/page.tsx` 侧栏导航 4 → 7 条（Blender 插件 / LibTV Plugin /
  百万积分大包上线，本地 status 占位——无路由后端）；
- batch 168 验证器同步迁移（nav 4→7、labels 列表补全），复跑全绿。

## 验收

- typecheck 0 错误；batch 168 全绿；
- `npm run check` 0 errors / 0 warnings；docs check 940 文件通过。

## 后续候选

- liblib.tv 画布页恢复重测 → BLOCKED_SOURCE 三项与 CLONE_DECISION
  替换；
- /project 页促销横幅（Seedance 2.5 年会员 5 折）是否已入 clone 的
  对照确认；
- jimeng batch 5-8 源站级深化对照（随并行路线节奏）。
