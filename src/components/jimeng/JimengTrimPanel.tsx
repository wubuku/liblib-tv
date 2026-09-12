"use client";

import { Play } from "lucide-react";
import { NodeToolbar, Position } from "@xyflow/react";

import type { JimengVideoNodeData } from "@/types/jimeng";

/**
 * 视频修剪编辑态 (Batch 10)。
 *
 * 证据 (SOURCE_FACT): 源站点击工具条「视频修剪」后，节点下方出现修剪条:
 * 全宽胶片帧条 + 两端白色拖拽把手 (整段选中，条内右侧时长标签 6.1s) +
 * 底部行 ▶ 00:00 / 00:06 + 白色可用「确认」钮 (区别于帧选择器的置灰确认)。
 * mock: 把手为静态整段选中；确认后退出修剪态。
 */
export function JimengTrimPanel({
  visible,
  data,
  onClose,
}: {
  visible: boolean;
  data: JimengVideoNodeData;
  onClose: () => void;
}) {
  const duration = data.duration ?? 0;
  const fmt = (s: number) =>
    `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(Math.floor(s % 60)).padStart(2, "0")}`;

  return (
    <NodeToolbar isVisible={visible} position={Position.Bottom} offset={16}>
      <div className="w-[672px] rounded-2xl bg-[#1A1A1A] p-3 shadow-[0_4px_16px_rgba(0,0,0,0.32)]">
        {/* 修剪帧条: 整段选中 + 两端把手 */}
        <div className="relative h-14 overflow-hidden rounded-md border-2 border-white/90">
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
          <span className="absolute right-2 top-1/2 -translate-y-1/2 rounded bg-black/60 px-1.5 py-0.5 text-[11px] text-white">
            {duration.toFixed(1)}s
          </span>
          <span className="absolute -left-1 top-1/2 h-7 w-1.5 -translate-y-1/2 rounded-full bg-white" />
          <span className="absolute -right-1 top-1/2 h-7 w-1.5 -translate-y-1/2 rounded-full bg-white" />
        </div>

        <div className="mt-2.5 flex items-center justify-between">
          <div className="flex items-center gap-2 text-white">
            <Play size={13} fill="currentColor" />
            <span className="text-[12px] tabular-nums">
              {fmt(0)} / {fmt(duration)}
            </span>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="h-9 rounded-lg bg-white px-5 text-[13px] font-medium text-black hover:bg-white/90"
          >
            确认
          </button>
        </div>
      </div>
    </NodeToolbar>
  );
}
