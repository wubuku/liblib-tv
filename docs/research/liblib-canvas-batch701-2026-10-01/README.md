# batch 701 — 「没记账」推不出「没接线」：命令账覆盖率的普查

## 起点

700 把「点了没反应」劈成三格，第三格是：
`motion-preset-button` / `motion-create-path` **真没接线**，
理由之一是「点了之后**没有任何命令被记录**，而源码里它们根本没有 `onClick`」。

本批来压力测试那条推理的**形式**（不是那两枚控件的结论）。

## 写下预测，再测

**预测（本批写死在代码里，先于任何测量）：凡是把 store 状态改掉的控件，都会留下命令记录。**

实测 8 枚入口控件（两轮，逐项完全相同），**2 枚当场推翻它**：

| 控件 | 改 store | 叶子数 | 命令账 |
|---|---|---|---|
| `data-director-playback` | ✅ | **10** | ❌ **零记录** |
| `data-director-open-curve-editor` | ✅ | **1** | ❌ **零记录** |
| `data-director-auto-keyframe` | ✅ | 64 | ✅ `PROJECT_MUTATION` / `COMMITTED` |
| `data-director-loop` | ✅ | 64 | ✅ `PROJECT_MUTATION` / `COMMITTED` |
| `data-director-remove-track` | ✅ | 86 | ✅ `DELETE_TRACK` / `COMMITTED` |

**`playback` 是活的、真的改了状态、却一个字都不记。**

`playback` 改的那 10 个叶子是：
`timeline.isPlaying` false→true、`timeline.currentTime` 0→0.5166，
**外加把插值结果回写进 `objects[0].transform.*` 与 `objects[4].camera.*`**。

`open-curve-editor` 改的那 1 个叶子是 `timeline.editorMode` `"timeline"`→`"curve"`。

## 于是 700 那条推理要更正

**「没记账」推不出「没接线」。**

**700 对那两枚指路牌的结论仍然成立**，但理由要换成一条**独立证据**：
`DirectorCameraMotionTab.tsx:308/319` 两个 `<button>` 上没有 `onClick` ——
这与记账无关。**结论没错，理由错了。**

## 三种「不记账」必须分开

| 类 | 控件 | 含义 |
|---|---|---|
| **A. 改了 store 却没记** | `playback` `open-curve-editor` | 命令账的**覆盖漏洞** |
| **B. 只改了非 store 状态** | `time-unit`（组件局部 `useState`，`DirectorTimeline.tsx:260`）`create-motion-path`（只展开一个下拉） | **不记账是预期的**，它们根本不是命令 |
| **C. 什么都没改** | `delete-keyframe`（在「选中机位」这一态下） | **第三态**，不能算进 A |

把 (B) 算成 (A)，等于给命令账记一笔它没欠的账；
把 (C) 算成 (A)，是 697 那条「读数的第三态不能被当成否定」又来一次。

## 命令账的规模 ≠ 命令账的覆盖

源码侧数得出来，**规模很厚**：

| disposition | 处数 |
|---|---|
| `REJECTED` | 41 |
| `STALE` | 21 |
| `NOOP` | 20 |
| `COMMITTED` | 17 |
| `CONFLICT` | 8 |
| `TOMBSTONED` / `SAVED` | 1 / 1 |

合计 **109 处**、**16 种 reason**。

**但它覆盖的是「走命令层的那一部分动作」，不是「所有改状态的动作」。**
播放与视图切换走的是另一条路。

## 判据

| 判据 | 断言 |
|---|---|
| `the-ledger-misses-store-changing-controls-and-that-is-stable` | 预测被推翻，**且两轮给出同一组越界者** |
| `no-ledger-entry-does-not-imply-no-wiring` | `playback` 活 + 改 store + 零记录 ⟹ 推理形式不成立；700 的结论靠独立证据幸存 |
| `three-kinds-of-no-ledger-entry-are-different` | A/B/C 逐枚归类正确 |
| `ledger-size-is-not-ledger-coverage` | 源码 109 处 vs 运行时 2 处缺口 |

**判据 1 断言的是「预测被推翻」这个事实，而不是预测本身** ——
一个永远 rc≠0 的验收器在账本里是谎话。跑两轮是因为 696 立过一条：
会在两轮里自相矛盾的行为不能写成确定条件。

## 本批自己踩的坑

**守卫挡住了噪声，也挡住了证据。**
第一版用 `if (isPlaying) return {__playing:true}` 挡掉播放中的逐帧漂移，
结果把 `playback` 整枚控件的 `changedStore` 归零 —— **它正是本批要的反例**。
改成：点完之后若进入播放，**再点一次暂停**再取样。启停是真人本来就会做的一对点击，
取样因此稳定，而 `isPlaying` 翻转与 `objects` 回写都仍留在 diff 里。

**没有「自身可见面」这一面，`time-unit` 会被误归成「什么都没改」** ——
它确实改了，只是改的是组件局部 `useState`，store 一动不动。

## 不声称

- 不声称播放/视图切换**应该**进命令账 —— 那是一个设计取舍，不是缺陷。
  本批只测出「它们不记账」这一事实，以及「用不记账推断没接线」这个推理形式不成立。
- 不声称 `objects[*]` 被回写是 bug —— 那看起来是刻意的求值实现，**未进一步取证**。
- 不声称源站有同样行为（**未取证，需授权点击**）。
- **不改 `src/`**

## 复现

```bash
$HOME/.pyenv/shims/python3 scripts/verify-liblib-batch701.py
```

需 dev server 跑在 4317。零 store 写入，两轮 × 8 枚 = 16 个全新页面，约 90 秒。
