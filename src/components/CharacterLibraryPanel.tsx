"use client";

import Image from "next/image";
import { useMemo, useRef, useState } from "react";
import { ChevronDown, ChevronLeft, ChevronRight, Plus, X } from "lucide-react";
import { cn } from "@/lib/utils";

interface CharacterLibraryPanelProps {
  onAddNode: (type: string, data?: Record<string, unknown>) => void;
  onClose: () => void;
}

const characterNames = [
  "甜妹/清新少女",
  "霸总/精英大佬",
  "温柔熟男/理想男友",
  "清冷千金/白切黑女主",
  "古风男主",
  "古风女主",
  "恶毒女配/白莲花",
  "正派长辈/父",
  "正派长辈/母",
  "反派长辈/势利亲戚",
  "反派长辈/势利亲戚",
  "生活方式普通人",
  "生活方式普通人",
  "时尚感亚洲男生",
  "时尚感亚洲女生",
  "时尚感欧美男生",
  "时尚感欧美女生",
  "小男孩",
  "小女孩",
  "时尚感亚洲女生",
  "时尚感亚洲女生",
  "时尚感亚洲男生",
  "时尚感欧美女生",
] as const;

const characters = characterNames.map((name, index) => ({
  id: `character-${index + 1}`,
  name,
  imageUrl: `/images/liblib-panels/character-thumb-${String(index + 1).padStart(2, "0")}.webp`,
}));

const detailLabels = ["角色立绘", "脸部近景", "表情参考", "三视图"] as const;

// Batch 111: 2026-09-05 补采样确认的两个角色标签；其余角色为启发式近似（SOURCE_UNKNOWN）。
const sampledTags: Record<string, string[]> = {
  "甜妹/清新少女": ["女主", "女", "现代", "青年", "温柔"],
  "温柔熟男/理想男友": ["男主", "男", "现代", "青年", "温柔"],
};

function tagsFor(name: string) {
  if (sampledTags[name]) return sampledTags[name];
  const lead = name.includes("女主") ? "女主" : name.includes("男主") ? "男主" : "角色";
  const gender = name.includes("女") || name.includes("母") || name.includes("千金") ? "女" : name.includes("男") || name.includes("父") ? "男" : "不限";
  const era = name.includes("古风") ? "古风" : "现代";
  return [lead, gender, era, name.includes("男孩") || name.includes("女孩") ? "儿童" : "青年"];
}

export function CharacterLibraryPanel({
  onAddNode,
  onClose,
}: CharacterLibraryPanelProps) {
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [recentOnly, setRecentOnly] = useState(false);
  const carouselRef = useRef<HTMLDivElement>(null);
  const selected = characters[selectedIndex];
  const tags = useMemo(() => tagsFor(selected.name), [selected.name]);

  const scroll = (direction: -1 | 1) => {
    carouselRef.current?.scrollBy({ left: direction * 357, behavior: "smooth" });
  };

  const applyCharacter = () => {
    onAddNode("image", {
      filename: selected.name,
      width: 568,
      height: 761,
      imageUrl: selected.imageUrl,
      watermarkUrl: "/images/watermark.png",
    });
    onClose();
  };

  return (
    <div className="fixed inset-0 z-[90] flex items-center justify-center bg-black/60 p-3 backdrop-blur-[3px]" onMouseDown={onClose}>
      <section
        aria-label="角色库"
        data-liblib-overlay="primary:character"
        className="flex h-[min(731px,calc(100vh-169px))] max-h-[calc(100vh-24px)] w-[min(1304px,calc(100vw-136px))] flex-col overflow-hidden rounded-2xl border border-white/[0.08] bg-[#222] text-[#ededed] shadow-[0_28px_80px_rgba(0,0,0,0.6)]"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <header className="flex h-14 shrink-0 items-center justify-between px-4">
          <h2 className="text-base font-semibold">角色库</h2>
          <button type="button" onClick={onClose} aria-label="close" className="flex size-8 items-center justify-center rounded-lg text-[#a4a4a4] hover:bg-white/[0.07] hover:text-white">
            <X size={20} />
          </button>
        </header>

        <div className="min-h-0 flex-1 overflow-y-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
          <section className="relative mx-[33px] h-[462px] min-h-[462px] rounded-xl bg-[#2a2a2a]">
            <div className="absolute left-4 top-[18px] flex items-center gap-2">
              <h3 className="text-sm font-medium">{selected.name}</h3>
              <div className="flex items-center rounded-lg bg-white/[0.06] px-2 py-1 text-[11px] text-[#b5b5b5]">
                {tags.map((tag) => <span key={tag} className="mr-1 last:mr-0">{tag}</span>)}
              </div>
            </div>

            <div className="absolute left-4 right-4 top-[57px] grid h-[301px] grid-cols-[repeat(3,minmax(0,1fr))_minmax(0,2.37fr)] gap-2 max-md:grid-cols-2 max-md:overflow-y-auto">
              {detailLabels.map((label, index) => (
                <div key={label} className="relative min-w-0 overflow-hidden rounded-lg bg-white">
                  <Image
                    src={selectedIndex === 0 ? `/images/liblib-panels/character-detail-${index + 1}.webp` : selected.imageUrl}
                    alt={label}
                    fill
                    sizes={index === 3 ? "310px" : "131px"}
                    className="object-cover object-top"
                    unoptimized
                  />
                </div>
              ))}
            </div>

            <p className="absolute bottom-[19px] left-4 right-[140px] truncate text-xs text-[#858585]">
              {selected.name}，详见角色全身图、面部特写、表情九宫格与人物呈现板。
            </p>
            <button type="button" onClick={applyCharacter} className="absolute bottom-[20px] right-4 flex h-8 w-[109px] items-center justify-center gap-1 rounded-lg bg-white text-sm text-[#242424] hover:bg-[#ededed]">
              <Plus size={16} />
              应用至画布
            </button>
          </section>

          <section className="relative mt-4 border-t border-white/[0.08] px-4 pt-3">
            <div className="flex h-9 items-center justify-between">
              <button type="button" className="flex h-7 items-center gap-1 rounded-lg bg-white/[0.06] px-2 text-xs text-[#d8d8d8] hover:bg-white/10">
                角色筛选
                <ChevronDown size={13} />
              </button>
              <label className="flex items-center gap-2 text-xs text-[#c4c4c4]">
                <input type="checkbox" checked={recentOnly} onChange={(event) => setRecentOnly(event.target.checked)} className="size-4 appearance-none rounded border border-[#555] bg-transparent checked:border-[#09caf5] checked:bg-[#09caf5]" />
                最近使用
              </label>
            </div>

            <div className="relative mt-0.5 h-[178px]">
              <button type="button" onClick={() => scroll(-1)} aria-label="上一组" className="absolute left-0 top-[63px] z-10 flex size-7 items-center justify-center rounded-lg border border-white/10 bg-[#262626] text-[#999] hover:text-white">
                <ChevronLeft size={16} />
              </button>
              <div ref={carouselRef} className="mx-[42px] flex h-full gap-[19px] overflow-x-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
                {characters.map((character, index) => (
                  <button key={character.id} type="button" onClick={() => setSelectedIndex(index)} className={cn("w-[100px] shrink-0 text-left", (index === 3 || index === 4) && "ml-[6px]")}>
                    <div className={cn("relative h-[134px] w-[100px] overflow-hidden rounded-lg bg-white", selectedIndex === index && "ring-2 ring-[#09caf5]") }>
                      <Image src={character.imageUrl} alt={character.name} fill sizes="100px" className="object-cover object-top" unoptimized />
                      {selectedIndex === index && <span className="absolute inset-x-0 bottom-0 bg-black/70 px-1.5 py-1 text-[10px] text-white">{character.name}</span>}
                    </div>
                    <span className="mt-1 block truncate text-xs text-[#777]">{character.name}</span>
                  </button>
                ))}
              </div>
              <button type="button" onClick={() => scroll(1)} aria-label="下一组" className="absolute right-0 top-[63px] z-10 flex size-7 items-center justify-center rounded-lg border border-white/10 bg-[#262626] text-[#999] hover:text-white">
                <ChevronRight size={16} />
              </button>
            </div>
          </section>
        </div>
      </section>
    </div>
  );
}
