# Batch 64 实施记录：Asset Drawer Host-Resize Anchor Preservation

> 实施日期：2026-08-27
> 计划 checkpoint：`7624f0a`
> 实施与 focused verifier checkpoint：`4b8f931`
> 当前状态：`SCRIPT_RECORDED_PASS`

## 1. 实施范围

本批关闭普通 LibTV clone 的一个布局跳动缺口：Asset drawer 打开、关闭或转入
Canvas dropdown 时，旧 React Flow host 中心下的 flow point 会继续位于新 host
中心。该操作只更新 viewport projection，不修改 graph、selection 或 graph
history。

覆盖 lower-left Asset toggle、drawer 显式 X 和 drawer Canvas context 三个入口，
并与 Batch 63 的 actual-host default add 组合验证。没有实现通用
`ResizeObserver`、browser resize/orientation、Agent drawer、live/stable viewport
全量分层或 LibTV source-exact drawer animation。

## 2. 代码变更

| 文件 | 结果 |
|---|---|
| `src/lib/libtvViewportPlacement.ts` | 新增 flow anchor 到新 host center 的 target viewport helper，以及 old host/viewport/new host 的纯 planning helper。 |
| `src/app/page.tsx` | 新增 page-owned Asset layout transaction；捕获 operation、canvas、React Flow instance、viewport 和旧 host center flow anchor，layout commit 后按 current guards 写入新 viewport。 |
| `src/components/BottomToolbar.tsx` | Asset toggle 改由 page callback 驱动；Batch 64 regression 保留完整 Asset/连线/吸附/缩放控件。 |
| `src/components/AssetManagerPanel.tsx` | 显式 X 和 Canvas context transition 统一走 page-owned layout callback。 |
| `src/components/LeftSidebar.tsx` | graph anchor 仍跟随 actual host center；仅对 screen toolbar 使用窄桌面 collision floor，避免与完整次级工具条重叠。 |
| `scripts/verify-liblib-batch64.py` | 覆盖 pure helper、desktop/mobile open/close、三个入口、stale canvas guard、zero graph/history/selection mutation、Batch 63 composition、overflow 和 diagnostics。 |
| `runtime-audit.json` | 保存本批 focused runtime 原始结果；复用既有截图识别台账，不新增截图。 |

## 3. Layout Transaction

每次 Asset layout command：

1. 从当前 actual React Flow host center 捕获 flow anchor；
2. 固定 active canvas、React Flow instance、controlled viewport 和 operation ID；
3. 执行既有 UI open/close/transition action；
4. 双 `requestAnimationFrame` 后重新量测 host；
5. 仅当 operation、canvas、instance 和 captured viewport 仍 current 时提交
   target viewport；
6. stale/invalid 分支只写诊断日志，不覆盖较新的 owner。

目标公式沿用正式空间合同：

```text
target.x = newHost.width / 2 - flowAnchor.x * zoom
target.y = newHost.height / 2 - flowAnchor.y * zoom
```

desktop `929x874` 和 mobile `390x844` 的 drawer open 均产生 `x=-120`，close
恢复 `x=0`；节点中心对各自 host 中心的实测误差为 `0px`。

## 4. 回归期修正

Batch 63 首版为避免两个固定工具条碰撞，在 asset-open 窄桌面隐藏了 Asset 文本、
snap 和 zoom。Batch 18/19 回归证明这破坏了既有 zoom 可达性和 minimap 严格
`+240px` drawer follow。

最终策略分开两个坐标职责：

- graph placement 和 viewport anchor 继续使用 actual host center；
- 次级工具条保留完整宽度与控件；
- 主工具条只在 screen space 应用 `704px` center floor，避免命中区重叠；
- screen clamp 不改变 graph flow anchor。

这一策略是 clone-owned responsive correctness，不是 LibTV source responsive
policy 的声明。

## 5. 验证结果

Focused：

```bash
python3 scripts/verify-liblib-batch64.py
```

结果：`PASS`。

相邻回归：

```text
Batch 17, 18, 19, 60, 61, 62, 63
```

均通过，覆盖 Asset tree/search、zoom menu、minimap drawer follow、图片双浮层、
React Flow routing、selection/context 和 actual-host default add。

项目门禁：

- `npm run check`：通过；保留 9 条既有 FrameOS/共享组件 lint warning，无 error；
- `npm run docs:check`：通过，531 个 Markdown、3130 个本地目标；
- `git diff --check`：通过。

回归脚本覆盖写入的 Batch 17/18/19 历史截图和 Batch 61/63 runtime audit 已恢复，
没有把随机测试副产物提交为新证据。

## 6. 边界与下一步

本批关闭 `LIBTV-GC-088` 的 Asset drawer center-anchor 子切片，并补充
`LIBTV-GC-080/082/089` 的 current operation/canvas/viewport guard 局部运行证据。
以下仍保持 runtime partial 或 source-gated：

- browser resize/orientation 和 generic host epoch；
- pan/zoom 的 `LIVE/STABLE` endpoint 分离与 cancel；
- responsive bootstrap 不覆盖 user-owned viewport；
- Agent drawer、Storyboard、selected overlay 在任意 host resize 下的组合；
- derived/duplicate/organize placement composition；
- LibTV source exact drawer anchor、animation、auto-pan 和 mobile degradation。

下一批应继续选择一个有界空间 owner slice，优先处理 viewport callback 的
canvas ownership 或 responsive bootstrap guard，不能把本批写成完整
`LIBTV-VR-020` source parity pass。

## 7. 保护性 Checkpoint

1. `7624f0a`：Batch 64 计划、证据边界和截图成本台账；
2. `4b8f931`：pure helper、page/component owner path、focused verifier 和
   runtime audit；
3. 本收口提交：回归修正、实施记录、稳定治理同步和完整验证结果。
