// ★★★ Batch 869：★ 「当前帧关键帧」这套语义的**唯一出处**。
//
// ★ 源站 chunk `0fmehki05gkzw.js.js` 的 `cZ` 函数**逐字**（★ 逐字全文见
// ★ `docs/research/liblib-canvas-batch869-2026-10-01/raw/source-869-cz-toggle.txt`）：
//
//   f = markers.find(e => .05 >= Math.abs(e.time - h)) ?? null   // ← 当前帧命中 ±0.05s
//   m = … if (n && n.time < t - .05) return n …                    // ← 上一关键帧取点
//   x = markers.find(e => e.time > h + .05) ?? null                // ← 下一关键帧取点
//
// ★ ⇒ 源站**三处**用**同一个** 0.05 秒窗口 ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⇒ clone 把这三处
// ★ 分散在两个文件里 ⟹ ⟹ ⟹ ⟹ ⇒ ★ `DirectorTimeline.tsx`（轨道行的
// ★ 「上一／当前／下一」三键）⟹ ⟹ ⟹ ⟹ ⇒ ★ 与 `DirectorInspector.tsx`
// ★ （每个数值框右端那枚开关）⟹ ⟹ ⟹ ⟹ ⇒ ★ 且**各写各的** ⟹ ⟹ ⟹ ⟹ ⇒ ★
// ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ 本模块把「命中／取点」这一个语义收成**一个出处**。
//
// ★ ★★ 另一个容差是**同时刻 upsert**（★ **不是**命中）⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ 二者
// ★ **必须分开**，否则会出现「以为在命中、其实在 upsert」的混账：
// ★   源站 batch 36 的**逐字规格**（★ `docs/research/liblib-canvas-batch36-2026-08-26/
// ★   DIRECTOR_TIMELINE.spec.md`）原文：
// ★     `◆ 添加关键帧` captures the selected track object's complete current value;
// ★     same-time add replaces the existing keyframe value;
// ★   ⟹ ⟹ ⟹ ⟹ ⟹ ⇒ ★ 「添加关键帧」是**取当前值覆盖**⟹ ⟹ ⟹ ⟹ ⟹ ⇒ ★ **不是**切换
// ★   ⟹ ⟹ ⟹ ⟹ ⟹ ⇒ ★ 「同一时刻」用**另一个**容差（★ 0.001 ⟹ ⟹ ⟹ ⟹ ⟹ ⇒ ★ `docs/
// ★   research/beeftv-canvas-2026-09-27/SOURCE_ANALYSIS.md` §23.3 把它记作
// ★   `DIRECTOR_KEYFRAME_EPSILON = 0.001`）⟹ ⟹ ⟹ ⟹ ⟹ ⇒ ★ 源码里 store 的
// ★   `upsertTrackKeyframe` 用的就是这个数。

/** ★ 源站**逐字**的「当前帧命中」窗口（★ 秒）。★ 见本文件头 `cZ` 原文。 */
export const DIRECTOR_SOURCE_KEYFRAME_HIT_WINDOW = 0.05;

/** ★ 「同一时刻 upsert」的容差（★ 秒）⟹ ⟹ ⟹ ⟹ ⇒ ★ **不是**命中窗口。 */
export const DIRECTOR_KEYFRAME_EPSILON = 1e-3;

/** ★ 源站 `f`：★ 「当前帧**有**关键帧」⟹ ⟹ ⟹ ⟹ ⇒ ★ 落在 ±0.05s 内。 */
export function directorKeyframeHit(
  time: number,
  currentTime: number,
): boolean {
  return Math.abs(time - currentTime) <= DIRECTOR_SOURCE_KEYFRAME_HIT_WINDOW;
}

/** ★ 源站 `m`：★ 「**上一**关键帧」⟹ ⟹ ⟹ ⟹ ⇒ ★ 严格早于播放头 0.05s。 */
export function directorKeyframeEarlier(
  time: number,
  currentTime: number,
): boolean {
  return time < currentTime - DIRECTOR_SOURCE_KEYFRAME_HIT_WINDOW;
}

/** ★ 源站 `x`：★ 「**下一**关键帧」⟹ ⟹ ⟹ ⟹ ⇒ ★ 严格晚于播放头 0.05s。 */
export function directorKeyframeLater(
  time: number,
  currentTime: number,
): boolean {
  return time > currentTime + DIRECTOR_SOURCE_KEYFRAME_HIT_WINDOW;
}
