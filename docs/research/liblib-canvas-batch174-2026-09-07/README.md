# Batch 174 — 模型菜单行系统对齐（源站 2026-09-07 三态直测）

## 源站事实（窗口 rAF ~31fps 可渲染期，CDP 采样，`source-model-row-geometry.json` / 截图已存档）

- **所有行固定 52px**：选中行、普通行、hover 行实测均为 52——选中不增高
  （推翻 clone 的 min-h-58 选中态 / min-h-48 普通态系统，58/48 为
  Batch 22 时代旧合同）。
- 背景：选中行 `rgba(255,255,255,0.15)`；普通行透明；hover 普通行
  `rgba(255,255,255,0.1)`（无描边）。
- 行结构：34×34 rounded-lg 图标瓦片 + 36px 高 `overflow-hidden` 文本列
  （`h-full flex-1 pr-1`，内部 `translate-y-2` + group-hover 位移过渡）；
  **描述文本常驻每行 DOM**，被 36px 列裁剪，不随选中展开；选中态展开
  描述为 clone 旧推断。
- 行按钮类：`group flex h-[52px] w-full items-center gap-1 rounded-xl p-2`；
  菜单列容器 360 宽（35 项全量，外层滚动）。

## 实施

- `VideoGenerationPanel` 模型菜单行：固定 `h-[52px]`（去 58/48 双态）、
  hover `bg-white/[0.1]`、选中 `bg-white/[0.15]`（去 `border-[#4a4a4a]`）、
  图标瓦片 34×34、文本列 `h-9 overflow-hidden`、描述常驻各行
  （`data-video-model-description` 不再仅选中行渲染）。
- `verify-liblib-batch22.py` 合同迁移（当前源站合同）：选中/普通行高
  58/48 → 52/52；描述断言改为按行定位（2.5 行、2.0 Fast VIP 行）；
  「selected-only descriptions」表述更新为 per-row。

## 验收

- `verify-liblib-batch174.py`：11 checks（三行 52 高/选中白 15/普通透明/
  hover 白 10/图标瓦片 34/两行描述常驻/0 console error）。
- `verify-liblib-batch22.py` 迁移后全过（35 项矩阵/380×410/5 premium/
  Fast 选择链/参数菜单交接/移动端/截图）。
- 回归绿：21 / 33 / 149 / 164 / 165 / 166 / 172 / 173。
- `npm run check`：0 errors（8 warnings 基线）；docs check 通过。
- 不证明：hover 描述位移的确切 transform 参数（46px 列内滑动细节）、
  选中行 hover 背景叠加、移动端 390 断点菜单表现（batch22 移动段仍绿）。
- 源站测试残留清理：采样用视频节点已删（0 残留）。
