# Batch 116 Plan：脚本生成器节点（脚本 NEW）

> 状态：`DONE`（见 [`README.md`](README.md)）
>
> 建档日期：2026-09-06。
>
> 上一批 checkpoint：Batch 115。
>
> 源站证据：[`../liblib-canvas-sampling-2026-09-06/README.md`](../liblib-canvas-sampling-2026-09-06/README.md) §3。

## 1. 范围

- **包含**：新增 `script-generator` 节点类型（350x350）；`ScriptGeneratorNode`
  渲染器（标题/三尝试/参考图/提示词/GVLM 3.1/积分 6）；nodeTypes 注册；
  默认数据；添加面板 脚本NEW → 创建节点。
- **不包含**：真实生成服务、三种尝试的子界面、参考图上传、生成结果节点。

## 2. 证据边界

| 标签 | 内容 |
|---|---|
| `SOURCE_FACT` | 节点标题、三种尝试文案、参考图、提示词 placeholder、GVLM 3.1、积分 6、350x350 |
| `CLONE_DECISION` | 尝试/提示词本地草稿、卡片视觉近似 |
| `SOURCE_UNKNOWN` | 尝试子界面、上传行为、生成结果形态 |

## 3. 验证与完成定义

- `verify-liblib-batch116.py`：脚本NEW 创建节点、卡片内容、尝试选择、
  提示词、尺寸样式、零诊断。
- batch98 两处断言迁移；相邻回归与全量门通过；master commit/push。
