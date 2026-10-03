# batch 700 — 「点了没反应」至少有两类：有据可查的拒绝，和没有账的沉默

## 起点

699 把导演台 14 枚入口类控件普查了一遍，判出 4 枚「惰」，并诚实地写下：
**`add-track` 点了什么都不发生，但本批没有测出为什么。**

本批只做一件事：**把那「不知道为什么」问出来。**

## 问出来了：导演台**自己在记账**

`directorStore` 每条命令都写 `lastCommandResult`
（`commandKind` / `disposition` / `reason`），并且把它翻到 DOM 属性上 ——
`[data-director-workspace]` 上的 `data-director-last-command` /
`data-director-last-disposition` / `data-director-last-reason`。

**699 的快照从来没读过这两面。** 于是「惰性」这个词把两件不同的事混成了一件：

| 控件 | 点了之后 | 属于哪一格 |
|---|---|---|
| `add-track` | `ADD_TRACK` / **`NOOP`** / **`DIRECTOR_COMMAND_NO_CHANGE`** | **有据可查的拒绝** |
| `add-keyframe`（播放头处已有关键帧） | **什么都没有** —— 无命令、无 toast、无 disposition | **没有账的沉默** |
| `add-keyframe`（播放头处无关键帧） | `PROJECT_MUTATION` / `COMMITTED`，**真的加了一个** | 正常 |
| `motion-preset-button` / `motion-create-path` | 源码无 `onClick`，**不可能有命令** | 真没接线 |

## `add-keyframe` 不是坏按钮

它是一个**幂等插入**：播放头所在时刻已有关键帧就不重复插。
而且 **`autoKeyframe` 开关对它毫无影响**（开/关两次实测都是 6→7）——
这排除了「它其实是自动帧的附属动作」这个自然的猜测。

## 逐时刻扫描（真实点击，零 store 写入）

播放头是**点标尺** `[data-director-timeline-ruler]` 挪的，实测 `t = f × duration`
（`duration = 8`），**不是 `setTimelineTime()`**。预测写在测量之前。

| f | 播放头 t | 该处已有关键帧 | 预测 Δ | 实测 Δ | 命令账 |
|---|---|---|---|---|---|
| 0.0 | 0 | 是 | 0 | **0** | `null` |
| 0.05 | 0.4 | 否 | 1 | **1** | `PROJECT_MUTATION / COMMITTED` |
| 0.125 | 1 | 否 | 1 | **1** | `PROJECT_MUTATION / COMMITTED` |
| 0.25 | 2 | 否 | 1 | **1** | `PROJECT_MUTATION / COMMITTED` |
| 0.375 | 3 | 否 | 1 | **1** | `PROJECT_MUTATION / COMMITTED` |
| 0.5 | 4 | 是 | 0 | **0** | `null` |

**6/6 逐行相符。** 判定完全由「该时刻是否已有关键帧」决定。

## 真正扎人的地方

**打开导演台时播放头在 t=0，而 t=0 处本来就有关键帧**（`[0, 4, 8]`）。

⟹ 用户什么都不做、直接点「添加关键帧」，**什么都不会发生，也没有任何提示**：
关键帧 6→6，`lastCommandResult` 从 `null` 到 `null`，toast 0 个、对话框 0 个。

699 把它记成「惰性」在这个状态下是对的，**成因却是「幂等」而不是「没接线」**。

## 判据

| 判据 | 断言 |
|---|---|
| `add-keyframe-no-op-is-idempotence-not-a-broken-wire` | 在无关键帧处它真的加（6→7）并记 `PROJECT_MUTATION/COMMITTED` |
| `per-timestep-scan-matches-the-keyframe-position-prediction` | 6 行扫描逐行与预先写下的预测相符 |
| `rejection-bookkeeping-is-inconsistent-and-both-paths-are-silent-to-the-user` | `add-track` 记 `NOOP`+理由并翻到 DOM 属性；`add-keyframe` 等价情形什么都不记 |
| `the-default-state-is-a-silent-no-op` | 默认态点「添加关键帧」不发生、无记账、无反馈 |

## 零点击自检仍然为空

快照多了 `lastCommandResult` 与三个 DOM 属性之后重测：
`nullClickDrift = []`。**仪器加了新面之后必须重新体检** ——
一个会自己抖的面会把每次点击都读成「有变化」。

## 不声称

- 不声称 `add-keyframe` **应该**在同一时刻重复插入关键帧（那多半是错的）。
  本批只测出「它不插」与「它不记账、不提示」。
- **要不要给 `add-keyframe` 补一条 `NOOP` 记账或一个轻提示，是产品决定** ——
  需要你拍板才动 `src/`。
- 不声称源站有同样行为（**未取证，需授权点击**）。
- 不声称 `add-track` 的 `NOOP` 是缺陷 —— 它的理由写得比 `add-keyframe` 清楚。
- **不改 `src/`**

## 复现

```bash
$HOME/.pyenv/shims/python3 scripts/verify-liblib-batch700.py
```

需 dev server 跑在 4317。零 store 写入，每个读数一个全新页面，约 60 秒。
