# Batch 363 — AGENTS.md marquee 注记更新（`DOC_RECORDED`）

> 状态：batch 362 记录的文档层复核项完成——AGENTS.md「Batch 6
> marquee 历史化」注记更新为 Shift 语义事实；CANVAS_NAVIGATION.md
> 补框选行与 macOS 鼠标段修正；sync-agent-rules 衍生配置同步。
> 无产品代码变更。源站恢复探测：`RECOVERY: still-broken`。

## 文档变更

1. **AGENTS.md** 硬约束段：原「Batch 6 marquee is historical」
   更新为「Blank-drag stays no-op; marquee is Shift+drag
   (v12 selectionOnDrag=false), verifier-covered since Batch 362
   (Batch 6 un-aged)」——保留 blank-drag no-op 与 Batch 77 证据
   管辖（wheel/middle/Space/H/V 均不变）；
2. **CANVAS_NAVIGATION.md**：
   - 交互表新增行「框选（marquee）| Shift + 左键拖动空白处 |
     v12 selectionOnDrag=false 语义，Batch 362 验证器覆盖」；
   - macOS 鼠标段修正为「无修饰键拖动空白处 = no-op；
     Shift + 拖动 = 框选」；
3. 同步衍生配置（.amazonq/.clinerules/.continue/.github）经
   `scripts/sync-agent-rules.sh` 再生成。

## 验收

- batch 6 复跑全绿（marquee Shift 语义合同）；
- docs check 通过（922 Markdown）；
- 提交按显式路径暂存（DEC-018：不扫入并行 jimeng WIP）。

## 后续候选

- 源站恢复后 BLOCKED_SOURCE 补采与 CLONE_DECISION 替换；
- jimeng 路线对照巡检（待并行 WIP 稳定）；
- 相机运动预设 append 语义的产品裁决（batch 352 记录）。
