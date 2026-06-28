"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";

// --- Types ---

interface HistoryItem {
  id: string;
  thumbnailColor: string;
  isFavorite: boolean;
}

interface HistoryPanelProps {
  onClose: () => void;
}

// --- Mock Data ---

const mockItems: HistoryItem[] = [
  { id: "1", thumbnailColor: "#3a5f8a", isFavorite: false },
  { id: "2", thumbnailColor: "#8a3a5f", isFavorite: true },
  { id: "3", thumbnailColor: "#5f8a3a", isFavorite: false },
];

// --- Sub-components ---

function ZoomControls() {
  return (
    <div className="flex items-center gap-1 text-xs text-[#919191]">
      <span className="px-1">100%</span>
      <button className="w-5 h-5 flex items-center justify-center rounded hover:bg-[#353639] transition-colors text-[#919191] hover:text-[#f7f7f7]">
        <svg width="10" height="2" viewBox="0 0 10 2" fill="none">
          <path d="M1 1H9" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
      </button>
      <button className="w-5 h-5 flex items-center justify-center rounded hover:bg-[#353639] transition-colors text-[#919191] hover:text-[#f7f7f7]">
        <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
          <path d="M5 1V9M1 5H9" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
      </button>
    </div>
  );
}

function TabButtons() {
  const tabs = [
    { label: "图片历史", count: 3, active: true },
    { label: "视频历史", count: 0, active: false },
    { label: "音频历史", count: 0, active: false },
  ];

  return (
    <div className="flex gap-1 px-3 py-2">
      {tabs.map((tab) => (
        <button
          key={tab.label}
          className={cn(
            "flex items-center gap-1 px-2.5 py-1 rounded-md text-xs transition-colors",
            tab.active
              ? "bg-[#353639] text-[#f7f7f7]"
              : "text-[#919191] hover:text-[#f7f7f7] hover:bg-[#2a2a2a]"
          )}
        >
          <span>{tab.label}</span>
          <span className={cn(tab.active ? "text-[#f7f7f7]" : "text-[#666]")}>
            ({tab.count})
          </span>
        </button>
      ))}
    </div>
  );
}

function SortAndBatchControls() {
  return (
    <div className="flex items-center justify-between px-3 py-2">
      <button className="flex items-center gap-1.5 px-2 py-1 rounded-md text-xs text-[#919191] hover:text-[#f7f7f7] hover:bg-[#353639] transition-colors">
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
          <path d="M3 5L7 9L11 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        <span>时间降序</span>
      </button>
      <button className="flex items-center gap-1.5 px-2 py-1 rounded-md text-xs text-[#919191] hover:text-[#f7f7f7] hover:bg-[#353639] transition-colors">
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
          <rect x="2" y="2" width="4" height="4" rx="0.5" stroke="currentColor" strokeWidth="1.2" />
          <rect x="8" y="2" width="4" height="4" rx="0.5" stroke="currentColor" strokeWidth="1.2" />
          <rect x="2" y="8" width="4" height="4" rx="0.5" stroke="currentColor" strokeWidth="1.2" />
          <rect x="8" y="8" width="4" height="4" rx="0.5" stroke="currentColor" strokeWidth="1.2" />
        </svg>
        <span>批量操作</span>
      </button>
    </div>
  );
}

function HistoryItemCard({ item }: { item: HistoryItem }) {
  const [hovered, setHovered] = useState(false);
  const [favorite, setFavorite] = useState(item.isFavorite);

  return (
    <div
      className="relative group"
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      {/* Thumbnail */}
      <div
        className="w-full aspect-square rounded-lg overflow-hidden"
        style={{ backgroundColor: item.thumbnailColor }}
      />

      {/* Hover overlay */}
      <div
        className={cn(
          "absolute inset-0 rounded-lg flex flex-col justify-between p-2 transition-opacity",
          hovered ? "opacity-100" : "opacity-0"
        )}
        style={{ backgroundColor: "rgba(0, 0, 0, 0.5)" }}
      >
        {/* Top row: favorite button */}
        <div className="flex justify-end">
          <button
            onClick={() => setFavorite(!favorite)}
            className="w-6 h-6 flex items-center justify-center rounded hover:bg-white/10 transition-colors"
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill={favorite ? "#f5a623" : "none"}>
              <path
                d="M7 1.5L8.5 5H12.5L9.5 7.5L10.5 11.5L7 9L3.5 11.5L4.5 7.5L1.5 5H5.5L7 1.5Z"
                stroke={favorite ? "#f5a623" : "#f7f7f7"}
                strokeWidth="1.2"
                strokeLinejoin="round"
              />
            </svg>
          </button>
        </div>

        {/* Bottom row: action buttons */}
        <div className="flex items-center justify-center gap-2">
          <button className="px-2 py-1 rounded bg-white/20 text-[10px] text-[#f7f7f7] hover:bg-white/30 transition-colors">
            查看
          </button>
          <button className="px-2 py-1 rounded bg-white/20 text-[10px] text-[#f7f7f7] hover:bg-white/30 transition-colors">
            使用
          </button>
          <button className="px-2 py-1 rounded bg-white/20 text-[10px] text-[#f7f7f7] hover:bg-white/30 transition-colors">
            下载
          </button>
        </div>
      </div>
    </div>
  );
}

// --- Main Component ---

export function HistoryPanel({ onClose }: HistoryPanelProps) {
  return (
    <div className="w-80 h-full bg-[#1f1f1f] border-l border-[#363636] flex flex-col overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-3 border-b border-[#363636]">
        <h3 className="text-sm font-semibold text-[#f7f7f7]">历史资产</h3>
        <div className="flex items-center gap-2">
          <ZoomControls />
          <button
            onClick={onClose}
            className="w-6 h-6 flex items-center justify-center rounded hover:bg-[#353639] transition-colors"
          >
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
              <path d="M2 2L10 10M10 2L2 10" stroke="#919191" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
          </button>
        </div>
      </div>

      {/* Tabs */}
      <TabButtons />

      {/* Sort / Batch */}
      <SortAndBatchControls />

      {/* Scrollable list */}
      <div className="flex-1 overflow-y-auto px-3 pb-3">
        {/* Date group */}
        <div className="mb-3">
          <div className="text-xs text-[#666] mb-2">2026-06-15</div>
          <div className="grid grid-cols-2 gap-2">
            {mockItems.map((item) => (
              <HistoryItemCard key={item.id} item={item} />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
