"use client";

import {
  MousePointer2,
  Pencil,
  SquareDashed,
  Undo2,
  X,
} from "lucide-react";
import { NodeToolbar, Position } from "@xyflow/react";

export type ImageElementEditTool = "point" | "box" | "brush";

interface ImageElementEditToolbarProps {
  activeTool: ImageElementEditTool;
  brushSize: number;
  onToolChange: (tool: ImageElementEditTool) => void;
  onBrushSizeChange: (size: number) => void;
  onClose: () => void;
}

export function ImageElementEditToolbar({
  activeTool,
  brushSize,
  onToolChange,
  onBrushSizeChange,
  onClose,
}: ImageElementEditToolbarProps) {
  const tools = [
    { key: "point", label: "点选", icon: MousePointer2 },
    { key: "box", label: "框选", icon: SquareDashed },
    { key: "brush", label: "画笔", icon: Pencil },
  ] as const;

  return (
    <NodeToolbar
      position={Position.Top}
      offset={52}
      align="center"
      className="nodrag nopan z-[1001]"
      data-image-element-edit-toolbar
    >
      <div
        onPointerDown={(event) => event.stopPropagation()}
        onClick={(event) => event.stopPropagation()}
        className="flex h-[44px] w-[272px] items-center gap-1.5 rounded-xl border border-[#363636] bg-[#262626] p-1.5 shadow-[0_8px_30px_rgba(0,0,0,0.38)]"
      >
        <button
          type="button"
          data-image-element-edit-close
          onClick={onClose}
          aria-label="关闭元素编辑"
          title="关闭元素编辑"
          className="flex size-8 shrink-0 items-center justify-center rounded-lg text-[#b8b8b8] hover:bg-white/[0.07] hover:text-white"
        >
          <X size={16} aria-hidden="true" />
        </button>
        <span aria-hidden="true" className="h-6 w-px shrink-0 bg-white/10" />
        {tools.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            type="button"
            data-image-element-edit-tool={key}
            data-active={activeTool === key ? "true" : "false"}
            aria-label={label}
            aria-pressed={activeTool === key}
            title={label}
            onClick={() => onToolChange(key)}
            className={`flex size-8 shrink-0 items-center justify-center rounded-lg text-[#b8b8b8] hover:bg-white/[0.07] hover:text-white ${
              activeTool === key ? "bg-white/[0.08] text-white" : ""
            }`}
          >
            <Icon size={16} aria-hidden="true" />
          </button>
        ))}
        <div
          data-image-element-edit-brush-size
          className="flex h-8 min-w-0 flex-1 items-center gap-1.5 rounded-lg px-1 text-[#9d9d9d]"
        >
          <span
            aria-hidden="true"
            className="shrink-0 rounded-full border border-current"
            style={{ width: Math.max(6, Math.min(14, brushSize)), height: Math.max(6, Math.min(14, brushSize)) }}
          />
          <input
            aria-label="画笔尺寸"
            type="range"
            min="1"
            max="40"
            step="1"
            value={brushSize}
            onChange={(event) => onBrushSizeChange(Number(event.target.value))}
            className="h-3 min-w-0 flex-1 accent-[#5ddcff]"
          />
        </div>
        <span aria-hidden="true" className="h-6 w-px shrink-0 bg-white/10" />
        <button
          type="button"
          data-image-element-edit-undo
          disabled
          aria-label="撤销"
          title="撤销"
          className="flex size-8 shrink-0 items-center justify-center rounded-lg text-[#676767] disabled:opacity-100"
        >
          <Undo2 size={16} aria-hidden="true" />
        </button>
      </div>
    </NodeToolbar>
  );
}

