"use client";

import Image from "next/image";
import { useState } from "react";
import { ArrowDownUp, Check, CheckSquare, ChevronDown, Download, Eye, Heart, Images, X } from "lucide-react";
import { cn } from "@/lib/utils";

interface HistoryPanelProps {
  onClose: () => void;
}

// Batch 101: 2026-09-05 源站模态结构——生成历史标题、本画布 chip、
// 图片/视频/音频计数 tab、所有评级/时间倒序/批量操作；计数沿用 clone 本地 mock。
const tabs = [
  { id: "image", label: "图片", count: 3 },
  { id: "video", label: "视频", count: 0 },
  { id: "audio", label: "音频", count: 0 },
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
  const [ratingMenuOpen, setRatingMenuOpen] = useState(false);
  const [ratingFilter, setRatingFilter] = useState<"all" | "favorited">("all");

  const toggleFavorite = (id: string) => {
    setFavorites((current) => current.includes(id) ? current.filter((item) => item !== id) : [...current, id]);
  };

  const visibleItems = ratingFilter === "favorited"
    ? historyItems.filter((item) => favorites.includes(item.id))
    : historyItems;

  return (
    <div className="fixed inset-0 z-[90] flex items-center justify-center bg-black/60 backdrop-blur-[4px]" onMouseDown={onClose}>
      <section
        aria-label="生成历史"
        data-liblib-overlay="primary:history"
        className="pointer-events-auto flex h-[calc(100vh-160px)] min-h-[520px] max-h-[calc(100vh-24px)] w-[90vw] max-w-[1600px] flex-col overflow-hidden rounded-2xl border border-[#363636] bg-[#262626] shadow-[0_28px_90px_rgba(0,0,0,0.65)]"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <header className="flex h-[61px] shrink-0 items-center border-b border-white/[0.07] px-4">
          <h2 className="text-base font-medium text-[#f0f0f0]">生成历史</h2>
          <span className="flex-1" />
          <div data-history-size-control className="flex h-8 items-center gap-2 rounded-lg bg-[#1d1d1d] px-2 text-[#d9d9d9]">
            <Images size={14} className="shrink-0 text-[#9a9a9a]" aria-hidden />
            <input
              type="range"
              min={50}
              max={150}
              step={10}
              value={zoom}
              onChange={(event) => setZoom(Number(event.target.value))}
              aria-label="历史缩略图大小"
              className="h-1 w-28 cursor-pointer appearance-none rounded-full bg-white/15 accent-[#09caf5]"
            />
            <Images size={18} className="shrink-0 text-[#9a9a9a]" aria-hidden />
          </div>
          <button type="button" onClick={onClose} aria-label="关闭生成历史" className="ml-4 flex size-8 items-center justify-center rounded-lg text-[#898989] hover:bg-white/[0.06] hover:text-white">
            <X size={20} />
          </button>
        </header>

        <div className="flex h-[60px] shrink-0 items-center px-4 max-sm:h-[88px] max-sm:flex-col max-sm:items-stretch max-sm:justify-center max-sm:gap-1">
          <button
            type="button"
            data-history-scope-chip
            aria-pressed="true"
            className="flex h-8 shrink-0 items-center gap-1.5 rounded-full bg-[#3d3d3d] px-3 text-xs text-[#ededed]"
          >
            <Images size={12} aria-hidden />
            本画布
          </button>
          <div className="ml-5 flex items-center gap-5 max-sm:justify-between max-sm:gap-2">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                type="button"
                data-history-tab={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={cn(
                  "flex h-9 items-center gap-1 whitespace-nowrap text-sm",
                  activeTab === tab.id ? "text-[#ededed]" : "text-[#777] hover:text-[#bbb]",
                )}
              >
                {tab.label}
                <span className="rounded bg-white/[0.08] px-1 py-0.5 text-[10px] leading-none tabular-nums text-[#bdbdbd]">{tab.count}</span>
              </button>
            ))}
          </div>
          <span className="flex-1 max-sm:hidden" />
          <div className="relative flex items-center justify-end">
            <button
              type="button"
              data-history-rating
              aria-expanded={ratingMenuOpen}
              onClick={() => setRatingMenuOpen((value) => !value)}
              className="flex h-8 items-center gap-1 whitespace-nowrap rounded-lg px-2 text-sm text-[#9a9a9a] hover:bg-white/[0.05] hover:text-white max-sm:text-xs"
            >
              {ratingFilter === "favorited" ? "已收藏" : "所有评级"}
              <ChevronDown size={14} />
            </button>
            {ratingMenuOpen && (
              <div data-history-rating-menu className="absolute right-0 top-9 z-10 w-32 rounded-xl border border-white/[0.1] bg-[#2d2d2d] p-1 shadow-[0_16px_40px_rgba(0,0,0,0.55)]">
                <button
                  type="button"
                  data-history-rating-option="all"
                  onClick={() => {
                    setRatingFilter("all");
                    setRatingMenuOpen(false);
                  }}
                  className="flex h-8 w-full items-center justify-between rounded-lg px-2 text-left text-xs text-[#e8e8e8] hover:bg-white/[0.07]"
                >
                  所有评级
                  {ratingFilter === "all" && <Check size={13} className="text-[#09caf5]" />}
                </button>
                <button
                  type="button"
                  data-history-rating-option="favorited"
                  onClick={() => {
                    setRatingFilter("favorited");
                    setRatingMenuOpen(false);
                  }}
                  className="flex h-8 w-full items-center justify-between rounded-lg px-2 text-left text-xs text-[#e8e8e8] hover:bg-white/[0.07]"
                >
                  已收藏
                  {ratingFilter === "favorited" && <Check size={13} className="text-[#09caf5]" />}
                </button>
              </div>
            )}
            <button type="button" className="ml-2 flex h-8 items-center gap-1.5 whitespace-nowrap rounded-lg px-2 text-sm text-[#9a9a9a] hover:bg-white/[0.05] hover:text-white max-sm:text-xs">
              <ArrowDownUp size={15} />
              时间倒序
            </button>
            <button type="button" onClick={() => setBatchMode((value) => !value)} className={cn("ml-2 flex h-8 items-center gap-1.5 whitespace-nowrap rounded-lg px-2 text-sm hover:bg-white/[0.05] max-sm:text-xs", batchMode ? "text-white" : "text-[#9a9a9a]") }>
              <CheckSquare size={15} />
              批量操作
            </button>
          </div>
        </div>

        <div className="min-h-0 flex-1 overflow-auto px-5 pb-5 pt-1 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
          {activeTab === "image" ? (
            visibleItems.length > 0 ? (
              <>
                <h3 className="mb-3 text-sm text-[#d6d6d6]">2026-06-15</h3>
                <div className="flex flex-wrap gap-3">
                  {visibleItems.map((item) => {
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
              <div className="flex h-full items-center justify-center text-sm text-[#777]">暂无历史记录</div>
            )
          ) : (
            <div className="flex h-full items-center justify-center text-sm text-[#777]">暂无历史记录</div>
          )}
        </div>
      </section>
    </div>
  );
}
