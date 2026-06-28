"use client";

import { useState, useRef, useCallback } from "react";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Data
// ---------------------------------------------------------------------------

interface Character {
  id: string;
  name: string;
  tags: string[];
  description: string;
  avatarColor: string;
}

const CHARACTERS: Character[] = [
  {
    id: "sweet-girl",
    name: "甜妹/清新少女",
    tags: ["女主", "女", "现代", "青年", "温柔"],
    description:
      "清新甜美的少女形象，适合现代都市、校园恋爱等场景，性格温柔善良，给人如沐春风的感觉。",
    avatarColor: "#f472b6",
  },
  {
    id: "ceo",
    name: "霸总/精英大佬",
    tags: ["男主", "男", "现代", "青年", "强势"],
    description:
      "商界精英形象，气场强大，适合职场、豪门等题材，外表冷酷内心深情。",
    avatarColor: "#60a5fa",
  },
  {
    id: "gentle-man",
    name: "温柔熟男/理想男友",
    tags: ["男主", "男", "现代", "青年", "温柔"],
    description:
      "温柔体贴的理想男友形象，成熟稳重又不失浪漫，适合都市情感类作品。",
    avatarColor: "#34d399",
  },
  {
    id: "cold-heiress",
    name: "清冷千金/白切黑女主",
    tags: ["女主", "女", "现代", "青年", "高冷"],
    description:
      "外表清冷高贵，内心腹黑的千金大小姐形象，适合豪门、复仇等题材。",
    avatarColor: "#a78bfa",
  },
  {
    id: "ancient-male",
    name: "古风男主",
    tags: ["男主", "男", "古风", "青年", "英俊"],
    description:
      "古代美男子形象，适合仙侠、武侠、宫廷等古风题材，气质飘逸出尘。",
    avatarColor: "#fbbf24",
  },
  {
    id: "ancient-female",
    name: "古风女主",
    tags: ["女主", "女", "古风", "青年", "温婉"],
    description:
      "古典美人形象，温婉大方，适合仙侠、宫廷、武侠等古风题材。",
    avatarColor: "#f9a8d4",
  },
  {
    id: "villainess",
    name: "恶毒女配/白莲花",
    tags: ["女配", "女", "现代", "青年", "心机"],
    description:
      "表面柔弱实则心机深沉的反派女性角色，适合都市、豪门等题材的配角。",
    avatarColor: "#fb923c",
  },
  {
    id: "father",
    name: "正派长辈/父",
    tags: ["配角", "男", "现代", "中年", "慈祥"],
    description:
      "慈祥正直的父亲形象，适合家庭、都市等题材中的长辈角色。",
    avatarColor: "#818cf8",
  },
  {
    id: "mother",
    name: "正派长辈/母",
    tags: ["配角", "女", "现代", "中年", "温柔"],
    description:
      "温柔贤惠的母亲形象，适合家庭、都市等题材中的长辈角色。",
    avatarColor: "#e879f9",
  },
  {
    id: "relative",
    name: "反派长辈/势利亲戚",
    tags: ["配角", "女", "现代", "中年", "势利"],
    description:
      "势利刻薄的亲戚形象，适合家庭矛盾、都市等题材中的反派配角。",
    avatarColor: "#f87171",
  },
  {
    id: "ordinary",
    name: "生活方式普通人",
    tags: ["配角", "不限", "现代", "青年", "普通"],
    description:
      "普通生活化的角色形象，适合日常、都市等写实题材。",
    avatarColor: "#9ca3af",
  },
  {
    id: "fashion-asian-m",
    name: "时尚感亚洲男生",
    tags: ["男主", "男", "现代", "青年", "时尚"],
    description:
      "时尚潮流的亚洲男生形象，适合都市、偶像等题材。",
    avatarColor: "#38bdf8",
  },
  {
    id: "fashion-asian-f",
    name: "时尚感亚洲女生",
    tags: ["女主", "女", "现代", "青年", "时尚"],
    description:
      "时尚潮流的亚洲女生形象，适合都市、偶像等题材。",
    avatarColor: "#f472b6",
  },
  {
    id: "fashion-western-m",
    name: "时尚感欧美男生",
    tags: ["男主", "男", "现代", "青年", "时尚"],
    description:
      "时尚帅气的欧美男生形象，适合国际化都市题材。",
    avatarColor: "#22d3ee",
  },
  {
    id: "fashion-western-f",
    name: "时尚感欧美女生",
    tags: ["女主", "女", "现代", "青年", "时尚"],
    description:
      "时尚靓丽的欧美女生形象，适合国际化都市题材。",
    avatarColor: "#fb7185",
  },
  {
    id: "boy",
    name: "小男孩",
    tags: ["配角", "男", "现代", "儿童", "活泼"],
    description:
      "活泼可爱的小男孩形象，适合家庭、亲子等题材。",
    avatarColor: "#facc15",
  },
  {
    id: "girl",
    name: "小女孩",
    tags: ["配角", "女", "现代", "儿童", "可爱"],
    description:
      "天真可爱的小女孩形象，适合家庭、亲子等题材。",
    avatarColor: "#f9a8d4",
  },
];

const THUMB_LABELS = ["角色立绘", "脸部近景", "表情参考", "三视图"] as const;

// ---------------------------------------------------------------------------
// Icons
// ---------------------------------------------------------------------------

function IconX({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={cn("size-4", className)}
    >
      <path d="M18 6 6 18" />
      <path d="m6 6 12 12" />
    </svg>
  );
}

function IconChevronLeft({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={cn("size-4", className)}
    >
      <path d="m15 18-6-6 6-6" />
    </svg>
  );
}

function IconChevronRight({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={cn("size-4", className)}
    >
      <path d="m9 18 6-6-6-6" />
    </svg>
  );
}

function IconChevronDown({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={cn("size-4", className)}
    >
      <path d="m6 9 6 6 6-6" />
    </svg>
  );
}

function IconDownload({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={cn("size-4", className)}
    >
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="7 10 12 15 17 10" />
      <line x1="12" x2="12" y1="15" y2="3" />
    </svg>
  );
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function ThumbnailPlaceholder({ label, color }: { label: string; color: string }) {
  return (
    <div className="flex flex-col items-center gap-1">
      <div
        className="size-14 rounded-md flex items-center justify-center text-[10px] text-white/70"
        style={{ backgroundColor: color }}
      >
        {label.charAt(0)}
      </div>
      <span className="text-[10px] text-[#919191] leading-tight">{label}</span>
    </div>
  );
}

function CharacterCard({
  character,
  isActive,
  onClick,
}: {
  character: Character;
  isActive: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "flex shrink-0 flex-col items-center gap-1.5 rounded-lg p-2 transition-colors",
        isActive
          ? "bg-[#353639] ring-1 ring-[#09caf5]"
          : "hover:bg-[#262626]"
      )}
    >
      <div
        className="size-12 rounded-full flex items-center justify-center text-xs font-medium text-white"
        style={{ backgroundColor: character.avatarColor }}
      >
        {character.name.charAt(0)}
      </div>
      <span className="w-16 truncate text-center text-[11px] text-[#f7f7f7] leading-tight">
        {character.name.split("/")[0]}
      </span>
    </button>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

interface CharacterLibraryPanelProps {
  onClose: () => void;
}

export function CharacterLibraryPanel({ onClose }: CharacterLibraryPanelProps) {
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [recentOnly, setRecentOnly] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  const selected = CHARACTERS[selectedIndex];

  const scrollBy = useCallback((direction: "left" | "right") => {
    if (!scrollRef.current) return;
    const amount = direction === "left" ? -200 : 200;
    scrollRef.current.scrollBy({ left: amount, behavior: "smooth" });
  }, []);

  return (
    <div className="flex h-full w-80 flex-col bg-[#1f1f1f] text-[#f7f7f7]">
      {/* ---- Header ---- */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-[#363636]">
        <h2 className="text-sm font-medium">角色库</h2>
        <button
          type="button"
          onClick={onClose}
          className="flex size-6 items-center justify-center rounded text-[#919191] transition-colors hover:bg-[#353639] hover:text-[#f7f7f7]"
          aria-label="关闭角色库"
        >
          <IconX />
        </button>
      </div>

      {/* ---- Scrollable content ---- */}
      <div className="flex-1 overflow-y-auto">
        {/* ---- Character detail ---- */}
        <div className="px-4 py-3 space-y-3 border-b border-[#363636]">
          {/* Name & tags */}
          <div>
            <h3 className="text-sm font-medium leading-snug">
              {selected.name}
            </h3>
            <div className="mt-1 flex flex-wrap gap-1">
              {selected.tags.map((tag) => (
                <span
                  key={tag}
                  className="inline-block rounded bg-[#363636] px-1.5 py-0.5 text-[10px] text-[#919191]"
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>

          {/* Thumbnails */}
          <div className="flex items-start justify-between">
            {THUMB_LABELS.map((label) => (
              <ThumbnailPlaceholder
                key={label}
                label={label}
                color={selected.avatarColor}
              />
            ))}
          </div>

          {/* Description */}
          <p className="text-xs leading-relaxed text-[#919191]">
            {selected.description}
          </p>

          {/* Apply button */}
          <button
            type="button"
            className="flex w-full items-center justify-center gap-1.5 rounded-md bg-[#09caf5] px-3 py-2 text-xs font-medium text-white transition-colors hover:bg-[#08b8e0]"
          >
            <IconDownload className="size-3.5" />
            应用至画布
          </button>
        </div>

        {/* ---- Filters ---- */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-[#363636]">
          <button
            type="button"
            className="flex items-center gap-1 rounded-md border border-[#525252] bg-[#1f1f1f] px-2.5 py-1.5 text-xs text-[#f7f7f7] transition-colors hover:border-[#09caf5]"
          >
            角色筛选
            <IconChevronDown className="size-3" />
          </button>

          <label className="flex cursor-pointer items-center gap-1.5 text-xs text-[#919191]">
            <input
              type="checkbox"
              checked={recentOnly}
              onChange={(e) => setRecentOnly(e.target.checked)}
              className="size-3.5 rounded border-[#525252] bg-[#1f1f1f] accent-[#09caf5]"
            />
            最近使用
          </label>
        </div>

        {/* ---- Carousel ---- */}
        <div className="relative px-4 py-3">
          {/* Prev button */}
          <button
            type="button"
            onClick={() => scrollBy("left")}
            className="absolute left-1 top-1/2 z-10 flex size-6 -translate-y-1/2 items-center justify-center rounded-full bg-[#363636]/80 text-[#f7f7f7] transition-colors hover:bg-[#525252]"
            aria-label="上一组"
          >
            <IconChevronLeft className="size-3.5" />
          </button>

          {/* Scrollable cards */}
          <div
            ref={scrollRef}
            className="flex gap-1 overflow-x-auto scrollbar-none px-6"
            style={{ scrollbarWidth: "none" }}
          >
            {CHARACTERS.map((char, idx) => (
              <CharacterCard
                key={char.id}
                character={char}
                isActive={idx === selectedIndex}
                onClick={() => setSelectedIndex(idx)}
              />
            ))}
          </div>

          {/* Next button */}
          <button
            type="button"
            onClick={() => scrollBy("right")}
            className="absolute right-1 top-1/2 z-10 flex size-6 -translate-y-1/2 items-center justify-center rounded-full bg-[#363636]/80 text-[#f7f7f7] transition-colors hover:bg-[#525252]"
            aria-label="下一组"
          >
            <IconChevronRight className="size-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
}
