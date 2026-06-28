"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";

interface ToolboxPanelProps {
  onClose: () => void;
}

interface PresetItem {
  id: string;
  title: string;
  category: string;
  previewColor: string;
}

const presets: PresetItem[] = [
  { id: "1", title: "【预设】左弧滑行", category: "周星驰经典名场面", previewColor: "#3a3a5c" },
  { id: "2", title: "【预设】电商手机弹出效果", category: "周星驰经典名场面", previewColor: "#4a3a3a" },
  { id: "3", title: "【预设】咖啡杯出场", category: "周星驰经典名场面", previewColor: "#3a4a3a" },
  { id: "4", title: "【预设】360旋转展示", category: "周星驰经典名场面", previewColor: "#5c4a3a" },
  { id: "5", title: "【预设】机械臂视角", category: "周星驰经典名场面", previewColor: "#3a4a5c" },
  { id: "6", title: "【预设】Live 2D", category: "周星驰经典名场面", previewColor: "#5c3a4a" },
  { id: "7", title: "【预设】瞳孔拉近", category: "周星驰经典名场面", previewColor: "#4a5c3a" },
  { id: "8", title: "【预设】飞鸟解体", category: "周星驰经典名场面", previewColor: "#3a3a4a" },
  { id: "9", title: "【预设】破盒而出", category: "周星驰经典名场面", previewColor: "#5c5c3a" },
  { id: "10", title: "【预设】商品震撼登场", category: "周星驰经典名场面", previewColor: "#3a5c5c" },
  { id: "11", title: "【预设】旋转渐显", category: "周星驰经典名场面", previewColor: "#4a3a5c" },
  { id: "12", title: "【预设】快速缩放", category: "周星驰经典名场面", previewColor: "#5c3a3a" },
];

const categories = ["周星驰经典名场面", "电商特效", "产品展示", "创意动画"];

function PresetCard({ preset, onUse }: { preset: PresetItem; onUse: (id: string) => void }) {
  return (
    <div className="relative group rounded-lg overflow-hidden">
      {/* Preview Image Placeholder */}
      <div
        className="w-full aspect-video bg-[#2a2a2a] flex items-center justify-center"
        style={{ backgroundColor: preset.previewColor }}
      >
        <svg
          className="w-8 h-8 text-[#666666]"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
          />
        </svg>
      </div>

      {/* Hover Overlay with Use Button */}
      <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
        <button
          onClick={() => onUse(preset.id)}
          className="px-4 py-1.5 bg-[#09caf5] text-white text-xs font-medium rounded-md hover:bg-[#5ddcff] transition-colors"
        >
          使用
        </button>
      </div>

      {/* Title */}
      <div className="px-2 py-2">
        <p className="text-xs text-[#f7f7f7] truncate">{preset.title}</p>
      </div>
    </div>
  );
}

export function ToolboxPanel({ onClose }: ToolboxPanelProps) {
  const [selectedCategory, setSelectedCategory] = useState(categories[0]);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  const filteredPresets = presets.filter((p) => p.category === selectedCategory);

  const handleUsePreset = (id: string) => {
    console.log("Use preset:", id);
    // TODO: Implement preset application logic
  };

  return (
    <div className="absolute left-14 top-0 w-[300px] h-full bg-[#1f1f1f] border-r border-[#363636] z-50 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-[#363636] shrink-0">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-semibold text-[#f7f7f7]">我的工具箱</h3>
          <button className="w-5 h-5 flex items-center justify-center rounded hover:bg-[#353639] transition-colors">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <circle cx="7" cy="7" r="5.5" stroke="#919191" strokeWidth="1" />
              <path d="M7 5V8M7 9.5V10" stroke="#919191" strokeWidth="1" strokeLinecap="round" />
            </svg>
          </button>
          <span className="text-[11px] text-[#919191]">工具箱模板说明</span>
        </div>
        <button
          onClick={onClose}
          className="w-6 h-6 flex items-center justify-center rounded hover:bg-[#353639] transition-colors"
        >
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
            <path d="M2 2L10 10M10 2L2 10" stroke="#919191" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
        </button>
      </div>

      {/* Category Selector */}
      <div className="px-4 py-3 border-b border-[#363636] shrink-0 relative">
        <button
          onClick={() => setIsDropdownOpen(!isDropdownOpen)}
          className="w-full flex items-center justify-between px-3 py-2 bg-[#363636] rounded-lg text-sm text-[#f7f7f7] hover:bg-[#404040] transition-colors"
        >
          <span>{selectedCategory}</span>
          <svg
            width="12"
            height="12"
            viewBox="0 0 12 12"
            fill="none"
            className={cn("transition-transform", isDropdownOpen && "rotate-180")}
          >
            <path d="M3 4.5L6 7.5L9 4.5" stroke="#919191" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>

        {/* Dropdown Menu */}
        {isDropdownOpen && (
          <div className="absolute left-4 right-4 top-full mt-1 bg-[#363636] rounded-lg border border-[#525252] shadow-xl z-10 overflow-hidden">
            {categories.map((category) => (
              <button
                key={category}
                onClick={() => {
                  setSelectedCategory(category);
                  setIsDropdownOpen(false);
                }}
                className={cn(
                  "w-full px-3 py-2 text-sm text-left transition-colors",
                  category === selectedCategory
                    ? "bg-[#09caf5]/10 text-[#09caf5]"
                    : "text-[#f7f7f7] hover:bg-[#404040]"
                )}
              >
                {category}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Presets Grid */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="grid grid-cols-1 gap-3">
          {filteredPresets.map((preset) => (
            <PresetCard key={preset.id} preset={preset} onUse={handleUsePreset} />
          ))}
        </div>
        {filteredPresets.length === 0 && (
          <div className="flex flex-col items-center justify-center h-32 text-[#919191]">
            <svg
              className="w-10 h-10 mb-2"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"
              />
            </svg>
            <span className="text-sm">暂无预设</span>
          </div>
        )}
      </div>
    </div>
  );
}
