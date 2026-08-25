"use client";

import Image from "next/image";
import { ArrowUp, AtSign, Box, ChevronDown, Expand, Languages, SlidersHorizontal, Undo2 } from "lucide-react";

const prompt = "近景镜头。陈默面容冷峻，他身穿黑色高领毛衣和极简羊绒大衣，三七分微卷的黑发整齐，侧脸面对镜头。他目光始终凝视着窗外街道，下颌线紧绷。侧逆光勾勒出他冷白皮的质感与深棕色的瞳孔。浅景深背景，店内陈设模糊，整体基调冰冷且充满孤立感。[视觉风格：现代都市·电影级写实。冷暖对比色调，以低饱和度冷蓝灰为主调，点缀暖橙色咖啡馆灯光。柔和的侧逆光，强调人物面部轮廓与眼神光。高清电影感，35mm胶片颗粒质感。真人媒介。]";

interface ImageEditPanelProps {
  zoom: number;
}

export function ImageEditPanel({ zoom }: ImageEditPanelProps) {
  return (
    <div
      className="nodrag nowheel nopan absolute -bottom-4 left-1/2 z-20 w-[660px] -translate-x-1/2 translate-y-full origin-top"
      // The original keeps the editor at a constant screen size inside the zoomed node layer.
      style={{ transform: `scale(${1 / zoom})` }}
    >
      <div className="flex h-[274px] w-full flex-col rounded-2xl border border-[#363636] bg-[#262626] p-3 shadow-[0_22px_60px_rgba(0,0,0,0.5)]">
        <button className="absolute right-3 top-3 flex h-7 w-7 items-center justify-center rounded-lg text-[#8b8b8b] hover:bg-white/[0.07] hover:text-white" aria-label="展开编辑器">
          <Expand size={15} />
        </button>

        <div className="flex h-8 items-center gap-1.5 pr-9">
          {["参考", "标记", "风格"].map((label, index) => (
            <button key={label} className="flex h-7 items-center gap-1.5 rounded-full bg-white/[0.06] px-2.5 text-xs text-[#a5a5a5] hover:bg-white/10 hover:text-white">
              {index === 0 ? <span className="text-lg leading-none">＋</span> : index === 1 ? <AtSign size={13} /> : <Box size={13} />}
              {label}
            </button>
          ))}
        </div>

        <div className="mt-2 flex h-14 items-center gap-2">
          <div className="relative h-12 w-12 overflow-hidden rounded-lg border border-white/10">
            <Image src="/images/scene-coffee-1.png" alt="陈默参考" fill sizes="48px" className="object-cover" unoptimized />
            <span className="absolute left-0.5 top-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-[#202020] text-[9px] text-white">1</span>
          </div>
          <div className="relative h-12 w-12 overflow-hidden rounded-lg border border-white/10">
            <Image src="/images/scene-coffee-2.png" alt="咖啡参考" fill sizes="48px" className="object-cover" unoptimized />
            <span className="absolute left-0.5 top-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-[#202020] text-[9px] text-white">2</span>
          </div>
        </div>

        <textarea
          defaultValue={prompt}
          aria-label="图片生成提示词"
          className="mt-2 min-h-0 flex-1 resize-none bg-transparent text-sm leading-6 text-[#ededed] outline-none selection:bg-[#09caf5]/30"
        />

        <footer className="mt-2 flex h-9 shrink-0 items-center gap-2 border-t border-white/[0.07] pt-2 text-xs text-[#dfdfdf]">
          <button className="flex h-7 items-center gap-1.5 rounded-md px-1.5 hover:bg-white/[0.06]">
            <span className="text-base">⌘</span>
            <span>Lib Image</span>
            <ChevronDown size={12} className="text-[#777]" />
          </button>
          <span className="h-4 w-px bg-white/10" />
          <button className="flex h-7 items-center gap-1 rounded-md px-1.5 hover:bg-white/[0.06]">
            <span>▭ 16:9 · 低画质 · 1K · 1张</span>
            <ChevronDown size={12} className="text-[#777]" />
          </button>
          <button className="flex h-7 w-7 items-center justify-center rounded-md text-[#9a9a9a] hover:bg-white/[0.06]" title="高级设置" aria-label="高级设置">
            <SlidersHorizontal size={14} />
          </button>
          <span className="ml-auto" />
          <button className="flex h-7 w-7 items-center justify-center rounded-md text-[#b5b5b5] hover:bg-white/[0.06]" title="翻译" aria-label="翻译">
            <Languages size={15} />
          </button>
          <button className="flex h-7 w-7 items-center justify-center rounded-md text-[#777] hover:bg-white/[0.06]" title="撤销" aria-label="撤销">
            <Undo2 size={14} />
          </button>
          <button className="flex h-8 w-8 items-center justify-center rounded-full bg-white text-[#222] hover:bg-[#efefef]" aria-label="生成图片">
            <ArrowUp size={17} />
          </button>
        </footer>
      </div>
    </div>
  );
}
