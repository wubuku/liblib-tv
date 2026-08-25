"use client";

import Image from "next/image";
import { useState } from "react";
import { Check, Film, Images, Music2, Play } from "lucide-react";
import { cn } from "@/lib/utils";

type BreakdownDimension = "storyboard" | "motion" | "music";

interface ShotBreakdownResultsPanelProps {
  zoom: number;
  activeDimensions: BreakdownDimension[];
}

const storyboardResults = [
  { id: "S01", title: "中景 · 固定｜出门微笑 · 引出人物", image: "/images/scene-coffee-1.png" },
  { id: "S02", title: "中近景 · 平稳｜吧台接咖啡 · 建立场景", image: "/images/scene-coffee-3.png" },
  { id: "S03", title: "近景 · 固定｜窗边举杯 · 人物性格建立", image: "/images/scene-coffee-4.png" },
  { id: "S04", title: "中景 · 侧面｜展示探店过程", image: "/images/storyboard-2.png" },
];

const motionResults = [
  { id: "M01", title: "6s · 中景跟拍｜走向咖啡馆", image: "/images/scene-coffee-3.png" },
  { id: "M02", title: "6s · 固定中景｜吧台互动", image: "/images/scene-coffee-1.png" },
  { id: "M03", title: "4s · 固定中近景｜日落沙滩", image: "/images/scene-coffee-4.png" },
];

export function ShotBreakdownResultsPanel({ zoom, activeDimensions }: ShotBreakdownResultsPanelProps) {
  const available = (["storyboard", "motion", "music"] as BreakdownDimension[]).filter((item) => activeDimensions.includes(item));
  const [activeTab, setActiveTab] = useState<BreakdownDimension>(available[0] ?? "storyboard");
  const [selectedItems, setSelectedItems] = useState<string[]>([]);
  const tabs = [
    { id: "storyboard" as const, label: "分镜", icon: Images },
    { id: "motion" as const, label: "动态", icon: Film },
    { id: "music" as const, label: "音乐", icon: Music2 },
  ].filter((tab) => available.includes(tab.id));

  const toggle = (id: string) => setSelectedItems((items) => items.includes(id) ? items.filter((item) => item !== id) : [...items, id]);

  return (
    <div
      className="nodrag nowheel nopan absolute -bottom-4 left-1/2 z-30 w-[660px] -translate-x-1/2 translate-y-full origin-top"
      // The original result/editor surfaces stay screen-sized inside the zoomed node layer.
      style={{ transform: `scale(${1 / zoom})` }}
    >
      <section className="flex h-[260px] flex-col overflow-hidden rounded-2xl border border-[#3a3a3a] bg-[#242424] shadow-[0_22px_60px_rgba(0,0,0,0.52)]">
        <header className="flex h-12 shrink-0 items-center border-b border-white/[0.07] px-3">
          <div className="flex items-center gap-1 rounded-lg bg-black/20 p-1">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button key={tab.id} type="button" onClick={() => setActiveTab(tab.id)} className={cn("flex h-7 items-center gap-1.5 rounded-md px-3 text-xs", activeTab === tab.id ? "bg-white/[0.1] text-white" : "text-[#8b8b8b] hover:text-white")}>
                  <Icon size={13} /> {tab.label}
                </button>
              );
            })}
          </div>
          <span className="ml-auto text-xs text-[#777]">分析完成 · 本地示例结果</span>
        </header>

        <div className="min-h-0 flex-1 overflow-y-auto p-3">
          {activeTab === "storyboard" && (
            <div className="grid grid-cols-2 gap-3">
              {storyboardResults.map((result) => (
                <ResultCard key={result.id} {...result} selected={selectedItems.includes(result.id)} onToggle={() => toggle(result.id)} />
              ))}
            </div>
          )}
          {activeTab === "motion" && (
            <div className="grid grid-cols-2 gap-3">
              {motionResults.map((result) => (
                <ResultCard key={result.id} {...result} selected={selectedItems.includes(result.id)} onToggle={() => toggle(result.id)} video />
              ))}
            </div>
          )}
          {activeTab === "music" && (
            <div className="rounded-xl border border-white/[0.08] bg-[#1c1c1c] p-4">
              <div className="mb-4 flex items-center gap-2 text-sm text-[#d7d7d7]"><Music2 size={15} /> BGM · 14.6s · 轻快节奏</div>
              <div className="flex h-20 items-center gap-1 rounded-lg border border-white/[0.08] bg-[#202020] px-3">
                <button type="button" aria-label="播放 BGM" className="mr-2 flex size-8 items-center justify-center rounded-full bg-white text-[#222]"><Play size={14} fill="currentColor" /></button>
                {Array.from({ length: 46 }, (_, index) => <span key={index} className="w-1 rounded-full bg-[#737373]" style={{ height: `${12 + ((index * 17) % 42)}px` }} />)}
              </div>
            </div>
          )}
        </div>

        <footer className="flex h-12 shrink-0 items-center border-t border-white/[0.07] px-3 text-xs text-[#8c8c8c]">
          <span>已选择 {selectedItems.length} 项，可继续作为 Seedance 参考</span>
          <button type="button" disabled={selectedItems.length === 0} className="ml-auto h-8 rounded-lg bg-white px-4 text-[#202020] disabled:bg-white/[0.08] disabled:text-[#555]">加入参考</button>
        </footer>
      </section>
    </div>
  );
}

function ResultCard({ id, title, image, selected, onToggle, video = false }: { id: string; title: string; image: string; selected: boolean; onToggle: () => void; video?: boolean }) {
  return (
    <button type="button" onClick={onToggle} className={cn("overflow-hidden rounded-lg border bg-[#1d1d1d] text-left", selected ? "border-[#09caf5]" : "border-white/[0.08]")}>
      <div className="relative aspect-video">
        <Image src={image} alt={title} fill sizes="300px" className="object-cover" unoptimized />
        {video && <span className="absolute inset-0 flex items-center justify-center"><span className="flex size-8 items-center justify-center rounded-full bg-black/55 text-white"><Play size={14} fill="currentColor" /></span></span>}
        {selected && <span className="absolute right-2 top-2 flex size-5 items-center justify-center rounded-full bg-[#09caf5] text-[#142126]"><Check size={12} /></span>}
      </div>
      <div className="truncate px-2 py-2 text-xs text-[#c9c9c9]"><span className="mr-1 text-[#8a8a8a]">{id}</span>{title}</div>
    </button>
  );
}
