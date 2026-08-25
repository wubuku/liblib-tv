"use client";

import Image from "next/image";
import { Clapperboard, FileText, ImageIcon, Layers3, Play, X } from "lucide-react";
import { useState } from "react";
import { useCanvasStore } from "@/store/canvasStore";
import { useUIStore } from "@/store/uiStore";
import { cn } from "@/lib/utils";

type AssetManagerTab = "canvas" | "assets";

function nodeLabel(type: string | undefined, data: Record<string, unknown>) {
  if (typeof data.filename === "string") return data.filename;
  if (typeof data.title === "string") return data.title;
  if (type === "script-execution") return "第一集：咖啡馆对峙";
  return "未命名节点";
}

function NodeTypeIcon({ type }: { type: string | undefined }) {
  if (type === "image") return <ImageIcon size={14} />;
  if (type === "video") return <Play size={14} />;
  if (type === "storyboard-group") return <Layers3 size={14} />;
  if (type === "script-execution") return <Clapperboard size={14} />;
  return <FileText size={14} />;
}

export function AssetManagerPanel() {
  const { getActiveCanvas, selectedNodeId, selectNode } = useCanvasStore();
  const toggleAssetPanel = useUIStore((state) => state.toggleAssetPanel);
  const [activeTab, setActiveTab] = useState<AssetManagerTab>("canvas");
  const nodes = getActiveCanvas()?.nodes ?? [];
  const assetNodes = nodes.filter((node) => node.type === "image" || node.type === "video");
  const visibleNodes = activeTab === "assets" ? assetNodes : nodes;

  return (
    <aside data-liblib-overlay="asset" className="relative z-50 flex h-screen w-60 shrink-0 flex-col border-r border-white/[0.07] bg-[#171717] pt-14 text-[#e7e7e7]">
      <div className="flex h-10 items-center border-b border-white/[0.07] px-3">
        <button
          type="button"
          data-asset-manager-tab="canvas"
          aria-pressed={activeTab === "canvas"}
          onClick={() => setActiveTab("canvas")}
          className={cn(
            "h-7 flex-1 rounded-md text-xs transition-colors",
            activeTab === "canvas" ? "bg-white/[0.08] text-white" : "text-[#777] hover:text-[#bbb]",
          )}
        >
          画布
        </button>
        <button
          type="button"
          data-asset-manager-tab="assets"
          aria-pressed={activeTab === "assets"}
          onClick={() => setActiveTab("assets")}
          className={cn(
            "h-7 flex-1 rounded-md text-xs transition-colors",
            activeTab === "assets" ? "bg-white/[0.08] text-white" : "text-[#777] hover:text-[#bbb]",
          )}
        >
          资产
        </button>
        <button onClick={toggleAssetPanel} className="ml-2 flex h-7 w-7 items-center justify-center rounded-md text-[#777] hover:bg-white/[0.07] hover:text-white" aria-label="关闭资产管理">
          <X size={14} />
        </button>
      </div>

      <div data-asset-manager-list={activeTab} className="min-h-0 flex-1 overflow-y-auto px-2 py-2">
        <div className="mb-2 flex items-center gap-2 px-2 text-xs text-[#777]">
          <Layers3 size={13} />
          <span>{activeTab === "assets" ? "当前画布资产" : "画布 2"}</span>
        </div>
        {activeTab === "assets" && (
          <p className="mb-2 px-2 text-[11px] leading-4 text-[#666]">图片和视频节点的本地引用视图</p>
        )}
        {visibleNodes.length > 0 ? (
          <div className="space-y-1">
            {visibleNodes.map((node) => {
            const data = node.data as Record<string, unknown>;
            const imageUrl = typeof data.imageUrl === "string" ? data.imageUrl : null;
            return (
              <button
                key={node.id}
                type="button"
                data-asset-manager-item={node.id}
                onClick={() => selectNode(node.id)}
                className={cn(
                  "flex h-10 w-full items-center gap-2 rounded-lg px-2 text-left hover:bg-white/[0.06]",
                  selectedNodeId === node.id && "bg-white/[0.09]",
                )}
              >
                {imageUrl ? (
                  <Image src={imageUrl} alt="" width={28} height={28} className="h-7 w-7 rounded object-cover" unoptimized />
                ) : (
                  <span className="flex h-7 w-7 items-center justify-center rounded bg-[#292929] text-[#929292]">
                    <NodeTypeIcon type={node.type} />
                  </span>
                )}
                <span className="min-w-0 flex-1 truncate text-xs text-[#cfcfcf]">{nodeLabel(node.type, data)}</span>
              </button>
            );
            })}
          </div>
        ) : (
          <div className="px-2 py-8 text-center text-xs text-[#666]">当前画布暂无媒体资产</div>
        )}
      </div>

      <div className="h-10 border-t border-white/[0.07] px-4 text-xs leading-10 text-[#777]">
        {activeTab === "assets" ? `共 ${assetNodes.length} 项资产` : `共 ${nodes.length} 节点`}
      </div>
    </aside>
  );
}
