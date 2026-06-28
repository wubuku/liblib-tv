"use client";

import { memo, useState, useEffect, useRef } from "react";
import { Handle, Position, type NodeProps, type Node, useReactFlow } from "@xyflow/react";
import { cn } from "@/lib/utils";

export interface TextNodeData extends Record<string, unknown> {
  content: string;
}

export type TextNodeType = Node<TextNodeData>;

function PlusIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
      <path d="M6 1V11M1 6H11" stroke="white" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

function TextNodeComponent({ id, data, selected }: NodeProps<TextNodeType>) {
  const [isEditing, setIsEditing] = useState(false);
  const [content, setContent] = useState(data.content);
  const { deleteElements } = useReactFlow();
  const nodeRef = useRef<HTMLDivElement>(null);
  const [showLeftHandle, setShowLeftHandle] = useState(false);
  const [showRightHandle, setShowRightHandle] = useState(false);

  const handleDelete = (e: React.MouseEvent) => {
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
  };

  return (
    <div
      ref={nodeRef}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      className={cn(
        "bg-[#212121] rounded-xl border min-w-[200px] max-w-[300px] overflow-visible flex flex-col group relative",
        selected ? "border-[#09caf5] shadow-[0_0_0_2px_rgba(9,202,245,0.3)]" : "border-[#363636]",
        "hover:shadow-lg transition-shadow"
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
      {/* Left "+" indicator */}
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
      {/* Right "+" indicator */}
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
      <div className="flex items-center gap-2 px-3 py-2 border-b border-[#363636]">
        <svg
          className="w-4 h-4 text-[#919191]"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M4 6h16M4 12h16m-7 6h7"
          />
        </svg>
        <span className="text-sm font-medium text-[#f7f7f7]">文本</span>
      </div>

      {/* Content */}
      <div className="p-3">
        {isEditing ? (
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            onBlur={() => setIsEditing(false)}
            onKeyDown={(e) => {
              if (e.key === "Escape") setIsEditing(false);
            }}
            className="w-full bg-[#363636] text-[#f7f7f7] text-sm p-2 rounded border border-[#525252] focus:border-[#09caf5] outline-none resize-none min-h-[60px]"
            autoFocus
          />
        ) : (
          <div
            onClick={() => setIsEditing(true)}
            className="text-sm text-[#f7f7f7] cursor-text hover:bg-[#363636] p-2 rounded min-h-[60px] whitespace-pre-wrap"
          >
            {content || "点击编辑文本..."}
          </div>
        )}
      </div>
    </div>
  );
}

export const TextNode = memo(TextNodeComponent);
