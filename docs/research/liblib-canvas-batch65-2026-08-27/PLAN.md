# Batch 65 计划：Responsive Viewport Bootstrap Ownership

> 状态：`PLAN_RECORDED` / `IMPLEMENTATION_NOT_STARTED`。
>
> 计划基线：`cf8da51`，Batch 64 已 commit/push，工作区干净。
>
> 日期：2026-08-27。
>
> 风险等级：中。改变普通 LibTV viewport owner/reconciliation，不改变 graph
> document、节点视觉或 source-backed overlay 公式。

## 1. 价值排序

| 候选 | 用户价值 | 证据成熟度 | 实施风险 | 本轮决策 |
|---|---:|---:|---:|---|
| demo bootstrap 不覆盖 user-owned viewport | 5 | 5 | 3 | **实施** |
| active-canvas switch 恢复 target stored viewport | 5 | 5 | 3 | **实施** |
| stale old-instance viewport callback zero mutation | 4 | 5 | 3 | **实施** |
| browser resize 保持 old-host center flow anchor | 5 | 4 | 4 | 暂缓独立批次 |
| pan/zoom `LIVE/STABLE` phase split | 5 | 5 | 5 | 暂缓独立批次 |
| generic host epoch / `ResizeObserver` | 4 | 4 | 5 | 暂缓 |

`LIBTV-GC-081` 已定义 bootstrap guard，`LIBTV-GI-047/063` 已明确 target
canvas stored viewport 与 bootstrap 的权威边界。当前代码缺口可由静态代码和本地
确定性 browser fixture 证明，不需要重新识别源站截图。

## 2. 当前 Clone 事实

当前 `page.tsx`：

1. `flowViewport` 初始化时为 `canvas-2` 选择 desktop/compact preset；
2. responsive effect 在 mount、`activeCanvasId` 改变和 media-query change 时再次
   为 `canvas-2` 选择固定 preset；
3. effect 同时把 preset 写回 `CanvasData.viewport`；
4. 因此用户 viewport 会在跨 breakpoint 或切回 `canvas-2` 时丢失；
5. `onViewportChange` 直接写 page state、当前 active canvas store viewport 和
   zoom projection，没有验证 callback 的 captured canvas owner。

这是 clone correctness 缺口，不是 LibTV source 行为结论。

## 3. 实施切片

### Slice A：纯 responsive projection plan

扩展 `libtvViewportPlacement.ts`：

- 声明 `BOOTSTRAP` / `STABLE` page-session ownership；
- 输入 stored viewport、当前 breakpoint preset 和 owner；
- bootstrap owner 返回 preset + store write；
- stable owner返回 stored viewport + zero store rewrite；
- invalid viewport/zoom 返回 `null`；
- 暴露 browser verifier helper，不读 DOM、不写 store。

### Slice B：page-owned per-canvas owner ledger

在普通 LibTV page：

- `canvas-2` 首次 owner 为 `BOOTSTRAP`，其他 canvas 为 `STABLE`；
- accepted viewport event、zoom/fit/organize/restore 或 Asset layout commit 将当前
  canvas 标记为 `STABLE`；
- active canvas effect 从 target canvas stored viewport 恢复；
- media-query change 只有 owner 仍为 `BOOTSTRAP` 时才应用对应 preset；
- stable owner 跨 breakpoint 保留 stored viewport，不重新写 preset；
- owner ledger 是 page-session UI authority，不进入 graph history/document。

### Slice C：viewport callback owner guard

- callback 捕获 render-time `activeCanvasId`；
- 写入前比较 store current active canvas；
- stale callback 不修改 `flowViewport`、store viewport 或 zoom；
- current invalid payload 也 zero mutation；
- 记录 stable diagnostic reason，供 focused verifier 使用。

### Slice D：focused verifier

新增 `scripts/verify-liblib-batch65.py`：

- pure bootstrap/stable/invalid cases；
- fresh desktop `canvas-2` 使用 desktop preset；
- fresh mobile `canvas-2` 使用 compact preset；
- bootstrap owner 在未交互时跨 breakpoint 可选择另一 preset；
- UI zoom/pan 后跨 breakpoint 不回到固定 preset；
- user-owned `canvas-2` 切到 `canvas-1` 再切回精确恢复；
- `canvas-1` 跨 breakpoint 不被 demo preset 污染；
- stale old-canvas viewport callback zero mutation；
- current invalid viewport callback zero mutation；
- graph/history/selection zero mutation、overflow 和 diagnostics。

## 4. 明确不做

- 不新增通用 `ResizeObserver` 或 host epoch registry；
- 不承诺 browser resize 后旧 host center flow anchor 本批已保持；
- 不把每帧 viewport event 拆成正式 LIVE/STABLE store；
- 不实现 pointercancel/animation cancel 或 fit/zoom endpoint reducer；
- 不修改 FrameOS、Director、graph history、图片双浮层公式；
- 不把 desktop/compact preset 声明为 LibTV 永久产品规则；
- 不移植 Open Canvas URL/hydrate/persistence。

## 5. 候选文件

| 路径 | 职责 |
|---|---|
| `src/lib/libtvViewportPlacement.ts` | pure responsive ownership plan / validation |
| `src/app/page.tsx` | per-canvas owner ledger、current callback guard、responsive projection |
| `scripts/verify-liblib-batch65.py` | focused browser verifier |
| 本批目录 | 计划、证据成本、runtime audit 和实施结果 |

## 6. 验收

Focused：

```bash
python3 scripts/verify-liblib-batch65.py
```

相邻：

```bash
python3 scripts/verify-liblib-batch6.py
python3 scripts/verify-liblib-batch7.py
python3 scripts/verify-liblib-batch16.py
python3 scripts/verify-liblib-batch18.py
python3 scripts/verify-liblib-batch19.py
python3 scripts/verify-liblib-batch61.py
python3 scripts/verify-liblib-batch62.py
python3 scripts/verify-liblib-batch63.py
python3 scripts/verify-liblib-batch64.py
npm run check
npm run docs:check
git diff --check
```

回归覆盖的历史截图/runtime audit 在收口前恢复。

## 7. 停止与 Checkpoint

1. 本计划与截图成本台账先 commit/push；
2. pure helper、page owner ledger 与 callback guard 完成后 checkpoint；
3. focused verifier、相邻回归和 runtime audit 通过后补实施记录；
4. 收口文档 commit/push 并确认工作区干净；
5. 下一批再处理 browser host-resize center anchor 或 LIVE/STABLE phase，不在本批
   横向扩展。
