# Batch 177 — 模型行 hover 滑层 + 尝试芯片非 toggle（源站 2026-09-08 直采）

## 源站事实（窗口 rAF ~31fps；视口下缘裁切用 CDP 设备度量覆盖绕过；JSON/截图已存档）

### 模型菜单行 hover/选中滑层（`source-model-hover-transform.json`）

- 机制（类名直证）：行内文本列包一层
  `translate-y-2 group-hover:translate-y-0 group-data-[selected=true]:translate-y-0`
  + `transition-transform duration-200`，外层 36px `overflow-hidden` 列。
- 默认态：内容下移 8px——20px 标题可见、16px 描述只剩 8px 被裁；
  hover **或选中**：上滑归位，描述完整露出；行高全程 52px 不变；
  hover 背景 white/10、选中 white/15（Batch 174 合同不变）。
- 选中行滑层类挂在 `group-data-[selected=true]`（行带 data-selected）。

### 尝试芯片行为（`source-chip-deselect.json` / 芯片类存档）

- **同芯片再点不取消**：长芯片按下后再点，长模式与 `Auto · 720P · 300s`
  原样保持——源站芯片不是 toggle（且无 aria-pressed、类名无选中标记，
  选中标记机制未采样到）。
- 点其它芯片=切换：首帧芯片 → 退出长模式，参数 `Auto · 720P · 5s · 1个`，
  **模式触发器显示 全能参考**；模型保持 2.5 不回切（Batch 176 的单向
  模型切换与源站一致）。
- 今日新建节点默认模型 2.5（又一个账号态数据点；Batch 173 勘误结论维持）。

## 实施

- `VideoGenerationPanel` ModelMenu：行加 `group` + `data-selected`，
  标题+描述包滑层 span（translate-y-2 → group-hover/group-data-selected
  归位，200ms 过渡）——hover 或选中露出描述，行高 52 不变。
- `VideoNode` 芯片 onClick：`setAttempt(label)`（再点同芯片保持选中，
  不再 toggle）。
- 联动初始化：`prevAttempt` 以 null 起步——面板重挂载（undo/重选）后
  attempt 仍在节点上时挂载即重放联动（非 toggle 后无法靠再点触发）。

## 验证器迁移（当前源站合同）

- batch128：取消断言 → 再点保持选中 + 设置不变（reclick:stays-selected）。
- batch155：取消钳制断言 → 再点保持 300s + 芯片保持按下。
- batch160：取消回常规断言 → 再点保持超长视频 + 参数不变。

## 验收

- `verify-liblib-batch177.py`：9 checks（滑层四类名/group/data-selected/
  hover 平移归位/hover 行高 52/选中行滑层类/芯片再点不取消/设置保持）。
- 回归绿：21 / 22 / 26 / 33 / 128 / 149 / 155 / 160 / 165 / 166 / 172 /
  173 / 174 / 175 / 176。
- `npm run check`：0 errors（8 warnings 基线）；docs check 通过。
- 不证明：源站芯片的选中态视觉标记机制；真正的取消路径（ESC/其它入口）；
  translate 用 Tailwind v4 `translate` 属性呈现（computed transform 为
  none，类名+视觉验证为准）。
- 源站测试残留清理：本批采样节点与盲点击产物已全部删除（0 残留）。
