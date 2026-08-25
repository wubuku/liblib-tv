"use client";

import Image from "next/image";
import { useState } from "react";
import { Check, ChevronDown, Info, X } from "lucide-react";
import { cn } from "@/lib/utils";

interface ToolboxPanelProps {
  onClose: () => void;
}

const presetTitles = [
  "【预设】左弧滑行",
  "【预设】电商手机弹出效果",
  "【预设】咖啡杯出场",
  "【预设】360旋转展示",
  "【预设】机械臂视角",
  "【预设】Live 2D",
  "【预设】瞳孔拉近",
  "【预设】飞鸟解体",
  "【预设】破盒而出",
  "【预设】商品震撼登场",
  "【预设】右弧滑行",
  "【预设】左弧滑行",
  "【预设】颠倒空间",
  "【预设】反重力漂浮",
  "【预设】粒子融解",
  "【预设】旅拍转场 zoom in",
  "【预设】旅拍转场 zoom out",
  "【预设】旅拍转场 向右旋转",
  "【预设】旅拍转场 向左旋转",
  "【预设】旅拍转场 生长",
  "【预设】英雄视角",
  "【预设】AI模特服饰动态展示",
  "【预设】机械臂视角",
  "【预设】大师分镜九宫格-经典暗调",
  "【预设】AI室内装修效果预览",
] as const;

const presets = presetTitles.map((title, index) => ({
  id: `preset-${index + 1}`,
  title,
  imageUrl: `/images/liblib-panels/toolbox-${String(index + 1).padStart(2, "0")}.webp`,
}));

export function ToolboxPanel({ onClose }: ToolboxPanelProps) {
  const [usedPresetId, setUsedPresetId] = useState<string | null>(null);

  return (
    <section
      aria-label="我的工具箱"
      data-liblib-overlay="primary:toolbox"
      className="fixed bottom-[73px] left-[calc(50%-64px)] z-[62] flex h-[460px] w-[480px] max-w-[calc(100vw-24px)] -translate-x-1/2 flex-col overflow-hidden rounded-xl border border-[#363636] bg-[#262626] pb-3 shadow-[0_18px_48px_rgba(0,0,0,0.5)] max-sm:bottom-[109px] max-sm:left-1/2 max-sm:max-h-[calc(100vh-130px)]"
    >
      <header className="flex h-[52px] shrink-0 items-center gap-2 px-4">
        <h2 className="text-[15px] font-medium text-[#f1f1f1]">我的工具箱</h2>
        <button type="button" title="工具箱模板说明" aria-label="工具箱模板说明" className="flex size-6 items-center justify-center text-[#777] hover:text-[#ddd]">
          <Info size={15} />
        </button>
        <button type="button" className="flex h-8 items-center gap-1 rounded-lg px-1.5 text-sm text-[#9b9b9b] hover:bg-white/[0.06] hover:text-[#ddd]">
          周星驰经典名场面
          <ChevronDown size={14} />
        </button>
        <span className="flex-1" />
        <button type="button" onClick={onClose} aria-label="关闭工具箱" className="flex size-8 items-center justify-center rounded-lg text-[#858585] hover:bg-white/[0.06] hover:text-white">
          <X size={19} />
        </button>
      </header>

      <div className="min-h-0 flex-1 overflow-y-auto px-4 pb-2 pt-4 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
        <div className="grid grid-cols-3 gap-x-3 gap-y-3">
          {presets.map((preset) => {
            const isUsed = usedPresetId === preset.id;
            return (
              <article key={preset.id} className="group min-w-0">
                <div className="relative aspect-square w-full overflow-hidden rounded-lg bg-[#1f1f1f]">
                  <Image src={preset.imageUrl} alt={preset.title} fill sizes="141px" className="object-cover" unoptimized />
                  <div className={cn("absolute inset-0 flex items-center justify-center bg-black/55 transition-opacity", isUsed ? "opacity-100" : "opacity-0 group-hover:opacity-100")}>
                    <button
                      type="button"
                      onClick={() => setUsedPresetId(preset.id)}
                      className="flex h-8 items-center gap-1.5 rounded-lg bg-white px-3 text-xs font-medium text-[#222] hover:bg-[#ededed]"
                    >
                      {isUsed && <Check size={14} />}
                      {isUsed ? "已使用" : "使用"}
                    </button>
                  </div>
                </div>
                <p className="mt-1.5 line-clamp-2 min-h-8 text-xs leading-4 text-[#d6d6d6]">{preset.title}</p>
              </article>
            );
          })}
        </div>
      </div>
    </section>
  );
}
