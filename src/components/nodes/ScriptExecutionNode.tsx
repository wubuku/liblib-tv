"use client";

import { memo } from "react";
import { Check, Menu } from "lucide-react";
import { Handle, Position, type Node, type NodeProps } from "@xyflow/react";
import { cn } from "@/lib/utils";

export interface ScriptExecutionData extends Record<string, unknown> {
  title?: string;
  steps?: Array<{ label: string; completed?: boolean }>;
}

export type ScriptExecutionType = Node<ScriptExecutionData, "script-execution">;

function ScriptExecutionNodeComponent({ data, selected }: NodeProps<ScriptExecutionType>) {
  const title = data.title || "第一集：咖啡馆对峙";
  const steps = data.steps || [
    { label: "确认镜头", completed: true },
    { label: "准备资产", completed: true },
    { label: "合成提示词", completed: true },
  ];

  return (
    <div
      className={cn(
        "group relative flex h-full w-full flex-col overflow-visible rounded-[4px] border bg-[#252525]",
        selected ? "border-[#09caf5] shadow-[0_0_0_2px_rgba(9,202,245,0.22)]" : "border-white/10",
      )}
    >
      <Handle type="target" position={Position.Left} id="target" style={{ width: 20, height: 20 }} />
      <Handle type="source" position={Position.Right} id="source" style={{ width: 20, height: 20 }} />

      <div className="pointer-events-none absolute -top-8 left-0 truncate text-sm text-[#7f7f7f]">{title}</div>
      <div className="flex flex-1 items-center justify-center border-b border-white/[0.06]">
        <Menu size={34} strokeWidth={1.2} className="text-[#6d6d6d]" />
      </div>
      <div className="flex h-[105px] items-center justify-center px-4">
        {steps.map((step, index) => (
          <div key={step.label} className="flex items-center">
            <div className="flex flex-col items-center gap-2">
              <span className="flex h-6 w-6 items-center justify-center rounded-full bg-[#f4f4f4] text-[#202020]">
                {step.completed ? <Check size={12} strokeWidth={2.5} /> : index + 1}
              </span>
              <span className="whitespace-nowrap text-[10px] text-[#d3d3d3]">{step.label}</span>
            </div>
            {index < steps.length - 1 && <span className="mb-5 h-px w-9 bg-[#838383]" />}
          </div>
        ))}
      </div>
      <div className="p-4 pt-0">
        <button className="flex h-9 w-full items-center justify-center gap-1 rounded bg-white/[0.08] text-xs text-[#f1f1f1] hover:bg-white/[0.12]">
          打开脚本节点 <span>→</span>
        </button>
      </div>
    </div>
  );
}

export const ScriptExecutionNode = memo(ScriptExecutionNodeComponent);
