# Batch 368 — jimeng 后续对照巡检（`REVIEW_RECORDED`）

> 状态：jimeng 路线（batch 8 态，14 组件）巡检完成——隔离合规、
> batch 1 验证器绿、typecheck 0 错误。liblib.tv 恢复重测：
> `RECOVERY: still-broken` 维持。无代码变更。

## 巡检结论

1. **隔离合规**（含新增组件 JimengContextMenu/GenPanel/HelpMenu/
   InferPanel/InsertMenu/NodeToolbar/RepaintPanel/VideoEditMode 等
   14 组件）：零引用 canvasStore/frameosStore——三 store 独立约束
   持续遵守；
2. **batch 1 验证器绿**：`verify-jimeng-batch1.py` 通过；
3. **typecheck 0 错误**：全工作区（含 jimeng）编译干净——batch 347
   记录的阻塞已完全解除；
4. **观察**：jimeng 的 batch 2-8（工具栏/生成面板/局部重拍/视频
   编辑/缩放菜单/帮助菜单/提示词反推）暂无验证器覆盖（仅 batch 1
   有）——验证器覆盖缺口由并行路线自行排期。

## 源站状态

`RECOVERY: still-broken` 维持（PAR-005 §10 在案；复测脚本
`scripts/probe-source-recovery.py` 已入库）。

## 后续候选

- 源站恢复后：BLOCKED_SOURCE 补采与 CLONE_DECISION 替换；
- jimeng batch 2-8 的验证器覆盖（由并行路线排期）；
- 相机运动预设 append 语义的产品裁决跟进。
