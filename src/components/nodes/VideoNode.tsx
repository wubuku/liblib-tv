"use client";

import { memo, useState, useRef } from "react";
import { Handle, Position, type NodeProps, type Node, useReactFlow } from "@xyflow/react";
import { cn } from "@/lib/utils";
import { CameraMovementDialog } from "../CameraMovementDialog";

export interface VideoNodeData extends Record<string, unknown> {
  filename?: string;
  duration?: number;
  cameraMovement?: {
    movementType: string;
    speed: string;
    duration: number;
    amplitude: number;
  };
}

export type VideoNodeType = Node<VideoNodeData, "video">;

function PlusIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
      <path d="M6 1V11M1 6H11" stroke="white" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

function VideoIcon({ className }: { className?: string }) {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 16 16"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <rect
        x="1.5"
        y="3.5"
        width="13"
        height="9"
        rx="1.5"
        stroke="currentColor"
        strokeWidth="1.2"
      />
      <path
        d="M6.5 6L10 8L6.5 10V6Z"
        fill="currentColor"
      />
    </svg>
  );
}

function CameraIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
      <path
        d="M2 4H12V11H2V4Z"
        stroke="currentColor"
        strokeWidth="1.2"
      />
      <circle cx="7" cy="7.5" r="2" stroke="currentColor" strokeWidth="1.2" />
      <path d="M5 4V3H9V4" stroke="currentColor" strokeWidth="1.2" />
    </svg>
  );
}

function VideoNodeComponent({ id, data, selected }: NodeProps<VideoNodeType>) {
  const { filename = "分镜视频", duration = 5, cameraMovement } = data;
  const { deleteElements } = useReactFlow();
  const nodeRef = useRef<HTMLDivElement>(null);
  const [showLeftHandle, setShowLeftHandle] = useState(false);
  const [showRightHandle, setShowRightHandle] = useState(false);
  const [isCameraOpen, setIsCameraOpen] = useState(false);

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    deleteElements({ nodes: [{ id }] });
  };

  return (
    <div
      ref={nodeRef}
      onMouseEnter={() => {
        setShowLeftHandle(true);
        setShowRightHandle(true);
      }}
      onMouseLeave={() => {
        setShowLeftHandle(false);
        setShowRightHandle(false);
      }}
      className={cn(
        "w-[320px] overflow-visible rounded-xl border bg-[#212121] flex flex-col transition-shadow group relative",
        selected ? "border-[#09caf5] shadow-[0_0_0_2px_rgba(9,202,245,0.3)]" : "border-[#363636]",
        !selected && "hover:shadow-[0_4px_12px_rgba(0,0,0,0.3)]"
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

      {/* Left Handle - Target */}
      <Handle
        type="target"
        position={Position.Left}
        id="target"
        className="!opacity-0 !pointer-events-auto"
      />
      <div
        className={cn(
          "absolute left-0 top-1/2 -translate-x-1/2 -translate-y-1/2 z-50",
          "w-5 h-5 rounded-full bg-[#09caf5] border-2 border-[#171717]",
          "flex items-center justify-center",
          "transition-all duration-150 ease-in-out",
          "pointer-events-none",
          showLeftHandle ? "opacity-100 scale-100" : "opacity-0 scale-50"
        )}
      >
        <PlusIcon />
      </div>

      {/* Right Handle - Source */}
      <Handle
        type="source"
        position={Position.Right}
        id="source"
        className="!opacity-0 !pointer-events-auto"
      />
      <div
        className={cn(
          "absolute right-0 top-1/2 translate-x-1/2 -translate-y-1/2 z-50",
          "w-5 h-5 rounded-full bg-[#09caf5] border-2 border-[#171717]",
          "flex items-center justify-center",
          "transition-all duration-150 ease-in-out",
          "pointer-events-none",
          showRightHandle ? "opacity-100 scale-100" : "opacity-0 scale-50"
        )}
      >
        <PlusIcon />
      </div>

      {/* Header */}
      <div className="flex items-center gap-2 border-b border-[#363636] px-4 py-3">
        <VideoIcon className="text-[#f7f7f7]" />
        <span className="text-sm font-semibold text-[#f7f7f7]">{filename}</span>
        <span className="ml-auto text-xs text-[#919191]">{duration}s</span>
      </div>

      {/* Video Preview area (placeholder) */}
      <div className="relative aspect-video bg-[#171717] flex items-center justify-center">
        <div className="flex flex-col items-center gap-2 text-[#525252]">
          <VideoIcon className="w-12 h-12" />
          <span className="text-xs">视频预览</span>
        </div>
        {/* Play overlay */}
        <button className="absolute inset-0 flex items-center justify-center group/play">
          <div className="w-12 h-12 rounded-full bg-black/60 flex items-center justify-center opacity-0 group-hover/play:opacity-100 transition-opacity">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M6 4L16 10L6 16V4Z" fill="white" />
            </svg>
          </div>
        </button>
      </div>

      {/* Camera Movement Config */}
      <div className="border-t border-[#363636] p-3">
        <button
          onClick={(e) => {
            e.stopPropagation();
            setIsCameraOpen(true);
          }}
          className="w-full flex items-center justify-between gap-2 px-3 py-2 rounded-lg bg-[#363636] hover:bg-[#525252] transition-colors text-[#f7f7f7] text-sm"
        >
          <div className="flex items-center gap-2">
            <CameraIcon />
            <span>运镜</span>
            {cameraMovement && (
              <span className="text-[#919191] text-xs">
                · {getMovementLabel(cameraMovement.movementType)}
              </span>
            )}
          </div>
          <svg
            width="12"
            height="12"
            viewBox="0 0 12 12"
            fill="none"
            className="text-[#919191]"
          >
            <path
              d="M3 4L6 7L9 4"
              stroke="currentColor"
              strokeWidth="1.2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </button>
      </div>

      {/* Camera Movement Dialog */}
      <CameraMovementDialog
        isOpen={isCameraOpen}
        onClose={() => setIsCameraOpen(false)}
        onApply={(config) => {
          console.log("Camera movement applied:", config);
        }}
      />
    </div>
  );
}

function getMovementLabel(id: string): string {
  const map: Record<string, string> = {
    static: "静止",
    pan: "横摇",
    tilt: "俯仰",
    dolly: "推拉",
    truck: "横移",
    pedestal: "升降",
    roll: "旋转",
    zoom: "变焦",
    orbit: "环绕",
    crane: "摇臂",
  };
  return map[id] || id;
}

export const VideoNode = memo(VideoNodeComponent);