# Batch 111：角色库模态几何与详情标签对齐 2026-09-05 补采样

> 状态：`SCRIPT_RECORDED_PASS`
>
> 建档日期：2026-09-05。
>
> 上一批 checkpoint：Batch 110（`batch/110-aged-gate-deprecation`）。

按 2026-09-05 补采样的精测几何与双角色标签，把角色库模态从 `793x710`
对齐到实测 `1304x731 @ (68,84)`，详情区按 33px 内边距 / 四图
`226:226:226:536`（h301）重排；标签改为两个已采样角色的精确映射
（甜妹→女主…温柔、温柔熟男→男主…温柔），未采样角色保留修正后的启发式
（`男主/女主` 前缀）；关闭按钮 aria 对齐源站 `close`。

## 导航

- [PLAN.md](PLAN.md)：采样事实、范围与证据边界。
- [runtime-audit.json](runtime-audit.json)：结构化运行时证据。

## 证据边界

| 标签 | 本批含义 |
|---|---|
| `SOURCE_FACT` | 模态壳 1304x731@68、内边距/四图几何、图标签、说明模板、两角色标签、close aria |
| `CLONE_DECISION` | clamp 策略、未采样角色启发式 |
| `SOURCE_UNKNOWN` | 其余角色标签、其他视口几何、卡片条精确几何 |

## 完成定义

1. `verify-liblib-batch111.py` 19 checks、`0/0/0` diagnostics 通过。
2. 相邻 batch11（断言迁移后）、batch106 通过。
3. `npm run check`、`npm run docs:check` 通过。
4. 特性分支 commit/push。

通过结果只证明 clone-owned 角色库模态在 1440x900 单视口的展示合同；
其余角色标签与多视口几何仍是 `SOURCE_UNKNOWN`。
