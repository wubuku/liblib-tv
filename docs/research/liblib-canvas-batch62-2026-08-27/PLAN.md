# Batch 62 计划：Selection Command Snapshot 与单层 Escape

> 状态：`PLAN_RECORDED` / `IMPLEMENTATION_NOT_STARTED`。
>
> 计划基线：`258ff57`，`master == origin/master`，工作区在建档前干净。
>
> 日期：2026-08-27。
>
> 风险等级：中。无预期视觉变化，但触及普通画布 keyboard、pane click、
> foreground panel 与 selection command ingress。

## 1. 候选排序

| 候选 | 用户价值 | 证据成熟度 | 实施风险 | 本轮决策 |
|---|---:|---:|---:|---|
| command selection snapshot | 4 | 5 | 2 | **实施** |
| editable/IME guard | 4 | 5 | 2 | **实施** |
| foreground shortcut suspension | 5 | 4 | 3 | **实施有界 surface 集合** |
| one-Escape + canvas focus fallback | 5 | 4 | 3 | **实施** |
| universal mixed node/edge primary | 4 | 2 | 4 | 暂缓，源站 policy 未知 |
| modal focus trap/roving focus | 4 | 2 | 5 | 暂缓，不引入 modal framework |
| mixed node+edge delete | 4 | 2 | 5 | 暂缓，依赖 delete planner/source fixture |

本批优先选择不会改变 graph schema、视觉皮肤或源站未证实行为的 correctness
slice。它为后续 primary、focus return、delete/copy 和 editor gating 提供输入
边界，但不宣称完成整个 `VR-019`。

## 2. 当前事实

### 2.1 `CLONE_FACT`

- Batch 61 已有 `selectedNodeIds/selectedNodeId/selectedEdgeIds`，selection 不进
  semantic graph/history。
- Delete、duplicate、group/ungroup 在 page handler 判断 selection 后，store
  action 再次读取“当前 selection”，没有显式 command input snapshot。
- page editable guard 只覆盖 input、textarea 与两类 contenteditable。
- page Escape 同时清 selection 和 `closeAllPanels()`；Canvas dropdown 另有
  document Escape listener，存在一键多层处理风险。
- Shortcuts、Add Node、Canvas dropdown、Zoom 和 primary panel 打开时，普通
  page Delete/undo/duplicate/group/viewport shortcuts 仍可继续运行。
- `<main>` 没有明确 canvas focus root；pane click 只清 node selection。

### 2.2 `RECORDED_RUNTIME`

- Batch 50：Director 完整隔离普通 page dispatcher。
- Batch 53/54：active image tool capture owner 消费 Escape/删除/历史等冲突键。
- Batch 60：pane click 清选后图片双浮层卸载。
- Batch 61：node/edge framework selection 由同一 routing ingress 提交，真实
  marquee、edge select、drag/delete 回归通过。

### 2.3 `SOURCE_UNKNOWN`

- 源站 mixed node+edge selection 的 primary 和 node editor gate；
- Character/History/Shortcuts 的 initial focus、Tab trap 与 close return；
- Canvas dropdown Escape 是否同时清 graph selection；
- foreground drawer 外部 canvas 快捷键是否继续有效。

本批采用合同中明确标注的 clone correctness floor，不将其升级为
`SOURCE_FACT`。

## 3. 实施切片

### Slice A：validated command selection snapshot

新增纯 helper，输出：

```text
canvasId
nodeIds
edgeIds
kind: none | node | edge | mixed
compatibility primary:
  valid selectedNodeId
  -> last valid selected node
  -> edge-only last valid edge
  -> null
```

- 输入中的 stale/duplicate ID 被过滤；
- snapshot 为新数组，不暴露 store mutable collection；
- mixed universal primary 不在本批定义；
- page Delete/duplicate/group/ungroup 捕获一次 snapshot，并把 node IDs 显式
  传给既有 named command；command 不在执行中重读 selection。

### Slice B：editable、ARIA 与 IME boundary

新增可测试 predicate，至少覆盖：

- input、textarea、select；
- contenteditable true/plaintext-only；
- role textbox/searchbox/combobox；
- `KeyboardEvent.isComposing`。

编辑或 IME owner 下，普通画布 Delete、Tab、Space、undo/redo、duplicate、
group、tool 与 viewport shortcuts 全部 pass，不改变 graph/selection/UI。

### Slice C：foreground command suspension 与 one-Escape

建立最小 foreground surface resolver：

- blocking surface：Shortcuts、Add Node、Canvas dropdown、Zoom、Share、
  Notification、User menu、`activePrimaryPanel`；
- route/local exclusive：Director 与三类 active image surface 继续沿用现有
  owner，不迁入新全局 manager；
- target-scoped Asset/Agent drawer 不做 blanket suspension，留待 containment
  marker 后续 slice。

Escape precedence：

```text
active image owner
  -> one blocking foreground surface
  -> no surface: clear node+edge selection
  -> focus current canvas root
  -> otherwise pass
```

一个 Escape 只改变一层。关闭 foreground surface 时保留 graph selection；
第二个 Escape 才允许清 selection。

### Slice D：canvas focus root

- 为普通 workbench host 增加不可进入正常 Tab 顺序的 focus root；
- pane click 清 node/edge selection，并把 focus 放到 current canvas root；
- 无 foreground 的 Escape 清选后使用同一 fallback；
- 不新增可见 focus ring，不修改节点 selected ring；
- Storyboard、FrameOS 与 Director 不共享该 root。

### Slice E：focused verifier

新增 `scripts/verify-liblib-batch62.py`，输出 `runtime-audit.json`，覆盖：

- pure snapshot duplicate/stale normalization；
- node-only、edge-only、mixed snapshot；
- page commands 使用 captured node IDs；
- input/textarea/select/contenteditable/ARIA/IME pass；
- Shortcuts/Add Node/Canvas dropdown 打开时 Delete/duplicate/group/undo/Tab/
  Space 不改变 graph/history/selection；
- 第一 Escape 只关闭 surface并保留 selection；
- 第二 Escape 清 node/edge selection并聚焦 canvas root；
- pane click 的 node+edge cleanup/focus；
- active image 与 Director 相邻隔离不回归；
- desktop `929x874`、mobile `390x844` overflow 和 diagnostics。

## 4. 明确不做

- 不实现 universal cross-kind primary ordering；
- 不实现 selected edge 删除、mixed copy/group 或 relation-aware delete；
- 不改变图片 mixed-selection editor visibility；
- 不引入 Radix、Base UI modal、focus-trap 或全局 context provider；
- 不修改 FrameOS、Director store/R3F、Open Canvas submodule；
- 不改变 Handle plus、edge pulse/glow、图片双浮层几何；
- 不新增源站未证实的快捷键、toast、focus ring 或动画；
- 不重新识别既有截图。

## 5. 预期文件

| 路径 | 职责 |
|---|---|
| `src/lib/libtvSelectionCommandContext.ts` | snapshot、editable/IME 与 foreground resolver |
| `src/store/canvasStore.ts` | snapshot getter；named command 接收 captured node IDs |
| `src/store/uiStore.ts` | close-one foreground action |
| `src/app/page.tsx` | keyboard precedence、one-Escape、pane/focus root |
| `scripts/verify-liblib-batch62.py` | focused Playwright verifier |
| 本批目录 | 计划、实施、runtime audit、截图成本台账 |

## 6. 验收与回归

Focused：

```bash
python3 scripts/verify-liblib-batch62.py
```

相邻：

```bash
python3 scripts/verify-liblib-batch6.py
python3 scripts/verify-liblib-batch11.py
python3 scripts/verify-liblib-batch50.py
python3 scripts/verify-liblib-batch53.py
python3 scripts/verify-liblib-batch54.py
python3 scripts/verify-liblib-batch60.py
python3 scripts/verify-liblib-batch61.py
npm run check
npm run docs:check
git diff --check
```

Batch 9 的旧 toolbar 断言继续按历史 mismatch 处理，不纳入本批修绿目标。

## 7. Checkpoint

1. 计划、证据边界和截图成本落档并 commit/push；
2. pure helper + store/page/UI 实施后 commit/push；
3. focused verifier、跨批回归、治理文档和实施结果收口后 commit/push；
4. 工作区恢复干净后，按 parity backlog 重新排序下一批。

