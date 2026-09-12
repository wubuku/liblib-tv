"use client";

import { useState } from "react";
import { Camera, Play } from "lucide-react";
import { NodeToolbar, Position } from "@xyflow/react";

import type { JimengVideoNodeData } from "@/types/jimeng";

/**
 * 截取帧 帧选择器 (Batch 9；Batch 10 支持 首帧/尾帧 预选)。
 *
 * 证据 (SOURCE_FACT): 源站从截取帧下拉选「自定义」后，节点下方出现选择条:
 * 胶片帧条 (左侧播放头竖线) + 底部行: ▶ 00:00 / 00:06 ｜ 📷 截取帧 ｜ 确认 (未截取禁用，
 * 截取后确认可用)。
 * 首帧/尾帧 (CLONE_DECISION): 播放头预选到 0 / 末尾，确认直接可用。
 * mock: 帧条为海报 repeat-x；点击「截取帧」后「确认」可用；确认后关闭。
 */
export function JimengFramePicker({
  visible,
  data,
  mode = "custom",
  onClose,
}: {
  visible: boolean;
  data: JimengVideoNodeData;
  mode?: "first" | "last" | "custom";
  onClose: () => void;
}) {
  const [captured, setCaptured] = useState(false);
  // 首帧/尾帧已确定帧位置，无需先截取
  const preset = mode !== "custom";
  const confirmed = captured || preset;
  const time = mode === "last" ? (data.duration ?? 0) : 0;
  const playheadLeft = mode === "last" ? "calc(98% - 2px)" : "2%";

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
          <span
            className="absolute inset-y-0 w-0.5 bg-white"
            style={{ left: playheadLeft }}
          />
        </div>

        <div className="mt-2.5 flex items-center justify-between">
          <div className="flex items-center gap-2 text-white">
            <Play size={13} fill="currentColor" />
            <span className="text-[12px] tabular-nums">
              {fmt(time)} / {fmt(data.duration ?? 0)}
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
          <button
            type="button"
            disabled={!confirmed}
            onClick={onClose}
            className={`h-9 rounded-lg px-4 text-[13px] ${
              confirmed
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
