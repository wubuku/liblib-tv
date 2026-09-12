# Batch 443 — VR-023 Slice C：编辑器变换正确性（cover/contain 映射 + 基线修订 + 彩色标记 fixture）

> 状态：`IMPLEMENTATION_RECORDED`（media rendition/geometry 合同
> Slice C；clone-only 政策，无源站依赖；心跳批次）。
>
> 证据：`runtime-audit.json`、
> `docs/design-references/liblib-clone-batch443-annotate-mapping-929-2026-09-13.png`、
> `scripts/verify-liblib-batch443.py`。

## 变更

- **变换纯函数（权威模块新增，§7 公式）**：
  `planLibTVFitTransform`（cover=max/contain=min 缩放 + 位置偏移，
  contain 偏移非负、cover 裁剪轴偏移非正）、
  `libTVVisiblePointToIntrinsic` / `libTVIntrinsicPointToVisible`
  （帧内可见点 ↔ 归一化固有平面互映射）、
  `makeLibTVEditorBaseline`（mediaId + 声明平面 + mediaRevision +
  fit 的基线快照）。
- **基线修订捕获**：图片节点默认数据新增 `mediaRevision: 1`；
  `ImageAnnotateState` 携带 `mediaRevision` + `fit`（声明
  full-media 平面基线）；`openImageAnnotate` 传入。
- **映射暴露**：`__libtv_annotate_fit_mapping` 从打开的标注编辑器
  live DOM 帧解析变换并返回基线；标注画布（canvas）marks 由此
  映射到声明的固有平面而非帧矩形。

## 验收（verify-liblib-batch443.py，SCRIPT_RECORDED_PASS —— 彩色标记 fixture）

- 打开 fixture 图片的标注编辑器 → 映射存在、基线 mediaRevision ≥1、
  fit=contain；
- contain 缩放 = min(轴缩放)、偏移非负、渲染尺寸 = 固有 × 缩放
  （§7.1 公式逐项核对）；
- **红色标记**绘制于固有点 (0.25, 0.25) 的映射位置 → 该像素读回
  红色；visible→intrinsic 往返精确返回 (0.25, 0.25)（误差 <1e-6）；
  媒体平面远角 (0.9, 0.9) 不受污染；
- console/pageerror/requestfailed 为 0；无溢出。

## 后续（VR-023）

Slice D（本地混合比例输出 fixture：per-output 元数据与切换策略）。
