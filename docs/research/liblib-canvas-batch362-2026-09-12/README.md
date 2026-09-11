# Batch 362 — batch 6 定案：框选需 Shift（`VERIFIER_FIXED`）

> 状态：**唯一非绿的 batch 6 转绿**（三连跑全绿）——AGED_GATE
> 清算 **13/13 全部完成**。无产品代码变更。源站恢复探测：
> `RECOVERY: still-broken`。

## 根因与修复

React Flow v12 配置 `selectionOnDrag={false}` + `panOnDrag={[1]}`：
左键拖拽 = 平移，**框选需 Shift+拖拽**。batch 6 的 marquee 无
Shift → 无选择框 → "selection rectangle did not appear"。

修复：`select_with_marquee` 加 `keyboard.down("Shift")` /
`up("Shift")` 包裹拖拽。三连跑全绿。

注：AGENTS.md 的「Batch 6 marquee 历史化」注记基于旧归档；本轮
实证 Shift 语义下框选合同完全可测——该历史化注记可复核更新
（属文档层小改，本批先以台账记录）。

## AGED_GATE 清算终态（**13/13 完成**）

| 批次 | 验证器 | 类型 |
|---|---|---|
| 338 | 29 | 产品缺陷（菜单 Portal 化） |
| 346 | 39 | 时序抖动→轮询 |
| 347 | 40 | Chrome 147 duration hack + 阈值校准 |
| 348 | 41 | 读错层→authored 层迁移 |
| 349 | 46 | 命名合同漂移迁移 |
| 351 | 64 | 专项现代化（六子流程 × 320px） |
| 353 | 48 | schema 演进超集断言 |
| 354 | 49 | 双时序抖动（observer + settle 轮询） |
| 355 | 57 | 产品缺陷（TextNode 把手 id） |
| 361 | 44 | 现代化至当前纯拼接语义 |
| 362 | 6 | Shift 语义迁移 |
| 356 | 61 | store deselect + fit-view + 清理 |

## 后续候选

- 源站恢复后 BLOCKED_SOURCE 补采与 CLONE_DECISION 替换；
- AGENTS.md「Batch 6 marquee 历史化」注记的文档层更新；
- jimeng 路线对照巡检（待并行 WIP 稳定）。
