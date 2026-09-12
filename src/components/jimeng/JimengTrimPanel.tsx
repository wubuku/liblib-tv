"use client";

import { useRef, useState } from "react";
import { Play } from "lucide-react";
import { NodeToolbar, Position } from "@xyflow/react";

import type { JimengVideoNodeData } from "@/types/jimeng";

/**
 * 视频修剪编辑态 (Batch 10/31)。
 *
 * 证据 (SOURCE_FACT): 源站点击工具条「视频修剪」后，节点下方出现修剪条:
 * 全宽胶片帧条 + 两端白色拖拽把手 (条内右侧时长标签) + ▶ 00:00/00:06 +
 * 白色可用「确认」钮。Batch 31: 把手可拖动，时长标签实时联动
 * (源站拖动行为未逐帧提取，拖动几何为 CLONE_DECISION)。
 */
export function JimengTrimPanel({
  visible,
  data,
  onConfirm,
}: {
  visible: boolean;
  data: JimengVideoNodeData;
  /** 确认修剪: 回传裁剪后的时长与新起点秒数 (Batch 33/44 真实联动) */
  onConfirm: (trimmedDuration: number, startOffset: number) => void;
}) {
  const duration = data.duration ?? 0;
  const trackRef = useRef<HTMLDivElement>(null);
  const dragging = useRef<"start" | "end" | null>(null);
  const [range, setRange] = useState({ start: 0, end: 1 });

  const fmt = (s: number) =>
    `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(Math.floor(s % 60)).padStart(2, "0")}`;

  const dragTo = (which: "start" | "end", clientX: number) => {
    const r = trackRef.current?.getBoundingClientRect();
    if (!r || r.width === 0) return;
    const f = Math.min(1, Math.max(0, (clientX - r.left) / r.width));
    setRange((prev) =>
      which === "start"
        ? { start: Math.min(f, prev.end - 0.05), end: prev.end }
        : { start: prev.start, end: Math.max(f, prev.start + 0.05) },
    );
  };
  const trimmed = (range.end - range.start) * duration;

  return (
    <NodeToolbar isVisible={visible} position={Position.Bottom} offset={16}>
      <div className="w-[672px] rounded-2xl bg-[#1A1A1A] p-3 shadow-[0_4px_16px_rgba(0,0,0,0.32)]">
        {/* 修剪帧条: 选区 + 两端拖拽把手 */}
        <div
          ref={trackRef}
          className="relative h-14 select-none overflow-hidden rounded-md border-2 border-white/90"
          onPointerMove={(e) => {
            if (dragging.current) dragTo(dragging.current, e.clientX);
          }}
          onPointerUp={() => {
            dragging.current = null;
          }}
        >
          <div
            className="absolute inset-0 opacity-90"
            style={
              data.poster
                ? {
                    backgroundImage: `url(${data.poster})`,
                    backgroundRepeat: "repeat-x",
                    backgroundSize: "auto 100%",
                  }
                : { background: "linear-gradient(to right, #222, #141414)" }
            }
          />
          <span
            className="absolute right-2 top-1/2 -translate-y-1/2 rounded bg-black/60 px-1.5 py-0.5 text-[11px] text-white"
            data-testid="trim-duration"
          >
            {trimmed.toFixed(1)}s
          </span>
          <span
            role="slider"
            aria-label="修剪起点"
            aria-valuenow={Math.round(range.start * 100)}
            className="nodrag absolute top-1/2 h-7 w-1.5 -translate-x-1/2 -translate-y-1/2 cursor-ew-resize rounded-full bg-white"
            style={{ left: `${range.start * 100}%` }}
            onPointerDown={(e) => {
              e.stopPropagation();
              dragging.current = "start";
              (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
            }}
            onPointerMove={(e) => {
              if (dragging.current === "start") dragTo("start", e.clientX);
            }}
            onPointerUp={() => {
              dragging.current = null;
            }}
          />
          <span
            role="slider"
            aria-label="修剪终点"
            aria-valuenow={Math.round(range.end * 100)}
            className="nodrag absolute top-1/2 h-7 w-1.5 -translate-x-1/2 -translate-y-1/2 cursor-ew-resize rounded-full bg-white"
            style={{ left: `${range.end * 100}%` }}
            onPointerDown={(e) => {
              e.stopPropagation();
              dragging.current = "end";
              (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
            }}
            onPointerMove={(e) => {
              if (dragging.current === "end") dragTo("end", e.clientX);
            }}
            onPointerUp={() => {
              dragging.current = null;
            }}
          />
        </div>

        <div className="mt-2.5 flex items-center justify-between">
          <div className="flex items-center gap-2 text-white">
            <Play size={13} fill="currentColor" />
            <span className="text-[12px] tabular-nums">
              {fmt(range.start * duration)} / {fmt(duration)}
            </span>
          </div>
          <button
            type="button"
            onClick={() => onConfirm(trimmed, range.start * duration)}
            className="h-9 rounded-lg bg-white px-5 text-[13px] font-medium text-black hover:bg-white/90"
          >
            确认
          </button>
        </div>
      </div>
    </NodeToolbar>
  );
}
