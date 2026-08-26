# Batch 55：源站新鲜度复核受阻留档

> 状态：`PARTIAL_RECORDED` / `BLOCKED_BY_SOURCE_SESSION`。
> 本批只记录一次主动尝试和可复用的已有证据，不把登录态失效误写成
> LibTV 当前行为已经完成复核。

## 目标

继续推进 `LIBTV-PAR-005` / `OC-EQ-001`，检查当前 LibTV 页面壳、顶层入口、
标准图片双浮层、响应式和 overlay freshness 是否发生漂移。

## 本轮实际结果

- 目标 URL：
  `https://www.liblib.tv/canvas?spaceId=670983&projectId=5f2550d0036944e2b618f494276fa1dd`
- 接管后目标地址重定向到 `https://www.liblib.tv/`；
- 没有可用的画布登录态，无法进入目标 `spaceId/projectId` 的当前画布；
- 浏览器运行时还报告 Playwright 插件版本路径错误：
  `26.818.41509/.../browser-service.mjs` 不存在，实际安装目录为
  `26.818.61809`；
- 没有输入、生成、保存、上传、下载、连线、删除或其他 graph mutation；
- 没有修改 `src/`、FrameOS、Director、verifier 或源站状态。

这意味着本批只能关闭“尝试已记录”这一文档任务，不能关闭
`OC-EQ-001` 的 source freshness 队列。

## 可复用的已有证据

本批不重复截图识别，直接引用已有的有界样本：

- [`open-canvas-2026-08-26/LIBTV_SOURCE_FRESHNESS_2026-08-27.md`](../open-canvas-2026-08-26/LIBTV_SOURCE_FRESHNESS_2026-08-27.md)：
  41% / `929x874` / 既有选中图片态；
- [`open-canvas-2026-08-26/LIBTV_MODEL_CATALOG_FRESHNESS_2026-08-27.md`](../open-canvas-2026-08-26/LIBTV_MODEL_CATALOG_FRESHNESS_2026-08-27.md)：
  35-row current catalog；
- [`open-canvas-2026-08-26/LIBTV_GRAPH_COMPATIBILITY_STATIC_AUDIT_2026-08-27.md`](../open-canvas-2026-08-26/LIBTV_GRAPH_COMPATIBILITY_STATIC_AUDIT_2026-08-27.md)：
  current bundle/DOM graph guard 静态审计；
- [`open-canvas-2026-08-26/NEXT_EVIDENCE_ACQUISITION_PLAN.md`](../open-canvas-2026-08-26/NEXT_EVIDENCE_ACQUISITION_PLAN.md)：
  后续允许动作、停止条件和 disposable fixture 闸门。

## 当前可保留的 source fact

只保留已有日期样本直接支持的结论：

- 标准图片工具条为 `1092.5x49`、13 个动作；
- 标准工具条顶部 gap 使用 `10 + 24 * zoom`；
- 下方面板保持 `660px` screen width，gap 使用 `16 * zoom`；
- toolbar、panel 与 selected node 共享 screen center；
- 靠近 viewport 边缘时允许自然裁切，不应擅自 clamp。

这些结论不能扩展为当前页面壳、mobile、selection transition、active tool
替换或多 zoom 已在本批重新验证。

## 接力入口

下一次若浏览器恢复登录态，按 [`SOURCE_FRESHNESS_AUDIT.md`](SOURCE_FRESHNESS_AUDIT.md)
从未覆盖的 selection transition、safe zoom、mobile 和 page shell 场景开始，
不要重复测已记录的 standard image frame。

若源站仍不可用，直接转入本地 clone 可确定性验证的批次；不要在共享源站
试探输入、生成、保存、上传、下载、连线或其他不可逆动作。
