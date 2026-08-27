# Batch 63 计划：Actual React Flow Host 中心定位

> 状态：`PLAN_RECORDED` / `IMPLEMENTATION_NOT_STARTED`。
>
> 计划基线：`d893061`，Batch 62 已 commit/push，工作区干净。
>
> 日期：2026-08-27。
>
> 风险等级：中。目标是 graph placement correctness；不预期改变节点视觉，但
> 资产抽屉打开后会改变新节点的屏幕落点。

## 1. 价值与证据

| 候选 | 用户价值 | 证据成熟度 | 实施风险 | 本轮决策 |
|---|---:|---:|---:|---|
| Add Node 使用 actual host center | 5 | 5 | 3 | **实施** |
| Character Library 使用 actual host center | 4 | 4 | 3 | **实施** |
| derived/duplicate/organize 统一 placement | 4 | 3 | 5 | 暂缓 |
| live/stable viewport 分离 | 4 | 3 | 5 | 暂缓 |
| host resize anchor preservation | 4 | 2 | 5 | 暂缓 |
| source exact add auto-pan | 4 | 2 | 4 | 保持 source gate |

固定审计已经证明当前 clone 的 `getViewportCenterPosition()` 使用
`window.innerWidth/innerHeight`，而普通 React Flow host 会被 Asset drawer
改变宽度和屏幕位置。正式空间合同将 `HOST_CENTER` 定义为：

```text
actual React Flow host center (CLIENT)
  -> current React Flow screenToFlowPosition
  -> FLOW_WORLD center
  -> node top-left using declared graph dimensions
```

这足以授权本批的 clone correctness 修复，但不能证明 LibTV 原站 exact add
anchor、auto-pan 或 selection policy。

## 2. 当前 clone 事实

- `canvasStore.addNode()` 在 store 内读取 `window.innerWidth/innerHeight`；
- `page.tsx` 已持有当前 React Flow instance 和 controlled viewport；
- `screenToFlowPosition()` 是 React Flow 12.11.1 的 actual host conversion API；
- Add Node Panel 和 Character Library 都直接调用 `canvasStore.addNode()`；
- Add Node 的 graph dimensions 由 store 内部 `getDefaultNodeDimensions()` 定义；
- Character Library 的图片 data dimensions 与 graph frame dimensions 不同，不能由
  caller 猜测 top-left；
- derived、duplicate、organize 等入口具有自己的 placement strategy，不应被本批
  的 default host center 改写。

## 3. 实施切片

### Slice A：纯 host-center placement helper

新增一个小型纯 helper，输入：

- host `DOMRect` 的 finite `left/top/width/height`；
- current React Flow `screenToFlowPosition` 转换结果；
- node graph dimensions。

输出：

- `CLIENT` host center；
- `FLOW_WORLD` node center；
- `FLOW_WORLD` top-left；
- invalid host/dimensions 时的 `null`。

它不读取 `window`，不写 graph，不负责 screen clamp。

### Slice B：store 保留 dimensions authority

新增 named action `addNodeAtFlowCenter(type, center, data?)`：

- 在 store 内读取 type 的 graph dimensions；
- 将 flow center 转成 node top-left；
- 复用既有 `addNodeAtPosition` 的 graph/history/selection semantics；
- 不改变既有 `addNode()` 的兼容行为，直到所有 default UI caller 迁移完成；
- derived/duplicate/organize 继续使用原策略。

### Slice C：page 作为 actual-host conversion owner

在普通 LibTV page：

- 从当前 React Flow instance 获取 `screenToFlowPosition`；
- 从实际 `.react-flow` host 获取 `getBoundingClientRect()`；
- 计算 host center；
- 转换为 flow center；
- 调用 `addNodeAtFlowCenter`；
- host 不可用或转换异常时不写 graph，保留明确的 zero-mutation guard。

通过 callback 将该入口传给 Add Node Panel 和 Character Library。不得让这些
组件重新读取 browser window dimensions。

### Slice D：focused runtime verifier

新增 `scripts/verify-liblib-batch63.py`，在 deterministic local page 中覆盖：

- pure helper identity/offset/invalid cases；
- Add Node 创建 text/image/video；
- Character Library 创建 image；
- asset drawer closed/open 的 actual host rect；
- host center与新节点 screen center误差；
- current selection、one history、graph count；
- desktop `929x874`、mobile `390x844`；
- no overflow、console/page/request diagnostics；
- existing default `addNode()` compatibility remains callable for non-UI paths。

截图策略：如果节点落点变化只体现为 graph position，不新增截图；若资产抽屉
打开后出现已有节点/浮层视觉回归，先记录最小必要截图再处理。

## 4. 明确不做

- 不把 `window.innerWidth/innerHeight` 从所有 store helper 中一次性删除；
- 不修改 derived outputs、duplicate delta、organize viewport、image overlay 公式；
- 不引入 Open Canvas 的菜单尺寸、offset、zoom bounds、drop 或 persistence；
- 不实现 live/stable viewport、host epoch、canvas generation 或 gesture cancel；
- 不修改 FrameOS 或 Director；
- 不重新识别已有源站截图；
- 不把 clone runtime pass 写成 LibTV source fact。

## 5. 候选文件边界

| 路径 | 职责 |
|---|---|
| `src/lib/libtvViewportPlacement.ts` | pure host-center placement result |
| `src/store/canvasStore.ts` | graph dimensions authority与 named flow-center add |
| `src/app/page.tsx` | actual React Flow host measurement/conversion |
| `src/components/LeftSidebar.tsx` | 传递 default add callback |
| `src/components/AddNodePanel.tsx` | 使用 page-owned default add callback |
| `src/components/CharacterLibraryPanel.tsx` | 使用 page-owned default add callback |
| `scripts/verify-liblib-batch63.py` | focused runtime verifier |
| 本批目录 | 计划、截图台账、实施和 runtime audit |

## 6. 验收

Focused：

```bash
python3 scripts/verify-liblib-batch63.py
```

相邻：

```bash
python3 scripts/verify-liblib-batch15.py
python3 scripts/verify-liblib-batch17.py
python3 scripts/verify-liblib-batch46.py
python3 scripts/verify-liblib-batch59.py
python3 scripts/verify-liblib-batch60.py
python3 scripts/verify-liblib-batch61.py
python3 scripts/verify-liblib-batch62.py
npm run check
npm run docs:check
git diff --check
```

Batch 9 的旧 toolbar 断言继续按历史 mismatch 处理，不纳入本批修绿目标。

## 7. 停止与 checkpoint

1. 本计划、证据边界和截图成本台账先 commit/push；
2. pure helper、store/page/component callback 实施后建立 checkpoint；
3. focused verifier 与必要回归通过后补实施台账；
4. 最终 commit/push 并确认工作区干净；
5. 再按 parity backlog 选择下一批，不把本批扩大为完整 `LIBTV-VR-020`。
