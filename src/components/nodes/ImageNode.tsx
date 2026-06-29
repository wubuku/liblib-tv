"use client";

import { useState, useRef, type MouseEvent } from "react";
import Image from "next/image";
import { X } from "lucide-react";
import { type NodeProps, type Node, useReactFlow } from "@xyflow/react";
import { Handle, Position } from "@xyflow/react";
import { cn } from "@/lib/utils";
import { ImageEditPanel } from "@/components/ImageEditPanel";
import { ImageToolbar } from "@/components/ImageToolbar";
import { PlusIndicator } from "../PlusIndicator";

export interface ImageNodeData extends Record<string, unknown> {
  filename: string;
  width: number;
  height: number;
  imageUrl: string;
  watermarkUrl?: string;
}

export type ImageNodeType = Node<ImageNodeData, "image">;

function PlusIcon() {
  return null;
}

export function ImageNode({ id, data, selected }: NodeProps<ImageNodeType>) {
  const [hovered, setHovered] = useState(false);
  const { deleteElements } = useReactFlow();
  const nodeRef = useRef<HTMLDivElement>(null);
  const [showLeftHandle, setShowLeftHandle] = useState(false);
  const [showRightHandle, setShowRightHandle] = useState(false);

  const { filename, width, height, imageUrl, watermarkUrl } = data;

  const handleDelete = (e: MouseEvent) => {
    e.stopPropagation();
    deleteElements({ nodes: [{ id }] });
  };

  // Show handles when hovering over the node
  const handleMouseEnter = () => {
    setShowLeftHandle(true);
    setShowRightHandle(true);
  };

  const handleMouseLeave = () => {
    setShowLeftHandle(false);
    setShowRightHandle(false);
    setHovered(false);
  };

  return (
    <div className="relative">
      <div
        ref={nodeRef}
        className={cn(
          "w-[360px] rounded-xl border border-[#363636] bg-[#171717] overflow-visible group",
          "transition-shadow duration-150",
          selected ? "border-[#09caf5] shadow-[0_0_0_2px_rgba(9,202,245,0.3)]" : "border-[#363636]",
          hovered && !selected && "shadow-[0_2px_12px_rgba(0,0,0,0.4)]"
        )}
        onMouseEnter={() => {
          setHovered(true);
          handleMouseEnter();
        }}
        onMouseLeave={handleMouseLeave}
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

        {/* Left Handle - Target */}
        <Handle
          type="target"
          position={Position.Left}
          id="target"
          className="!opacity-0 !pointer-events-auto"
        />
        {/* Left "+" indicator (42x42 transparent circle) */}
        <div
          className={cn(
            "transition-opacity duration-150",
            showLeftHandle ? "opacity-100" : "opacity-0"
          )}
        >
          <PlusIndicator side="left" />
        </div>

        {/* Right Handle - Source */}
        <Handle
          type="source"
          position={Position.Right}
          id="source"
          className="!opacity-0 !pointer-events-auto"
        />
        {/* Right "+" indicator (42x42 transparent circle) */}
        <div
          className={cn(
            "transition-opacity duration-150",
            showRightHandle ? "opacity-100" : "opacity-0"
          )}
        >
          <PlusIndicator side="right" />
        </div>

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
      </div>

      {/* Image Edit Panel - appears below when selected */}
      {selected && (
        <ImageEditPanel onClose={() => {}} />
      )}

      {/* Image Toolbar - appears on the right when selected */}
      {selected && <ImageToolbar />}
    </div>
  );
}
