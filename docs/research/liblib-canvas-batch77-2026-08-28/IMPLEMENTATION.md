# Batch 77 实施与验证记录

> 日期：2026-08-28。
>
> 本记录同时收口两条高价值修复：Director `TransformControls` 真实拖动回归，
> 以及普通 LibTV 画布导航与已登录源站的 runtime parity。

## 1. 实施切片

### A. Director TransformControls

- object、character group 和 motion-path control 改为 Drei explicit
  `object={transformTarget}` attachment；
- commit 从同一个真实 `Group` 读取 preview transform；
- gesture begin 只在命令成功时激活；
- `pointerup`、Drei `onMouseUp`、`pointercancel` 和 unmount cleanup 不重复提交；
- pointer cancel 会恢复 authoring transform，成功 drag 最多产生一条 Director history。
- 无位移 drag 会恢复 Three.js object 并结束 gesture，但不会调用
  `recordObjectKeyframe`，因此不会留下 history residue。

### B. 普通画布导航

- `panOnScrollSpeed={1}` 对齐源站 wheel 平移比例；
- `panOnDrag={effectivePan ? [0, 1] : [1]}`：中键在所有工具模式下平移，
  `H`/`Space` 额外允许左键；
- `selectionOnDrag={false}`：移除当前源站未核实且与源站 runtime 冲突的空白框选；
- 保留 `V/H/Space` 状态机、输入焦点 guard、blur/visibility cleanup 和
  `panActivationKeyCode={null}`。

## 2. 代码变更

| 文件 | 变更 |
|---|---|
| [`src/components/director/DirectorViewport.tsx`](../../../src/components/director/DirectorViewport.tsx) | explicit object attachment、gesture commit/cancel cleanup |
| [`src/app/page.tsx`](../../../src/app/page.tsx) | source-aligned React Flow pan/scroll/selection policy |
| [`docs/CANVAS_NAVIGATION.md`](../../CANVAS_NAVIGATION.md) | 开发者/agent 易发现的普通画布操作手册 |
| [`SOURCE_NAVIGATION_AUDIT_2026-08-28.md`](SOURCE_NAVIGATION_AUDIT_2026-08-28.md) | 登录态源站只读手势证据与 parity 决策 |

## 3. 运行验证

### Navigation runtime

已在 source 和 clone 使用相同的 `(1040,650)` 空白点及 `(90,50)` drag delta：

- wheel vertical/horizontal：clone 与 source 均为 1:1 viewport pan；
- `Command`/`Control` wheel：均为 pointer-centered zoom；
- default `V` blank left drag：均 no-op，无 selection rectangle；
- default middle drag：均平移；
- `Space` / `H` left drag：均平移；
- `V`/`H` persistent state 和 `Space` temporary state 均可恢复。

### Director runtime

此前临时 Playwright 验证已经真实命中 mug gizmo：

- mug position 从 `[0.25, 1.08, 0.05]` 改为约 `[1.353, 1.08, 0.05]`；
- authored/runtime position 同步；
- Director history `0 -> 1`；
- `activeGesture` 清空；
- last command 为 `GESTURE_COMMIT / COMMITTED / entries=1`。

正式 verifier `scripts/verify-liblib-batch77.py` 已覆盖上述真实 pointer drag，而
不是只调用 store action。最终结构化结果写入
[`runtime-audit.json`](runtime-audit.json)，状态为 `SCRIPT_RECORDED_PASS`，且
`errors` 与 `screenshots` 均为空。

运行命令：

```bash
LIBLIB_BASE_URL=http://localhost:3001 \
  python3 scripts/verify-liblib-batch77.py
```

专项 verifier 覆盖：

- desktop 普通纵/横向 wheel 平移，默认中键平移；
- `Command`/`Control` wheel 指针中心缩放；
- `V` 空白拖动 no-op、`H` 持久抓手、`Space` 临时抓手及 cleanup；
- mobile `390x844` 无横向溢出；
- mug gizmo 真实 pointer drag、`authoredObjects`/runtime projection 同步、
  一条 Director history、undo/redo、zero-distance drag 零 history；
- 普通 graph nodes/edges/history 与 Director 操作隔离；
- static explicit attachment、pointerup/pointercancel cleanup；
- console、page、request failed 诊断为空。

## 4.1 跨批回归补充

同一轮还串行通过了 Batch 18、35、49、59、67、68、69、70、71、72、73、74、
75、76。Batch 67-76 的 Python verifier 会先运行对应的 `.mjs` pure verifier。

Batch 18 是历史脚本，本轮只做了两项测试入口兼容修复：

- `URL` 支持 `LIBLIB_BASE_URL`，便于复用现有 `3001` dev server；
- zoom menu 断言等待 React overlay 进入 visible，避免状态提交后的即时读取竞争。

没有放宽 Batch 18 的 zoom action、fit view、overlay cleanup、asset mutual exclusion
或 mobile overflow 断言。

## 4. 文档和证据边界

- `docs/CANVAS_NAVIGATION.md` 是当前操作入口；
- Batch 6 的“普通画布空白框选”是早期 clone-only 合同，已由本批 source runtime
  audit supersede；Batch 6 历史实现仍保留用于追溯；
- 普通画布手势 parity 不等于 LibTV 内部使用 React Flow 的 source proof；
- 不把 Director R3F 物体移动写成普通画布平移；
- 不把源站快捷键面板的 plain `0` 文案当成运行时 fit handler；
- 没有重复识别截图；本批证据以 DOM/computed style 和 pointer/wheel runtime 为主。

## 5. 待完成门禁

- [x] 更新/新增正式 `scripts/verify-liblib-batch77.py`；
- [x] 运行 Batch 77 navigation + Director pointer verifier；
- [x] 运行 Batch 35、49、59、67-76 及受影响的 Batch 18/69-71；
- [x] 更新当前导航合同、Big Picture、Behaviors 和 verifier ledger；
- [x] `npm run docs:check`、`git diff --check`、`npm run check`；
- [x] commit/push 并确认工作区干净。

## 6. 交接边界

- `docs/CANVAS_NAVIGATION.md` 是普通 LibTV 画布拖动、缩放、鼠标和 macOS
  触摸板操作的首要入口；
- 源站只读导航审计证明了行为结果，不证明源站内部使用 React Flow，也不证明
  Director exact DOM/CSS；
- 本批没有重新识别截图，避免重复消耗已有 screenshot analysis 预算；
- Batch 6 的空白框选属于历史 clone-only 合同，当前行为以 Batch 77 源站运行态
  审计和 `selectionOnDrag={false}` 为准；
- Director 的 R3F TransformControls 与普通 React Flow viewport/navigation 是
  两个独立的输入域和 history owner。
