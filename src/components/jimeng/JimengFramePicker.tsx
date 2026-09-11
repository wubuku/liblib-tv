"use client";

import { useState } from "react";
import { Camera, Play } from "lucide-react";
import { NodeToolbar, Position } from "@xyflow/react";

import type { JimengVideoNodeData } from "@/types/jimeng";

/**
 * 截取帧 → 自定义 帧选择器 (Batch 9)。
 *
 * 证据 (SOURCE_FACT): 源站从截取帧下拉选「自定义」后，节点下方出现选择条:
 * 胶片帧条 (左侧播放头竖线) + 底部行: ▶ 00:00 / 00:06 ｜ 📷 截取帧 ｜ 确认 (未截取禁用)。
 * mock: 帧条为海报 repeat-x；点击「截取帧」后「确认」可用；确认后关闭。
 */
export function JimengFramePicker({
  visible,
  data,
  onClose,
}: {
  visible: boolean;
  data: JimengVideoNodeData;
  onClose: () => void;
}) {
  const [captured, setCaptured] = useState(false);

  const fmt = (s: number) =>
    `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(Math.floor(s % 60)).padStart(2, "0")}`;

  return (
    <NodeToolbar isVisible={visible} position={Position.Bottom} offset={16}>
      <div className="w-[640px] rounded-2xl bg-[#1A1A1A] p-3 shadow-[0_4px_16px_rgba(0,0,0,0.32)]">
        {/* 帧条 + 播放头 */}
        <div className="relative h-14 overflow-hidden rounded-md border border-white/10">
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
          <span className="absolute inset-y-0 left-[2%] w-0.5 bg-white" />
        </div>

        <div className="mt-2.5 flex items-center justify-between">
          <div className="flex items-center gap-2 text-white">
            <Play size={13} fill="currentColor" />
            <span className="text-[12px] tabular-nums">
              {fmt(0)} / {fmt(data.duration ?? 0)}
            </span>
          </div>
          <button
            type="button"
            onClick={() => setCaptured(true)}
            className="flex h-9 items-center gap-1.5 rounded-lg bg-white/[0.08] px-3.5 text-[13px] text-white hover:bg-white/[0.14]"
          >
            <Camera size={14} />
            截取帧
          </button>
          <button
            type="button"
            disabled={!captured}
            onClick={onClose}
            className={`h-9 rounded-lg px-4 text-[13px] ${
              captured
                ? "bg-white text-black hover:bg-white/90"
                : "cursor-default bg-white/[0.10] text-white/35"
            }`}
          >
            确认
          </button>
        </div>
      </div>
    </NodeToolbar>
  );
}
