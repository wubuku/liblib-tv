# Batch 178 — 尝试芯片选中标记 + 取消路径（源站 2026-09-08 直采）

## 源站事实（窗口 rAF ~31fps；`source-chips-*.json` / `source-deselect-paths.json` / 截图已存档）

### 芯片选中态视觉标记

- 选中 = **背景 white/10%**（未选中透明），文字两态均为 `#f7f7f7`
  （`text-fg-default`），类名完全相同（无额外选中类、无 aria-pressed）。
- 芯片为 rounded-lg（px-3 py-2、36px 高）、**行前有 14px iconify 图标**
  （长视频=双环环 绕形、首尾帧=层叠帧、首帧=单帧形）。

### 取消路径

- **ESC 不取消芯片**：仅取消节点选择；重选后长模式与
  `Auto · 720P · 300s` 原样保持（attempt 挂在节点上持久）。
- **真正取消 = 模式菜单切出超长视频**：点 文生视频 后芯片清除、
  时长 300→30 钳制、比例保持 Auto、模式按用户选择。

## 实施

- `VideoNode` 芯片：选中样式 `bg-[#09caf5]/15 text-[#09caf5]` →
  `bg-white/[0.1] text-[#f7f7f7]`（未选中文字 #aaa→#f7f7f7）、
  `rounded-full`→`rounded-lg`、行前加 14px lucide 图标（Infinity/
  GalleryHorizontalEnd/Frame——iconify 原字形替代，形似非等同）。
- `VideoGenerationPanel`：新增 `onAttemptChange` 可选 prop（VideoNode 传
  `setAttempt`）；`selectMode` 在长模式下切出时调用 `onAttemptChange(null)`
  ——清除芯片；联动分支 `setMode` 改功能式守卫（用户已另选模式则保留，
  只钳制时长 ≤30），避免清芯片联动覆盖用户模式选择。
- ESC 行为 clone 已一致（仅清选择，attempt 持久），无代码改动，验证器
  新增 esc:attempt-persists 合同。

## 验收

- `verify-liblib-batch178.py`：11 checks（选中白 10%/文字 #f7f7f7/
  rounded-lg/单图标；模式菜单取消→芯片清除/时长钳 30/模式按选择；
  ESC→attempt 持久/模式仍超长）。
- 回归绿：21 / 22 / 26 / 33 / 128 / 149 / 155 / 160 / 165 / 166 / 172 /
  173 / 174 / 175 / 176 / 177。
- `npm run check`：0 errors（8 warnings 基线）；docs check 通过。
- 不证明：源站图标原字形（iconify libtv 集，clone 用 lucide 替代）；
  芯片 hover 背景色值（`hover:bg-canvas-controls-hover` token 未解析）；
  其它取消入口（如有）。
- 源站测试残留清理：采样节点已删（0 残留）。

## 采样环境备注

视口一度缩至 854px 高导致面板 footer 触发器在可视区外：鼠标不可点时
可 JS click 开菜单（菜单本体向上展开仍在区内）或 CDP
`Emulation.setDeviceMetricsOverride` 临时抬高视口（本批 hover/采样混用）。
