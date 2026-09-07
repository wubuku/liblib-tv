# Batch 180 — 芯片图标原字形对齐 + z 层级迁移评估（源站 2026-09-08 直采）

## 源站事实（窗口 rAF ~31fps；`source-chip-icons.json` 已存档）

### 尝试芯片 iconify (libtv 集) 图标原字形

- 三枚芯片行前 14×14 图标的完整 SVG（viewBox + path d）已逐字采得：
  - 5分钟超长视频：`viewBox 0 0 16 16`，`g transform=translate(1 1)`，
    双环环绕 path；
  - 首尾帧生成视频：`viewBox 0 0 20.05 22`，三层叠帧 path；
  - 首帧生成视频：`viewBox 0 0 22 22`，四角圆星框 path。
- 均 `fill=currentColor`，size 14。

### z 层级迁移评估（只评估，不改）

- 直采：源站 topnav `z-index: 1000`、`--z-panel 400`、`--z-modal 500`、
  React Flow 根 z=0。
- clone 现状：面板级映射 z-62/63（Batch 172 决策），顶栏约 z-50 刻度。
- 评估结论：**维持映射，不迁移**。理由：单切面板到 400 而顶栏仍 ~50 会
  反转堆叠（源站 topnav 1000 > panel 400）；全量迁移需重排 clone 所有
  overlay/toolbar/modal 的 z 刻度，影响 10+ 组件与 20+ 验证器合同，
  换来的仅是内部数值一致而非可见差异。留待出现真实堆叠 bug 再立项。

## 实施

- 新增 `src/components/nodes/AttemptChipIcons.tsx`：三个图标组件内嵌
  源站原字形 SVG（viewBox/path/尺寸逐字一致，`fill=currentColor`）。
- `VideoNode` 芯片行前图标由 lucide（Infinity/GalleryHorizontalEnd/Frame）
  替换为原字形组件（lucide 三枚 import 移除）。

## 验收

- `verify-liblib-batch180.py`：7 checks（三枚芯片 svg viewBox 与源站
  直采值逐一相同 + path 非空 + 0 console error）。
- 回归绿：21 / 22 / 26 / 33 / 128 / 149 / 155 / 160 / 165 / 166 / 169 /
  172-179 全量。
- `npm run check`：0 errors（8 warnings 基线）；docs check 通过。
- 不证明：iconify 集内其它图标字形（本批只采三枚芯片图标）。
- 源站测试残留清理：采样节点已删（0 残留）。
