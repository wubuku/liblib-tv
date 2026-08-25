"use client";

import Image from "next/image";
import { useState } from "react";
import { ArrowDownUp, CheckSquare, Download, Eye, Heart, Minus, Plus, X } from "lucide-react";
import { cn } from "@/lib/utils";

interface HistoryPanelProps {
  onClose: () => void;
}

const tabs = [
  { id: "image", label: "图片历史", count: 3 },
  { id: "video", label: "视频历史", count: 0 },
  { id: "audio", label: "音频历史", count: 0 },
] as const;

const historyItems = [
  { id: "history-1", imageUrl: "/images/liblib-panels/history-01.webp", badge: "AI生成" },
  { id: "history-2", imageUrl: "/images/liblib-panels/history-02.webp", badge: "AI生成" },
  { id: "history-3", imageUrl: "/images/liblib-panels/history-03.webp", badge: null },
] as const;

export function HistoryPanel({ onClose }: HistoryPanelProps) {
  const [activeTab, setActiveTab] = useState<(typeof tabs)[number]["id"]>("image");
  const [zoom, setZoom] = useState(100);
  const [batchMode, setBatchMode] = useState(false);
  const [favorites, setFavorites] = useState<string[]>([]);

  const toggleFavorite = (id: string) => {
    setFavorites((current) => current.includes(id) ? current.filter((item) => item !== id) : [...current, id]);
  };

  return (
    <div className="fixed inset-0 z-[90] flex items-center justify-center bg-black/60 backdrop-blur-[4px]" onMouseDown={onClose}>
      <section
        aria-label="历史资产"
        className="pointer-events-auto flex h-[calc(100vh-160px)] min-h-[520px] max-h-[calc(100vh-24px)] w-[90vw] max-w-[1600px] flex-col overflow-hidden rounded-2xl border border-[#363636] bg-[#262626] shadow-[0_28px_90px_rgba(0,0,0,0.65)]"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <header className="flex h-[61px] shrink-0 items-center border-b border-white/[0.07] px-4">
          <h2 className="text-base font-medium text-[#f0f0f0]">历史资产</h2>
          <span className="flex-1" />
          <div className="flex h-8 items-center rounded-lg bg-[#1d1d1d] text-sm text-[#d9d9d9]">
            <button type="button" onClick={() => setZoom((value) => Math.max(50, value - 10))} aria-label="缩小历史缩略图" className="flex size-8 items-center justify-center rounded-lg hover:bg-white/[0.06]">
              <Minus size={14} />
            </button>
            <span className="w-12 text-center text-xs tabular-nums">{zoom}%</span>
            <button type="button" onClick={() => setZoom((value) => Math.min(150, value + 10))} aria-label="放大历史缩略图" className="flex size-8 items-center justify-center rounded-lg hover:bg-white/[0.06]">
              <Plus size={14} />
            </button>
          </div>
          <button type="button" onClick={onClose} aria-label="关闭历史资产" className="ml-4 flex size-8 items-center justify-center rounded-lg text-[#898989] hover:bg-white/[0.06] hover:text-white">
            <X size={20} />
          </button>
        </header>

        <div className="flex h-[60px] shrink-0 items-center px-4 max-sm:h-[88px] max-sm:flex-col max-sm:items-stretch max-sm:justify-center max-sm:gap-1">
          <div className="flex items-center gap-6 max-sm:justify-between max-sm:gap-2">
            {tabs.map((tab) => (
              <button key={tab.id} type="button" onClick={() => setActiveTab(tab.id)} className={cn("h-9 whitespace-nowrap border-b text-sm max-sm:h-7 max-sm:text-xs", activeTab === tab.id ? "border-[#e8e8e8] text-[#ededed]" : "border-transparent text-[#777] hover:text-[#bbb]") }>
                {tab.label}({tab.count})
              </button>
            ))}
          </div>
          <span className="flex-1 max-sm:hidden" />
          <div className="flex items-center justify-end">
            <button type="button" className="flex h-8 items-center gap-1.5 whitespace-nowrap rounded-lg px-2 text-sm text-[#9a9a9a] hover:bg-white/[0.05] hover:text-white max-sm:text-xs">
              <ArrowDownUp size={15} />
              时间降序
            </button>
            <button type="button" onClick={() => setBatchMode((value) => !value)} className={cn("ml-3 flex h-8 items-center gap-1.5 whitespace-nowrap rounded-lg px-2 text-sm hover:bg-white/[0.05] max-sm:text-xs", batchMode ? "text-white" : "text-[#9a9a9a]") }>
              <CheckSquare size={15} />
              批量操作
            </button>
          </div>
        </div>

        <div className="min-h-0 flex-1 overflow-auto px-5 pb-5 pt-1 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
          {activeTab === "image" ? (
            <>
              <h3 className="mb-3 text-sm text-[#d6d6d6]">2026-06-15</h3>
              <div className="flex flex-wrap gap-3">
                {historyItems.map((item) => {
                  const isFavorite = favorites.includes(item.id);
                  return (
                    <article
                      key={item.id}
                      className="group relative overflow-hidden rounded-lg bg-[#363636]"
                      // History zoom is a local thumbnail control, independent of the canvas viewport.
                      style={{ width: 144 * zoom / 100, height: 144 * zoom / 100 }}
                    >
                      <Image src={item.imageUrl} alt="" fill sizes="216px" className="object-cover" unoptimized />
                      <Image src="/images/watermark.png" alt="" width={35} height={17} className="absolute left-1.5 top-1.5 h-[17px] w-[35px] object-contain" unoptimized />
                      {item.badge && <span className="absolute left-1.5 top-1.5 rounded bg-black/50 px-1 py-0.5 text-[9px] text-[#cfcfcf]">{item.badge}</span>}
                      {batchMode && <span className="absolute right-2 top-2 size-4 rounded border border-white/60 bg-black/30" />}
                      <div className="absolute inset-0 flex flex-col justify-between bg-black/55 p-2 opacity-0 transition-opacity group-hover:opacity-100">
                        <button type="button" onClick={() => toggleFavorite(item.id)} aria-label="收藏" className="ml-auto flex size-7 items-center justify-center rounded-lg bg-black/30 text-white hover:bg-black/50">
                          <Heart size={15} fill={isFavorite ? "currentColor" : "none"} />
                        </button>
                        <div className="flex justify-center gap-1.5">
                          <button type="button" title="查看" aria-label="查看" className="flex size-7 items-center justify-center rounded-lg bg-white/20 text-white hover:bg-white/30"><Eye size={14} /></button>
                          <button type="button" className="rounded-lg bg-white/20 px-2 text-[10px] text-white hover:bg-white/30">使用</button>
                          <button type="button" title="下载" aria-label="下载" className="flex size-7 items-center justify-center rounded-lg bg-white/20 text-white hover:bg-white/30"><Download size={14} /></button>
                        </div>
                      </div>
                    </article>
                  );
                })}
              </div>
              <p className="mt-12 text-center text-xs text-[#777]">没有更多了</p>
            </>
          ) : (
            <div className="flex h-full items-center justify-center text-sm text-[#777]">暂无{activeTab === "video" ? "视频" : "音频"}历史</div>
          )}
        </div>
      </section>
    </div>
  );
}
