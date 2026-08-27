# Batch 71 计划：Director Pointer Lifecycle And Gesture Adapter

> **Purpose**：把 Director 仍然直接写 store 的高频输入接入 Batch 70
> project-local command/history 边界，保证完整用户动作最多一条 history。
> **Status**：`COMPLETE / POINTER_LIFECYCLE_FOCUSED_PASS`。
> **Date**：2026-08-27。

## 1. 依据与当前缺口

前置实现：

- Batch 67：`DirectorProjectDocumentV1` strict codec；
- Batch 68：按 `route + canvasId + sourceNodeId` 隔离的 owner/session；
- Batch 69：`authoredObjects` baseline 与 runtime `objects` projection；
- Batch 70：typed command result、project-local `past/future`、
  undo/redo、object/group TransformControls 和 speed-curve gesture adapter。

当前仍存在的高价值缺口：

- Inspector `number` 字段每次 `onChange` 都直接写入；
- camera FOV 与 pose slider 连续写入，没有统一 pointerup/blur/cancel；
- motion-path anchor、Bezier handle 和 path transform 仍没有显式 gesture；
- free-path draft 已有 pointer capture，但没有与 Director history gesture
  建立明确的 begin/finish/cancel 关系；
- `Escape`、`pointercancel`、输入失焦和 owner/session 失效的边界没有统一
  verifier。

这些是 clone-owned reliability work，不是 LibTV source-exact undo/redo 事实。
LibTV 原站的 commit 时机、快捷键文案和删除交互仍保持 source-unknown 边界。

## 2. 本批目标

### Slice A：统一 DOM input gesture boundary

- 为 numeric/target/follow-offset/path transform 字段建立
  `focus/pointerdown -> update* -> blur/pointerup -> commit`；
- `Escape` 取消并恢复 baseline；
- `pointercancel` 取消并清理 active gesture；
- 同一个字段从鼠标、键盘或连续输入完成后最多一条 history；
- disabled/derived field 不得启动 gesture。

### Slice B：pose/camera controls

- pose slider 连续变化只保留一条 history；
- camera FOV slider 与 pose slider 统一 pointer lifecycle；
- preset、toggle、select 等离散 command 不机械套用 slider gesture；
- owner 切换或 Director close 后不消费旧 gesture。

### Slice C：path controls

- Inspector path anchor position、handle in/out 和 path transform
  接入同一 gesture boundary；
- R3F path anchor/Bezier handle TransformControls begin/commit/cancel；
- path edit 的 runtime projection 仍保持 authored source authority；
- 不把 selection/path preview 写入 semantic history。

### Slice D：free path drawing

- pencil/pen draft begin 时记录一个 path-draw gesture；
- pointermove 只更新 draft；
- pointerup/完成按钮/Enter 提交一次；
- Escape、pointercancel、无效点数、close/switch 清理且零 history residue；
- 不让 draft 的 preview 状态成为 portable document。

### Slice E：focused verifier and governance

- 新增 pure/static assertions；
- 新增 fresh-page Batch 71 verifier；
- 覆盖 number、range、pose、path、free-draw 的 commit/cancel/no-op/stale；
- 运行 Batch 67-71、Batch 59、docs check 和 `npm run check`；
- 更新 current manifest、fixture catalog、verification ledger、coverage、
  traceability、decision register、Big Picture 和 changelog。

## 3. 实施决策

1. 使用小型 typed UI helper 复用 DOM boundary，不改造全局 form framework。
2. 以 `beginDirectorGesture` 的 `projectId + generation` 作为 active owner；
   `commit/cancel` 继续执行 Batch 70 的 freshness 检查。
3. 使用现有 store mutation 作为 update phase，依赖 active gesture 抑制中间
   history；不在本批机械重命名所有 85 个 action。
4. 对 free-draw 让 draft 保持 runtime-only；正式 path 创建后由显式 gesture
   commit 收口，避免 observer 与 gesture 产生双 history。
5. 不通过截图推导新的 LibTV source UI；本批不新增截图识别。

## 4. 验收矩阵

| 场景 | 期望 |
|---|---|
| numeric field 多次输入后 blur | 1 条 Director history |
| range/pose 多次 pointermove 后 pointerup | 1 条 Director history |
| path anchor/handle 多次 update 后 commit | 1 条 Director history |
| free path 多次 draft update 后 finish | 1 条 Director history |
| same-value / invalid / disabled | 0 条 history |
| Escape / pointercancel / outside close | baseline restore，0 条新增 history |
| owner/canvas switch 或 close | stale gesture 不得写当前 project |
| Director undo/redo | ordinary canvas graph/history 不变 |
| verifier diagnostics | console/page/request error 为 0 |

## 5. 明确不在本批

- object/group/camera/asset 的 reference-aware delete；
- last-camera policy、copy/paste、clipboard remap；
- capture/export async destination freshness；
- durable persistence、真实 mesh/panorama/resource loading；
- LibTV source-exact Director DOM/CSS、undo/redo 文案和提交时机；
- 普通 LibTV editor session 的统一 runtime；
- 全部旧 Director action 一次性迁移到 command bus。

## 6. 预期交付

- 一个可复用的 Director DOM gesture boundary helper；
- Inspector、pose、path 和 free-draw 的最小安全接入；
- Batch 71 pure/browser verifier 与结构化 runtime audit；
- 更新后的 `LIBTV-VR-024` 当前 manifest 和交接台账；
- 独立 commit/push checkpoint。

## 7. 完成状态

- [x] DOM number/range gesture boundary；
- [x] object/group/camera/path Inspector 接入；
- [x] pose 与 camera FOV slider 接入；
- [x] R3F path anchor/Bezier TransformControls 接入；
- [x] pencil/pen draft begin/commit/cancel 接入；
- [x] Escape、pointercancel、no-op 和 graph isolation verifier；
- [x] Batch 71 pure/browser gate；
- [x] 批次实施记录与结构化 runtime audit；
- [ ] 项目级 manifest、fixture、coverage、traceability 和 Hub 同步；
- [ ] 跨批回归、`npm run check`、最终 commit/push。
