# Batch 441 — VR-023 Slice A：尺寸权威分类 + 冲突可观测（无视觉变化）

> 状态：`IMPLEMENTATION_RECORDED`（media rendition/geometry 合同首个
> runtime 切片；clone-only 诊断，无源站依赖；心跳批次）。
>
> 证据：`runtime-audit.json`、
> `docs/design-references/liblib-clone-batch441-dimension-authorities-929-2026-09-13.png`、
> `scripts/verify-liblib-batch441.py`。

## 变更

- **`src/lib/libtvMediaDimensionAuthority.ts`（新，纯模块）**：
  - 五权威分类表（GI-102：intrinsic / request / node-frame / measured /
    export-frame + unknown）：`width/height`(data)=intrinsic 声明值
    （解码未验证——静态审计 2026-08-27 的发现）、`resolution`=
    intrinsic 显示串投影、`generationSettings`/`aspectRatio`=request
    显示串（§3.4：opaque 展示投影，永非规范几何）、`editorHeight`=
    unknown 标量（编辑器面板表面态）；
  - `parseLibTVDisplayDimensions`：解析 "1280 × 720"/"622x350"；
  - `detectLibTVDimensionAuthorityConflicts` 三类冲突：
    `intrinsic-display-string-only`（视频只有分辨率显示串、无类型化
    尺寸）、`request-display-string-only`（图片只有 generationSettings
    展示串、无规范 request 字段）、`derived-frame-generic-default`
    （派生节点仍持通用 512×288 帧、而源固有比例差 >2%——静态审计
    「隐性 16:9 重构」发现的观测化）。
- **`src/app/page.tsx`**：只读诊断挂载
  （`__libtv_detect_dimension_conflicts` / `__libtv_classify_dimension_field`
  / `__libtv_parse_display_dimensions`），经边装配派生谱系；不改状态、
  不改渲染。

## 验收（verify-liblib-batch441.py，SCRIPT_RECORDED_PASS）

- **pure_classification**：分类表与显示串解析逐项精确；
- **fixture_scan_readonly**：扫描前后 canvases JSON 逐字节不变；
  fixture 图片节点出 `request-display-string-only`、视频节点出
  `intrinsic-display-string-only`；
- **derived_generic_frame_detection**：真实 createSmartMatting 派生
  节点（通用 512×288 帧）在非 16:9 源下被标记
  `derived-frame-generic-default`；
- console/pageerror/requestfailed 为 0；无溢出。

## 后续（VR-023）

Slice B（确定性 frame/rendition 政策）、Slice C（编辑器变换正确性）、
Slice D（本地混合比例 fixture）。
