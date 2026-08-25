"use client";

import {
  Box,
  GalleryHorizontalEnd,
  Grid3X3,
  Lightbulb,
  Redo2,
  ScanLine,
  SlidersHorizontal,
  Sparkles,
  Undo2,
} from "lucide-react";
import { NodeToolbar, Position } from "@xyflow/react";

const actions = [
  { label: "人像质感调节", icon: SlidersHorizontal, badge: "NEW" },
  { label: "全景", icon: GalleryHorizontalEnd },
  { label: "多角度", icon: Box },
  { label: "打光", icon: Lightbulb },
  { label: "九宫格", icon: Grid3X3 },
  { label: "高清", icon: Sparkles },
  { label: "宫格切分", icon: ScanLine },
];

export type ImageToolbarAction = (typeof actions)[number]["label"];

interface ImageToolbarProps {
  portraitEnhanced: boolean;
  onAction: (action: ImageToolbarAction) => void;
}

export function ImageToolbar({ portraitEnhanced, onAction }: ImageToolbarProps) {
  return (
    <NodeToolbar
      position={Position.Top}
      offset={16}
      align="center"
      className="nodrag nopan z-[1001]"
      data-image-toolbar
    >
      <div
        onPointerDown={(event) => event.stopPropagation()}
        onClick={(event) => event.stopPropagation()}
        className="flex h-[49px] w-[900.5px] items-center gap-1 rounded-xl border border-[#363636] bg-[#262626] p-2 shadow-[0_8px_30px_rgba(0,0,0,0.38)]"
      >
        {actions.map((action) => {
          const Icon = action.icon;
          return (
            <button
              key={action.label}
              type="button"
              onClick={() => onAction(action.label)}
              aria-pressed={action.label === "人像质感调节" ? portraitEnhanced : undefined}
              className={`relative flex h-8 shrink-0 items-center gap-2 rounded-lg px-2.5 text-sm hover:bg-white/[0.07] ${
                action.label === "人像质感调节" && portraitEnhanced ? "bg-[#09caf5]/10 text-[#09caf5]" : "text-[#e5e5e5]"
              }`}
            >
              <Icon size={16} />
              <span>{action.label}</span>
              {action.badge && <span className="rounded bg-[#0d5964] px-1 py-0.5 text-[9px] text-[#4de1f4]">{action.badge}</span>}
            </button>
          );
        })}
        <span className="min-w-3 flex-1" />
        <span className="h-5 w-px shrink-0 bg-white/10" />
        <button type="button" className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-[#a8a8a8] hover:bg-white/[0.07] hover:text-white" title="撤销" aria-label="撤销">
          <Undo2 size={15} />
        </button>
        <button type="button" className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-[#a8a8a8] hover:bg-white/[0.07] hover:text-white" title="重做" aria-label="重做">
          <Redo2 size={15} />
        </button>
      </div>
    </NodeToolbar>
  );
}
