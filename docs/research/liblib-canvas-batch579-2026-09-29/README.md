# Batch 579 — 关键帧菱形点击 seek 播头

> 状态：`SCRIPT_RECORDED_PASS`（commit 本批）。源站证据：CDP 补采
> （截图 63，batch 578）——播头在 2s 时点击 0s 关键帧菱形，播头跳回
> 0s、时间输入同步 0.00：菱形点击 = 选中 + seek 到关键帧时间。

## 合同

- 关键帧菱形 onClick：`selectTimelineKeyframe(track.id, keyframe.id)` +
  `setTimelineTime(keyframe.time)`——选中并 seek；
- 播头 scrub（beginScrub）仍跳过菱形（不互相干扰，既有守卫不变）。

## 内容

- `src/components/director/DirectorTimeline.tsx`（菱形 onClick 追加
  setTimelineTime(keyframe.time)）；
- `scripts/verify-liblib-batch579.py`（5 检查：菱形可见、播头离开、
  点击 seek 到关键帧实际时间（动态读取 data-director-keyframe-time，
  因 selectObject 会重置播头——实测留痕）、关键帧选中）；
- 回归：batch 36/70/553 全绿；typecheck 净；lint 0 error。
- `runtime-audit.json`：本目录。
