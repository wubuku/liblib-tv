# Batch 248 — 工具行 pill 集随模型分布 + OmniHuman 1.5 特殊面板发现（源站 2026-09-09 直采）

> 状态：`IMPLEMENTED`（采样 → `MODEL_PILL_SETS` 实施 → 5 checks 验收）。
>
> 证据：`omnihuman.png`、`sample-log.json`（首帧附着态逐模型采样）。

## 源站事实（`SOURCE_FACT`）

### 工具行 pill 集随模型（首帧附着态，逐模型对照）

| 模型 | 模式 | pill 集 |
|---|---|---|
| 2.5 | 全能参考 | 参考 / 标记 / 特效 / 角色库 / 运镜（全 5） |
| Happy Horse 1.1 | 首帧 | **仅 参考** |
| Happy Horse 1.0 | 首帧 | **仅 参考** |
| Wan 2.6 | 首帧 | 参考 / 标记 / 特效 |
| Wan 2.2 | 图生视频 | 标记 / 特效 / 运镜（无 参考；clone 无该状态，仅记录） |

pill 集按 **模型**（非仅模式）分化——同为 首帧 态，Happy Horse 与 Wan 2.6
不同。其余模型分布 `SOURCE_UNKNOWN`，缺省全 5。

### OmniHuman 1.5 特殊面板（omnihuman.png，记录缓实现）

- 模式触发器 = **模型名本身**（无独立模式标签）；
- 引用区为**需求槽**：`图片 1/1`（已满足）+ `音频 0/1` + 警示
  **「请提供音频」**——双输入（图+音频）模型；
- 设置芯片 **「自适应 · 1个」**（无比例/清晰度/时长段）；
- 积分 **28**；下方独立 **「快速模式」** 开关 + 智能引用 AutoLink。

## 实施（`VideoGenerationPanel.tsx`）

`MODEL_PILL_SETS`：Happy Horse 1.1/1.0 → [参考]；Wan 2.6 →
[参考,标记,特效]。首帧附着态（`attempt` 非空）且模型入表时按表过滤
pill（`替换` 归一化回 `特效`）；其余模型/状态缺省全 5。

## 验收

- `verify-liblib-batch248.py`：**5 checks**（2.5 全 5 → Happy Horse 1.1
  单 参考 → Wan 2.6 三 pill 无 角色库/运镜 → 回切 2.5 恢复全 5）。
- 回归绿：125 / 236 / 237 / 239 / 240 / 244 / 149。
- `npm run check`：0 errors（8 warnings 基线）；docs check 通过。
- 源站测试残留清理：**0 节点**。

## 不证明 / 后续候选

- OmniHuman 1.5 特殊面板（需求槽/自适应芯片/快速模式）的复刻；
- 其余模型×模式组合的 pill 分布；
- Style Video / Kling3.0 动作迁移（BLOCKED_AUTOMATION）。
