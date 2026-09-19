"use client";

import { useRef, useState } from "react";
import { Play } from "lucide-react";
import { NodeToolbar, Position } from "@xyflow/react";

import type { JimengVideoNodeData } from "@/types/jimeng";

/**
 * 视频修剪编辑态 (Batch 10/31；批 372 源站再采样保真修正)。
 *
 * 证据 (SOURCE_FACT 372-video-trim.png / 372c-trim-full.json): 源站点击
 * 工具条「视频修剪」后，节点下方出现修剪条——透明底（无面板容器），
 * 胶片帧条 40px 高、白色 2px 描边、68×40 连续帧格；两端白色拖拽把手
 * （48px，上下越出条体）；条内右端深色小徽章只显示「6.1s」数字
 * （12px 白），「Selected duration: 6.1s」全文是 1px 裁切的隐藏叶
 * （推翻批 213「标签含前缀」判读——那是批 62 FramePicker 的可见前缀，
 * 两组件同族但徽章形态不同）。下方 ▶ + 「00:04 / 00:06」为播放走表
 * current/total（12px white/88），右端白色「确认」胶囊钮。修剪态工具
 * 条隐藏、标题行保持可见（批 372 截图）。
 * Batch 31: 把手可拖动，时长标签实时联动。
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
      {/* 批 372 SOURCE_FACT: 修剪条无面板容器（透明底，直接贴画布） */}
      <div className="w-[672px]">
        {/* 修剪帧条: 40px 白描边条 + 选区外压暗 + 两端越出拖拽把手 */}
        <div
          ref={trackRef}
          className="relative h-10 select-none rounded-md border-2 border-white/90"
        >
          <div className="absolute inset-0 overflow-hidden rounded-md">
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
              className="absolute right-2 top-1/2 -translate-y-1/2 rounded bg-black/60 px-1.5 py-0.5 text-[12px] text-white"
              data-testid="trim-duration"
            >
              {trimmed.toFixed(1)}s
            </span>
            {/* 批 372 SOURCE_FACT: 全文前缀是 1px 裁切隐藏叶（镜像源站 DOM） */}
            <span className="pointer-events-none absolute left-0 top-0 h-px w-px overflow-hidden text-[16px] text-white">
              Selected duration: {trimmed.toFixed(1)}s
            </span>
          </div>
          <span
            role="slider"
            aria-label="修剪起点"
            aria-valuenow={Math.round(range.start * 100)}
            className="nodrag absolute top-1/2 h-12 w-1.5 -translate-x-1/2 -translate-y-1/2 cursor-ew-resize rounded-full bg-white"
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
            className="nodrag absolute top-1/2 h-12 w-1.5 -translate-x-1/2 -translate-y-1/2 cursor-ew-resize rounded-full bg-white"
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
          {/* 批 372 SOURCE_FACT: 时间行为播放走表 current/total (white/88) */}
          <div className="flex items-center gap-2 text-white">
            <Play size={13} fill="currentColor" />
            <span className="text-[12px] tabular-nums text-white/[0.88]">
              {fmt(data.currentTime ?? 0)} / {fmt(duration)}
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
