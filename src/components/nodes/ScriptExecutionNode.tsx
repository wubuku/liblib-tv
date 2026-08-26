"use client";

import { memo } from "react";
import { Clapperboard } from "lucide-react";
import { Handle, Position, type Node, type NodeProps } from "@xyflow/react";
import { cn } from "@/lib/utils";
import { useUIStore } from "@/store/uiStore";

export interface ScriptExecutionData extends Record<string, unknown> {
  title?: string;
  steps?: Array<{ label: string; completed?: boolean }>;
}

export type ScriptExecutionType = Node<ScriptExecutionData, "script-execution">;

function ScriptExecutionNodeComponent({ id, data, selected }: NodeProps<ScriptExecutionType>) {
  const openDirectorDesk = useUIStore((state) => state.openDirectorDesk);
  const title = data.title || "第一集：咖啡馆对峙";
  const objectCount = typeof data.objectCount === "number" ? data.objectCount : 4;
  const cameraCount = typeof data.cameraCount === "number" ? data.cameraCount : 1;

  return (
    <div
      data-director-node
      data-director-node-id={id}
      className={cn(
        "group relative flex h-full w-full flex-col overflow-visible rounded-[4px] border bg-[#252525]",
        selected ? "border-[#09caf5] shadow-[0_0_0_2px_rgba(9,202,245,0.22)]" : "border-white/10",
      )}
    >
      <Handle type="target" position={Position.Left} id="target" style={{ width: 20, height: 20 }} />
      <Handle type="source" position={Position.Right} id="source" style={{ width: 20, height: 20 }} />

      <div className="pointer-events-none absolute -top-8 left-0 truncate text-sm text-[#7f7f7f]">{title}</div>
      <div className="flex flex-1 flex-col items-center justify-center gap-3 border-b border-white/[0.06]">
        <span className="flex h-14 w-14 items-center justify-center rounded-full border border-white/10 bg-white/[0.04]">
          <Clapperboard size={30} strokeWidth={1.2} className="text-[#b6b6b6]" />
        </span>
        <div className="text-center">
          <p className="text-sm text-[#ededed]">3D导演台</p>
          <p className="mt-1 text-[11px] text-[#8e8e8e]">搭建3D场景，截图作为构图参考</p>
        </div>
      </div>
      <div className="flex h-[64px] items-center justify-center gap-4 text-[11px] text-[#a9a9a9]">
        <span>{objectCount} 个场景对象</span>
        <span className="h-3 w-px bg-white/10" />
        <span>{cameraCount} 个机位</span>
      </div>
      <div className="p-4 pt-0">
        <button
          type="button"
          data-open-director
          onClick={(event) => {
            event.stopPropagation();
            openDirectorDesk(id);
          }}
          className="flex h-9 w-full items-center justify-center gap-1 rounded bg-white/[0.08] text-xs text-[#f1f1f1] hover:bg-white/[0.12]"
        >
          进入导演台 <span>→</span>
        </button>
      </div>
    </div>
  );
}

export const ScriptExecutionNode = memo(ScriptExecutionNodeComponent);
