"use client";

import {
  Box,
  Download,
  Expand,
  GalleryHorizontalEnd,
  Grid3X3,
  Layers3,
  Lightbulb,
  MousePointer2,
  PencilLine,
  RotateCw,
  ScanLine,
  SlidersHorizontal,
  Sparkles,
} from "lucide-react";
import { NodeToolbar, Position } from "@xyflow/react";

const actions = [
  {
    label: "人像质感调节",
    icon: SlidersHorizontal,
    badge: "NEW",
    testId: "image-toolbar-portrait-texture",
    widthClass: "w-[178px]",
    available: true,
  },
  {
    label: "全景",
    icon: GalleryHorizontalEnd,
    testId: "image-toolbar-panorama-slash",
    widthClass: "w-[62px]",
    available: true,
  },
  {
    label: "多角度",
    icon: Box,
    testId: "image-toolbar-angle",
    widthClass: "w-[75px]",
    available: true,
  },
  {
    label: "打光",
    icon: Lightbulb,
    testId: "image-toolbar-light",
    widthClass: "w-[62px]",
    available: true,
  },
  {
    label: "九宫格",
    icon: Grid3X3,
    testId: "image-toolbar-nine-grid",
    widthClass: "w-[91px]",
    available: true,
  },
  {
    label: "高清",
    icon: Sparkles,
    testId: "image-editor-primary-tool-trigger",
    widthClass: "w-[78px]",
    available: true,
  },
  {
    label: "元素编辑",
    icon: MousePointer2,
    testId: "image-toolbar-interactive-edit",
    widthClass: "w-[88px]",
    available: true,
  },
  {
    label: "图层分离",
    icon: Layers3,
    testId: "image-toolbar-layer-separation",
    widthClass: "w-[88px]",
    available: false,
  },
  {
    label: "宫格切分",
    icon: ScanLine,
    testId: "image-toolbar-grid-split",
    widthClass: "w-[104px]",
    available: true,
  },
  {
    label: "标注",
    icon: PencilLine,
    testId: "image-toolbar-annotate",
    widthClass: "w-8",
    available: true,
    iconOnly: true,
  },
  {
    label: "旋转",
    icon: RotateCw,
    testId: "image-toolbar-rotate",
    widthClass: "w-8",
    available: true,
    mediaRequired: true,
    iconOnly: true,
  },
  {
    label: "下载",
    icon: Download,
    testId: "image-toolbar-download",
    widthClass: "w-8",
    available: false,
    iconOnly: true,
  },
  {
    label: "预览",
    icon: Expand,
    testId: "image-toolbar-preview",
    widthClass: "w-8",
    available: true,
    iconOnly: true,
  },
] as const;

export type ImageToolbarAction = (typeof actions)[number]["label"];

interface ImageToolbarProps {
  zoom: number;
  portraitEnhanced: boolean;
  hasMedia: boolean;
  onAction: (action: ImageToolbarAction) => void;
}

export function ImageToolbar({
  zoom,
  portraitEnhanced,
  hasMedia,
  onAction,
}: ImageToolbarProps) {
  return (
    <NodeToolbar
      position={Position.Top}
      offset={10 + 24 * zoom}
      align="center"
      className="nodrag nopan z-[1001]"
      data-image-toolbar
    >
      <div
        onPointerDown={(event) => event.stopPropagation()}
        onClick={(event) => event.stopPropagation()}
        className="flex h-[49px] w-[1092.5px] items-center justify-center gap-2 rounded-xl border border-[#363636] bg-[#262626] p-2 shadow-[0_8px_30px_rgba(0,0,0,0.38)]"
      >
        {actions.map((action) => {
          const Icon = action.icon;
          const iconOnly = "iconOnly" in action && action.iconOnly;
          const isAvailable =
            action.available && (!("mediaRequired" in action) || hasMedia);
          return (
            <button
              key={action.label}
              type="button"
              data-testid={action.testId}
              disabled={!isAvailable}
              onClick={() => onAction(action.label)}
              aria-pressed={action.label === "人像质感调节" ? portraitEnhanced : undefined}
              aria-label={iconOnly ? action.label : undefined}
              title={iconOnly ? action.label : undefined}
              className={`relative flex h-8 shrink-0 items-center justify-center gap-2 rounded-lg text-sm hover:bg-white/[0.07] disabled:opacity-100 disabled:hover:bg-transparent ${action.widthClass} ${
                action.label === "人像质感调节" && portraitEnhanced ? "bg-[#09caf5]/10 text-[#09caf5]" : "text-[#e5e5e5]"
              }`}
            >
              <Icon size={16} />
              {!iconOnly && <span>{action.label}</span>}
              {"badge" in action && action.badge && (
                <span className="rounded bg-[#0d5964] px-1 py-0.5 text-[9px] text-[#4de1f4]">
                  {action.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>
    </NodeToolbar>
  );
}
