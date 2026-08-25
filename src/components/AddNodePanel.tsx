"use client";

import { useEffect, useRef } from "react";
import {
  Clapperboard,
  FileText,
  Film,
  FolderOpen,
  ImageIcon,
  Library,
  Mic2,
  ScanLine,
  Upload,
  Video,
} from "lucide-react";
import { useCanvasStore } from "@/store/canvasStore";
import { useUIStore } from "@/store/uiStore";

interface NodeEntry {
  type: string;
  label: string;
  icon: React.ComponentType<{ size?: number }>;
  badge?: string;
}

const nodeEntries: NodeEntry[] = [
  { type: "text", label: "文本", icon: FileText },
  { type: "image", label: "图片", icon: ImageIcon },
  { type: "video", label: "视频", icon: Video },
  { type: "video", label: "视频编辑", icon: Film, badge: "Beta" },
  { type: "script-execution", label: "导演台", icon: Clapperboard, badge: "NEW" },
  { type: "image", label: "逐帧拉片", icon: ScanLine, badge: "SD 2.5" },
  { type: "text", label: "音频", icon: Mic2 },
  { type: "script", label: "脚本", icon: FileText },
  { type: "image", label: "素材库", icon: Library },
];

export function AddNodePanel() {
  const { isAddNodePanelOpen, toggleAddNodePanel } = useUIStore();
  const addNode = useCanvasStore((state) => state.addNode);
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isAddNodePanelOpen) return;

    const handleClickOutside = (event: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(event.target as Node)) {
        toggleAddNodePanel();
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [isAddNodePanelOpen, toggleAddNodePanel]);

  if (!isAddNodePanelOpen) return null;

  const add = (type: string) => {
    addNode(type);
    toggleAddNodePanel();
  };

  return (
    <div
      ref={panelRef}
      className="fixed bottom-[69px] left-[calc(50%-242px)] z-[62] h-[481px] w-[196px] rounded-xl border border-[#363636] bg-[#262626] p-2 shadow-[0_18px_48px_rgba(0,0,0,0.5)] max-sm:bottom-[109px] max-sm:left-3"
    >
      <h3 className="px-2 pb-1.5 pt-1 text-xs font-medium text-[#9a9a9a]">添加节点</h3>
      <div className="space-y-1">
        {nodeEntries.map((entry, index) => {
          const Icon = entry.icon;
          return (
            <button
              key={`${entry.label}-${index}`}
              onClick={() => add(entry.type)}
              className="flex h-8 w-full items-center gap-2.5 rounded-lg px-2 text-left text-sm text-[#eeeeee] hover:bg-white/[0.07]"
            >
              <Icon size={15} />
              <span className="flex-1">{entry.label}</span>
              {entry.badge && (
                <span className="rounded bg-[#3b3b3b] px-1.5 py-0.5 text-[9px] text-[#bcbcbc]">
                  {entry.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      <div className="my-2 h-px bg-white/[0.08]" />
      <h3 className="px-2 pb-1.5 text-xs font-medium text-[#9a9a9a]">添加资源</h3>
      <button className="flex h-8 w-full items-center gap-2.5 rounded-lg px-2 text-sm text-[#eeeeee] hover:bg-white/[0.07]">
        <Upload size={15} />
        <span>上传</span>
      </button>
      <button className="flex h-8 w-full items-center gap-2.5 rounded-lg px-2 text-sm text-[#eeeeee] hover:bg-white/[0.07]">
        <FolderOpen size={15} />
        <span>从生成历史选择</span>
      </button>
    </div>
  );
}
