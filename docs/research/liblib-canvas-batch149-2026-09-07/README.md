# Batch 149 — 高级设置纵向列 + 默认模型 2.0（源站 2026-09-07 复采）

## 概要

外部 Chrome for Testing（CDP 9222）会话重新可用后，对源站画布（项目
`98f28a66270f4092a34999a3d4d435db`，含「预设 - 首尾帧生成视频」分组）做了结构级
复采，并据此落地三项对齐：

1. **高级设置纵向开关列**（替代 Batch 126 的横向 compact 行）。
2. **默认模型迁移为 Seedance 2.0 VIP**，触发器显示缩写「2.0」（解决 Batch 145
   遗留的「源站显示 2.0 vs clone 2.5」缺口）。
3. **引用槽 48×55 cursor-grab**。

## 会话诊断（重要勘误）

此前多轮记录的「源站会话降级（面板条目不渲染/点击无效）」根因是 **背景窗口渲染
节流**：Chrome 窗口被遮挡/最小化时，面板展开动画冻结在中间态（`min-w-[196px]`
容器实测 39px、`h-8` 行实测 18px），截图 API 挂起。会话本身（登录态、DOM、
点击、导航）始终健康。DOM 取证不受影响；涉及动画完成态或截图的采样需要窗口
前置。本 batch 全部结论均来自 DOM 证据。

## 源站事实（2026-09-07，DOM 取证）

### 1. 生成面板内嵌于分组节点

生成面板不是独立浮层，而是 React Flow **group 节点**
`react-flow__node-group ... parent draggable`（标签「预设 - 首尾帧生成视频」，
实测 1471×1001）的一部分。分组内：

- 左列：首帧、尾帧两个 image 节点（各 469×350，标题行 24px）。
- 右列：视频节点 1（350×350）；选中态展开卡 622 宽；下方生成面板 643 宽。
- 选中视频节点展开卡内出现「尝试：」建议列（3 个纵向 pill，h=36）：
  5分钟超长视频 / 首尾帧生成视频 / 首帧生成视频。点击其一后该列消失、生成面板出现。

### 2. 生成面板结构（x=1190-1833，右列）

- 工具行：参考 / 标记 / 特效 / 角色库 / 运镜（pill，h=26，`rounded-full px-2 py-1`，
  `text-xs text-fg-muted`）。
- 引用槽：两个编号槽 `1@` `2@`（48×55，`cursor-grab`；首尾帧模式 2 槽）。
- 提示词区：`generator-prompt-scroll-region ... min-h-20 max-h-[100px]`，无底色。
- 页脚（h=32）：模型触发器 **「2.0」**（13px）· 模式 **「全能参考」**（h-8）·
  参数 **「16:9 · 720P · 5s · 1个 · 」**（w=204）· 积分 **「135」**
  （`min-w-[85px] justify-end`）。
- 高级设置：标题 `pt-3 text-xs font-bold text-neutral-500 mx-2` + 纵向列
  `flex flex-col gap-1 pb-2 pt-1 px-2`，3 行 `flex items-center justify-between py-2`
  （行高 36）：联网搜索 / 自动校验素材 / 智能引用 AutoLink，Mantine Switch
  （38×20）右对齐。

### 3. 积分公式第 4 个数据点

2.0 / 16:9 / 720P / 5s / 1个 → **135** = 5 × 1 × 27。16:9→27/s 因子再次证实；
公式与模型选择无关。

### 4. 跟随横幅实况核对

源站画布处于「正在跟随」状态，横幅 DOM 与 clone FollowBanner（Batch 138）实现
逐类吻合：`fixed left-1/2 top-0 z-[305] -translate-x-1/2`、白色取消 pill
`rounded-full bg-white px-2 py-0.5 text-xs text-gray-900`、tooltip「按 ESC 退出」。

### 5. /project 卡片点击新开标签

源站 /project 页项目卡（封面为真实 `<img>` object-cover）点击后在**新标签页**
打开画布（`/canvas?spaceId=…&projectId=…`）。clone 当前为同页路由跳转 —— 记为
后续候选对齐项。

### 6. 添加节点面板容器（动画中间态勘误）

面板容器类：`border-hair border-canvas-controls-border flex min-w-[196px] w-max
flex-col gap-1 rounded-2xl p-2 backdrop-blur-[32px]`。39px 窄栏为动画冻结中间态，
**不是**折叠模式；目标态（196px、h-8 行）与 clone 现实现一致。clone 容器当前
`rounded-xl bg-[#262626]`，源站为 `rounded-2xl` + `backdrop-blur-[32px]` + hairline
token —— 记为候选视觉对齐项。

## 冲突记录：尝试芯片联动（batch128 vs 本次观察）

Batch 128 采样：首尾帧/首帧芯片 → ratio=Auto + duration=5s。本次观察：首尾帧
芯片点击后面板显示 `16:9 · 720P · 5s`（ratio 未变 Auto）。可能解释：分组预设
自带 16:9 配置，芯片未覆盖 ratio。batch128 的点击实验契约保留不变；此冲突待
源站窗口前置后做受控复测。

## Clone 变更

- `VideoGenerationPanel.tsx`
  - 默认模型（非续写）`2.5` → `"2.0 VIP"`；触发器显示去 ` VIP` 后缀
    （`2.0 Fast VIP` → `2.0 Fast`，CLONE_DECISION：缩写规则为剥尾部 VIP）。
  - 高级设置区改为纵向列（标题 + 3 行 justify-between，行高 36，开关 38×20 右对齐）；
    `showProcess` 态隐藏（过程视图独占面板，batch33 契约）。
  - 引用槽 `size-12` → `h-[55px] w-12 cursor-grab`。
  - 移除未用的 `initialModel` prop（VideoNode 同步）。
  - 续写面板 mode 触发器保留「全能参考」（提示文案「仅支持 … 全能参考模式」），
    普通面板 omnireference 仍显示「文生视频」（Batch 145）——修复 batch26 回归。
- 验证器迁移：batch22（触发器缩写、默认选中 2.0 VIP、菜单 y 偏移 -27.8）、
  batch21（菜单 y 偏移 -27.8）、batch33（process model 快照 2.0 VIP）。
- 新验证器 `verify-liblib-batch149.py`：15 checks（触发器缩写 / 菜单选中态 /
  积分 135 / 纵向列几何 / 开关往返 / 引用槽 48×55 / 0 diagnostics）。

## 验收

- `verify-liblib-batch149.py`：15 checks 通过（runtime-audit.json）。
- 相邻回归绿：21 / 22 / 26 / 29 / 33 / 36 / 43 / 100 / 125 / 126 / 128。
- `npm run check`：0 errors、8 warnings（既有基线）。
