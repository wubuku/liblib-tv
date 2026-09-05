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
  Search,
  Upload,
  Video,
} from "lucide-react";
import { useUIStore } from "@/store/uiStore";

interface NodeEntry {
  type: string;
  label: string;
  icon: React.ComponentType<{ size?: number }>;
  badge?: string;
  action?: "create" | "material" | "script";
  arrow?: boolean;
}

const nodeEntries: NodeEntry[] = [
  { type: "text", label: "文本", icon: FileText },
  { type: "image", label: "图片", icon: ImageIcon },
  { type: "video", label: "视频", icon: Video },
  { type: "video-clip", label: "智能剪辑", icon: Film, badge: "Beta" },
  { type: "script-execution", label: "导演台", icon: Clapperboard, badge: "NEW" },
  { type: "shot-breakdown", label: "逐帧拉片", icon: ScanLine, badge: "SD 2.5" },
  { type: "audio", label: "音频", icon: Mic2 },
  { type: "script", label: "脚本", icon: FileText, action: "script", arrow: true },
  { type: "material", label: "素材库", icon: Library, action: "material", arrow: true },
];

interface AddNodePanelProps {
  onAddNode: (type: string, data?: Record<string, unknown>) => void;
}

export function AddNodePanel({ onAddNode }: AddNodePanelProps) {
  const { isAddNodePanelOpen, toggleAddNodePanel, setPrimaryPanel } = useUIStore();
  const panelRef = useRef<HTMLDivElement>(null);
  const [materialSubmenuOpen, setMaterialSubmenuOpen] = useState(false);
  const [scriptSubmenuOpen, setScriptSubmenuOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [status, setStatus] = useState("");
  const closePanel = useCallback(() => {
    setMaterialSubmenuOpen(false);
    setScriptSubmenuOpen(false);
    setSearchOpen(false);
    setSearchQuery("");
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
    onAddNode(type);
    closePanel();
  };

  const openMaterialLibrary = () => {
    setPrimaryPanel("material");
  };

  const normalizedQuery = searchQuery.trim().toLowerCase();
  const visibleEntries = normalizedQuery
    ? nodeEntries.filter((entry) => entry.label.toLowerCase().includes(normalizedQuery))
    : nodeEntries;

  return (
    <div
      ref={panelRef}
      data-liblib-overlay="add-node"
      className="fixed bottom-[69px] left-[calc(50%-242px)] z-[62] h-[481px] w-[196px] rounded-xl border border-[#363636] bg-[#262626] p-2 shadow-[0_18px_48px_rgba(0,0,0,0.5)] max-sm:bottom-[109px] max-sm:left-3"
    >
      <div className="flex items-center justify-between px-2 pb-1.5 pt-1">
        <h3 className="text-xs font-medium text-[#9a9a9a]">添加节点</h3>
        <button
          type="button"
          data-add-node-search-toggle
          aria-label="搜索画布节点"
          title="搜索画布节点"
          onClick={() => {
            setSearchOpen((value) => !value);
            setSearchQuery("");
          }}
          className="flex size-6 items-center justify-center rounded-md text-[#9a9a9a] hover:bg-white/[0.07] hover:text-white"
        >
          <Search size={13} />
        </button>
      </div>
      {searchOpen && (
        <div className="px-1 pb-1.5">
          <input
            data-add-node-search
            value={searchQuery}
            onChange={(event) => setSearchQuery(event.target.value)}
            placeholder="搜索画布节点"
            aria-label="搜索画布节点"
            className="h-7 w-full rounded-lg border border-white/[0.1] bg-[#1f1f1f] px-2 text-xs text-[#eeeeee] outline-none placeholder:text-[#666] focus:border-white/25"
          />
        </div>
      )}
      <div className="space-y-1">
        {visibleEntries.map((entry) => {
          const Icon = entry.icon;
          return (
            <button
              key={entry.type}
              type="button"
              data-add-node-entry={entry.type}
              onClick={() => {
                if (entry.action === "material") {
                  setScriptSubmenuOpen(false);
                  setMaterialSubmenuOpen((value) => !value);
                  return;
                }
                if (entry.action === "script") {
                  setMaterialSubmenuOpen(false);
                  setScriptSubmenuOpen((value) => !value);
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
        {visibleEntries.length === 0 && (
          <p data-add-node-empty className="px-2 py-1.5 text-[11px] text-[#888]">
            无匹配节点
          </p>
        )}
      </div>

      {scriptSubmenuOpen && (
        <div
          data-add-node-submenu="script"
          className="absolute left-[calc(100%+8px)] top-[252px] w-44 rounded-xl border border-[#363636] bg-[#262626] p-1.5 shadow-[0_18px_48px_rgba(0,0,0,0.5)] max-sm:left-3 max-sm:top-[calc(100%+8px)]"
        >
          <p className="px-2 py-1.5 text-[11px] text-[#888]">脚本</p>
          <button
            type="button"
            data-add-node-entry="script-new"
            onClick={() => createNode("script-generator")}
            className="flex h-9 w-full items-center justify-between rounded-lg px-2 text-left text-xs text-[#e8e8e8] hover:bg-white/[0.07]"
          >
            脚本
            <span className="rounded bg-[#3b3b3b] px-1.5 py-0.5 text-[9px] text-[#bcbcbc]">NEW</span>
          </button>
          <button
            type="button"
            data-add-node-entry="script-legacy"
            onClick={() => createNode("script")}
            className="flex h-9 w-full items-center justify-between rounded-lg px-2 text-left text-xs text-[#e8e8e8] hover:bg-white/[0.07]"
          >
            脚本（旧版）
            <span className="rounded bg-[#3b3b3b] px-1.5 py-0.5 text-[9px] text-[#bcbcbc]">Beta</span>
          </button>
        </div>
      )}

      {materialSubmenuOpen && (
        <div
          data-add-node-submenu="material"
          className="absolute left-[calc(100%+8px)] top-[288px] w-44 rounded-xl border border-[#363636] bg-[#262626] p-1.5 shadow-[0_18px_48px_rgba(0,0,0,0.5)] max-sm:left-3 max-sm:top-[calc(100%+8px)]"
        >
          <p className="px-2 py-1.5 text-[11px] text-[#888]">素材库</p>
          <button type="button" data-add-node-entry="material-style" onClick={openMaterialLibrary} className="flex h-9 w-full items-center rounded-lg px-2 text-left text-xs text-[#e8e8e8] hover:bg-white/[0.07]">
            风格库
          </button>
          <button type="button" data-add-node-entry="material-effect" onClick={openMaterialLibrary} className="flex h-9 w-full items-center rounded-lg px-2 text-left text-xs text-[#e8e8e8] hover:bg-white/[0.07]">
            特效库
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
