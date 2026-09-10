# Batch 315 — clone 侧对齐项盘点确认（音频节点/AI生成 徽章/画布下拉）

> 状态：`CONFIRMED_ALIGNED`（对照 batch 309/267/286 采样；无代码变更）。
>
> 源站证据：`../liblib-canvas-batch309-2026-09-11/after-workflow.png`、
> `../liblib-canvas-batch267-2026-09-10/disambig-late.png`。

## 对齐核对（逐项）

| 源站要素 | clone 状态 |
|---|---|
| 音频节点：波形条（28 bars） | ✓ `AudioNode` 波形条列 |
| 音频节点：时长显示 | ✓ 右侧 duration 字段（源站为 00:00 / 00:03 当前/总格式——轻微布局方差，记录不实施） |
| 音频节点：播放键 | ✓ 圆形白底 Play |
| 图片节点：AI生成 徽章（媒体左上） | ✓ batch 268 已实装 |
| 图片节点：尺寸徽章（右上 1080×1446） | ✓ 标题栏既有 |
| 画布下拉：画布 header + 新建 + 每画布操作 | ✓ batch 287 结构匹配（源站 ∨ 子菜单内容仍 SOURCE_UNKNOWN） |
| 画布下拉：入口/弹层位置 | ✓ CanvasTabDropdown |

## 结论

等待授权/人工采样期间的可对照项**全部已对齐**。剩余 BLOCKED_MANUAL
项（OmniHuman 音频连线、待确认生成 确认/取消、Style Video/动作迁移
费率、每画布 ∨ 子菜单）与需授权项（素材库门后）维持等待状态。

## 验收

- typecheck 通过；docs check 通过；无源站操作；无代码变更。
