# Batch 252 — 首尾帧生成视频芯片流受控实施（源站 2026-09-09 采样落地）

> 状态：`IMPLEMENTED`（batch 251 采样 → 实施 → 13 checks 验收 → 13 项回归绿）。
>
> 源站证据：`../liblib-canvas-batch251-2026-09-09/a-firstlast.png`——本批
> 无新增源站采样，纯实施批次。

## 复刻范围（对齐 batch 251 采样事实 `SOURCE_FACT`）

点击「首尾帧生成视频」尝试芯片后：

1. **自动创建两个图片节点**（首帧上/尾帧下，堆叠于视频节点左侧），
   各以一条边连入视频节点（`type: "default"` = bezier 曲线，与源站
   曲线形态一致——未改边流效果，符合硬约束）；
2. **双参考槽**（角标 1/2，本地图占位——源站为示例图内容，
   `CLONE_DECISION`）；
3. **提示词预填**采样的 AI 过渡文案（`FIRST_LAST_PROMPT` 原样存档），
   提示词框可编辑；
4. 页脚联动：**模型切 2.0**、模式 全能参考、`16:9 · 720P · 5s · 1个`。

## 实施

1. `canvasStore.createFirstLastFrameReference(videoNodeId)`：单事务创建
   两图片节点 + 两边；保持视频节点选中；单条历史记录；入边图片节点
   已存在时跳过（防重，同首帧守卫）。
2. `VideoNode` 芯片 onClick 增加首尾帧分支。
3. `VideoGenerationPanel`：
   - 尝试联动增加首尾帧分支（`setMode("first-frame")` + `setModel("2.0")`
     + 16:9 + 5s + `setPrompt(FIRST_LAST_PROMPT)`）；
   - 面板 `attempt === "首尾帧生成视频"` 分支：双参考槽 +
     预填提示词框。

## 验收

- `verify-liblib-batch252.py`：**13 checks**（+2 节点 +2 边；双槽；
  提示词预填含「青柠气泡水罐」；页脚 2.0/全能参考/16:9·720P·5s；积分
  135（clone 平价率公式，源站 155 漂移已记录）；重击防重；切 2.5 后
  230（batch 238 数据点复认））。
- 回归绿：125 / 149 / 160 / 176 / 22 / 236 / 237 / 238 / 239 / 240 /
  244 / 248 / 249。
- `npm run check`：0 errors（8 warnings 基线）；docs check 通过。

## 不证明 / 漂移记录

- 积分 155 vs clone 135：源站读数未受控（模式溢价假设见 batch 251
  README），clone 按平价率表给出 135；
- 源站双图为示例内容（青柠气泡水场景），clone 用本地图占位；
- 首尾帧态去选重选后芯片是否恢复：本轮未获干净读数（探针误用 clone
  选择器），待补采。
