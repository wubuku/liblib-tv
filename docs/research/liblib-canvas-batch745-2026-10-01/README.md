# batch 745 — B 档 7 个两段式命令逐个走完：**5 个真跑通、2 个被「视频时长」挡住（且 UI 有说明）**

## 起点

744 把 16 个记账命令分成 A 档 8 / B 档 8，但 B 档里**只实测了「智能续写」的入口**，
其余 7 个标为未取证。本批把它们逐个走完 —— 把「入口可达」升成「命令真跑」。

全部读数来自 clone，**不碰源站**。

## 汇总表：7 个 B 档命令

| 命令 | 段数 | 入口 | 面板 | `past` | 节点 | 边 | 新增节点类型 |
|---|---|---|---|---|---|---|---|
| `addDerivedNode`（逐帧拉片） | 1 | ✓ | — | 1→**2** | 11→**12** | 11→**12** | `shot-breakdown` |
| `createVideoFrameCapture`（抽帧） | 1 | ✓ | — | 1→**2** | 11→**12** | 11→**12** | （帧节点） |
| `createAudioSplit`（音视频分离） | 1 | ✓ | — | 1→**2** | 11→**13** | 11→**13** | `audio` + `silent-video`（**一步产 2 个**） |
| `createSubtitleErase`（智能去字幕） | 2 | ✓ | ✓ | 1→**2** | 11→**12** | 11→**12** | |
| `createSmartMatting`（智能抠像） | 2 | ✓ | ✓ | 1→**2** | 11→**12** | 11→**12** | |
| `createPictureEdit`（主体消除） | **3** | ✓ | ✗（30s）→✓（10s） | 1→1 / 2→2 | 11→11 | | **提交按钮 `disabled`** |
| `createDepthMotionCapture`（深度动作捕捉） | 2 | ✓ | ✗（30s）→✓（10s） | 1→1 / 2→**3** | 11→**12** | | |

（每条命令**重载页面**取独立基线；`past` 基线 1 来自新建视频卡那一步本身也记账。）

## 决定性读数

### ① 入口链逐个命中（每一跳都点到）

7 条命令的入口链全部点到，包括两级菜单（触发器 → 菜单项）：
`[data-video-subtitle-menu-trigger] → [data-video-subtitle-mode="smart"]`、
`[data-video-picture-edit-menu-trigger] → [data-video-picture-edit-action="matting"|"subjectRemove"]`、
`[data-video-frame-menu-trigger] → [data-video-frame-kind="current"]`、
`[data-video-audio-menu-trigger] → [data-video-audio-mode="av"]`。

### ② **两个命令有第三层门控：视频时长**

```
VideoNode.tsx:265   openDepthMotionCapture   if (durationSeconds > 15) { setDepthMotionFeedback("视频时长超过处理上限…"); return; }
VideoNode.tsx:338   selectPictureEdit        if (durationSeconds > 15) { showPictureEditFeedback("视频大于15秒…"); return; }
VideoNode.tsx:342   selectPictureEdit        if (durationSeconds < 2.5) { showPictureEditFeedback("源视频时长需在 3~15 秒之间…"); return; }
```

新建视频卡的默认 `durationSeconds` = **30** ⟹ 两个命令**一创建就用不了**：

| | 面板 | 提交按钮 | `past` / 节点 | UI 反馈横幅 |
|---|---|---|---|---|
| 默认 30 秒 | **不出现** | — | 1→1 / 11→11 | `data-video-picture-edit-feedback`：**「视频大于15秒，暂不支持该功能」**<br>`data-video-depth-motion-feedback`：**「视频时长超过处理上限，暂不支持深度动作捕捉」** |
| 改成 10 秒 | **出现** | 在 | 深度动作 2→**3** / 11→**12** | — |

⟹ **这不是静默失败**：UI 用横幅写明了原因（横幅 1800ms 后自动消失）。
⟹ **门控就是时长**：只把 `durationSeconds` 改成 10、其他字段不动，面板立刻出现。

### ③ **主体消除是三段式**

面板出现后，提交按钮是 `disabled`：

```
PictureEditPanel.tsx:880-884
  <button data-picture-edit-submit
          data-picture-edit-submit-status={submitting ? "analyzing" : "idle"}
          disabled={!canSubmit}
          onClick={() => onConfirm(cloneMarks(marksRef.current))}
```

⟹ 要先在画面上**标记主体**才能提交。本批未做标记那一跳，
所以 `createPictureEdit` **没有被真正触发**（只证到「面板能开、提交按钮 disabled」）。

### ④ 门控是**四层**不是三层

| 层 | 条件 | 位置 | 挡住谁 |
|---|---|---|---|
| L1 | `selected && selectedNodeCount <= 1` | `VideoNode.tsx:120` | 全部 16 个命令 |
| L2 | `status === "ready"` | `:412-415`、`:748-801` | 整块工具栏 + 5 个面板（B 档 8 个命令） |
| **L3** | **`durationSeconds` 在 2.5~15 秒** | `:265`、`:338`、`:342` | **主体消除、深度动作捕捉** |
| L4 | `status !== "pending"` | `:658-659` | `VideoGenerationPanel` 与尝试列 |

## 探针返工五处（全部是我自己的错）

1. **两跳入口在同一个 tick 里点完** —— React 还没重渲染，菜单项根本不存在 ⟹ 抽帧/音视频分离两条入口读成 `False`。改成两次 `evaluate` + 中间等 700ms。
2. **`entryOk` 用解析日志字符串算**（`all(x.endswith("True"))`），而第二条日志以 `"(exists=True)"` 结尾 ⟹ 读出 `entryOk=False`，**而命令其实真跑了**（节点 +1、`audio` 节点出现）。改成用布尔值累积。
3. **`PANEL_JS` 用字符串拼接推 submit 选择器**，拼出非法选择器 `[data-subtitle-erase-panel]submit` 直接抛异常。改成 spec 里显式写 submit 选择器。
4. **深度动作捕捉那条 spec 只给了一个选择器**，代码按两跳拆包 ⟹ `ValueError`。改成允许单选择器。
5. **反馈横幅等满 1200ms 才读** —— 横幅 **1800ms 自动消失**，两条都读成 `null`，差点把「UI 有说明」判成 FAIL。改成点完入口 400ms 后立刻读。

## 判据（7/7）

| | 判据 | 读数 |
|---|---|---|
| C1 | 7 个命令的入口链逐个命中 | `entryOk` 全 ✓ |
| C2 | 无时长门控的 5 个：3 个一段式 + 2 个两段式，全部真跑并记账 | `past` 各 +1、节点各 +1 |
| C3 | 两个时长门控命令：默认 30 秒下面板不出现、store 不动、**但 UI 有说明** | `duration: 30` + 两条横幅文案 |
| C4 | 时长对照：改成 10 秒后两个面板都出现；深度动作捕捉提交后 `past` +1 且建节点 | `10s → panel ✓` |
| C4b | 主体消除是**三段式**：面板出现但提交按钮 `disabled` | `submitDisabled: true` |
| C5 | 每个命令都在 `status === "ready"` 的新卡上验（744 的 B 档门控前提） | 全 `ready` |
| C6 | 门控是**时长**不是别的：只改 `durationSeconds` 一个字段 | `30 → 10` |

## 不声称

- 两个时长门控命令只验了上界（30 秒被拒）与 10 秒可用；**下界 <2.5 秒未验**。
- **「新建视频卡默认 30 秒」是否有意 —— 未取证**。
- 抽帧只验了 `frameKind="current"`；`first`/`last` 未验。
- 音视频分离只验了 `av`；`vocals` / `background` 未验。
- 主体消除只验了 `subjectRemove`；`subjectModify` / `subjectReplace` 未验。
- **主体消除的「标记主体」那一跳没做** ⟹ `createPictureEdit` 本批**未真跑**。
- 面板提交后的异步阶段（如 depth-motion 的 `delayMs 520`）是否有后续变更，未取证。
- 多选态（`selectedNodeCount > 1`）下这 7 个命令全部不可达那一格未测。

## 验收器

`scripts/verify-liblib-batch745.py` — 7 条命令逐条走完（含两级菜单链）
+ 2 条时长门控对照，两轮连跑逐字段一致。
