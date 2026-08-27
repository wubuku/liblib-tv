# Batch 60 计划：图片双浮层选择切换与 owner 一致性

> 状态：`COMPLETED`（实施、focused verifier、质量门禁和回归收口见
> [`IMPLEMENTATION.md`](IMPLEMENTATION.md)）。
>
> 建档：2026-08-26
> 领域：普通 LibTV 画布，selected image overlay interaction
> 目标：保护并完善“选中一个图片节点时，上工具条 + 下编辑面板作为一个
> owner 一起迁移”的 clone 行为，不重写已经通过的 source-shaped 几何公式。

## 1. 审计发现

已有合同已经覆盖：

- toolbar 与 selected node 共享 screen center；
- toolbar top gap 为 `10 + 24 * zoom`；
- editor panel bottom gap 为 `16 * zoom`；
- zoom/pan 后两层保持屏幕尺寸并跟随节点；
- 空白点击、active tool、删除和换画布的 owner cleanup。

本轮本地运行时发现一个未被专项保护的交互问题：

```text
selected image A
  -> A 的下方面板覆盖 image B 的节点中心
  -> 点击 B 的被覆盖区域
  -> 点击被 A 的 panel 消费，B 没有成为 selection
  -> A 的双浮层继续存在
```

这不是 source 几何公式错误，但会被用户感知为“点击图片后上下弹出层
位置乱了”，也使相邻节点之间的切换不可靠。

## 2. 价值排序

| 候选 | 价值 | 风险 | 决策 |
|---|---:|---:|---|
| 统一 selection -> 双浮层 owner 迁移回归 | 5 | 2 | 本批实施 |
| 改写 toolbar/panel 几何公式 | 2 | 4 | 不做，已有 source contract |
| 把 panel 提升为 page-level portal | 2 | 4 | 不做，会破坏节点锚定 |
| 通过 viewport clamp 避让相邻节点 | 2 | 4 | 不做，源站允许自然裁切 |
| 完善真实图片编辑保存 | 5 | 5 | fixture blocked，另批处理 |

## 3. 本批目标

1. 为图片双浮层建立明确的单一 active owner：
   - 最多一个 standard `ImageToolbar`；
   - 最多一个 standard `ImageEditPanel`；
   - 两者对应同一个 selected image node。
2. selection 迁移后，旧 node 的双浮层在同一 React commit 中卸载，新 node
   的双浮层挂载。
3. 避免 panel 的非交互背景阻止相邻节点选择；panel 内按钮、textarea 和
   控件仍必须可操作。
4. 保留 source-shaped panel overlap、自然裁切和 node-relative anchor。
5. 覆盖节点切换、pan、zoom、空白点击、active tool replacement 和
   desktop/mobile no-overflow。

## 4. 明确不做

- 不改变 `10 + 24 * zoom`、`16 * zoom`、`1092.5x49` 或 `660px` 合同；
- 不把节点浮层改成固定在浏览器中心的 portal；
- 不引入全局 overlay manager；
- 不改变普通 graph、history、selection transaction 的数据模型；
- 不推断源站在面板覆盖相邻节点时的 pointer hit-testing 细节；
- 不处理真实 annotate/element-edit save、rotate editor 或 provider。

## 5. 验收

### Runtime

- 任意可命中的第二个图片节点成为 selected owner 后，旧 toolbar/panel
  消失，新 toolbar/panel 出现；
- toolbar 和 panel 的 `data-owner-node-id` 与 selected node 一致；
- 标准态不出现两个 toolbar 或两个 panel；
- panel 可交互区域仍能输入 Prompt、点击生成和打开 AutoLink；
- panel 非交互空白区域不捕获 pointer，允许底层节点选择；
- active annotate/element-edit 仍替换标准双浮层，不出现第三层。

### Geometry

- 以同一 frame 读取 node、toolbar、panel rect；
- center、top gap、bottom gap 继续满足现有 contract；
- zoom/pan 后 owner 和几何不漂移；
- mobile 不出现 document/body 横向溢出。

### Evidence boundary

本批只形成 clone-owned interaction contract。现有 source evidence 继续支持
几何和层级；源站对重叠 panel 的 pointer hit-test 未直接取得，不写成
`SOURCE_FACT`。

## 6. 接力

- focused verifier：`scripts/verify-liblib-batch60.py`
- 实施记录：`IMPLEMENTATION.md`
- 截图台账：若 DOM/geometry 足够，则记录 `NO_NEW_SCREENSHOT_REQUIRED`
- 完成后更新 `docs/research/README.md`、`docs/index.md`、
  `VERIFICATION_LEDGER.md` 和 parity backlog。
