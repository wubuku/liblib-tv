# Batch 116：脚本生成器节点（脚本 NEW）

> 状态：`SCRIPT_RECORDED_PASS`
>
> 建档日期：2026-09-06。
>
> 上一批 checkpoint：Batch 115。
>
> 源站证据：[`../liblib-canvas-sampling-2026-09-06/README.md`](../liblib-canvas-sampling-2026-09-06/README.md) §3。

新增 `script-generator` 节点类型（350x350）：标题「脚本生成器」、三种尝试
模式（剧本生成分镜脚本/角色生成分镜脚本/自己编写分镜脚本）、参考图入口、
提示词（placeholder「描述剧情片段、故事，为你生成分镜脚本」）、GVLM 3.1
模型角标与积分「6」。添加面板 脚本NEW 由本地 status no-op 改为创建该节点。

## 导航

- [PLAN.md](PLAN.md)：范围与证据边界。
- [runtime-audit.json](runtime-audit.json)：结构化运行时证据。

## 证据边界

| 标签 | 本批含义 |
|---|---|
| `SOURCE_FACT` | 节点标题/三种尝试/参考图/提示词 placeholder/GVLM 3.1/积分 6、350x350 尺寸、双击生成流 |
| `CLONE_DECISION` | 尝试选择与提示词为本地草稿、卡片视觉近似、节点无真实生成服务 |
| `SOURCE_UNKNOWN` | 三种尝试点开后的源站子界面、参考图上传行为、生成结果形态 |

## 实施结果

- 新增 `src/components/nodes/ScriptGeneratorNode.tsx`；nodeTypes 注册
  `script-generator`；dimensions 350x350；default data `{ title: 脚本生成器 }`。
- `AddNodePanel` 脚本NEW → `onAddNode("script-generator")`（面板关闭，节点创建）。
- batch98 两处断言随采样迁移（脚本NEW 创建节点、流程共 +2 节点）。

## 完成定义

1. `verify-liblib-batch116.py` 15 checks、`0/0/0` diagnostics 通过。
2. 相邻 `verify-liblib-batch98.py`（迁移后）通过。
3. `npm run check`、`npm run docs:check` 通过。
4. master commit/push。

通过结果只证明 clone-owned 节点卡片合同；真实生成/子界面仍是
`SOURCE_UNKNOWN`。
