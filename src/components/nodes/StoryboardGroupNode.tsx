"use client";

import { memo } from "react";
import { Handle, Position, type NodeProps, type Node, useReactFlow } from "@xyflow/react";
import { cn } from "@/lib/utils";

export interface StoryboardGroupData extends Record<string, unknown> {
  title?: string;
  images?: Array<{
    url: string;
    label?: string;
  }>;
}

export type StoryboardGroupType = Node<StoryboardGroupData, "storyboard-group">;

function StoryboardGroupNodeComponent({ id, data, selected }: NodeProps<StoryboardGroupType>) {
  const { deleteElements } = useReactFlow();

  const title = data.title || "分镜图 · 第一集：咖啡馆对峙-图片组";
  const images = data.images || [
    { url: "/images/scene-coffee-1.png", label: "img1" },
  ];

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    deleteElements({ nodes: [{ id }] });
  };

  return (
    <div
      className={cn(
        "w-[320px] overflow-visible rounded-xl bg-[#1f1f1f] border flex flex-col group relative",
        selected ? "border-[#09caf5] shadow-[0_0_0_2px_rgba(9,202,245,0.3)]" : "border-[#363636]",
        "shadow-xl"
      )}
    >
      {/* Delete button - visible when selected */}
      {selected && (
        <button
          onClick={handleDelete}
          className="absolute -top-2 -right-2 z-10 w-5 h-5 bg-[#f53f3f] rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity hover:bg-[#ff6a6f]"
          aria-label="Delete node"
        >
          <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
            <path d="M2 2L8 8M8 2L2 8" stroke="white" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
        </button>
      )}

      {/* Left Handle (target) */}
      <Handle
        type="target"
        position={Position.Left}
        id="target"
        style={{ width: 20, height: 20 }}
      />

      {/* Right Handle (source) */}
      <Handle
        type="source"
        position={Position.Right}
        id="source"
        style={{ width: 20, height: 20 }}
      />

      {/* Title */}
      <div className="px-4 py-2 text-xs text-[#919191] truncate" title={title}>
        {title}
      </div>

      {/* Image grid */}
      <div className="grid grid-cols-1 gap-2 p-3 pt-0">
        {images.map((img, idx) => (
          <div
            key={idx}
            className="relative aspect-video rounded-lg overflow-hidden bg-[#171717] border border-[#363636]"
          >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={img.url}
              alt={img.label || `image-${idx}`}
              className="w-full h-full object-cover"
            />
            {img.label && (
              <div className="absolute top-1 left-1 text-[10px] px-1.5 py-0.5 bg-black/60 text-white rounded">
                {img.label}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export const StoryboardGroupNode = memo(StoryboardGroupNodeComponent);