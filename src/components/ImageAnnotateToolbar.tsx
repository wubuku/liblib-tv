"use client";

import { useState } from "react";
import {
  Circle,
  Pencil,
  Redo2,
  Square,
  Type,
  Undo2,
  X,
} from "lucide-react";
import { NodeToolbar, Position } from "@xyflow/react";

interface ImageAnnotateToolbarProps {
  activeTool: ImageAnnotateTool;
  color: string;
  strokeWidth: number;
  onToolChange: (tool: ImageAnnotateTool) => void;
  onColorChange: (color: string) => void;
  onStrokeWidthChange: (strokeWidth: number) => void;
  onClose: () => void;
}

export type ImageAnnotateTool = "pencil" | "rect" | "text";

export function ImageAnnotateToolbar({
  activeTool,
  color,
  strokeWidth,
  onToolChange,
  onColorChange,
  onStrokeWidthChange,
  onClose,
}: ImageAnnotateToolbarProps) {
  const [isColorOpen, setIsColorOpen] = useState(false);
  const tools = [
    { key: "pencil", label: "画笔", icon: Pencil },
    { key: "rect", label: "矩形", icon: Square },
    { key: "text", label: "文字", icon: Type },
  ] as const;
  const colors = ["#ffcc00", "#ff7a00", "#ff2d55", "#ff0000", "#8e5cff", "#3a86ff", "#ffffff"];

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
          aria-label="标注"
          title="关闭标注"
          className="flex h-8 w-[68px] shrink-0 items-center justify-center gap-2 rounded-lg text-[13px] text-[#d7d7d7] hover:bg-white/[0.07] hover:text-white"
        >
          <X size={16} />
          <span>标注</span>
        </button>
        <span aria-hidden="true" className="h-6 w-px shrink-0 bg-white/10" />
        {tools.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            type="button"
            data-image-annotate-control={key}
            data-active={activeTool === key ? "true" : "false"}
            aria-pressed={activeTool === key}
            aria-label={label}
            title={label}
            onClick={() => onToolChange(key)}
            className={`flex size-8 shrink-0 items-center justify-center rounded-lg text-[#b8b8b8] hover:bg-white/[0.07] hover:text-white ${
              activeTool === key ? "bg-white/[0.08] text-white" : ""
            }`}
          >
            <Icon size={16} aria-hidden="true" />
          </button>
        ))}
        <span aria-hidden="true" className="h-6 w-px shrink-0 bg-white/10" />
        <div className="relative shrink-0">
          <button
            type="button"
            data-image-annotate-color
            aria-label="颜色"
            title="颜色"
            aria-expanded={isColorOpen}
            onClick={() => setIsColorOpen((open) => !open)}
            className={`flex size-8 items-center justify-center rounded-lg text-[#b8b8b8] hover:bg-white/[0.07] hover:text-white ${
              isColorOpen ? "bg-white/[0.08] text-white" : ""
            }`}
          >
            <Circle size={16} style={{ fill: color, color }} aria-hidden="true" />
          </button>
          {isColorOpen && (
            <div
              data-image-annotate-color-menu
              className="absolute left-1/2 top-full z-20 mt-2 grid w-[140px] -translate-x-1/2 grid-cols-4 gap-1 rounded-xl border border-[#363636] bg-[#262626] p-2 shadow-[0_8px_24px_rgba(0,0,0,0.42)]"
            >
              {colors.map((option) => (
                <button
                  key={option}
                  type="button"
                  aria-label={option}
                  onClick={() => {
                    onColorChange(option);
                    setIsColorOpen(false);
                  }}
                  className={`flex size-7 items-center justify-center rounded-lg hover:bg-white/[0.07] ${
                    option === color ? "ring-1 ring-white/70" : ""
                  }`}
                >
                  <span
                    className="size-4 rounded-full border border-white/30"
                    style={{ backgroundColor: option }}
                  />
                </button>
              ))}
            </div>
          )}
        </div>
        <div
          data-image-annotate-line-width
          className="flex h-8 w-[96px] shrink-0 items-center gap-2 rounded-lg px-2 text-[#9d9d9d]"
        >
          <span aria-hidden="true" className="h-4 w-4 rounded-full border border-current" />
          <input
            aria-label="线宽"
            type="range"
            min="1"
            max="40"
            step="1"
            value={strokeWidth}
            onChange={(event) => onStrokeWidthChange(Number(event.target.value))}
            className="h-3 min-w-0 flex-1 accent-[#5ddcff]"
          />
        </div>
        <span aria-hidden="true" className="h-6 w-px shrink-0 bg-white/10" />
        <button
          type="button"
          data-image-annotate-undo
          disabled
          aria-label="撤销"
          title="撤销"
          className="flex size-8 shrink-0 items-center justify-center rounded-lg text-[#676767] disabled:opacity-100"
        >
          <Undo2 size={16} />
        </button>
        <button
          type="button"
          data-image-annotate-redo
          disabled
          aria-label="重做"
          title="重做"
          className="flex size-8 shrink-0 items-center justify-center rounded-lg text-[#676767] disabled:opacity-100"
        >
          <Redo2 size={16} />
        </button>
        <button
          type="button"
          data-image-annotate-save
          aria-label="保存"
          title="保存"
          className="flex h-8 w-[56px] shrink-0 items-center justify-center rounded-lg bg-white text-[13px] text-[#202020] hover:bg-[#ededed]"
        >
          保存
        </button>
      </div>
    </NodeToolbar>
  );
}
