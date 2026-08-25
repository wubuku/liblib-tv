"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  ArrowRight,
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
  action?: "create" | "material";
  arrow?: boolean;
}

const nodeEntries: NodeEntry[] = [
  { type: "text", label: "文本", icon: FileText },
  { type: "image", label: "图片", icon: ImageIcon },
  { type: "video", label: "视频", icon: Video },
  { type: "video-clip", label: "视频编辑", icon: Film, badge: "Beta" },
  { type: "script-execution", label: "导演台", icon: Clapperboard, badge: "NEW" },
  { type: "shot-breakdown", label: "逐帧拉片", icon: ScanLine, badge: "SD 2.5" },
  { type: "audio", label: "音频", icon: Mic2 },
  { type: "script", label: "脚本", icon: FileText, arrow: true },
  { type: "material", label: "素材库", icon: Library, action: "material", arrow: true },
];

export function AddNodePanel() {
  const { isAddNodePanelOpen, toggleAddNodePanel, setPrimaryPanel } = useUIStore();
  const addNode = useCanvasStore((state) => state.addNode);
  const panelRef = useRef<HTMLDivElement>(null);
  const [materialSubmenuOpen, setMaterialSubmenuOpen] = useState(false);
  const [status, setStatus] = useState("");
  const closePanel = useCallback(() => {
    setMaterialSubmenuOpen(false);
    setStatus("");
    toggleAddNodePanel();
  }, [toggleAddNodePanel]);

  useEffect(() => {
    if (!isAddNodePanelOpen) return;

    const handleClickOutside = (event: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(event.target as Node)) {
        closePanel();
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [closePanel, isAddNodePanelOpen]);

  if (!isAddNodePanelOpen) return null;

  const createNode = (type: string) => {
    addNode(type);
    closePanel();
  };

  const openMaterialLibrary = () => {
    setPrimaryPanel("material");
  };

  return (
    <div
      ref={panelRef}
      data-liblib-overlay="add-node"
      className="fixed bottom-[69px] left-[calc(50%-242px)] z-[62] h-[481px] w-[196px] rounded-xl border border-[#363636] bg-[#262626] p-2 shadow-[0_18px_48px_rgba(0,0,0,0.5)] max-sm:bottom-[109px] max-sm:left-3"
    >
      <h3 className="px-2 pb-1.5 pt-1 text-xs font-medium text-[#9a9a9a]">添加节点</h3>
      <div className="space-y-1">
        {nodeEntries.map((entry) => {
          const Icon = entry.icon;
          return (
            <button
              key={entry.type}
              type="button"
              data-add-node-entry={entry.type}
              onClick={() => {
                if (entry.action === "material") {
                  setMaterialSubmenuOpen((value) => !value);
                  return;
                }
                createNode(entry.type);
              }}
              className="flex h-8 w-full items-center gap-2.5 rounded-lg px-2 text-left text-sm text-[#eeeeee] hover:bg-white/[0.07]"
            >
              <Icon size={15} />
              <span className="flex-1">{entry.label}</span>
              {entry.badge && (
                <span className="rounded bg-[#3b3b3b] px-1.5 py-0.5 text-[9px] text-[#bcbcbc]">
                  {entry.badge}
                </span>
              )}
              {entry.arrow && <ArrowRight data-add-node-arrow size={13} className="text-[#777]" />}
            </button>
          );
        })}
      </div>

      {materialSubmenuOpen && (
        <div
          data-add-node-submenu="material"
          className="absolute left-[calc(100%+8px)] top-[278px] w-44 rounded-xl border border-[#363636] bg-[#262626] p-1.5 shadow-[0_18px_48px_rgba(0,0,0,0.5)] max-sm:left-3 max-sm:top-[calc(100%+8px)]"
        >
          <p className="px-2 py-1.5 text-[11px] text-[#888]">素材库</p>
          <button type="button" data-add-node-entry="material-mine" onClick={openMaterialLibrary} className="flex h-9 w-full items-center rounded-lg px-2 text-left text-xs text-[#e8e8e8] hover:bg-white/[0.07]">
            我的素材库
          </button>
          <button type="button" data-add-node-entry="material-preset" onClick={openMaterialLibrary} className="flex h-9 w-full items-center rounded-lg px-2 text-left text-xs text-[#e8e8e8] hover:bg-white/[0.07]">
            预设素材库
          </button>
        </div>
      )}

      <div className="my-2 h-px bg-white/[0.08]" />
      <h3 className="px-2 pb-1.5 text-xs font-medium text-[#9a9a9a]">添加资源</h3>
      <button type="button" data-add-node-resource="upload" onClick={() => setStatus("本地原型：上传服务未连接")} className="flex h-8 w-full items-center gap-2.5 rounded-lg px-2 text-sm text-[#eeeeee] hover:bg-white/[0.07]">
        <Upload size={15} />
        <span>上传</span>
      </button>
      <button type="button" data-add-node-resource="history" onClick={() => setStatus("本地原型：生成历史未连接")} className="flex h-8 w-full items-center gap-2.5 rounded-lg px-2 text-sm text-[#eeeeee] hover:bg-white/[0.07]">
        <FolderOpen size={15} />
        <span>从生成历史选择</span>
      </button>
      {status && <p data-add-node-status className="mt-2 px-2 text-[10px] leading-4 text-[#75d7e8]">{status}</p>}
    </div>
  );
}
