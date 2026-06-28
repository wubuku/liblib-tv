"use client";

import { cn } from "@/lib/utils";
import { useCanvasStore } from "@/store/canvasStore";
import { useUIStore } from "@/store/uiStore";

interface MaterialItemProps {
  icon: React.ReactNode;
  title: string;
  subtitle: string;
  badge?: string;
  onClick?: () => void;
}

function MaterialItem({ icon, title, subtitle, badge, onClick }: MaterialItemProps) {
  return (
    <button
      onClick={onClick}
      className="flex items-center gap-3 w-full p-3 rounded-lg hover:bg-[#353639] transition-colors group"
    >
      <div className="w-10 h-10 rounded-lg bg-[#363636] flex items-center justify-center text-[#919191] group-hover:text-[#f7f7f7] transition-colors">
        {icon}
      </div>
      <div className="flex-1 text-left">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-[#f7f7f7]">{title}</span>
          {badge && (
            <span className="text-[10px] px-1.5 py-0.5 bg-[#f53f3f] text-white rounded">
              {badge}
            </span>
          )}
        </div>
        <span className="text-xs text-[#919191]">{subtitle}</span>
      </div>
    </button>
  );
}

export function MaterialLibraryPanel() {
  const { addNode } = useCanvasStore();
  const { toggleMaterialPanel } = useUIStore();

  const handleAddStyleNode = () => {
    addNode("style", {
      title: "风格节点",
      content: "自定义风格设置",
    });
    toggleMaterialPanel();
  };

  const handleAddEffectNode = () => {
    addNode("effect", {
      title: "特效节点",
      content: "自定义特效设置",
    });
    toggleMaterialPanel();
  };

  return (
    <div className="absolute left-14 top-0 w-72 bg-[#1f1f1f] border border-[#363636] rounded-xl shadow-xl z-50 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-[#363636]">
        <h3 className="text-sm font-semibold text-[#f7f7f7]">素材库</h3>
        <button
          onClick={toggleMaterialPanel}
          className="w-6 h-6 flex items-center justify-center rounded hover:bg-[#353639] transition-colors"
        >
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
            <path d="M2 2L10 10M10 2L2 10" stroke="#919191" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
        </button>
      </div>

      {/* Material Items */}
      <div className="p-2 space-y-1">
        <MaterialItem
          icon={
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <circle cx="10" cy="10" r="7" stroke="currentColor" strokeWidth="1.5" />
              <path d="M7 10L10 13L13 10M10 7V13" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          }
          title="风格库"
          subtitle="新增风格节点"
          badge="NEW"
          onClick={handleAddStyleNode}
        />

        <MaterialItem
          icon={
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M10 2L12 8H18L13 12L15 18L10 14L5 18L7 12L2 8H8L10 2Z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
            </svg>
          }
          title="特效库"
          subtitle="新增特效节点"
          badge="NEW"
          onClick={handleAddEffectNode}
        />
      </div>
    </div>
  );
}
