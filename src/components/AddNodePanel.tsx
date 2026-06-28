"use client";

import { useRef, useEffect } from "react";
import { useCanvasStore } from "@/store/canvasStore";
import { useUIStore } from "@/store/uiStore";
import { cn } from "@/lib/utils";

interface NodeType {
  type: string;
  label: string;
  icon: React.ReactNode;
  badge?: string;
}

const nodeTypes: NodeType[] = [
  {
    type: "text",
    label: "文本",
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16m-7 6h7" />
      </svg>
    ),
  },
  {
    type: "image",
    label: "图片",
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
      </svg>
    ),
  },
  {
    type: "video",
    label: "视频",
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
      </svg>
    ),
  },
  {
    type: "composition",
    label: "视频合成",
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 4V2a1 1 0 011-1h8a1 1 0 011 1v2m-9 0h10m-10 0H5a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2V6a2 2 0 00-2-2h-2" />
      </svg>
    ),
    badge: "Beta",
  },
  {
    type: "director",
    label: "导演台",
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
      </svg>
    ),
    badge: "NEW",
  },
  {
    type: "audio",
    label: "音频",
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
      </svg>
    ),
  },
  {
    type: "script",
    label: "脚本",
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    ),
  },
  {
    type: "library",
    label: "素材库",
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
      </svg>
    ),
    badge: "NEW",
  },
];

export function AddNodePanel() {
  const { isAddNodePanelOpen, toggleAddNodePanel } = useUIStore();
  const { addNode } = useCanvasStore();
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        panelRef.current &&
        !panelRef.current.contains(event.target as Node)
      ) {
        toggleAddNodePanel();
      }
    }
    if (isAddNodePanelOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [isAddNodePanelOpen, toggleAddNodePanel]);

  const handleAddNode = (type: string) => {
    addNode(type);
    toggleAddNodePanel();
  };

  if (!isAddNodePanelOpen) return null;

  return (
    <div
      ref={panelRef}
      className="absolute left-14 top-0 w-64 bg-[#1f1f1f] border border-[#363636] rounded-lg shadow-xl z-50 overflow-hidden"
    >
      {/* 添加节点 Section */}
      <div className="p-3 border-b border-[#363636]">
        <h4 className="text-sm font-medium text-[#f7f7f7] mb-3">添加节点</h4>
        <div className="grid grid-cols-2 gap-2">
          {nodeTypes.map((nodeType) => (
            <button
              key={nodeType.type}
              onClick={() => handleAddNode(nodeType.type)}
              className="flex flex-col items-center gap-2 p-3 rounded-lg hover:bg-[#353639] transition-colors group relative"
            >
              <div className="text-[#919191] group-hover:text-[#f7f7f7] transition-colors">
                {nodeType.icon}
              </div>
              <span className="text-xs text-[#f7f7f7]">{nodeType.label}</span>
              {nodeType.badge && (
                <span className="absolute top-1 right-1 text-[10px] px-1 py-0.5 bg-[#f53f3f] text-white rounded">
                  {nodeType.badge}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* 添加资源 Section */}
      <div className="p-3">
        <h4 className="text-sm font-medium text-[#f7f7f7] mb-3">添加资源</h4>
        <div className="space-y-2">
          <button className="w-full flex items-center gap-3 p-2 rounded-lg hover:bg-[#353639] transition-colors">
            <svg
              className="w-5 h-5 text-[#919191]"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"
              />
            </svg>
            <span className="text-sm text-[#f7f7f7]">上传</span>
          </button>
          <button className="w-full flex items-center gap-3 p-2 rounded-lg hover:bg-[#353639] transition-colors">
            <svg
              className="w-5 h-5 text-[#919191]"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <span className="text-sm text-[#f7f7f7]">从生成历史选择</span>
          </button>
        </div>
      </div>
    </div>
  );
}
