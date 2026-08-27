# Batch 65 实施记录：Responsive Viewport Bootstrap Ownership

> 实施日期：2026-08-27
>
> 计划 checkpoint：`65f1b74`
>
> 实施与 focused verifier checkpoint：`5d2222b`
>
> 当前状态：`IMPLEMENTED_FOCUSED_PASS`

## 1. 实施范围

本批把普通 LibTV demo canvas 的 `desktopViewport` / `compactViewport` 限制为
page-session bootstrap。用户一旦通过 pan、zoom、fit、organize、restore 或 Asset
layout transaction 产生有效 viewport，当前 canvas 即进入 stable ownership；
后续 breakpoint change 和 canvas switch 使用该 canvas 的 stored viewport。

同时，React Flow viewport callback 现在携带 render-time canvas owner。旧画布
callback 和非法 viewport 都在写 page state、store viewport、zoom projection 前
被拒绝。该 owner ledger 与 diagnostics 只属于 clone runtime，不进入 graph
document、selection 或 semantic history。

## 2. 代码变更

| 文件 | 结果 |
|---|---|
| `src/lib/libtvViewportPlacement.ts` | 新增 `bootstrap/stable` ownership、严格 viewport validation 和纯 responsive projection planner；stable restore 只依赖 stored viewport，不受无关 bootstrap preset 影响。 |
| `src/app/page.tsx` | 新增 per-canvas page-session ownership ledger、current-canvas callback guard、bootstrap projection、stable restore 和 verifier diagnostics；organize/restore/Asset layout 统一进入有效 viewport commit。 |
| `scripts/verify-liblib-batch65.py` | 覆盖 pure planner、desktop/mobile bootstrap、未交互与已交互 breakpoint、A/B canvas restore、projection echo、stale/invalid callback、graph/history/selection isolation、overflow 和 diagnostics。 |
| `runtime-audit.json` | 保存本批 focused runtime 原始结果；复用既有截图识别台账，不新增截图。 |

## 3. Ownership 语义

当前 clone 使用两级 page-session owner：

```text
BOOTSTRAP
  -> demo canvas 可按当前 breakpoint 使用 source-shaped preset
  -> 精确 preset echo 不建立新的用户状态

STABLE
  -> 任一有效、实际改变 viewport 的 callback 或具名 layout command
  -> stored per-canvas viewport 成为 switch / breakpoint restore authority
```

应用 viewport event 前依次验证：

1. `expectedCanvasId` 仍是 current active canvas；
2. `x/y/zoom` 有限且 zoom 位于 `0.1..8`；
3. bootstrap owner 的 exact current-preset event 只作为 projection echo；
4. 其他 accepted event 标记 stable，并同步 controlled React Flow viewport、
   active canvas stored viewport 和 zoom projection。

该实现没有声称 React Flow controlled prop 一定产生 echo，也不依赖 echo 才能
完成 bootstrap。运行探针确认当前 12.11.1 受控 prop 更新不触发
`onViewportChange`；实际 zoom/fit 动画会发出连续 callback，本批仍逐帧写 stable
store，完整 `LIVE/STABLE` endpoint 压缩留给后续批次。

## 4. Focused 验证

```bash
python3 scripts/verify-liblib-batch65.py
```

结果：`PASS`。

已验证：

- fresh desktop `canvas-2` 精确使用 `-583.8 / 260.8 / 0.526`；
- fresh mobile `canvas-2` 精确使用 `17 / 128 / 0.28`；
- 未交互 owner 保持 bootstrap，可在 breakpoint 间切换 preset；
- zoom 后 owner 转 stable，跨 breakpoint 保留用户 viewport；
- `canvas-2 -> canvas-1 -> canvas-2` 精确恢复两个 stored viewport；
- 非 demo canvas 不接收 demo preset；
- exact projection echo 不误建立 stable ownership；
- stale old-canvas callback 与 invalid viewport zero mutation；
- graph、history、selection、overflow 和 browser diagnostics 均通过。

## 5. 相邻回归与门禁

通过：

```text
Batch 6, 7, 16, 18, 19, 61, 62, 63, 64
```

覆盖导航手势、organize、canvas lifecycle、zoom、minimap、React Flow routing、
selection/context、actual-host placement 和 Asset drawer anchor。

项目门禁：

- `npm run check`：通过；保留 9 条既有 FrameOS/共享组件 warning，无 error；
- `npm run docs:check`：通过；
- `git diff --check`：通过。

回归脚本重写的历史截图和 Batch 61/63 runtime audit 已恢复；只保留 Batch 65
新 runtime evidence。

## 6. 证据边界

本批是 clone-owned correctness，不证明 LibTV 原站：

- 使用 `bootstrap/stable` 相同状态名或 owner ledger；
- 使用 `768px` breakpoint 或同一 desktop/mobile preset；
- 在 browser resize 时保持同一 screen point 或 host-center flow anchor；
- 在 pan/zoom 动画期间逐帧持久化或仅在 endpoint 持久化；
- 使用 React Flow、Zustand 或相同 callback 时序。

Open Canvas 只提供 live/stable、screen/flow owner 分离和 stale guard 的机制启发。
没有新的 source screenshot、DOM 或 bundle claim。

## 7. 后续入口

当前已关闭：

- actual-host default add；
- Asset drawer host-center anchor；
- responsive bootstrap overwrite；
- current/old canvas viewport callback guard。

下一批优先处理 browser host resize 的 old-host-center flow anchor preservation，
并明确区分：

- browser resize/orientation；
- Asset drawer transaction；
- stable viewport restore；
- selected overlay 同 frame geometry。

完整 pan/zoom `LIVE/STABLE` endpoint、programmatic animation operation ID、
pointercancel、generic canvas generation/host epoch、derived/duplicate/organize
composition 和 source-exact responsive policy继续保持独立范围。

## 8. 保护性 Checkpoint

1. `65f1b74`：计划、价值排序、证据边界和截图成本台账；
2. `5d2222b`：pure planner、page ownership、focused verifier 和 runtime audit；
3. 本收口提交：相邻回归、稳定文档同步和实施历史。
