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
  RectangleHorizontal,
  SlidersHorizontal,
  Undo2,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";

type ImageEditorVariant = "empty" | "prompt" | "referenced" | "tool" | "panorama";
export type ImageEditorHeight = 191 | 211 | 252 | 274;

interface ImageEditPanelProps {
  zoom: number;
  variant: ImageEditorVariant;
  panelHeight?: ImageEditorHeight;
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
  panelHeight,
  initialPrompt,
  initialReferences,
  generationSettings,
}: ImageEditPanelProps) {
  if (variant === "panorama") {
    return (
      <PanoramaEditPanel
        zoom={zoom}
        panelHeight={panelHeight}
        initialReferences={initialReferences}
        generationSettings={generationSettings}
      />
    );
  }

  return (
    <StandardImageEditPanel
      zoom={zoom}
      variant={variant}
      panelHeight={panelHeight}
      initialPrompt={initialPrompt}
      initialReferences={initialReferences}
      generationSettings={generationSettings}
    />
  );
}

function StandardImageEditPanel({
  zoom,
  variant,
  panelHeight,
  initialPrompt = "",
  initialReferences = [],
  generationSettings = "16:9 · 低画质 · 1K · 1张",
}: ImageEditPanelProps) {
  const [prompt, setPrompt] = useState(initialPrompt);
  const [references, setReferences] = useState(initialReferences);
  const [showAutoLink, setShowAutoLink] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const resolvedPanelHeight =
    panelHeight ?? (variant === "empty" ? 191 : variant === "prompt" ? 211 : 274);
  const canSuggest = prompt.trim().length > 0 && references.length === 0;
  const referenceItems = useMemo(
    () => references.map((image, index) => ({ image, name: index === 0 ? "陈默" : index === 1 ? "咖啡" : `参考 ${index + 1}` })),
    [references],
  );
  const topControls = referenceItems.length > 0
    ? ["参考", "标记", "风格"]
    : ["标记", "风格"];

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
        // Source-observed height is explicit per known node; variant is compatibility fallback only.
        style={{ height: resolvedPanelHeight }}
      >
        <button type="button" className="absolute right-3 top-3 flex size-7 items-center justify-center rounded-lg text-[#8b8b8b] hover:bg-white/[0.07] hover:text-white" aria-label="展开编辑器">
          <Expand size={15} />
        </button>

        <div data-image-editor-top-controls className="flex h-[26px] shrink-0 items-center gap-1 pr-9">
          {topControls.map((label) => (
            <button
              key={label}
              type="button"
              data-image-editor-control={label}
              className="flex h-[26px] w-[54px] items-center justify-center gap-1 rounded-full bg-white/[0.06] text-xs text-[#a5a5a5] hover:bg-white/10 hover:text-white"
            >
              {label === "参考" ? <Images size={13} /> : label === "标记" ? <AtSign size={13} /> : <Box size={13} />}
              {label}
            </button>
          ))}
        </div>

        {showAutoLink && (
          <div data-image-editor-autolink-popover className="absolute left-3 right-3 top-12 z-10 flex h-14 items-center rounded-xl border border-[#09caf5]/25 bg-[#202a2c] px-3 shadow-xl">
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
          <div className="mt-2 flex h-[47px] shrink-0 items-center gap-[9px]">
            {referenceItems.map((reference, index) => (
              <div
                key={`${reference.image}-${index}`}
                data-image-editor-reference
                className="group/reference relative size-[47px] overflow-hidden rounded-lg border border-white/10"
              >
                <Image src={reference.image} alt={`${reference.name}参考`} fill sizes="47px" className="object-cover" unoptimized />
                <span className="absolute left-0.5 top-0.5 flex size-4 items-center justify-center rounded-full bg-[#202020]/90 text-[9px] text-white">{index + 1}</span>
                <button type="button" onClick={() => setReferences((items) => items.filter((_, itemIndex) => itemIndex !== index))} aria-label={`移除${reference.name}参考`} className="absolute right-0.5 top-0.5 hidden size-4 items-center justify-center rounded-full bg-black/75 text-white group-hover/reference:flex"><X size={9} /></button>
              </div>
            ))}
          </div>
        )}

        <textarea
          value={prompt}
          onChange={(event) => { setPrompt(event.target.value); setSubmitted(false); }}
          placeholder="可直接文字生图，或上传图片输入文字指令对图片进行编辑，如：将背景改为雪夜"
          aria-label="图片生成提示词"
          className={cn(
            "min-h-0 flex-1 resize-none bg-transparent text-sm leading-6 text-[#ededed] outline-none selection:bg-[#09caf5]/30 placeholder:text-[#5e5e5e]",
            variant === "empty" ? "mt-3" : "mt-2",
          )}
        />

        <footer className="mt-2 flex h-[41px] shrink-0 items-end gap-1 border-t border-white/[0.07] pt-2 text-xs text-[#dfdfdf]">
          <button data-image-editor-model type="button" className="flex h-8 items-center gap-1.5 rounded-md px-1.5 hover:bg-white/[0.06]">
            <Link2 size={14} className="text-[#9a9a9a]" /><span>Lib Image</span><ChevronDown size={12} className="text-[#777]" />
          </button>
          <span className="h-4 w-px bg-white/10" />
          <button data-image-editor-settings type="button" className="flex h-8 items-center gap-1 rounded-md px-1.5 hover:bg-white/[0.06]">
            <RectangleHorizontal size={14} className="text-[#9a9a9a]" />
            <span>{generationSettings}</span><ChevronDown size={12} className="text-[#777]" />
          </button>
          <button data-image-editor-footer-icon type="button" className="flex size-8 items-center justify-center rounded-md text-[#9a9a9a] hover:bg-white/[0.06]" title="高级设置" aria-label="高级设置"><SlidersHorizontal size={14} /></button>
          <span className="ml-auto" />
          {submitted && <span className="text-[#09caf5]">已创建本地生成任务</span>}
          {canSuggest && (
            <button
              data-image-editor-autolink
              data-image-editor-footer-icon
              type="button"
              onClick={() => setShowAutoLink((value) => !value)}
              className="flex size-8 items-center justify-center rounded-md text-[#9a9a9a] hover:bg-white/[0.06] hover:text-[#09caf5]"
              title="智能引用 AutoLink"
              aria-label="智能引用 AutoLink"
            >
              <Link2 size={15} />
            </button>
          )}
          <button data-image-editor-footer-icon type="button" className="flex size-8 items-center justify-center rounded-md text-[#b5b5b5] hover:bg-white/[0.06]" title="翻译" aria-label="翻译"><Languages size={15} /></button>
          <button data-image-editor-footer-icon type="button" className="flex size-8 items-center justify-center rounded-md text-[#777] hover:bg-white/[0.06]" title="撤销" aria-label="撤销"><Undo2 size={14} /></button>
          <button data-image-editor-footer-icon type="button" onClick={() => setSubmitted(true)} disabled={!prompt.trim()} className="flex size-8 items-center justify-center rounded-full bg-white text-[#222] hover:bg-[#efefef] disabled:bg-white/[0.08] disabled:text-[#555]" aria-label="生成图片"><ArrowUp size={17} /></button>
        </footer>
      </section>
    </div>
  );
}

interface PanoramaEditPanelProps {
  zoom: number;
  panelHeight?: ImageEditorHeight;
  initialReferences?: string[];
  generationSettings?: string;
}

function PanoramaEditPanel({
  zoom,
  panelHeight = 252,
  initialReferences = [],
  generationSettings = "2:1 · 标准画质 · 2K · 1张",
}: PanoramaEditPanelProps) {
  const [submitted, setSubmitted] = useState(false);
  const reference = initialReferences[0];

  return (
    <div
      data-image-edit-panel
      data-panorama-edit-panel
      className="nodrag nowheel nopan absolute -bottom-[17px] left-1/2 z-20 w-[660px] -translate-x-1/2 translate-y-full origin-top"
      // The panorama editor follows the same source-observed node anchor and inverse zoom model.
      style={{ transform: `scale(${1 / zoom})` }}
    >
      <section
        className="relative flex w-full flex-col rounded-2xl border border-[#363636] bg-[#262626] p-3 shadow-[0_22px_60px_rgba(0,0,0,0.5)]"
        style={{ height: panelHeight }}
      >
        <button type="button" className="absolute right-3 top-3 flex size-7 items-center justify-center rounded-lg text-[#8b8b8b] hover:bg-white/[0.07] hover:text-white" aria-label="展开全景编辑器">
          <Expand size={15} />
        </button>

        <div className="flex h-[55px] shrink-0 items-start gap-2 pr-9">
          <button
            type="button"
            data-panorama-add-reference
            className="flex h-[26px] items-center gap-1 rounded-full bg-white/[0.06] px-2.5 text-xs text-[#a5a5a5] hover:bg-white/10 hover:text-white"
          >
            <Images size={13} />
            +参考
          </button>
          {reference && (
            <div
              data-panorama-reference
              className="relative size-[47px] overflow-hidden rounded-lg border border-white/10"
            >
              <Image src={reference} alt="全景参考图" fill sizes="47px" className="object-cover" unoptimized />
              <span className="absolute left-0.5 top-0.5 flex size-4 items-center justify-center rounded-full bg-[#202020]/90 text-[9px] text-white">1</span>
            </div>
          )}
        </div>

        <div className="flex min-h-0 flex-1 items-start gap-3 rounded-lg bg-[#202020]/55 px-3 py-2.5">
          <span className="flex h-6 min-w-9 items-center justify-center rounded-md bg-[#6652d9]/20 px-1.5 text-[11px] font-medium text-[#a999ff]">
            720
          </span>
          <div className="min-w-0 flex-1">
            <div className="flex h-6 items-center gap-2 text-sm text-[#ededed]">
              <span>720全景</span>
              <SlidersHorizontal size={13} className="text-[#777]" />
            </div>
            <p data-panorama-prompt className="mt-1 text-xs leading-5 text-[#858585]">
              点击生成，直接将场景图像转为720全景图，支持文生/参考图
            </p>
          </div>
        </div>

        <footer className="mt-2 flex h-[41px] shrink-0 items-end gap-1 border-t border-white/[0.07] pt-2 text-xs text-[#dfdfdf]">
          <button data-image-editor-model type="button" className="flex h-8 items-center gap-1.5 rounded-md px-1.5 hover:bg-white/[0.06]">
            <Link2 size={14} className="text-[#9a9a9a]" /><span>Lib Image</span><ChevronDown size={12} className="text-[#777]" />
          </button>
          <span className="h-4 w-px bg-white/10" />
          <button data-image-editor-settings type="button" className="flex h-8 items-center gap-1 rounded-md px-1.5 hover:bg-white/[0.06]">
            <RectangleHorizontal size={14} className="text-[#9a9a9a]" />
            <span>{generationSettings}</span><ChevronDown size={12} className="text-[#777]" />
          </button>
          <button data-image-editor-footer-icon type="button" className="flex size-8 items-center justify-center rounded-md text-[#9a9a9a] hover:bg-white/[0.06]" title="高级设置" aria-label="高级设置"><SlidersHorizontal size={14} /></button>
          <span className="ml-auto" />
          {submitted && <span className="text-[#09caf5]">已创建本地全景任务</span>}
          <button
            data-panorama-submit
            data-image-editor-footer-icon
            type="button"
            onClick={() => setSubmitted(true)}
            className="flex size-8 items-center justify-center rounded-full bg-white text-[#222] hover:bg-[#efefef]"
            aria-label="生成720全景图"
          >
            <ArrowUp size={17} />
          </button>
        </footer>
      </section>
    </div>
  );
}
