# Batch 249 — OmniHuman 1.5 特殊面板受控实施（源站 2026-09-09 采样落地）

> 状态：`IMPLEMENTED`（batch 248 采样 → 实施 → 14 checks 验收 → 回归绿）。
>
> 源站证据：`../liblib-canvas-batch248-2026-09-09/omnihuman.png`——本批
> 无新增源站采样，纯实施批次。

## 复刻范围（对齐 batch 248 采样事实 `SOURCE_FACT`）

模型切到 **OmniHuman 1.5**（双输入图+音频模型）后面板整体切换：

1. **无工具行 pill**——需求槽行替代：`图片 1/1`（已满足，图槽 +
   角标 1）+ `音频 0/1`（虚线空槽）+ 警示 **「请提供音频」**；
2. **模式触发器 = 模型名本身**（「OmniHuman 1.5」，无独立模式标签）；
3. **设置芯片 = 「自适应 · 1个」**（无比例/清晰度/时长段）；
4. 积分 **28**（该态定值，`SOURCE_FACT` 单读数）；
5. 高级区为 **快速模式 + 智能引用 AutoLink** 两行（无 高级设置 标题、
   无 联网搜索/自动校验素材）。

## 实施（`VideoGenerationPanel.tsx`）

- `isOmniHuman = model === "OmniHuman 1.5"` 分支：
  - 工具行整体隐藏（`!isOmniHuman && pills…`），需求槽行
    `data-omnihuman-*`（image-slot / audio-slot / audio-warning）插入
    工具行之后；
  - 内容区分支：空 flex 占位（无 textarea）；
  - `modeLabel` / `settingsLabel` / `credits`（28 定值）三处分支；
  - 高级区内联切换为 快速模式（`fastMode` state，Zap 图标）+ AutoLink。

## 验收

- `verify-liblib-batch249.py`：**14 checks**（模式/芯片/积分；三需求
  元素；无 pill、无 textarea；快速模式行有、联网搜索行无；回切 2.5
  恢复标准芯片/5 pill/高级设置行）。
- 回归绿：125 / 149 / 160 / 176 / 22 / 236 / 237 / 238 / 239 / 240 /
  244 / 248。
- `npm run check`：0 errors（8 warnings 基线）；docs check 通过。

## CLONE_DECISION / 不证明

- 图片槽为本地图占位（源站为已附着参考图内容）；
- 音频槽点击/上传流、需求满足后的状态变化、快速模式开关的生成行为、
  OmniHuman 参数菜单展开态均未采样；
- 模式触发器点击行为保持 clone 现状（打开模式菜单）。
