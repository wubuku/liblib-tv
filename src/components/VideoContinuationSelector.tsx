"use client";

import Image from "next/image";
import { useEffect, useRef, useState } from "react";
import { Check, X } from "lucide-react";

interface VideoContinuationSelectorProps {
  zoom: number;
  durationSeconds: number;
  onCancel: () => void;
  onConfirm: (startSeconds: number, endSeconds: number) => void;
}

type DragMode = "start" | "end" | "region";

interface DragSession {
  mode: DragMode;
  pointerX: number;
  startSeconds: number;
  endSeconds: number;
}

const MIN_DURATION = 4;
const MAX_DURATION = 30;
const thumbnails = [
  "/images/scene-coffee-1.png",
  "/images/scene-coffee-3.png",
  "/images/scene-coffee-4.png",
  "/images/storyboard-2.png",
];

function clamp(value: number, minimum: number, maximum: number) {
  return Math.min(maximum, Math.max(minimum, value));
}

export function VideoContinuationSelector({
  zoom,
  durationSeconds,
  onCancel,
  onConfirm,
}: VideoContinuationSelectorProps) {
  const sourceDuration = Math.max(MIN_DURATION, durationSeconds);
  const [range, setRange] = useState(() => ({
    start: 0,
    end: Math.min(sourceDuration, MAX_DURATION),
  }));
  const timelineRef = useRef<HTMLDivElement>(null);
  const dragSessionRef = useRef<DragSession | null>(null);

  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      event.preventDefault();
      event.stopImmediatePropagation();
      onCancel();
    };

    window.addEventListener("keydown", handleEscape, true);
    return () => window.removeEventListener("keydown", handleEscape, true);
  }, [onCancel]);

  useEffect(() => {
    const handlePointerMove = (event: PointerEvent) => {
      const session = dragSessionRef.current;
      const timeline = timelineRef.current;
      if (!session || !timeline) return;

      event.preventDefault();
      const timelineBox = timeline.getBoundingClientRect();
      const secondsPerPixel = sourceDuration / timelineBox.width;

      if (session.mode === "region") {
        const selectedDuration = session.endSeconds - session.startSeconds;
        const deltaSeconds = (event.clientX - session.pointerX) * secondsPerPixel;
        const start = clamp(
          session.startSeconds + deltaSeconds,
          0,
          sourceDuration - selectedDuration,
        );
        setRange({ start, end: start + selectedDuration });
        return;
      }

      const pointerSeconds = clamp(
        (event.clientX - timelineBox.left) * secondsPerPixel,
        0,
        sourceDuration,
      );
      if (session.mode === "start") {
        const start = clamp(
          pointerSeconds,
          Math.max(0, session.endSeconds - MAX_DURATION),
          session.endSeconds - MIN_DURATION,
        );
        setRange({ start, end: session.endSeconds });
        return;
      }

      const end = clamp(
        pointerSeconds,
        session.startSeconds + MIN_DURATION,
        Math.min(sourceDuration, session.startSeconds + MAX_DURATION),
      );
      setRange({ start: session.startSeconds, end });
    };

    const handlePointerUp = () => {
      dragSessionRef.current = null;
    };

    window.addEventListener("pointermove", handlePointerMove, { passive: false });
    window.addEventListener("pointerup", handlePointerUp);
    window.addEventListener("pointercancel", handlePointerUp);
    return () => {
      window.removeEventListener("pointermove", handlePointerMove);
      window.removeEventListener("pointerup", handlePointerUp);
      window.removeEventListener("pointercancel", handlePointerUp);
    };
  }, [sourceDuration]);

  const beginDrag = (
    mode: DragMode,
    event: React.PointerEvent<HTMLElement>,
  ) => {
    event.preventDefault();
    event.stopPropagation();
    dragSessionRef.current = {
      mode,
      pointerX: event.clientX,
      startSeconds: range.start,
      endSeconds: range.end,
    };
  };

  const startPercent = (range.start / sourceDuration) * 100;
  const endPercent = (range.end / sourceDuration) * 100;
  const selectedDuration = range.end - range.start;

  return (
    <div
      data-video-continuation-selector
      className="nodrag nowheel nopan absolute -bottom-[9px] left-1/2 z-20 h-[56px] w-[660px] -translate-x-1/2 translate-y-full origin-top"
      // The bordered node is the containing block, so 9 flow units produce the source's 8-unit outer gap.
      style={{ transform: `scale(${1 / zoom})` }}
      onPointerDown={(event) => event.stopPropagation()}
      onClick={(event) => event.stopPropagation()}
    >
      <section className="flex h-full items-center gap-2 rounded-xl border border-[#343434] bg-[#262626]/95 p-1 shadow-[0_12px_32px_rgba(0,0,0,0.42)] backdrop-blur-xl">
        <button
          data-video-continuation-close
          type="button"
          onClick={onCancel}
          aria-label="取消智能续写"
          className="flex size-8 shrink-0 items-center justify-center rounded-lg text-[#9a9a9a] hover:bg-white/[0.07] hover:text-white"
        >
          <X size={15} />
        </button>

        <div
          ref={timelineRef}
          data-video-continuation-timeline
          aria-label="请截取续写前置视频"
          className="relative h-12 min-w-0 flex-1 select-none overflow-hidden rounded-xl bg-[#191919]"
        >
          <div className="absolute inset-0 flex">
            {Array.from({ length: 12 }, (_, index) => (
              <span
                key={index}
                className="relative min-w-0 flex-1 border-r border-black/20 last:border-r-0"
              >
                <Image
                  src={thumbnails[index % thumbnails.length]}
                  alt=""
                  fill
                  sizes="48px"
                  className="pointer-events-none object-cover"
                  unoptimized
                />
              </span>
            ))}
            <span className="pointer-events-none absolute inset-0 bg-black/25" />
          </div>

          <div
            data-video-continuation-region
            role="slider"
            aria-label="拖动续写前置视频范围"
            aria-valuemin={0}
            aria-valuemax={sourceDuration}
            aria-valuenow={selectedDuration}
            onPointerDown={(event) => beginDrag("region", event)}
            className="absolute inset-y-0 z-10 cursor-grab border-y-2 border-[#09caf5] bg-[#09caf5]/10 active:cursor-grabbing"
            style={{
              left: `${startPercent}%`,
              width: `${endPercent - startPercent}%`,
            }}
          />

          <button
            data-video-continuation-start
            type="button"
            aria-label="调整续写开始时间"
            onPointerDown={(event) => beginDrag("start", event)}
            className="absolute inset-y-0 z-20 w-4 cursor-ew-resize rounded-l-xl bg-[#09caf5] shadow-[0_0_12px_rgba(9,202,245,0.42)]"
            style={{
              left: `${startPercent}%`,
              transform: startPercent === 0 ? undefined : "translateX(-50%)",
            }}
          />
          <button
            data-video-continuation-end
            type="button"
            aria-label="调整续写结束时间"
            onPointerDown={(event) => beginDrag("end", event)}
            className="absolute inset-y-0 z-20 w-4 cursor-ew-resize rounded-r-xl bg-[#09caf5] shadow-[0_0_12px_rgba(9,202,245,0.42)]"
            style={{ left: `${endPercent}%`, transform: "translateX(-100%)" }}
          />

          <span
            data-video-continuation-duration
            data-start-seconds={range.start.toFixed(2)}
            data-end-seconds={range.end.toFixed(2)}
            className="pointer-events-none absolute top-1/2 z-30 -translate-x-1/2 -translate-y-1/2 rounded-md bg-black/80 px-2 py-1 text-[11px] font-medium tabular-nums text-white shadow-lg"
            style={{ left: `${(startPercent + endPercent) / 2}%` }}
          >
            {selectedDuration.toFixed(2)} 秒
          </span>
        </div>

        <button
          data-video-continuation-confirm
          type="button"
          onClick={() => onConfirm(range.start, range.end)}
          className="flex h-8 shrink-0 items-center gap-1.5 rounded-lg bg-white px-3 text-xs font-medium text-[#202020] hover:bg-[#e8fbff]"
        >
          <Check size={13} />
          确认续写
        </button>
      </section>
    </div>
  );
}
