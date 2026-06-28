"use client";

import { useState, type MouseEvent } from "react";
import Image from "next/image";
import { X } from "lucide-react";
import { type NodeProps, type Node } from "@xyflow/react";
import { Handle, Position } from "@xyflow/react";
import { cn } from "@/lib/utils";

export interface ImageNodeData extends Record<string, unknown> {
  filename: string;
  width: number;
  height: number;
  imageUrl: string;
  watermarkUrl?: string;
}

export type ImageNodeType = Node<ImageNodeData, "image">;

export function ImageNode({ data, selected }: NodeProps<ImageNodeType>) {
  const [hovered, setHovered] = useState(false);

  const { filename, width, height, imageUrl, watermarkUrl } = data;

  return (
    <div
      className={cn(
        "rounded-lg border border-[#363636] bg-[#1f1f1f] overflow-hidden",
        "transition-shadow duration-150",
        selected ? "border-[#09caf5]" : "border-[#363636]",
        hovered && !selected && "shadow-[0_2px_12px_rgba(0,0,0,0.4)]",
        selected && "shadow-[0_0_0_1px_#09caf5,0_2px_12px_rgba(9,202,245,0.15)]"
      )}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      {/* Header */}
      <div className="flex items-center gap-2 border-b border-[#363636] px-3 py-2">
        {/* Image icon */}
        <svg
          width="16"
          height="16"
          viewBox="0 0 16 16"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="shrink-0"
        >
          <rect
            x="1.5"
            y="2.5"
            width="13"
            height="11"
            rx="1.5"
            stroke="#f7f7f7"
            strokeWidth="1.2"
          />
          <circle cx="5" cy="6" r="1.5" fill="#f7f7f7" />
          <path
            d="M1.5 11.5L5 8L8 11L10.5 8.5L14.5 11.5"
            stroke="#f7f7f7"
            strokeWidth="1.2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>

        {/* Filename */}
        <span className="min-w-0 flex-1 truncate text-xs text-[#f7f7f7]">
          {filename}
        </span>

        {/* Dimensions */}
        <span className="shrink-0 text-xs text-[#919191]">
          {width} x {height}
        </span>

        {/* Close button - visible on hover */}
        <button
          className={cn(
            "flex h-5 w-5 shrink-0 items-center justify-center rounded",
            "text-[#919191] transition-colors hover:bg-[#363636] hover:text-[#f7f7f7]",
            "opacity-0 transition-opacity duration-150",
            hovered && "opacity-100"
          )}
          onClick={(e: MouseEvent) => {
            e.stopPropagation();
          }}
          aria-label="Close"
        >
          <X size={12} />
        </button>
      </div>

      {/* Image container */}
      <div className="relative overflow-hidden">
        <Image
          src={imageUrl}
          alt={filename}
          width={width}
          height={height}
          className="h-auto w-full object-cover"
          unoptimized
        />

        {/* Watermark overlay */}
        {watermarkUrl && (
          <div
            className="pointer-events-none absolute z-10"
            style={{ width: 210, height: 102 }}
          >
            <Image
              src={watermarkUrl}
              alt="Watermark"
              width={210}
              height={102}
              className="h-full w-full object-contain"
              unoptimized
            />
          </div>
        )}
      </div>

      {/* React Flow handles */}
      <Handle type="target" position={Position.Left} className="!bg-[#919191]" />
      <Handle type="source" position={Position.Right} className="!bg-[#919191]" />
    </div>
  );
}
