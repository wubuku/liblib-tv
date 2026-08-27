# Batch 64 计划：Asset Drawer Host-Resize Anchor Preservation

> 状态：`PLAN_RECORDED` / `IMPLEMENTATION_NOT_STARTED`。
>
> 计划基线：`8acb13a`，Batch 63 已 commit/push，工作区干净。
>
> 日期：2026-08-27。
>
> 风险等级：中。只改变 drawer layout transaction 的 viewport endpoint，不改变
> graph document 或节点视觉。

## 1. 价值与证据

| 候选 | 用户价值 | 证据成熟度 | 实施风险 | 本轮决策 |
|---|---:|---:|---:|---|
| Asset drawer 开/关保持 host-center flow anchor | 5 | 5 | 3 | **实施** |
| drawer X / Canvas dropdown 使用同一 owner path | 4 | 5 | 3 | **实施** |
| newest-operation/current-canvas/current-instance guard | 4 | 4 | 3 | **实施** |
| browser resize/orientation 通用 observer | 4 | 3 | 5 | 暂缓 |
| Agent drawer anchor preservation | 3 | 2 | 4 | 暂缓 |
| live/stable viewport phase 全量分离 | 5 | 4 | 5 | 独立后续批次 |
| source exact drawer animation/anchor | 4 | 1 | 4 | 保持 source gate |

正式合同 `§7.2` 已定义 clone correctness default：

```text
oldCenterFlow = clientToFlow(oldHost.center, oldLiveViewport)
newViewport.x = newHost.width / 2 - oldCenterFlow.x * zoom
newViewport.y = newHost.height / 2 - oldCenterFlow.y * zoom
```

Batch 63 已证明 drawer closed/open host 分别是 desktop `929x874` 与
`x=240,width=689,height=874`，并已建立 actual-host conversion helper。本批
不需要重新识别同一截图。

该策略是 conservative clone usability，不是 LibTV source fact。源站
`LIBTV-VGP-DQ-002` 仍需 disposable panel/viewport rect trace。

## 2. 当前 clone 事实

- Asset drawer 作为根 flex child 插入在 React Flow `main` 前，宽度固定 `240px`；
- 当前 controlled viewport 在 drawer 开合时保持原 `{x,y,zoom}`；
- React Flow host local origin 随 drawer 插入移动，宽度也改变；
- 因此既有节点 screen position 会跳动，旧 host center 下的 flow point不会保持；
- `BottomToolbar` 和 `AssetManagerPanel` 各自直接调用 `uiStore` toggle；
- Canvas context 通过 `toggleCanvasDropdown()` 的统一关闭态移除 drawer；
- page 已拥有 React Flow instance、actual host selector、controlled viewport 和
  per-canvas store viewport write。

## 3. 实施切片

### Slice A：纯 new-host viewport helper

扩展 `libtvViewportPlacement.ts`：

- 输入 captured flow anchor、new host dimensions、captured zoom；
- 输出使 flow anchor 位于 new host local center 的 target viewport；
- 提供 old-host/old-viewport/new-host 组合 plan 供 verifier；
- invalid host/anchor/zoom 返回 `null`；
- 不读取 DOM、不写 store、不进入 graph history。

### Slice B：page-owned layout transaction

在普通 LibTV page 增加具名 Asset layout command：

1. action 前从 actual host center 捕获 flow anchor；
2. 捕获 active canvas、React Flow instance、viewport 与 newest operation ID；
3. 执行现有 UI action；
4. 等待 drawer layout commit；
5. 重新量测 actual host；
6. 仅在 operation、canvas、instance 和 captured viewport仍 current 时写 target
   controlled viewport；
7. 同步 per-canvas viewport 与 zoom projection；
8. invalid/stale 时不覆盖较新的 viewport。

### Slice C：统一 drawer entry

- `BottomToolbar` 的 Asset toggle 由 page callback 驱动；
- `AssetManagerPanel` 的 X 使用同一路径；
- Canvas context 转入 dropdown 先捕获 anchor，再执行 dropdown action；
- 组件不持有 React Flow instance 或坐标公式。

### Slice D：focused verifier

新增 `scripts/verify-liblib-batch64.py`：

- pure identity、open、close、invalid cases；
- deterministic center node；
- desktop/mobile drawer open/close；
- toolbar toggle、drawer X、Canvas context 三个关闭路径；
- before/after node center 对各自 host center；
- expected viewport delta；
- graph/history/selection zero mutation；
- rapid/newer owner 或 canvas switch stale guard；
- drawer-open default add 继续通过；
- overflow 与 browser diagnostics。

## 4. 明确不做

- 不增加通用 `ResizeObserver`；
- 不监听所有 DOM/font/scrollbar resize；
- 不处理 Agent drawer、browser orientation 或 Storyboard；
- 不重写 `onViewportChange` 为 live/stable reducer；
- 不改变 `desktopViewport` / `compactViewport` bootstrap；
- 不增加动画、auto-pan、fitView 或 source-shaped easing；
- 不修改 FrameOS、Director、图片双浮层或 graph placement strategy；
- 不把 Open Canvas 实现写成 LibTV source behavior。

## 5. 候选文件边界

| 路径 | 职责 |
|---|---|
| `src/lib/libtvViewportPlacement.ts` | pure host-resize target viewport |
| `src/app/page.tsx` | current owner capture、layout action、viewport commit |
| `src/components/BottomToolbar.tsx` | 接收 page-owned Asset toggle |
| `src/components/AssetManagerPanel.tsx` | 接收 close / Canvas context callbacks |
| `scripts/verify-liblib-batch64.py` | focused runtime verifier |
| 本批目录 | 计划、DOM/截图台账、实施和 runtime audit |

## 6. 验收

Focused：

```bash
python3 scripts/verify-liblib-batch64.py
```

相邻：

```bash
python3 scripts/verify-liblib-batch17.py
python3 scripts/verify-liblib-batch18.py
python3 scripts/verify-liblib-batch19.py
python3 scripts/verify-liblib-batch60.py
python3 scripts/verify-liblib-batch61.py
python3 scripts/verify-liblib-batch62.py
python3 scripts/verify-liblib-batch63.py
npm run check
npm run docs:check
git diff --check
```

回归脚本覆盖写入的历史截图/runtime audit 在验证后恢复，不提交随机副产物。

## 7. 停止与 checkpoint

1. 本计划、证据边界和截图成本台账先 commit/push；
2. pure helper 与 page/component owner path 完成后建立 checkpoint；
3. focused verifier 和相邻回归通过后补实施记录；
4. 收口文档 commit/push，确认工作区干净；
5. 继续选择 `LIBTV-VR-020` 或 parity backlog 的下一批，不把本批扩成完整
   live/stable/host-epoch architecture。
