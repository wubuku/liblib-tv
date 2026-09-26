"use client";

import { Asterisk, BarChart2, Flower2, RefreshCw } from "lucide-react";
import { cn } from "@/lib/utils";

// Batch 530: 2026-09-27 源站第一轮采样实测可开（liblib-source-exploration-2026-09-25
// NOTES §3 + 截图 03b-image-model-menu.png）——图片节点参数条模型触发菜单。
// 7 行模型（名称 + 时长胶囊 + 选中态描述 + Qwen image 3.0 上新徽标）；
// Seedream 5.0 Pro 描述在菜单内截断，取 AgentDrawer 模型目录（batch 234 采样）
// 同名条目的完整文案（evidence-backed cross-reference）；
// Qwen image 3.0 行无描述采样，留空（SOURCE_FACT gap）。
export interface ImageModelOption {
  id: string;
  name: string;
  duration: string;
  description: string;
  badge?: "上新";
}

export const imageModels: ImageModelOption[] = [
  { id: "lib-image-2-5-pro", name: "Lib Image 2.5 Pro", duration: "30s", description: "精准生成与编辑，复杂指令稳定还原" },
  { id: "lib-image-2-5-fast", name: "Lib Image 2.5 Fast", duration: "20s", description: "极速高质量图像生成，兼顾效果与效率" },
  { id: "lib-image", name: "Lib Image", duration: "60s", description: "最新图片模型、长文本能力突出" },
  { id: "general-image-pro", name: "General image Pro", duration: "50s", description: "最强图片编辑模型，一致性好" },
  { id: "general-image-v2", name: "General image V2", duration: "25s", description: "支持联网搜索、文字准确、速度更快" },
  { id: "seedream-5-0-pro", name: "Seedream 5.0 Pro", duration: "20s", description: "精准交互式编辑，支持原生多语言排版" },
  { id: "qwen-image-3-0", name: "Qwen image 3.0", duration: "60s", description: "", badge: "上新" },
];

const modelIcons: Record<string, React.ReactNode> = {
  "lib-image-2-5-pro": <Flower2 size={14} />,
  "lib-image-2-5-fast": <Flower2 size={14} />,
  "lib-image": <Flower2 size={14} />,
  "general-image-pro": <Asterisk size={14} />,
  "general-image-v2": <Asterisk size={14} />,
  "seedream-5-0-pro": <BarChart2 size={14} />,
  "qwen-image-3-0": <RefreshCw size={14} />,
};

interface ImageModelMenuProps {
  selectedId: string;
  onSelect: (model: ImageModelOption) => void;
}

export function ImageModelMenu({ selectedId, onSelect }: ImageModelMenuProps) {
  return (
    <div
      data-image-model-menu
      className="absolute bottom-[calc(100%+8px)] left-0 z-30 w-[440px] rounded-2xl border border-white/10 bg-[#1c1c1c] p-1.5 shadow-[0_20px_60px_rgba(0,0,0,0.6)]"
    >
      {imageModels.map((model) => {
        const selected = model.id === selectedId;
        return (
          <button
            key={model.id}
            type="button"
            data-image-model-option={model.id}
            aria-pressed={selected}
            onClick={() => onSelect(model)}
            className={cn(
              "flex w-full items-center gap-2.5 rounded-xl px-2 py-2 text-left transition-colors",
              selected ? "bg-white/[0.08]" : "hover:bg-white/[0.05]",
            )}
          >
            <span className="flex size-7 shrink-0 items-center justify-center rounded-lg bg-white/[0.08] text-[#c8c8c8]">
              {modelIcons[model.id]}
            </span>
            <span className="min-w-0 flex-1">
              <span className="flex items-center gap-1.5">
                <span className="truncate text-sm text-[#ededed]">{model.name}</span>
                {model.badge && (
                  <span className="shrink-0 rounded bg-[#09caf5]/15 px-1 py-px text-[10px] leading-none text-[#09caf5]">
                    {model.badge}
                  </span>
                )}
              </span>
              {selected && model.description && (
                <span className="block truncate text-xs text-[#8c8c8c]">{model.description}</span>
              )}
            </span>
            <span className="shrink-0 rounded-md bg-white/[0.06] px-1.5 py-0.5 text-[11px] text-[#9a9a9a]">
              {model.duration}
            </span>
          </button>
        );
      })}
    </div>
  );
}
