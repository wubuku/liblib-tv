"use client";

import { useRef, useState } from "react";
import { Camera, Play } from "lucide-react";
import { NodeToolbar, Position } from "@xyflow/react";

import type { JimengVideoNodeData } from "@/types/jimeng";

/**
 * 截取帧 帧选择器 (Batch 9/34；Batch 202 几何对齐)。
 *
 * 证据 (SOURCE_FACT): 源站从截取帧下拉选「自定义」后，节点下方出现选择条
 * (202-custom-picker.json): 面板与节点同宽 (564×116)；胶片帧条 540×54
 * (64×36 缩略图平铺) + 底部行 (h36): ▶ 00:00/00:06 (12px) ｜ 📷 截取帧
 * (89×36) ｜ 未截取时提示「请至少截取 1 帧」(12px) + 确认 (82×36 r8，
 * 禁用态 bg 白/16 + 字 白/20)；截取后确认可用 (batch 9)。
 * 首帧/尾帧预选播放头并直接可用 (CLONE_DECISION)。
 * Batch 34: 点击帧条可移动播放头，确认把帧号写回节点 currentTime。
 */
export function JimengFramePicker({
  visible,
  data,
  mode = "custom",
  onConfirm,
}: {
  visible: boolean;
  data: JimengVideoNodeData;
  mode?: "first" | "last" | "custom";
  onConfirm: (frameTime: number) => void;
}) {
  const duration = data.duration ?? 0;
  // 自定义模式默认播放头在起点；首帧/尾帧由 mode 预选 (Batch 34)
  const [frac, setFrac] = useState(mode === "last" ? 1 : 0);
  const [captured, setCaptured] = useState(mode !== "custom");
  const stripRef = useRef<HTMLDivElement>(null);

  const confirmed = mode === "custom" ? captured : true;
  const time = frac * duration;

  const fmt = (s: number) =>
    `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(Math.floor(s % 60)).padStart(2, "0")}`;

  const clickStrip = (clientX: number) => {
    const r = stripRef.current?.getBoundingClientRect();
    if (!r || r.width === 0) return;
    setFrac(Math.min(1, Math.max(0, (clientX - r.left) / r.width)));
  };

  return (
    <NodeToolbar isVisible={visible} position={Position.Bottom} offset={16}>
      {/* 批 202 SOURCE_FACT: 面板与节点同宽 (源站 564 @ 节点 569) */}
      <div
        className="rounded-2xl bg-[#1A1A1A] p-3 shadow-[0_4px_16px_rgba(0,0,0,0.32)]"
        style={{ width: Math.max(data.width ?? 569, 480) }}
      >
        {/* 帧条 + 播放头 (点击移动)；源站帧条 540×54 (批 202) */}
        <div
          ref={stripRef}
          className="relative h-[54px] cursor-pointer overflow-hidden rounded-md border border-white/10"
          onClick={(e) => {
            if (mode === "custom") clickStrip(e.clientX);
          }}
        >
          <div
            className="absolute inset-0 opacity-85"
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
            className="absolute inset-y-0 w-0.5 bg-white"
            style={{ left: `${frac * 100}%` }}
          />
        </div>

        <div className="mt-2.5 flex h-9 items-center justify-between">
          <div className="flex items-center gap-2 text-white">
            <Play size={13} fill="currentColor" />
            <span className="text-[12px] tabular-nums" data-testid="frame-readout">
              {fmt(time)} / {fmt(duration)}
            </span>
          </div>
          {mode === "custom" ? (
            <button
              type="button"
              onClick={() => setCaptured(true)}
              className="flex h-9 items-center gap-1.5 rounded-lg bg-white/[0.08] px-3.5 text-[13px] text-white hover:bg-white/[0.14]"
            >
              <Camera size={14} />
              截取帧
            </button>
          ) : (
            <span />
          )}
          <div className="flex items-center gap-2.5">
            {/* 批 202 SOURCE_FACT: 未截取时确认左侧提示「请至少截取 1 帧」
                (12px；透明度为 CLONE_DECISION，源站仅容器级色值) */}
            {mode === "custom" && !confirmed ? (
              <span className="text-[12px] text-white/40" data-testid="frame-hint">
                请至少截取 1 帧
              </span>
            ) : null}
            <button
              type="button"
              disabled={!confirmed}
              onClick={() => onConfirm(time)}
              className={`h-9 rounded-lg px-4 text-[13px] ${
                confirmed
                  ? "bg-white text-black hover:bg-white/90"
                  : "cursor-default bg-white/[0.16] text-white/20"
              }`}
            >
              确认
            </button>
          </div>
        </div>
      </div>
    </NodeToolbar>
  );
}
