# Batch 102 Plan：资产管理抽屉对齐 2026-09-05 源站

> 状态：`PLANNED`
>
> 建档日期：2026-09-05。
>
> 上一批 checkpoint：Batch 101（`batch/101-history-panel-source`）。
>
> 源站证据：[`../liblib-live-2026-09-05/README.md`](../liblib-live-2026-09-05/README.md) §7（资产左抽屉 dialog 结构，含与 Agent 抽屉双开）。

## 1. 范围

### 包含

1. **工具行补控件**（`SOURCE_FACT` 按钮 + `CLONE_DECISION` 行为）：`所有评级`、`展示设置` 两个按钮；点击给出诚实本地 hint「本地原型：…未接入」，不伪造菜单语义。
2. **空态文案**（`SOURCE_FACT`）：canvas tab 空态 `当前画布暂无节点` → `画布暂无节点`。
3. **底部行**（`SOURCE_FACT`）：计数旁新增 `收起节点侧栏` 按钮（调用既有 onClose）。
4. **命名对齐**（`SOURCE_FACT`）：搜索 aria/placeholder → `搜索节点`；筛选按钮 aria → `筛选：{label}`。
5. 保留：项目/画布上下文行、画布/资产双 tab、排序、筛选菜单、行树、`共 N 节点/项资产`。

### 不包含

- 评级/展示设置的真实菜单与语义（源站未采样）；
- 资产 tab 非空态源站样式；抽屉宽度/双开几何再校准（clone 已 240px 双开可用）。

## 2. 证据边界

| 标签 | 内容 |
|---|---|
| `SOURCE_FACT` | 所有评级/展示设置按钮存在、`画布暂无节点`、`收起节点侧栏`、`搜索节点`、`筛选：全部` |
| `CLONE_DECISION` | 两按钮的本地 hint、控件排布 |
| `SOURCE_UNKNOWN` | 评级/展示设置菜单内容、资产 tab 空态、双开精确几何 |

## 3. 影响面与兼容

- 仅 `src/components/AssetManagerPanel.tsx`；
- batch12 断言 tab/list/item 选择器不受影响（复跑确认）；batch64/65 抽屉锚点回归复跑。

## 4. 验证

- 新增 `scripts/verify-liblib-batch102.py`：desktop `1440x900`，断言双 tab、搜索/筛选 aria、评级/展示设置按钮与本地 hint、demo 画布 `共 10 节点`、空画布 `画布暂无节点`、收起按钮关闭抽屉、零诊断。
- 复跑 `verify-liblib-batch12.py`、`verify-liblib-batch64.py`、`verify-liblib-batch65.py`。
- `npm run check`、`npm run docs:check`。

## 5. 完成定义

1. 抽屉控件集合与源站 2026-09-05 快照一致（除标注项）。
2. 相邻 verifier 与全量检查通过；特性分支 commit/push。
