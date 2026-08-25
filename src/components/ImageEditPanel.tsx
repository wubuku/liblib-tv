"use client";

import Image from "next/image";
import { useMemo, useState } from "react";
import {
  ArrowUp,
  AtSign,
  Box,
  Check,
  ChevronDown,
  Expand,
  Images,
  Languages,
  Link2,
  SlidersHorizontal,
  Undo2,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";

type ImageEditorVariant = "empty" | "prompt" | "referenced" | "tool";

interface ImageEditPanelProps {
  zoom: number;
  variant: ImageEditorVariant;
  initialPrompt?: string;
  initialReferences?: string[];
  generationSettings?: string;
}

const autoLinkCandidates = [
  { id: "character", name: "陈默", image: "/images/scene-coffee-1.png", token: "@陈默（图片 1）" },
  { id: "prop", name: "咖啡", image: "/images/scene-coffee-2.png", token: "@咖啡（图片 2）" },
];

export function ImageEditPanel({
  zoom,
  variant,
  initialPrompt = "",
  initialReferences = [],
  generationSettings = "16:9 · 低画质 · 1K · 1张",
}: ImageEditPanelProps) {
  const [prompt, setPrompt] = useState(initialPrompt);
  const [references, setReferences] = useState(initialReferences);
  const [showAutoLink, setShowAutoLink] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const panelHeight = variant === "empty" ? 191 : variant === "prompt" ? 211 : 274;
  const canSuggest = prompt.trim().length > 0 && references.length === 0;
  const referenceItems = useMemo(
    () => references.map((image, index) => ({ image, name: index === 0 ? "陈默" : index === 1 ? "咖啡" : `参考 ${index + 1}` })),
    [references],
  );

  const acceptAutoLink = () => {
    const newReferences = autoLinkCandidates.map((candidate) => candidate.image);
    const tokenPrefix = autoLinkCandidates.map((candidate) => candidate.token).join("、");
    setReferences(newReferences);
    setPrompt((value) => `${tokenPrefix}。${value}`);
    setShowAutoLink(false);
  };

  return (
    <div
      data-image-edit-panel
      className="nodrag nowheel nopan absolute -bottom-[17px] left-1/2 z-20 w-[660px] -translate-x-1/2 translate-y-full origin-top"
      // The bordered node is the containing block, so 17 flow units produce the source's 16-unit outer gap.
      style={{ transform: `scale(${1 / zoom})` }}
    >
      <section
        className="relative flex w-full flex-col rounded-2xl border border-[#363636] bg-[#262626] p-3 shadow-[0_22px_60px_rgba(0,0,0,0.5)]"
        // Three source-observed node states use distinct fixed screen heights.
        style={{ height: panelHeight }}
      >
        <button type="button" className="absolute right-3 top-3 flex size-7 items-center justify-center rounded-lg text-[#8b8b8b] hover:bg-white/[0.07] hover:text-white" aria-label="展开编辑器">
          <Expand size={15} />
        </button>

        <div className="flex h-8 shrink-0 items-center gap-1.5 pr-9">
          {(variant === "empty" ? ["标记", "风格"] : ["参考", "标记", "风格"]).map((label) => (
            <button key={label} type="button" className="flex h-7 items-center gap-1.5 rounded-full bg-white/[0.06] px-2.5 text-xs text-[#a5a5a5] hover:bg-white/10 hover:text-white">
              {label === "参考" ? <Images size={13} /> : label === "标记" ? <AtSign size={13} /> : <Box size={13} />}
              {label}
            </button>
          ))}
          {canSuggest && (
            <button type="button" onClick={() => setShowAutoLink((value) => !value)} className="ml-auto flex h-7 items-center gap-1.5 rounded-full bg-[#09caf5]/10 px-2.5 text-xs text-[#09caf5]">
              <Link2 size={12} />智能引用 AutoLink
            </button>
          )}
        </div>

        {showAutoLink && (
          <div className="absolute left-3 right-3 top-12 z-10 flex h-14 items-center rounded-xl border border-[#09caf5]/25 bg-[#202a2c] px-3 shadow-xl">
            <div className="flex -space-x-1.5">
              {autoLinkCandidates.map((candidate) => (
                <div key={candidate.id} className="relative size-8 overflow-hidden rounded-lg border border-[#262626]">
                  <Image src={candidate.image} alt={candidate.name} fill sizes="32px" className="object-cover" unoptimized />
                </div>
              ))}
            </div>
            <span className="ml-2 text-xs text-[#b8c5c7]">匹配到陈默、咖啡 2 个画布素材</span>
            <button type="button" onClick={acceptAutoLink} className="ml-auto flex h-7 items-center gap-1 rounded-lg bg-[#09caf5] px-2.5 text-xs text-[#162125]"><Check size={12} />引用</button>
          </div>
        )}

        {referenceItems.length > 0 && (
          <div className="mt-2 flex h-14 shrink-0 items-center gap-2">
            {referenceItems.map((reference, index) => (
              <div key={`${reference.image}-${index}`} className="group/reference relative size-12 overflow-hidden rounded-lg border border-white/10">
                <Image src={reference.image} alt={`${reference.name}参考`} fill sizes="48px" className="object-cover" unoptimized />
                <span className="absolute left-0.5 top-0.5 flex size-4 items-center justify-center rounded-full bg-[#202020]/90 text-[9px] text-white">{index + 1}</span>
                <button type="button" onClick={() => setReferences((items) => items.filter((_, itemIndex) => itemIndex !== index))} aria-label={`移除${reference.name}参考`} className="absolute right-0.5 top-0.5 hidden size-4 items-center justify-center rounded-full bg-black/75 text-white group-hover/reference:flex"><X size={9} /></button>
              </div>
            ))}
          </div>
        )}

        <textarea
          value={prompt}
          onChange={(event) => { setPrompt(event.target.value); setSubmitted(false); }}
          placeholder="描述你想要生成的画面，或使用 @ 引用画布素材"
          aria-label="图片生成提示词"
          className={cn(
            "min-h-0 flex-1 resize-none bg-transparent text-sm leading-6 text-[#ededed] outline-none selection:bg-[#09caf5]/30 placeholder:text-[#5e5e5e]",
            variant === "empty" ? "mt-3" : "mt-2",
          )}
        />

        <footer className="mt-2 flex h-9 shrink-0 items-center gap-2 border-t border-white/[0.07] pt-2 text-xs text-[#dfdfdf]">
          <button type="button" className="flex h-7 items-center gap-1.5 rounded-md px-1.5 hover:bg-white/[0.06]">
            <span className="text-base">⌘</span><span>Lib Image</span><ChevronDown size={12} className="text-[#777]" />
          </button>
          <span className="h-4 w-px bg-white/10" />
          <button type="button" className="flex h-7 items-center gap-1 rounded-md px-1.5 hover:bg-white/[0.06]">
            <span>▭ {generationSettings}</span><ChevronDown size={12} className="text-[#777]" />
          </button>
          <button type="button" className="flex size-7 items-center justify-center rounded-md text-[#9a9a9a] hover:bg-white/[0.06]" title="高级设置" aria-label="高级设置"><SlidersHorizontal size={14} /></button>
          <span className="ml-auto" />
          {submitted && <span className="text-[#09caf5]">已创建本地生成任务</span>}
          <button type="button" className="flex size-7 items-center justify-center rounded-md text-[#b5b5b5] hover:bg-white/[0.06]" title="翻译" aria-label="翻译"><Languages size={15} /></button>
          <button type="button" className="flex size-7 items-center justify-center rounded-md text-[#777] hover:bg-white/[0.06]" title="撤销" aria-label="撤销"><Undo2 size={14} /></button>
          <button type="button" onClick={() => setSubmitted(true)} disabled={!prompt.trim()} className="flex size-8 items-center justify-center rounded-full bg-white text-[#222] hover:bg-[#efefef] disabled:bg-white/[0.08] disabled:text-[#555]" aria-label="生成图片"><ArrowUp size={17} /></button>
        </footer>
      </section>
    </div>
  );
}
