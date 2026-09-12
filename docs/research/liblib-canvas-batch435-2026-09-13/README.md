# Batch 435 — VR-017 切片：setActiveCanvas invalid target guard（zero-partial NOOP）

> 状态：`IMPLEMENTATION_RECORDED`（多画布 lifecycle 合同
> `LIBTV-VR-017` 的首个 runtime 切片；clone-only 正确性，无源站依赖）。
>
> 证据：`runtime-audit.json`、
> `docs/design-references/liblib-clone-batch435-invalid-target-guard-929-2026-09-13.png`、
> `scripts/verify-liblib-batch435.py`。

## 变更

- `src/store/canvasStore.ts` `setActiveCanvas`：目标 id 不在 registry 时
  **整体返回（NOOP）**——不写 `activeCanvasId`、不清 selection（零部分
  变更）。此前任意 id 均被无条件写入，未知 id 会使全部下游 active-canvas
  消费者（`routeReactFlowChanges`、history、viewport restore 的
  `canvases.find(...)`）解析为 undefined，形成中毒会话。

## 合同依据

- `LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md`
  §11.2 scene 9（`INVALID_TARGET`：unknown canvas ID）、
  §12 pure planner 行（switch unknown → noop / zero-partial）与
  static registry 行（unknown target guarded）。
- 既有守卫对照：`routeReactFlowChanges` 已有 `!currentCanvas` 早退
  （canvasStore.ts:3354）；`deleteCanvas` 已有 fallback
  （registry 永不失效）。本切片补上唯一未守卫的 ingress。

## 验收（verify-liblib-batch435.py，SCRIPT_RECORDED_PASS）

- **invalid_target_noop**：选中节点后分别以未知 id 与空串调用
  `setActiveCanvas` —— activeCanvasId 不变且仍可解析、selection 原样、
  canvases 与 historyByCanvas 深度一致（零部分变更）；
- **valid_switch / switch_back**：真实目标切换语义不变（selection 清空、
  active 可解析），返回后 graphs/histories 完整；
- console/pageerror/requestfailed 为 0；desktop 929 无溢出。

## 后续（VR-017 剩余缺口，未变更）

demo viewport ownership、page transaction generation、late callback、
async/resource isolation。
