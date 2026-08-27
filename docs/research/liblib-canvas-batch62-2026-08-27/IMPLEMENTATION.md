# Batch 62 实施记录：Selection Command Snapshot 与单层 Escape

> 实施日期：2026-08-27  
> 计划基线：`258ff57`  
> 实施 checkpoint：`dba3aab`  
> focused verifier checkpoint：`8af9853`  
> 当前状态：`SCRIPT_RECORDED_PASS`

## 1. 实施范围

本批按计划只处理普通 LibTV 路由的 selection、keyboard context、foreground
surface 和 canvas focus correctness。没有修改 FrameOS、Director、Open Canvas
submodule、图片双浮层几何或 edge/Handle 视觉合同。

## 2. 代码变更

| 文件 | 结果 |
|---|---|
| `src/lib/libtvSelectionCommandContext.ts` | 新增 validated node/edge selection snapshot、stale/duplicate 净化、`none/node/edge/mixed` 分类、compatibility primary、editable/ARIA/IME predicate 和 blocking foreground surface resolver。 |
| `src/store/canvasStore.ts` | 提供 `getSelectionSnapshot()` 与 browser verifier capture；Delete、duplicate、group/ungroup 接受 captured node IDs，避免 command 执行过程中重新读取变化后的 selection。 |
| `src/store/uiStore.ts` | 新增 `closeTopForegroundSurface()`；一次只关闭一个 blocking surface，保留 graph selection。 |
| `src/app/page.tsx` | 按 active image owner、Director、editable/IME、blocking foreground、普通 canvas 的顺序分发键盘事件；第一层 Escape 只关闭一个 foreground surface，第二层才清 node/edge selection；pane click 同时清 node/edge selection并把焦点放回 canvas root。 |
| `scripts/verify-liblib-batch62.py` | 新增 focused Playwright verifier，覆盖 pure snapshot、command capture、foreground suspension、Escape/focus、editable/IME、pane cleanup、desktop/mobile 和 diagnostics。 |
| `docs/research/liblib-canvas-batch62-2026-08-27/runtime-audit.json` | 记录可重复的 focused runtime 结果。 |

## 3. 关键行为

### 3.1 Selection snapshot

- 只保留当前 active canvas 中仍存在的 node/edge ID；
- 去除 stale ID 与重复 ID；
- `mixed` 保留 node/edge 两类集合；
- compatibility primary 继续优先合法 `selectedNodeId`，再回退到最后一个合法
  node，最后才回退到 edge-only；
- mixed node+edge 的 universal primary policy 没有被本批擅自定义。

### 3.2 Command capture

Delete、duplicate、group 和 ungroup 在 page handler 中先捕获 snapshot 的
node IDs，再把 immutable target 传给 store command。验证中先把 node A 选中，
再把 selection 改成 node B，最后执行 A 的 captured delete；结果只删除 A，
且只产生一个 graph history entry。

### 3.3 Foreground surface

Shortcuts、Canvas dropdown、Add Node、Zoom、Share、Notification、User menu
和 active primary panel 被视为 blocking foreground surface。它们打开时：

- Delete、Backspace、Meta/Ctrl+D、G、Meta/Ctrl+Z、H、Alt+Shift+F、Space 和
  Tab 不得触发普通画布命令；
- 第一次 Escape 只关闭当前 top foreground surface，selection、graph 和
  history 保持不变；
- 第二次 Escape 才清除 node/edge selection，并把焦点放回
  `[data-libtv-canvas-focus-root]`。

Asset/Agent drawer 没有被 blanket 纳入该 resolver，因为它们是
target-scoped/layout-changing surface，仍需单独的 containment 证据。

### 3.4 Editable 与 IME

`input`、`textarea`、`select`、可编辑区域、ARIA textbox/searchbox/combobox
和 IME composition target 会跳过普通 canvas dispatcher，保留 native/editor
keyboard ownership。

## 4. 验证结果

执行：

```bash
python3 scripts/verify-liblib-batch62.py
```

结果：`PASS`。详细结果见
[`runtime-audit.json`](runtime-audit.json)。

覆盖内容：

- node-only、edge-only、mixed selection；
- stale/duplicate selection normalization；
- captured command target；
- 8 类 blocking foreground surface；
- 8 类被阻断的 canvas command；
- first Escape / second Escape；
- canvas focus root；
- input、textarea、select、contenteditable、ARIA textbox/searchbox/combobox、
  IME；
- pane click node+edge cleanup；
- desktop `929x874` 与 mobile `390x844`；
- console、page error、request failure 和 overflow。

相邻回归保持通过：

```text
Batch 6, 11, 50, 53, 54, 60, 61, 62
```

项目门禁：

- `npm run check`：通过；
- `npm run docs:check`：通过；
- `git diff --check`：通过。

## 5. 截图与证据成本

本批没有新的视觉几何变化，按
[`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md) 的登记结果不重复识别既有
截图。验证使用 DOM state、activeElement、graph/history 和 diagnostics；没有
把 clone runtime 结果写成 LibTV 源站事实。

## 6. 未完成与边界

以下事项继续保持 `SOURCE_UNKNOWN`、runtime partial 或后续设计队列：

- universal mixed node+edge primary；
- mixed edge delete/copy/group；
- modal focus trap、roving focus 和 opener 精确恢复；
- LibTV 源站 exact modal/Escape/focus policy；
- Asset/Agent target-scoped keyboard containment；
- source-exact Canvas dropdown Escape compound behavior。

因此本批是 clone-owned `SCRIPT_RECORDED_PASS`，不是完整的
`LIBTV-VR-019` source parity pass。

## 7. 保护性 checkpoint

本批分三段保护：

1. `01ffaba`：计划、证据边界和截图台账；
2. `dba3aab`：helper、store、UI 和 page 实施；
3. `8af9853`：focused verifier 与 runtime audit。

本收口提交补齐实施记录、稳定治理索引和 Batch 62 状态。提交后工作区应恢复
干净，并以 Batch 63 的 actual React Flow host placement 作为下一批入口。
