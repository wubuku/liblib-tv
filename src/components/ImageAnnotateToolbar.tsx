"use client";

import {
  Eraser,
  Paintbrush,
  PencilLine,
  Redo2,
  RotateCcw,
  Undo2,
  X,
} from "lucide-react";
import { NodeToolbar, Position } from "@xyflow/react";

export type ImageAnnotateTool = "brush" | "eraser";

interface ImageAnnotateToolbarProps {
  activeTool: ImageAnnotateTool;
  onToolChange: (tool: ImageAnnotateTool) => void;
  onClose: () => void;
}

export function ImageAnnotateToolbar({
  activeTool,
  onToolChange,
  onClose,
}: ImageAnnotateToolbarProps) {
  return (
    <NodeToolbar
      position={Position.Top}
      offset={10}
      align="center"
      className="nodrag nopan z-[1001]"
      data-image-annotate-toolbar
    >
      <div
        onPointerDown={(event) => event.stopPropagation()}
        onClick={(event) => event.stopPropagation()}
        className="flex h-[49px] w-[536px] items-center justify-center gap-2 rounded-xl border border-[#363636] bg-[#262626] p-2 shadow-[0_8px_30px_rgba(0,0,0,0.38)]"
      >
        <button
          type="button"
          data-image-annotate-close
          onClick={onClose}
          aria-label="关闭标注"
          title="关闭标注"
          className="flex size-8 shrink-0 items-center justify-center rounded-lg text-[#d7d7d7] hover:bg-white/[0.07] hover:text-white"
        >
          <X size={16} />
        </button>
        <button
          type="button"
          data-image-annotate-label
          aria-label="标注"
          title="标注"
          className="flex h-8 w-[84px] shrink-0 items-center justify-center gap-2 rounded-lg bg-white/[0.07] text-sm text-[#ededed]"
        >
          <PencilLine size={16} />
          <span>标注</span>
        </button>
        <button
          type="button"
          data-image-annotate-brush
          data-active={activeTool === "brush" ? "true" : "false"}
          onClick={() => onToolChange("brush")}
          aria-pressed={activeTool === "brush"}
          aria-label="画笔"
          title="画笔"
          className={`flex size-8 shrink-0 items-center justify-center rounded-lg ${
            activeTool === "brush" ? "bg-[#09caf5]/15 text-[#09caf5]" : "text-[#b8b8b8] hover:bg-white/[0.07] hover:text-white"
          }`}
        >
          <Paintbrush size={16} />
        </button>
        <button
          type="button"
          data-image-annotate-eraser
          data-active={activeTool === "eraser" ? "true" : "false"}
          onClick={() => onToolChange("eraser")}
          aria-pressed={activeTool === "eraser"}
          aria-label="橡皮"
          title="橡皮"
          className={`flex size-8 shrink-0 items-center justify-center rounded-lg ${
            activeTool === "eraser" ? "bg-[#09caf5]/15 text-[#09caf5]" : "text-[#b8b8b8] hover:bg-white/[0.07] hover:text-white"
          }`}
        >
          <Eraser size={16} />
        </button>
        <button
          type="button"
          data-image-annotate-clear
          disabled
          aria-label="清空标注"
          title="清空标注"
          className="flex size-8 shrink-0 items-center justify-center rounded-lg text-[#676767] disabled:opacity-100"
        >
          <RotateCcw size={16} />
        </button>
        <button
          type="button"
          data-image-annotate-undo
          disabled
          aria-label="撤销标注"
          title="撤销"
          className="flex size-8 shrink-0 items-center justify-center rounded-lg text-[#676767] disabled:opacity-100"
        >
          <Undo2 size={16} />
        </button>
        <button
          type="button"
          data-image-annotate-redo
          disabled
          aria-label="重做标注"
          title="重做"
          className="flex size-8 shrink-0 items-center justify-center rounded-lg text-[#676767] disabled:opacity-100"
        >
          <Redo2 size={16} />
        </button>
        <button
          type="button"
          data-image-annotate-save
          disabled
          aria-label="保存"
          title="保存"
          className="flex h-8 w-[84px] shrink-0 items-center justify-center rounded-lg bg-white/[0.08] text-sm text-[#666] disabled:opacity-100"
        >
          保存
        </button>
      </div>
    </NodeToolbar>
  );
}
