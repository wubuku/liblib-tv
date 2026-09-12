# Batch 439 — VGP §6.3/DQ-003 live/stable endpoint phase（逐帧 live、手势端点一次 stable）

> 状态：`IMPLEMENTATION_RECORDED`（viewport 合同 live/stable 相变切片；
> clone-only 正确性，无源站依赖；心跳批次）。
>
> 证据：`runtime-audit.json`、
> `docs/design-references/liblib-clone-batch439-endpoint-phase-929-2026-09-13.png`、
> `scripts/verify-liblib-batch439.py`。

## 变更（src/app/page.tsx）

此前 `onViewportChange` 每帧都写 store viewport（每帧一次稳定写入）。
本批按 §6.3/DQ-003 分相：

- **live 相**（`onViewportChange` 逐帧）：只更新 live 投影
  （`setFlowViewport` + zoom 读数），不写 store、不翻所有权，日志记
  `live-frame`（新 reason）；
- **stable 端点**（新 `onMoveEnd`）：手势结束提交一次稳定端点——
  store 写入 + bootstrap→stable 所有权翻转 + `viewport-accepted`；
- **显式命令**保持默认立即稳定提交（§6.4 无动画命令允许单次验证
  提交）——`__libtv_apply_viewport_event` 两参语义不变，batch 65
  验证器契约保持；batch 438 resize anchor 观察器的直接稳定提交亦
  不变。

## 验收（verify-liblib-batch439.py，SCRIPT_RECORDED_PASS）

- **bootstrap_pan_endpoint**：连续 wheel 手势的帧记为
  `live-frame`（ownership 仍 bootstrap），端点一次翻转为 stable 并
  写 store；live 帧先于端点；
- **explicit_command_still_stable**：两参调用返回
  `viewport-accepted` 且 store 立即写入（batch 65 语义保持）；
- console/pageerror/requestfailed 为 0；无溢出。

## 实现注记

- xyflow 的 panOnScroll 处理器在手势**最后一个 wheel tick 后 150ms**
  才排程 end（首个 tick 只触发 start）——batch 438 验证器的单 tick
  wheel 相应更新为多 tick 手势（端点语义变更的预期联动）。
- 挂起期间的 store 视口可能滞后至多一个手势（切换时最后一帧丢失）
  ——GC-049 陈旧回调跳过语义主导，属声明取舍。

## 后续

VGP 合同 runtime 余项：generic generation/host epoch（与 §5.3 一并
gated）。
