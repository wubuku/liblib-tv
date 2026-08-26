# Batch 32 Source Evidence

> 采样日期：2026-08-26  
> 页面：`https://www.liblib.tv/canvas?spaceId=670983&projectId=5f2550d0036944e2b618f494276fa1dd`

## 1. Evidence Boundary

本批先复用已经保存的登录态研究和当前页面的匿名 HTML 字符串，不把匿名
页面当作画布 DOM 证据，也不重复识别旧 contact sheet。

当前可复核的证据：

- [`../liblib-seedance-2.5-2026-08-25/live-script-string-evidence.json`](../liblib-seedance-2.5-2026-08-25/live-script-string-evidence.json)
  中保存了 `depthMapRef*` 字符串；
- 2026-08-26 请求当前 canvas HTML 后，页面嵌入的 i18n 数据仍包含同一组
  `depthMapRef*` keys；
- [`../liblib-canvas-batch28-2026-08-25/PLAN.md`](../liblib-canvas-batch28-2026-08-25/PLAN.md)
  与 [`../liblib-canvas-batch29-2026-08-25/PLAN.md`](../liblib-canvas-batch29-2026-08-25/PLAN.md)
  将该能力保留为“dialog、校验、参数和派生节点可确认”的后续候选。

当前没有：

- 本批新增的登录态深度动作捕捉截图；
- 可复用的深度动作捕捉 DOM rect、CSS 状态、动画时序；
- 具体 `{maxMin}`、`{maxSec}` 替换值；
- 可复现的深度结果媒体 URL、任务协议或完整 bundle handler。

因此本批所有入口位置、面板几何、pending node 视觉和测试 fixture 都必须
标为 clone calibration 或 clone-only decision。

## 2. Confirmed String Contract

```text
depthMapRefLabel = 深度动作捕捉
depthMapRefNodeName = 深度动作捕捉-{nodeLabel}
depthMapRefResolution = 清晰度
depthMapRefDurationExceedHint = 视频超过 {maxMin}min 处理上限
depthMapRef720pDurationHint = 720P 仅支持处理 {maxSec}s 以内的视频
depthMapRefConfirmSubmit = 确认提取
depthMapRefIntroDesc =
  提取视频深度信息，为镜头运动、人物动作和空间关系提供参考，
  减少原视频细节对生成结果的干扰。
```

These strings prove a user-facing extraction workflow is represented in the
current product assets. They do not prove that the feature is visible in every
project, that it is enabled for every video, or that the exact UI placement
matches the clone calibration.

## 3. Existing Research Linkage

- Batch 28 first identified deep motion capture as a distinct candidate beside
  audio split, frame capture and subject editing.
- Batch 29 kept it as a next candidate after frame capture and documented that
  the entry, intro, parameter and derived-node semantics were worth a separate
  source-evidence pass.
- Batch 30/31 completed the higher-confidence subject-edit path, leaving this
  capability as the next isolated workflow rather than mixing it into the
  picture-edit store.

## 4. Evidence Classification

| Observation | Classification |
|---|---|
| `深度动作捕捉` label and node-name template | source-backed string |
| `清晰度` and duration-limit placeholders | source-backed string; values unresolved |
| depth information purpose copy | source-backed string |
| standalone config panel and source-linked result workflow | inference from strings + historical plan |
| toolbar placement, panel width, colors, spinner timing | clone calibration |
| `720P / 1080P` local options and `?duration=10` | clone-only test decision |
| pending reference node and request metadata | clone-only prototype handoff |
