"use client";

import { Handle, Position } from "@xyflow/react";
import type { NodeProps } from "@xyflow/react";

import type { JimengImageNodeData } from "@/types/jimeng";
import { FileBadgeIcon } from "@/components/jimeng/icons";

/**
 * 图片节点 (Batch 17)。结构与视频节点同族 (SOURCE_FACT §5 的视频节点骨架)，
 * 尺寸/占位为 CLONE_DECISION (源站图片节点未提取)。
 */
export function JimengImageNode({ data, selected }: NodeProps) {
  const d = data as JimengImageNodeData;

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
        className="relative h-full w-full overflow-hidden rounded-lg"
        style={{
          background:
            "linear-gradient(to right bottom, rgb(34,34,34), rgb(20,20,20))",
          boxShadow:
            selected === true
              ? "0 0 0 1.5px rgba(255,255,255,0.92)"
              : undefined,
        }}
      >
        <span className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 text-white/40">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden>
            <rect x="2" y="2" width="16" height="16" rx="3" stroke="currentColor" strokeWidth="1.3" />
            <circle cx="7" cy="7.5" r="1.6" fill="currentColor" />
            <path d="m4 15 4.5-5 3 3.4L14 10.5l2.5 3" stroke="currentColor" strokeWidth="1.3" fill="none" />
          </svg>
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
