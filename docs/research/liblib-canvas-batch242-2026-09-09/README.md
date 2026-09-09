# Batch 242 — 首帧态模型锁定证伪 + Pixverse 费率 + OmniHuman 数据点（源站 2026-09-09 直采）

> 状态：`IMPLEMENTED`（受控采样 → 2 表项实施 → batch240 验证器扩至 18 checks）。
>
> 证据：`pixverse-controlled.png`（芯片直证）、`m-*` 截图、`sample-log.json`。

## 关键结论

### 首帧态模型选择器锁定——证伪（lock-test.png）

首帧态（首帧芯片已提交 + 参考图连接）下模型触发器 **未禁用**（SPAN
「2.5」、disabled=n/a、aria-disabled=none），点击后模型菜单**正常打开**。
Batch 241 的「疑似 首帧 态锁定模型选择器」假说**不成立**；Happy Horse 系
进入 首帧 紧凑态后的采样失败另有成因（待查——疑似紧凑页脚的元素结构差异）。

### Pixverse 费率（芯片受控，pixverse-controlled.png）

| 模型 | 芯片 | 积分 | 速率 |
|---|---|---|---|
| Pixverse V5.5（💎 premium） | 16:9 · 720P · 5s · 1个 | 60 | **12/s** |
| Pixverse V5（同流程） | 16:9 · 720P · 5s · 1个 | 45 | **9/s** |

附带：两模型均从 5分钟超长视频 态切出——切后芯片为 **16:9 · 720P · 5s**，
与 batch 236 的 2.0 VIP 切出态（Auto · 720P · **15s**）不同：**长视频态切出
的重置目标随模型不同**（比例/时长重置值非全局常量，`SOURCE_UNKNOWN` 全貌）。

### OmniHuman 1.5（数据点）

文生视频 态 14 积分，模式标签未匹配（疑有专属模式名）、芯片未捕获——
不足以入表（`SOURCE_UNKNOWN`）。

### 仍未采样

Style Video、Kling3.0 动作迁移（行点击未生效——重试待续）。

## 实施（`VideoGenerationPanel.tsx`）

`MODEL_RATES` 增补：Pixverse V5.5→12、Pixverse V5→9。
`verify-liblib-batch240.py` 扩至 18 checks（两模型费率断言）。

## 验收

- batch240 验证器 18 checks 全绿；回归 22 / 149 / 151 / 236 / 237 / 238 /
  239 / 21 抽测全绿（全量回归见上一批次基线，本批仅增两表项无结构变更）。
- `npm run typecheck` 通过；源站测试残留清理：**0 节点**。
