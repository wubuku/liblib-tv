"use client";

import { memo, useState, useRef } from "react";
import { Handle, Position, type NodeProps, type Node, useReactFlow } from "@xyflow/react";
import { cn } from "@/lib/utils";
import { PlusIndicator } from "../PlusIndicator";

export interface ScriptExecutionData extends Record<string, unknown> {
  steps?: Array<{
    label: string;
    completed?: boolean;
  }>;
}

export type ScriptExecutionType = Node<ScriptExecutionData, "script-execution">;

function PlusIcon() {
  return null;
}

function MenuIcon({ className }: { className?: string }) {
  return (
    <svg
      width="20"
      height="20"
      viewBox="0 0 20 20"
      fill="none"
      className={className}
    >
      <path
        d="M3 5h14M3 10h14M3 15h14"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    </svg>
  );
}

function CheckIcon() {
  return (
    <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
      <path
        d="M2 5L4 7L8 3"
        stroke="#171717"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function ScriptExecutionNodeComponent({ id, data, selected }: NodeProps<ScriptExecutionType>) {
  const { deleteElements } = useReactFlow();
  const nodeRef = useRef<HTMLDivElement>(null);
  const [showLeftHandle, setShowLeftHandle] = useState(false);
  const [showRightHandle, setShowRightHandle] = useState(false);

  const steps = data.steps || [
    { label: "确认镜头", completed: true },
    { label: "准备资产", completed: true },
    { label: "合成提示词", completed: false },
  ];

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
        "w-[260px] overflow-visible rounded-xl bg-[#2a2d3d] border flex flex-col group relative",
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

      {/* Left Handle - Target */}
      <Handle
        type="target"
        position={Position.Left}
        id="target"
        className="!opacity-0 !pointer-events-auto"
      />
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
      <div
        className={cn(
          "transition-opacity duration-150",
          showRightHandle ? "opacity-100" : "opacity-0"
        )}
      >
        <PlusIndicator side="right" />
      </div>

      {/* Header - drag handle area */}
      <div className="flex items-center justify-center py-4 border-b border-[#363636] cursor-grab active:cursor-grabbing">
        <MenuIcon className="text-[#919191]" />
      </div>

      {/* Steps */}
      <div className="flex items-center justify-between px-3 py-4">
        {steps.map((step, index) => (
          <div key={step.label} className="flex items-center">
            {/* Circle with check or number */}
            <div className="flex flex-col items-center gap-1.5">
              <div
                className={cn(
                  "w-7 h-7 rounded-full flex items-center justify-center text-xs font-medium transition-colors",
                  step.completed
                    ? "bg-[#09caf5] text-[#171717]"
                    : "bg-[#363636] text-[#919191] border border-[#525252]"
                )}
              >
                {step.completed ? <CheckIcon /> : index + 1}
              </div>
              <span className="text-[10px] text-[#f7f7f7] whitespace-nowrap">
                {step.label}
              </span>
            </div>

            {/* Connector line between circles (except after last) */}
            {index < steps.length - 1 && (
              <div
                className={cn(
                  "w-6 h-px mx-1 mb-4",
                  step.completed && steps[index + 1]?.completed
                    ? "bg-[#09caf5]"
                    : "bg-[#525252]"
                )}
              />
            )}
          </div>
        ))}
      </div>

      {/* Action button */}
      <div className="px-3 pb-3">
        <button className="w-full py-2 rounded-lg bg-[#363636] hover:bg-[#525252] transition-colors text-sm text-[#f7f7f7] flex items-center justify-center gap-1">
          打开脚本节点
          <span>→</span>
        </button>
      </div>
    </div>
  );
}

export const ScriptExecutionNode = memo(ScriptExecutionNodeComponent);