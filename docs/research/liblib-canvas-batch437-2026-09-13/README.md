# Batch 437 — VR-017 Slice E：async/resource isolation（延迟完成按属主画布提交）

> 状态：`IMPLEMENTATION_RECORDED`（多画布 lifecycle 合同 Slice E；
> clone-only 正确性，无源站依赖；心跳批次）。
>
> 证据：`runtime-audit.json`、
> `docs/design-references/liblib-clone-batch437-background-commit-929-2026-09-13.png`、
> `scripts/verify-liblib-batch437.py`。

## 变更（src/store/canvasStore.ts）

§5.7 的区分此前缺失：四个**延迟定时器完成**的派生节点动作
（`createAudioSplit` / `createDepthMotionCapture` / `createSmartMatting` /
`createPictureEdit`，VideoNode 480–600ms 模拟任务）在完成时按**当时
激活画布**解析源节点——若完成时其它画布激活，写入丢失（null）且无
稳定处置。本批：

- 四动作改为**按源节点属主定位画布**（declared-canvas commit），
  源节点不存在时返回稳定 null 处置；
- selection 写入**仅在目标画布 === 激活画布时**执行（GC-056：后台
  提交不得偷走激活画布选中）；graph/edge/history 写入按属主画布；
- batch-268 的 0ms 选中迁移（组创建后延迟一拍迁移选中到容器）补
  GC-056 守卫：武装画布仍激活且仍持有组节点时才提交；
- 同步点击调用的动作（`createVideoFrameCapture` /
  `createLongVideoProcess` / Director 两个）保持激活画布解析不变
  （§5.7 即时命令类，构造上正确）。

## 处置声明（§5.7 product decision）

VideoNode 卸载清理（既有）会清掉七个挂起定时器 → **切换画布即取消**
挂起模拟任务（canceled，非后台继续）。这是本 clone 的声明处置；
后台继续 + 结果通知归 Slice E 的产品裁决（CLONE_DECISION 保持）。

## 验收（verify-liblib-batch437.py，SCRIPT_RECORDED_PASS）

- **declared_canvas_commit（GC-056）**：canvas-2 的源节点在 canvas-1
  激活时触发 createSmartMatting —— 节点/边/历史落在 canvas-2（属主），
  canvas-1 逐字节不变，选中不被偷走；切回后输出节点与连线在位；
- **stale_disposition**：未知源 id → 稳定 null，零变更；
- **switch_cancels_pending_task**：真实 matting 提交（submitting 态）
  被切换打断 → 挂起任务取消，两侧画布均无迟到产物；
- console/pageerror/requestfailed 为 0；desktop 929 无溢出。

## 后续（VR-017 剩余）

demo viewport ownership 余项（resize anchor、live/stable endpoint）。
