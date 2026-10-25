# 源站逐字规格摘录（★ batch 36 解码源站 chunk 得到的**产品合同**）

## 出处

- 文件：`docs/research/liblib-canvas-batch36-2026-08-26/DIRECTOR_TIMELINE.spec.md`
- 它是 **2026-08-26 从源站 chunk 逐字解码**得到的规格 ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ 不是
  clone 的设计文档 ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ 也不是事后补写的解释。
- 同目录的 `SOURCE_EVIDENCE.md` 记着解码时的 chunk 路径与 sha256。

## 逐字摘录

```text
### Track And Keyframe Commands

- `+ 轨道` creates a transform or camera track for the selected object;
- duplicate object tracks are not created;
- `◆ 添加关键帧` captures the selected track object's complete current value;
- same-time add replaces the existing keyframe value;
- delete removes only the selected keyframe;
- previous/next searches all keyframes and skips the current timestamp using a
  small epsilon.
```

## ★ 对本批的三条直接结论

1. 「◆ 添加关键帧」＝**取当前值、同时刻覆盖既有值** ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ **不是**
   切换 ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ 所以 clone 的 `addTimelineKeyframe()`（→
   `upsertTrackKeyframe`）**本来就是源站语义**。
2. 「same-time add replaces」里的「同一时刻」用**另一个**容差（★ 0.001 ⟹ ⟹ ⟹ ⟹ ⇒
   ★ ⟹ 见 `SOURCE_ANALYSIS.md` §23.3）⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ 它与「当前帧命中」那个
   ±0.05s 窗口**必须分开**。
3. 「previous/next searches all keyframes and skips the current timestamp using a
   **small epsilon**」⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ 与源站 chunk 的 `cZ` 逐字对上（★ `.05`）⟹ ⟹ ⟹ ⟹ ⇒ ★
   ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ 命中窗口与「上一／下一」取点窗口是**同一个数**。
