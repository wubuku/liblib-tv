"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type { PointerEvent as ReactPointerEvent } from "react";
import {
  Camera,
  ChartSpline,
  Circle,
  DiamondPlus,
  Minus,
  Move3D,
  Pause,
  PenTool,
  PersonStanding,
  Pencil,
  Play,
  Plus,
  RectangleHorizontal,
  Repeat2,
  Route,
  SkipBack,
  SkipForward,
  Trash2,
  Waypoints,
  Users,
  X,
  ZoomIn,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useDirectorStore } from "@/store/directorStore";
import { DirectorCurveEditor } from "@/components/director/DirectorCurveEditor";
import {
  DIRECTOR_CAMERA_MOTION_PRESETS,
  type DirectorCameraMotionPresetMode,
} from "@/components/director/directorCameraPresets";

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
  const objects = useDirectorStore((state) => state.objects);
  const selectedObjectId = useDirectorStore((state) => state.selectedObjectId);
  const selectedGroupId = useDirectorStore((state) => state.selectedGroupId);
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
  const setTimelineEditorMode = useDirectorStore(
    (state) => state.setTimelineEditorMode,
  );
  const createMotionPath = useDirectorStore(
    (state) => state.createMotionPath,
  );
  const applyCameraMotionPreset = useDirectorStore(
    (state) => state.applyCameraMotionPreset,
  );
  const startMotionPathDrawing = useDirectorStore(
    (state) => state.startMotionPathDrawing,
  );
  const beginDirectorGesture = useDirectorStore(
    (state) => state.beginDirectorGesture,
  );
  const toggleMotionPathEnabled = useDirectorStore(
    (state) => state.toggleMotionPathEnabled,
  );
  const toggleMotionPathOrient = useDirectorStore(
    (state) => state.toggleMotionPathOrient,
  );
  const deleteMotionPath = useDirectorStore(
    (state) => state.deleteMotionPath,
  );
  const timelineRootRef = useRef<HTMLElement>(null);
  const timelineCanvasRef = useRef<HTMLDivElement>(null);
  const pathTriggerRef = useRef<HTMLButtonElement>(null);
  const pathMenuRef = useRef<HTMLDivElement>(null);
  const presetTriggerRef = useRef<HTMLButtonElement>(null);
  const presetPanelRef = useRef<HTMLDivElement>(null);
  const [pathMenuLeft, setPathMenuLeft] = useState<number | null>(null);
  const [presetPanelLeft, setPresetPanelLeft] = useState<number | null>(null);
  const [presetMode, setPresetMode] =
    useState<DirectorCameraMotionPresetMode>("replace");

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
  const selectedPath = selectedTrack?.motionPathId
    ? timeline.motionPaths.find(
        (path) => path.id === selectedTrack.motionPathId,
      ) ?? null
    : null;
  const selectedTrackObject =
    selectedTrack?.kind === "group"
      ? undefined
      : objects.find((object) => object.id === selectedTrack?.objectId);
  const cameraFollowActive = Boolean(
    selectedTrackObject?.camera?.followTargetId,
  );
  const selectedPresetApplication =
    timeline.cameraMotionPreset.application?.trackId === selectedTrack?.id
      ? timeline.cameraMotionPreset.application
      : null;
  const presetError = timeline.cameraMotionPreset.error;
  const selectedPresetError =
    presetError &&
    presetError.trackId === selectedTrack?.id &&
    presetError.mode === presetMode
      ? presetError
      : null;
  const hasSelectedObjectTrack = timeline.tracks.some(
    (track) =>
      selectedGroupId
        ? track.kind === "group" && track.groupId === selectedGroupId
        : track.objectId === selectedObjectId && track.kind !== "pose",
  );
  const timelineWidth = Math.max(
    640,
    timeline.duration * 80 * timeline.zoom,
  );
  const playheadPosition =
    timeline.duration > 0
      ? (timeline.currentTime / timeline.duration) * 100
      : 0;

  useEffect(() => {
    if (pathMenuLeft === null) return;
    const close = (event: PointerEvent) => {
      const target = event.target;
      if (
        target instanceof Node &&
        (pathMenuRef.current?.contains(target) ||
          pathTriggerRef.current?.contains(target))
      ) {
        return;
      }
      setPathMenuLeft(null);
    };
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setPathMenuLeft(null);
    };
    window.addEventListener("pointerdown", close);
    window.addEventListener("keydown", closeOnEscape);
    return () => {
      window.removeEventListener("pointerdown", close);
      window.removeEventListener("keydown", closeOnEscape);
    };
  }, [pathMenuLeft]);

  useEffect(() => {
    if (presetPanelLeft === null) return;
    const close = (event: PointerEvent) => {
      const target = event.target;
      if (
        target instanceof Node &&
        (presetPanelRef.current?.contains(target) ||
          presetTriggerRef.current?.contains(target))
      ) {
        return;
      }
      setPresetPanelLeft(null);
    };
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setPresetPanelLeft(null);
    };
    window.addEventListener("pointerdown", close);
    window.addEventListener("keydown", closeOnEscape);
    return () => {
      window.removeEventListener("pointerdown", close);
      window.removeEventListener("keydown", closeOnEscape);
    };
  }, [presetPanelLeft]);

  const togglePathMenu = () => {
    if (cameraFollowActive) return;
    setPresetPanelLeft(null);
    if (pathMenuLeft !== null) {
      setPathMenuLeft(null);
      return;
    }
    const root = timelineRootRef.current?.getBoundingClientRect();
    const trigger = pathTriggerRef.current?.getBoundingClientRect();
    if (!root || !trigger) return;
    setPathMenuLeft(
      Math.max(8, Math.min(trigger.left - root.left, root.width - 176)),
    );
  };

  const togglePresetPanel = () => {
    if (selectedTrack?.kind !== "camera" || cameraFollowActive) return;
    if (presetPanelLeft !== null) {
      setPresetPanelLeft(null);
      return;
    }
    const root = timelineRootRef.current?.getBoundingClientRect();
    const trigger = presetTriggerRef.current?.getBoundingClientRect();
    if (!root || !trigger) return;
    setPathMenuLeft(null);
    setPresetPanelLeft(
      Math.max(8, Math.min(trigger.left - root.left, root.width - 312)),
    );
  };

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
      ref={timelineRootRef}
      data-director-timeline
      data-director-timeline-mode={timeline.editorMode}
      className="relative flex h-[196px] shrink-0 flex-col overflow-visible border-t border-white/[0.08] bg-[#161616] max-[899px]:h-[176px]"
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
          ref={presetTriggerRef}
          type="button"
          data-director-camera-preset-trigger
          disabled={selectedTrack?.kind !== "camera" || cameraFollowActive}
          title={
            cameraFollowActive
              ? "跟随目标时不可使用预设运镜"
              : undefined
          }
          aria-expanded={presetPanelLeft !== null}
          onClick={togglePresetPanel}
          className="flex h-7 shrink-0 items-center gap-1 rounded px-2 text-[11px] text-[#a7a7a7] hover:bg-white/[0.06] hover:text-white disabled:text-[#4f4f4f]"
        >
          <Camera size={13} />
          预设运镜
        </button>
        {cameraFollowActive && selectedTrack?.kind === "camera" ? (
          <span
            data-director-camera-preset-error
            className="shrink-0 text-[10px] text-[#c9a36c]"
          >
            跟随目标时不可使用预设运镜
          </span>
        ) : null}
        <button
          ref={pathTriggerRef}
          type="button"
          data-director-create-motion-path
          disabled={
            !selectedTrack ||
            selectedTrack.kind === "pose" ||
            selectedTrack.kind === "group" ||
            cameraFollowActive
          }
          title={
            cameraFollowActive
              ? "请先关闭机位跟随，再绘制轨迹"
              : undefined
          }
          aria-expanded={pathMenuLeft !== null}
          onClick={togglePathMenu}
          className="flex h-7 shrink-0 items-center gap-1 rounded px-2 text-[11px] text-[#a7a7a7] hover:bg-white/[0.06] hover:text-white disabled:text-[#4f4f4f]"
        >
          <Route size={13} />
          创建运动轨迹
        </button>
        {cameraFollowActive ? (
          <span
            data-director-camera-follow-conflict
            className="shrink-0 text-[10px] text-[#c9a36c]"
          >
            请先关闭机位跟随，再绘制轨迹
          </span>
        ) : null}
        <button
          type="button"
          data-director-open-curve-editor
          disabled={!selectedTrack}
          aria-pressed={timeline.editorMode === "curve"}
          onClick={() => setTimelineEditorMode("curve")}
          className={cn(
            "flex h-7 shrink-0 items-center gap-1 rounded px-2 text-[11px] text-[#a7a7a7] hover:bg-white/[0.06] hover:text-white disabled:text-[#4f4f4f]",
            timeline.editorMode === "curve" &&
              "bg-white/[0.07] text-[#5ddcff]",
          )}
        >
          <ChartSpline size={13} />
          曲线编辑器
        </button>
        {selectedPath ? (
          <>
            <button
              type="button"
              data-director-motion-path-enabled={selectedPath.id}
              aria-label="启用曲线"
              title="启用曲线"
              aria-pressed={selectedPath.enabled}
              onClick={() => toggleMotionPathEnabled(selectedPath.id)}
              className={cn(
                "flex h-7 shrink-0 items-center gap-1 rounded px-2 text-[11px] text-[#777] hover:bg-white/[0.06] hover:text-white",
                selectedPath.enabled && "bg-white/[0.07] text-[#5ddcff]",
              )}
            >
              <Route size={13} />
              启用曲线
            </button>
            {selectedTrack?.kind === "transform" ? (
              <button
                type="button"
                data-director-motion-path-orient={selectedPath.id}
                aria-label="绑定对象沿路径朝向"
                title="绑定对象沿路径朝向"
                aria-pressed={selectedPath.orientToPath}
                onClick={() => toggleMotionPathOrient(selectedPath.id)}
                className={cn(
                  "flex h-7 shrink-0 items-center gap-1 rounded px-2 text-[11px] text-[#777] hover:bg-white/[0.06] hover:text-white",
                  selectedPath.orientToPath &&
                    "bg-white/[0.07] text-[#5ddcff]",
                )}
              >
                <Waypoints size={13} />
                沿路径朝向
              </button>
            ) : null}
            <button
              type="button"
              data-director-delete-motion-path={selectedPath.id}
              aria-label="删除曲线"
              title="删除曲线"
              onClick={() => deleteMotionPath(selectedPath.id)}
              className="flex h-7 w-7 shrink-0 items-center justify-center rounded text-[#777] hover:bg-white/[0.06] hover:text-[#f08d8d]"
            >
              <Trash2 size={13} />
            </button>
          </>
        ) : null}
        <button
          type="button"
          data-director-add-track
          disabled={
            (!selectedObjectId && !selectedGroupId) || hasSelectedObjectTrack
          }
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

      {presetPanelLeft !== null ? (
        <div
          ref={presetPanelRef}
          data-director-camera-preset-panel
          data-director-camera-preset-panel-mode={presetMode}
          className="absolute bottom-full z-50 max-h-[calc(100vh-88px)] w-[304px] max-w-[calc(100%-16px)] overflow-hidden rounded border border-white/[0.1] bg-[#202020] shadow-[0_16px_38px_rgba(0,0,0,0.48)]"
          style={{ left: presetPanelLeft }}
        >
          <header className="flex h-10 items-center border-b border-white/[0.07] px-3">
            <Camera size={14} className="text-[#66d9f4]" />
            <h3 className="ml-2 text-[11px] font-medium text-[#dedede]">
              预设运镜
            </h3>
            <span className="ml-auto text-[9px] text-[#5f5f5f]">预设</span>
            <button
              type="button"
              aria-label="关闭预设运镜"
              title="关闭"
              onClick={() => setPresetPanelLeft(null)}
              className="ml-1 flex h-7 w-7 items-center justify-center rounded text-[#727272] hover:bg-white/[0.06] hover:text-white"
            >
              <X size={13} />
            </button>
          </header>

          <div className="max-h-[calc(100vh-136px)] overflow-y-auto p-3">
            <div
              data-director-camera-preset-mode={presetMode}
              className="grid h-8 grid-cols-2 gap-1 rounded border border-white/[0.08] bg-[#181818] p-0.5"
            >
              {(
                [
                  ["replace", "替换运镜"],
                  ["append", "追加运镜"],
                ] as const
              ).map(([mode, label]) => (
                <button
                  key={mode}
                  type="button"
                  data-director-camera-preset-mode-option={mode}
                  aria-pressed={presetMode === mode}
                  onClick={() => setPresetMode(mode)}
                  className={cn(
                    "rounded text-[10px] text-[#818181] hover:text-white",
                    presetMode === mode &&
                      "bg-[#303030] text-[#6eddf6]",
                  )}
                >
                  {label}
                </button>
              ))}
            </div>

            <div className="mt-2 grid grid-cols-2 gap-1.5">
              {DIRECTOR_CAMERA_MOTION_PRESETS.map((preset) => {
                const active =
                  selectedPresetApplication?.preset === preset.id &&
                  selectedPresetApplication.mode === presetMode;
                return (
                  <button
                    key={preset.id}
                    type="button"
                    data-director-camera-preset-option={preset.id}
                    aria-pressed={active}
                    onClick={() =>
                      applyCameraMotionPreset(
                        preset.id,
                        presetMode,
                        selectedTrack?.id,
                      )
                    }
                    className={cn(
                      "flex h-8 min-w-0 items-center justify-center gap-1.5 rounded border border-white/[0.07] bg-[#252525] px-2 text-[10px] text-[#9b9b9b] hover:border-white/[0.14] hover:text-white",
                      active &&
                        "border-[#65d9f4]/35 bg-[#0c6579]/20 text-[#78e0f7]",
                    )}
                  >
                    {preset.id === "orbit" ? (
                      <Circle size={12} />
                    ) : preset.id === "half-arc" ? (
                      <Waypoints size={12} />
                    ) : preset.id === "spiral-up" ? (
                      <Route size={12} />
                    ) : (
                      <Move3D size={12} />
                    )}
                    <span className="truncate">{preset.label}</span>
                  </button>
                );
              })}
            </div>

            <div className="mt-2 min-h-8 border-t border-white/[0.07] pt-2">
              {selectedPresetError ? (
                <p
                  data-director-camera-preset-error
                  className="text-[9px] leading-4 text-[#d5a86d]"
                >
                  {selectedPresetError.message}
                </p>
              ) : selectedPresetApplication ? (
                <p
                  data-director-camera-preset-status
                  data-preset={selectedPresetApplication.preset}
                  data-mode={selectedPresetApplication.mode}
                  data-start-time={selectedPresetApplication.startTime}
                  data-end-time={selectedPresetApplication.endTime}
                  data-keyframe-count={
                    selectedPresetApplication.generatedKeyframeIds.length
                  }
                  className="text-[9px] leading-4 text-[#72d995]"
                >
                  {selectedPresetApplication.mode === "replace"
                    ? "替换运镜"
                    : "追加运镜"}
                  {" · "}
                  {
                    DIRECTOR_CAMERA_MOTION_PRESETS.find(
                      (item) =>
                        item.id === selectedPresetApplication.preset,
                    )?.label
                  }
                </p>
              ) : (
                <p className="text-[9px] leading-4 text-[#5f5f5f]">预设</p>
              )}
            </div>
          </div>
        </div>
      ) : null}

      {pathMenuLeft !== null ? (
        <div
          ref={pathMenuRef}
          data-director-motion-path-menu
          className="absolute top-10 z-50 w-44 border border-white/[0.1] bg-[#232323] p-1 shadow-[0_12px_30px_rgba(0,0,0,0.42)]"
          style={{ left: pathMenuLeft }}
        >
          <div
            data-director-motion-path-free-draw
            className="px-2 pb-1 pt-1.5 text-[10px] text-[#626262]"
          >
            自由绘制
          </div>
          {[
            {
              tool: "pencil" as const,
              label: "铅笔路径",
              Icon: Pencil,
            },
            {
              tool: "pen" as const,
              label: "钢笔路径",
              Icon: PenTool,
            },
          ].map(({ tool, label, Icon }) => (
            <button
              key={tool}
              type="button"
              data-director-motion-path-draw-tool={tool}
              onClick={() => {
                startMotionPathDrawing(tool);
                const draft =
                  useDirectorStore.getState().timeline.motionPathDraft;
                if (draft) {
                  beginDirectorGesture({
                    commandKind: "path-draw",
                    targetId: draft.trackId,
                    fieldScope: draft.tool,
                  });
                }
                setPathMenuLeft(null);
              }}
              className="flex h-8 w-full items-center gap-2 px-2 text-left text-[11px] text-[#bcbcbc] hover:bg-white/[0.06] hover:text-white"
            >
              <Icon size={13} className="text-[#777]" />
              {label}
            </button>
          ))}
          <div className="mx-2 my-1 h-px bg-white/[0.07]" />
          {[
            {
              preset: "line" as const,
              label: "直线路径",
              Icon: Minus,
            },
            {
              preset: "ring" as const,
              label: "圆环路径",
              Icon: Circle,
            },
            {
              preset: "rectangle" as const,
              label: "矩形路径",
              Icon: RectangleHorizontal,
            },
          ].map(({ preset, label, Icon }) => (
            <button
              key={preset}
              type="button"
              data-director-motion-path-preset={preset}
              onClick={() => {
                createMotionPath(preset);
                setPathMenuLeft(null);
              }}
              className="flex h-8 w-full items-center gap-2 px-2 text-left text-[11px] text-[#bcbcbc] hover:bg-white/[0.06] hover:text-white"
            >
              <Icon size={13} className="text-[#777]" />
              {label}
            </button>
          ))}
        </div>
      ) : null}

      {timeline.editorMode === "curve" ? (
        <DirectorCurveEditor />
      ) : (
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
                      ) : track.kind === "group" ? (
                        <Users size={12} />
                      ) : track.kind === "pose" ? (
                        <PersonStanding size={12} />
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
                    {track.motionPathId ? (
                      <Route
                        size={11}
                        className="shrink-0 text-[#5ddcff]"
                        aria-label="已绑定运动轨迹"
                      />
                    ) : null}
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
                data-director-track-group-id={
                  track.kind === "group" ? track.groupId : undefined
                }
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
      )}
    </section>
  );
}
