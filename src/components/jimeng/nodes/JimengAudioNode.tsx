"use client";

import { Handle, Position } from "@xyflow/react";
import { useEffect, useMemo, useState } from "react";
import type { NodeProps } from "@xyflow/react";

import type { JimengAudioNodeData } from "@/types/jimeng";
import { FileBadgeIcon } from "@/components/jimeng/icons";

/**
 * 音频节点 (Batch 19)。样式为 CLONE_DECISION (源站音频节点未提取):
 * 视频节点同族骨架 + 波形条 mock (伪随机高度) + 底部时长。
 */
function fmt(s: number) {
  return `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(
    Math.floor(s % 60),
  ).padStart(2, "0")}`;
}

export function JimengAudioNode({ data, selected }: NodeProps) {
  const d = data as JimengAudioNodeData;
  // 播放交互 (Batch 47): 点击播放钮推进波形进度，播完自停 (CLONE_DECISION mock)
  const [playing, setPlaying] = useState(false);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    if (!playing) return;
    const timer = window.setInterval(() => {
      setProgress((p) => {
        const next = p + 4;
        if (next >= 100) {
          setPlaying(false);
          return 0;
        }
        return next;
      });
    }, 120);
    return () => window.clearInterval(timer);
  }, [playing]);

  const bars = useMemo(() => {
    const heights: number[] = [];
    let seed = 7;
    for (let i = 0; i < 44; i += 1) {
      seed = (seed * 31 + 17) % 23;
      heights.push(8 + ((seed * 5) % 26));
    }
    return heights;
  }, []);

  return (
    <div
      className="group relative"
      style={{ width: d.width, height: d.height }}
      data-jimeng-node-selected={selected || undefined}
    >
      <div className="absolute inset-x-0 bottom-full z-10 flex h-8 items-center gap-1.5 text-left text-white/70">
        <FileBadgeIcon size={16} />
        <span className="max-w-full truncate whitespace-nowrap text-[13px] leading-[22px]">
          {d.title}
        </span>
      </div>

      <div
        className="relative flex h-full w-full items-center gap-3 overflow-hidden rounded-lg px-4"
        style={{
          background:
            "linear-gradient(to right bottom, rgb(30,30,32), rgb(22,22,24))",
          boxShadow:
            selected === true
              ? "0 0 0 1.5px rgba(255,255,255,0.92)"
              : "0 0 0 1px rgba(255,255,255,0.06) inset",
        }}
      >
        <button
          type="button"
          aria-label={playing ? "暂停音频" : "播放音频"}
          onClick={() => {
            if (progress >= 100) setProgress(0);
            setPlaying((v) => !v);
          }}
          className="flex size-8 shrink-0 items-center justify-center rounded-full bg-white/[0.08] text-white/80 hover:bg-white/[0.16]"
        >
          {playing ? (
            <svg width="12" height="12" viewBox="0 0 14 14" aria-hidden>
              <path d="M3 2h3v10H3zM8 2h3v10H8z" fill="currentColor" />
            </svg>
          ) : (
            <svg width="14" height="14" viewBox="0 0 14 14" aria-hidden>
              <path d="M4 2v10l7-5Z" fill="currentColor" />
            </svg>
          )}
        </button>
        <div className="flex h-10 flex-1 items-center gap-[3px] overflow-hidden">
          {bars.map((h, i) => (
            <span
              key={i}
              className={`w-[3px] shrink-0 rounded-full ${
                playing && (i / bars.length) * 100 <= progress
                  ? "bg-[#7FD8C9]"
                  : "bg-[#7FD8C9]/40"
              }`}
              style={{ height: h }}
            />
          ))}
        </div>
        <span className="shrink-0 text-[11px] tabular-nums text-white/55">
          {fmt(d.duration)}
        </span>
      </div>

      <Handle
        type="target"
        position={Position.Left}
        className="!z-10"
        style={{
          width: 60,
          height: 120,
          background: "transparent",
          border: "none",
          borderRadius: 0,
          left: -30,
          top: "50%",
          transform: "translateY(-50%)",
        }}
      />
      <Handle
        type="source"
        position={Position.Right}
        className="!z-10"
        style={{
          width: 60,
          height: 120,
          background: "transparent",
          border: "none",
          borderRadius: 0,
          right: -30,
          top: "50%",
          transform: "translateY(-50%)",
        }}
      />
    </div>
  );
}
