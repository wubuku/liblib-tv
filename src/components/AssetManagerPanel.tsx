"use client";

import Image from "next/image";
import { Clapperboard, FileText, ImageIcon, Layers3, Play, X } from "lucide-react";
import { useCanvasStore } from "@/store/canvasStore";
import { useUIStore } from "@/store/uiStore";
import { cn } from "@/lib/utils";

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
  const nodes = getActiveCanvas()?.nodes ?? [];

  return (
    <aside data-liblib-overlay="asset" className="relative z-50 flex h-screen w-60 shrink-0 flex-col border-r border-white/[0.07] bg-[#171717] pt-14 text-[#e7e7e7]">
      <div className="flex h-10 items-center border-b border-white/[0.07] px-3">
        <button className="h-7 flex-1 rounded-md bg-white/[0.08] text-xs text-white">画布</button>
        <button className="h-7 flex-1 rounded-md text-xs text-[#777] hover:text-[#bbb]">资产</button>
        <button onClick={toggleAssetPanel} className="ml-2 flex h-7 w-7 items-center justify-center rounded-md text-[#777] hover:bg-white/[0.07] hover:text-white" aria-label="关闭资产管理">
          <X size={14} />
        </button>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto px-2 py-2">
        <div className="mb-2 flex items-center gap-2 px-2 text-xs text-[#777]">
          <Layers3 size={13} />
          <span>画布 2</span>
        </div>
        <div className="space-y-1">
          {nodes.map((node) => {
            const data = node.data as Record<string, unknown>;
            const imageUrl = typeof data.imageUrl === "string" ? data.imageUrl : null;
            return (
              <button
                key={node.id}
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
      </div>

      <div className="h-10 border-t border-white/[0.07] px-4 text-xs leading-10 text-[#777]">共 {nodes.length} 节点</div>
    </aside>
  );
}
