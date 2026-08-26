"use client";

import { useEffect, useMemo, useRef } from "react";
import type { PointerEvent as ReactPointerEvent } from "react";
import {
  Camera,
  DiamondPlus,
  Move3D,
  Pause,
  Play,
  Plus,
  Repeat2,
  SkipBack,
  SkipForward,
  Trash2,
  ZoomIn,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useDirectorStore } from "@/store/directorStore";

function formatTimelineTime(seconds: number): string {
  const safeSeconds = Math.max(0, seconds);
  const minutes = Math.floor(safeSeconds / 60);
  const remaining = safeSeconds - minutes * 60;
  return `${minutes.toString().padStart(2, "0")}:${remaining
    .toFixed(2)
    .padStart(5, "0")}`;
}

export function DirectorTimeline() {
  const timeline = useDirectorStore((state) => state.timeline);
  const selectedObjectId = useDirectorStore((state) => state.selectedObjectId);
  const setTimelineTime = useDirectorStore((state) => state.setTimelineTime);
  const setTimelinePlaying = useDirectorStore(
    (state) => state.setTimelinePlaying,
  );
  const advanceTimeline = useDirectorStore((state) => state.advanceTimeline);
  const toggleTimelineLoop = useDirectorStore(
    (state) => state.toggleTimelineLoop,
  );
  const toggleAutoKeyframe = useDirectorStore(
    (state) => state.toggleAutoKeyframe,
  );
  const setTimelineZoom = useDirectorStore((state) => state.setTimelineZoom);
  const selectTimelineTrack = useDirectorStore(
    (state) => state.selectTimelineTrack,
  );
  const selectTimelineKeyframe = useDirectorStore(
    (state) => state.selectTimelineKeyframe,
  );
  const addTimelineTrack = useDirectorStore(
    (state) => state.addTimelineTrack,
  );
  const removeTimelineTrack = useDirectorStore(
    (state) => state.removeTimelineTrack,
  );
  const addTimelineKeyframe = useDirectorStore(
    (state) => state.addTimelineKeyframe,
  );
  const deleteTimelineKeyframe = useDirectorStore(
    (state) => state.deleteTimelineKeyframe,
  );
  const seekTimelineKeyframe = useDirectorStore(
    (state) => state.seekTimelineKeyframe,
  );
  const timelineCanvasRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!timeline.isPlaying) return;
    let frame = 0;
    let previous = performance.now();
    const tick = (now: number) => {
      const deltaSeconds = Math.min((now - previous) / 1000, 0.1);
      previous = now;
      advanceTimeline(deltaSeconds);
      if (useDirectorStore.getState().timeline.isPlaying) {
        frame = window.requestAnimationFrame(tick);
      }
    };
    frame = window.requestAnimationFrame(tick);
    return () => window.cancelAnimationFrame(frame);
  }, [advanceTimeline, timeline.isPlaying]);

  const ticks = useMemo(
    () =>
      Array.from(
        { length: Math.floor(timeline.duration) + 1 },
        (_, index) => index,
      ),
    [timeline.duration],
  );
  const selectedTrack =
    timeline.tracks.find((track) => track.id === timeline.selectedTrackId) ??
    null;
  const hasSelectedObjectTrack = timeline.tracks.some(
    (track) => track.objectId === selectedObjectId,
  );
  const timelineWidth = Math.max(
    640,
    timeline.duration * 80 * timeline.zoom,
  );
  const playheadPosition =
    timeline.duration > 0
      ? (timeline.currentTime / timeline.duration) * 100
      : 0;

  const seekFromClientX = (clientX: number) => {
    const element = timelineCanvasRef.current;
    if (!element) return;
    const rect = element.getBoundingClientRect();
    const progress = Math.min(
      Math.max((clientX - rect.left) / rect.width, 0),
      1,
    );
    setTimelineTime(progress * timeline.duration);
  };

  const beginScrub = (event: ReactPointerEvent<HTMLElement>) => {
    if (
      event.target instanceof Element &&
      event.target.closest("[data-director-keyframe-id]")
    ) {
      return;
    }
    event.preventDefault();
    setTimelinePlaying(false);
    seekFromClientX(event.clientX);

    const handleMove = (pointerEvent: PointerEvent) => {
      seekFromClientX(pointerEvent.clientX);
    };
    const handleUp = () => {
      window.removeEventListener("pointermove", handleMove);
      window.removeEventListener("pointerup", handleUp);
    };
    window.addEventListener("pointermove", handleMove);
    window.addEventListener("pointerup", handleUp, { once: true });
  };

  return (
    <section
      data-director-timeline
      className="flex h-[196px] shrink-0 flex-col border-t border-white/[0.08] bg-[#161616] max-[899px]:h-[176px]"
    >
      <header
        data-director-timeline-controls
        className="flex h-10 shrink-0 items-center gap-1 overflow-x-auto border-b border-white/[0.07] px-2"
      >
        <h2 className="mr-2 shrink-0 text-xs font-medium text-[#d8d8d8]">
          动画时间轴
        </h2>
        <button
          type="button"
          data-director-playback
          aria-label={timeline.isPlaying ? "暂停" : "播放"}
          title={timeline.isPlaying ? "暂停" : "播放"}
          aria-pressed={timeline.isPlaying}
          onClick={() => setTimelinePlaying(!timeline.isPlaying)}
          className="flex h-7 w-7 shrink-0 items-center justify-center rounded text-[#bcbcbc] hover:bg-white/[0.06] hover:text-white"
        >
          {timeline.isPlaying ? <Pause size={14} /> : <Play size={14} />}
        </button>
        <button
          type="button"
          aria-label="上一关键帧"
          title="上一关键帧"
          onClick={() => seekTimelineKeyframe(-1)}
          className="flex h-7 w-7 shrink-0 items-center justify-center rounded text-[#858585] hover:bg-white/[0.06] hover:text-white"
        >
          <SkipBack size={14} />
        </button>
        <button
          type="button"
          aria-label="下一关键帧"
          title="下一关键帧"
          onClick={() => seekTimelineKeyframe(1)}
          className="flex h-7 w-7 shrink-0 items-center justify-center rounded text-[#858585] hover:bg-white/[0.06] hover:text-white"
        >
          <SkipForward size={14} />
        </button>
        <button
          type="button"
          data-director-loop
          aria-label="循环播放"
          title="循环播放"
          aria-pressed={timeline.loop}
          onClick={toggleTimelineLoop}
          className={cn(
            "flex h-7 w-7 shrink-0 items-center justify-center rounded text-[#777] hover:bg-white/[0.06] hover:text-white",
            timeline.loop && "bg-white/[0.07] text-[#5ddcff]",
          )}
        >
          <Repeat2 size={14} />
        </button>
        <span
          data-director-timeline-time={timeline.currentTime.toFixed(3)}
          className="w-[108px] shrink-0 text-center text-[11px] tabular-nums text-[#a7a7a7]"
        >
          {formatTimelineTime(timeline.currentTime)} /{" "}
          {formatTimelineTime(timeline.duration)}
        </span>
        <span className="mx-1 h-5 w-px shrink-0 bg-white/10" />
        <button
          type="button"
          data-director-auto-keyframe
          aria-pressed={timeline.autoKeyframe}
          onClick={toggleAutoKeyframe}
          className={cn(
            "flex h-7 shrink-0 items-center gap-1.5 rounded px-2 text-[11px] text-[#858585] hover:bg-white/[0.06] hover:text-white",
            timeline.autoKeyframe && "bg-white/[0.07] text-[#5ddcff]",
          )}
        >
          <span
            className={cn(
              "h-2 w-2 rounded-full border border-current",
              timeline.autoKeyframe && "bg-current",
            )}
          />
          自动关键帧
        </button>
        <button
          type="button"
          data-director-add-track
          disabled={!selectedObjectId || hasSelectedObjectTrack}
          onClick={() => addTimelineTrack()}
          className="flex h-7 shrink-0 items-center gap-1 rounded px-2 text-[11px] text-[#a7a7a7] hover:bg-white/[0.06] hover:text-white disabled:text-[#4f4f4f]"
        >
          <Plus size={13} />
          轨道
        </button>
        <button
          type="button"
          data-director-add-keyframe
          disabled={!selectedTrack}
          onClick={() => addTimelineKeyframe()}
          className="flex h-7 shrink-0 items-center gap-1 rounded px-2 text-[11px] text-[#a7a7a7] hover:bg-white/[0.06] hover:text-white disabled:text-[#4f4f4f]"
        >
          <DiamondPlus size={13} />
          添加关键帧
        </button>
        <button
          type="button"
          data-director-delete-keyframe
          aria-label="删除关键帧"
          title="删除关键帧"
          disabled={!timeline.selectedKeyframeId}
          onClick={() => deleteTimelineKeyframe()}
          className="flex h-7 w-7 shrink-0 items-center justify-center rounded text-[#777] hover:bg-white/[0.06] hover:text-[#f08d8d] disabled:text-[#3f3f3f]"
        >
          <Trash2 size={13} />
        </button>
        <span className="mx-1 h-5 w-px shrink-0 bg-white/10" />
        <label className="flex h-7 shrink-0 items-center gap-1.5 text-[#777]">
          <ZoomIn size={13} />
          <input
            type="range"
            aria-label="时间轴缩放"
            data-director-timeline-zoom
            min="0.75"
            max="2.5"
            step="0.25"
            value={timeline.zoom}
            onChange={(event) =>
              setTimelineZoom(Number(event.currentTarget.value))
            }
            className="w-20 accent-[#09caf5]"
          />
        </label>
      </header>

      <div className="flex min-h-0 flex-1">
        <div className="w-[220px] shrink-0 border-r border-white/[0.07] max-[899px]:w-[132px]">
          <div className="flex h-7 items-center px-2 text-[10px] text-[#666]">
            轨道
          </div>
          {timeline.tracks.length === 0 ? (
            <div className="px-3 py-6 text-center text-[11px] text-[#555]">
              选择对象后新建轨道
            </div>
          ) : (
            timeline.tracks.map((track) => {
              const selected = track.id === timeline.selectedTrackId;
              return (
                <div
                  key={track.id}
                  data-director-track-label={track.id}
                  className={cn(
                    "flex h-8 items-center border-t border-white/[0.045] px-2",
                    selected && "bg-[#09caf5]/[0.08]",
                  )}
                >
                  <button
                    type="button"
                    onClick={() => selectTimelineTrack(track.id)}
                    className="flex min-w-0 flex-1 items-center gap-1.5 text-left"
                  >
                    <span
                      className={selected ? "text-[#5ddcff]" : "text-[#696969]"}
                    >
                      {track.kind === "camera" ? (
                        <Camera size={12} />
                      ) : (
                        <Move3D size={12} />
                      )}
                    </span>
                    <span
                      className={cn(
                        "min-w-0 flex-1 truncate text-[11px] text-[#929292]",
                        selected && "text-[#d9d9d9]",
                      )}
                    >
                      {track.label}
                    </span>
                  </button>
                  {selected ? (
                    <button
                      type="button"
                      aria-label={`移除${track.label}轨道`}
                      title="移除轨道"
                      onClick={() => removeTimelineTrack(track.id)}
                      className="flex h-6 w-6 shrink-0 items-center justify-center text-[#5c5c5c] hover:text-[#f08d8d]"
                    >
                      <Trash2 size={11} />
                    </button>
                  ) : null}
                </div>
              );
            })
          )}
        </div>

        <div className="min-w-0 flex-1 overflow-x-auto overflow-y-hidden">
          <div
            ref={timelineCanvasRef}
            data-director-timeline-canvas
            className="relative min-h-full min-w-full"
            style={{ width: timelineWidth }}
          >
            <div
              data-director-timeline-ruler
              onPointerDown={beginScrub}
              className="relative h-7 cursor-ew-resize border-b border-white/[0.06] bg-[#191919]"
            >
              {ticks.map((tick) => (
                <span
                  key={tick}
                  className="absolute bottom-0 top-0 border-l border-white/[0.08]"
                  style={{ left: `${(tick / timeline.duration) * 100}%` }}
                >
                  <span className="absolute left-1 top-1 text-[9px] tabular-nums text-[#5e5e5e]">
                    {tick}s
                  </span>
                </span>
              ))}
            </div>

            {timeline.tracks.map((track) => (
              <div
                key={track.id}
                data-director-track-id={track.id}
                data-director-track-kind={track.kind}
                data-director-track-object-id={track.objectId}
                data-director-track-selected={
                  track.id === timeline.selectedTrackId
                }
                onPointerDown={beginScrub}
                className={cn(
                  "relative h-8 cursor-ew-resize border-b border-white/[0.045]",
                  track.id === timeline.selectedTrackId &&
                    "bg-[#09caf5]/[0.035]",
                )}
              >
                {ticks.map((tick) => (
                  <span
                    key={tick}
                    className="pointer-events-none absolute bottom-0 top-0 border-l border-white/[0.045]"
                    style={{ left: `${(tick / timeline.duration) * 100}%` }}
                  />
                ))}
                {track.keyframes.map((keyframe) => {
                  const selected =
                    keyframe.id === timeline.selectedKeyframeId;
                  return (
                    <button
                      key={keyframe.id}
                      type="button"
                      data-director-keyframe-id={keyframe.id}
                      data-director-keyframe-time={keyframe.time}
                      aria-label={`${track.label} ${formatTimelineTime(keyframe.time)} 关键帧`}
                      title={`${formatTimelineTime(keyframe.time)} 关键帧`}
                      onPointerDown={(event) => event.stopPropagation()}
                      onClick={() =>
                        selectTimelineKeyframe(track.id, keyframe.id)
                      }
                      className={cn(
                        "absolute top-1/2 z-10 h-3 w-3 -translate-x-1/2 -translate-y-1/2 rotate-45 border bg-[#7b858d]",
                        selected
                          ? "border-white bg-[#09caf5] shadow-[0_0_0_2px_rgba(9,202,245,0.2)]"
                          : "border-[#b8c0c6] hover:bg-[#b9c2c8]",
                      )}
                      style={{
                        left: `clamp(9px, ${
                          (keyframe.time / timeline.duration) * 100
                        }%, calc(100% - 9px))`,
                      }}
                    />
                  );
                })}
              </div>
            ))}

            <div
              data-director-playhead
              data-director-playhead-time={timeline.currentTime.toFixed(3)}
              className="pointer-events-none absolute bottom-0 top-0 z-20 w-px bg-[#09caf5] shadow-[0_0_6px_rgba(9,202,245,0.48)]"
              style={{ left: `${playheadPosition}%` }}
            >
              <span className="absolute -left-1.5 top-0 h-0 w-0 border-l-[6px] border-r-[6px] border-t-[7px] border-l-transparent border-r-transparent border-t-[#09caf5]" />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
