"use client";

import { useEffect, useRef } from "react";
import type { PointerEvent as ReactPointerEvent } from "react";
import { ArrowLeft } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  useDirectorStore,
  type DirectorSpeedCurvePreset,
} from "@/store/directorStore";

const curvePresets: Array<{
  preset: Exclude<DirectorSpeedCurvePreset, "custom">;
  label: string;
}> = [
  { preset: "linear", label: "线性" },
  { preset: "smooth", label: "平滑" },
  { preset: "ease-in", label: "缓入" },
  { preset: "ease-out", label: "缓出" },
  { preset: "ease-in-out", label: "缓入缓出" },
];

const graph = {
  width: 440,
  height: 112,
  left: 24,
  right: 416,
  top: 12,
  bottom: 92,
};

function graphPoint(point: [number, number]) {
  return {
    x: graph.left + point[0] * (graph.right - graph.left),
    y: graph.bottom - point[1] * (graph.bottom - graph.top),
  };
}

export function DirectorCurveEditor() {
  const timeline = useDirectorStore((state) => state.timeline);
  const setTimelineEditorMode = useDirectorStore(
    (state) => state.setTimelineEditorMode,
  );
  const setTrackSpeedCurvePreset = useDirectorStore(
    (state) => state.setTrackSpeedCurvePreset,
  );
  const setTrackSpeedCurveControl = useDirectorStore(
    (state) => state.setTrackSpeedCurveControl,
  );
  const beginDirectorGesture = useDirectorStore(
    (state) => state.beginDirectorGesture,
  );
  const commitDirectorGesture = useDirectorStore(
    (state) => state.commitDirectorGesture,
  );
  const cancelDirectorGesture = useDirectorStore(
    (state) => state.cancelDirectorGesture,
  );
  const svgRef = useRef<SVGSVGElement>(null);
  const dragCleanupRef = useRef<
    ((disposition?: "commit" | "cancel") => void) | null
  >(null);
  const selectedTrack =
    timeline.tracks.find((track) => track.id === timeline.selectedTrackId) ??
    null;

  useEffect(() => {
    return () => {
      dragCleanupRef.current?.();
    };
  }, []);

  const beginHandleDrag = (
    event: ReactPointerEvent<SVGCircleElement>,
    handle: 1 | 2,
  ) => {
    if (!selectedTrack) return;
    event.preventDefault();
    event.stopPropagation();
    const result = beginDirectorGesture({
      commandKind: "speed-curve",
      targetId: selectedTrack.id,
      fieldScope: `control-${handle}`,
    });
    if (result.disposition !== "COMMITTED") return;

    const target = event.currentTarget;
    const pointerId = event.pointerId;
    let active = true;
    const update = (pointerEvent: PointerEvent) => {
      if (pointerEvent.pointerId !== pointerId) return;
      const svg = svgRef.current;
      if (!svg) return;
      const rect = svg.getBoundingClientRect();
      const x =
        (pointerEvent.clientX -
          rect.left -
          (graph.left / graph.width) * rect.width) /
        (((graph.right - graph.left) / graph.width) * rect.width);
      const y =
        ((graph.bottom / graph.height) * rect.height -
          (pointerEvent.clientY - rect.top)) /
        (((graph.bottom - graph.top) / graph.height) * rect.height);
      setTrackSpeedCurveControl(selectedTrack.id, handle, [x, y]);
    };
    const cleanup = (disposition: "commit" | "cancel" = "cancel") => {
      if (!active) return;
      active = false;
      window.removeEventListener("pointermove", update);
      window.removeEventListener("pointerup", handleUp);
      window.removeEventListener("pointercancel", handleCancel);
      window.removeEventListener("blur", handleBlur);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      target.removeEventListener("lostpointercapture", handleLostPointerCapture);
      if (target.hasPointerCapture(pointerId)) {
        target.releasePointerCapture(pointerId);
      }
      if (dragCleanupRef.current === cleanup) {
        dragCleanupRef.current = null;
      }
      if (disposition === "commit") {
        commitDirectorGesture();
      } else {
        cancelDirectorGesture();
      }
    };
    const handleUp = (pointerEvent: PointerEvent) => {
      if (pointerEvent.pointerId === pointerId) cleanup("commit");
    };
    const handleCancel = (pointerEvent: PointerEvent) => {
      if (pointerEvent.pointerId === pointerId) cleanup("cancel");
    };
    const handleBlur = () => cleanup("cancel");
    const handleVisibilityChange = () => {
      if (document.visibilityState === "hidden") cleanup("cancel");
    };
    const handleLostPointerCapture = () => cleanup("cancel");

    dragCleanupRef.current?.();
    dragCleanupRef.current = cleanup;
    target.setPointerCapture(pointerId);
    update(event.nativeEvent);
    window.addEventListener("pointermove", update);
    window.addEventListener("pointerup", handleUp);
    window.addEventListener("pointercancel", handleCancel);
    window.addEventListener("blur", handleBlur);
    document.addEventListener("visibilitychange", handleVisibilityChange);
    target.addEventListener("lostpointercapture", handleLostPointerCapture);
  };

  if (!selectedTrack) {
    return (
      <div
        data-director-curve-editor
        className="flex min-h-0 flex-1 flex-col bg-[#151515]"
      >
        <header className="flex h-8 shrink-0 items-center border-b border-white/[0.06] px-2">
          <button
            type="button"
            data-director-back-to-timeline
            onClick={() => setTimelineEditorMode("timeline")}
            className="flex h-6 items-center gap-1 rounded px-1.5 text-[11px] text-[#888] hover:bg-white/[0.06] hover:text-white"
          >
            <ArrowLeft size={12} />
            返回时间线
          </button>
          <span className="ml-2 text-[11px] text-[#cfcfcf]">设置曲线</span>
        </header>
        <div className="flex flex-1 items-center justify-center text-xs text-[#666]">
          选择一个轨道后编辑速度曲线
        </div>
      </div>
    );
  }

  const control1 = graphPoint(selectedTrack.speedCurve.control1);
  const control2 = graphPoint(selectedTrack.speedCurve.control2);
  const path = `M ${graph.left} ${graph.bottom} C ${control1.x} ${control1.y}, ${control2.x} ${control2.y}, ${graph.right} ${graph.top}`;

  return (
    <div
      data-director-curve-editor
      data-director-curve-track-id={selectedTrack.id}
      className="flex min-h-0 flex-1 flex-col bg-[#151515]"
    >
      <header className="flex h-8 shrink-0 items-center gap-1 overflow-x-auto border-b border-white/[0.06] px-2">
        <button
          type="button"
          data-director-back-to-timeline
          onClick={() => setTimelineEditorMode("timeline")}
          className="flex h-6 shrink-0 items-center gap-1 rounded px-1.5 text-[11px] text-[#888] hover:bg-white/[0.06] hover:text-white"
        >
          <ArrowLeft size={12} />
          返回时间线
        </button>
        <span className="mx-1 h-4 w-px shrink-0 bg-white/10" />
        <span className="mr-1 shrink-0 text-[11px] text-[#cfcfcf]">设置曲线</span>
        {curvePresets.map(({ preset, label }) => (
          <button
            key={preset}
            type="button"
            data-director-curve-preset={preset}
            aria-pressed={selectedTrack.speedCurve.preset === preset}
            onClick={() => setTrackSpeedCurvePreset(selectedTrack.id, preset)}
            className={cn(
              "h-6 shrink-0 rounded px-2 text-[10px] text-[#858585] hover:bg-white/[0.06] hover:text-white",
              selectedTrack.speedCurve.preset === preset &&
                "bg-white/[0.08] text-[#5ddcff]",
            )}
          >
            {label}
          </button>
        ))}
        <span
          data-director-curve-values
          className="ml-auto shrink-0 text-[10px] tabular-nums text-[#6f6f6f]"
        >
          贝塞尔曲线参数{" "}
          {selectedTrack.speedCurve.control1
            .map((value) => value.toFixed(2))
            .join(", ")}{" "}
          ·{" "}
          {selectedTrack.speedCurve.control2
            .map((value) => value.toFixed(2))
            .join(", ")}
        </span>
      </header>

      <div className="flex min-h-0 flex-1 items-center overflow-x-auto px-2">
        <svg
          ref={svgRef}
          viewBox={`0 0 ${graph.width} ${graph.height}`}
          preserveAspectRatio="none"
          aria-label="调整贝塞尔曲线"
          className="h-[112px] min-w-[440px] flex-1"
        >
          <rect
            x={graph.left}
            y={graph.top}
            width={graph.right - graph.left}
            height={graph.bottom - graph.top}
            fill="#181818"
            stroke="rgba(255,255,255,0.06)"
          />
          {[0.25, 0.5, 0.75].map((value) => (
            <g key={value} stroke="rgba(255,255,255,0.045)">
              <line
                x1={graph.left + value * (graph.right - graph.left)}
                y1={graph.top}
                x2={graph.left + value * (graph.right - graph.left)}
                y2={graph.bottom}
              />
              <line
                x1={graph.left}
                y1={graph.bottom - value * (graph.bottom - graph.top)}
                x2={graph.right}
                y2={graph.bottom - value * (graph.bottom - graph.top)}
              />
            </g>
          ))}
          <line
            x1={graph.left}
            y1={graph.bottom}
            x2={control1.x}
            y2={control1.y}
            stroke="#65747d"
            strokeWidth="1"
          />
          <line
            x1={graph.right}
            y1={graph.top}
            x2={control2.x}
            y2={control2.y}
            stroke="#65747d"
            strokeWidth="1"
          />
          <path
            data-director-speed-curve-path
            d={path}
            fill="none"
            stroke="#09caf5"
            strokeWidth="2"
          />
          {[
            { handle: 1 as const, point: control1 },
            { handle: 2 as const, point: control2 },
          ].map(({ handle, point }) => (
            <circle
              key={handle}
              role="button"
              tabIndex={0}
              aria-label={`贝塞尔控制点 ${handle}`}
              data-director-curve-handle={handle}
              cx={point.x}
              cy={point.y}
              r="5"
              fill="#09caf5"
              stroke="#e6fbff"
              strokeWidth="1.5"
              className="cursor-grab outline-none active:cursor-grabbing"
              onPointerDown={(event) => beginHandleDrag(event, handle)}
            />
          ))}
        </svg>
      </div>
    </div>
  );
}
