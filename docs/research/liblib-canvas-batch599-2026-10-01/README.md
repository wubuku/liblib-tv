# Batch 599 — 打开导演台不再把时间轴缩放打回 1

日期：2026-10-01
取证：clone 运行时订阅抓栈（`/tmp/src599/zoom.py`、`zoom-trap.py`）
验收：`scripts/verify-liblib-batch599.py`（10 项检查全过）

---

## 一、缺陷

batch 594 把 `timeline.zoom` 的初值从 1 改成 44（依据源站当前项目读数 43.7751，
四舍五入显示 44；那是用户自己拖出来的值，**默认值不可考**，44 是为了让 clone
打开时的标尺密度与源站当前观感一致而取的**推断**）。

**这个初值从来没有到达过 UI。**

`DirectorDesk` 在 `useEffect` 里调 `openSession` 打开导演台；`openSession` 经
`restoreDirectorProjectState` → `restoreDirectorProjectRuntimeSnapshotV1` 从工程文档
重建运行时 timeline。工程文档 schema 故意不含视图态字段（同一个函数把
`currentTime` 补成 0、`isPlaying` 补成 false），但 `zoom` 被补成了**字面量 1**。

于是每次打开导演台都把 44 覆盖成 1，标尺停在最密档，8s ≈ 640px（`min-w-full`
兜到容器宽 1120px），而不是预期的 1779px。

### 1.1 实测（全新 profile，1920×1150，改动前）

```
页面加载后          zoom = 44
openDirectorDesk 后 zoom = 1     ← 缺陷
缩放滑杆 value      1
```

### 1.2 订阅抓到的调用栈

```
openSession
  → restoreDirectorProjectState
    → restoreDirectorProjectRuntimeSnapshotV1   (src/lib/directorProjectRuntimeAdapter.ts:258  zoom: 1)
  ← DirectorDesk.useEffect
```

顺带确认：仓库里另外两处 restore 路径都显式写了 `zoom: state.timeline.zoom`
（保留当前值），只有这条 `openSession` 的默认路径经由 adapter 重建时丢掉了默认值。

---

## 二、改动

新增共享常量，让「文档默认值」和「从文档重建运行时」两处不再各写各的：

- `src/lib/directorProjectRuntimeAdapter.ts`
  - 新增 `export const DIRECTOR_TIMELINE_DEFAULT_ZOOM = 44`，附完整取值说明
  - 重建 timeline 时 `zoom: 1` → `zoom: DIRECTOR_TIMELINE_DEFAULT_ZOOM`
- `src/store/directorStore.ts`
  - `createDefaultTimeline()` 的 `zoom: 44` → 同一个常量
  - import 改为同时引入常量与 `restoreDirectorProjectRuntimeSnapshotV1`

常量放在 adapter 而不是 store：`directorStore` 已经**从 adapter 导入**，若把常量放
store 再反向导入就成环。

---

## 三、未取证 / 不声称（记录，不臆造）

- **源站关闭再打开导演台时 zoom 是否保留，没有观测过。** 所以本批**没有**让 clone
  保留活动 zoom 值——只统一了两个常量，打开时仍然回到默认 44。这是有意的最小修复：
  没有源站证据就不加持久化语义。
- 源站的 zoom 默认值本身仍不可考，44 沿用 594 的推断标注。

---

## 四、验收合同

`scripts/verify-liblib-batch599.py` 10 项：

1. adapter 导出并使用 `DIRECTOR_TIMELINE_DEFAULT_ZOOM`
2. adapter 里不再有 `zoom: 1,` 字面量
3. store 的 `createDefaultTimeline` 用同一个常量，不再写 `zoom: 44,`
4. 页面加载后 zoom === 44
5. **`openDirectorDesk` 后 zoom 仍是 44**（本批回归点）
6. 缩放滑杆读数为 44，且 min=0 / max=100
7. 关闭再打开同一节点，仍是 44
8. 导出 → 导入工程文档往返后仍是 44（走的正是曾经丢值的那条 adapter 路径）
9. batch 594 的钳制仍成立：`setTimelineZoom(-5) → 0`、`setTimelineZoom(150) → 100`
10. 无 console 报错
