"use client";

import Image from "next/image";
import { useMemo, useState } from "react";
import { ArrowUp, Check, ChevronDown, Scissors, TimerReset, X } from "lucide-react";
import { cn } from "@/lib/utils";

interface SegmentReshootPanelProps {
  zoom: number;
  mode: "reshoot" | "continue";
  onClose: () => void;
}

const segments = [
  { id: "0-4", start: 0, end: 4, image: "/images/scene-coffee-1.png" },
  { id: "4-8", start: 4, end: 8, image: "/images/scene-coffee-3.png" },
  { id: "8-12", start: 8, end: 12, image: "/images/scene-coffee-4.png" },
  { id: "12-16", start: 12, end: 16, image: "/images/storyboard-2.png" },
  { id: "16-20", start: 16, end: 20, image: "/images/scene-coffee-2.png" },
  { id: "20-24", start: 20, end: 24, image: "/images/scene-coffee-1.png" },
  { id: "24-28", start: 24, end: 28, image: "/images/scene-coffee-3.png" },
  { id: "28-30", start: 28, end: 30, image: "/images/scene-coffee-4.png", disabled: true },
];

function time(value: number) {
  return `00:${String(value).padStart(2, "0")}`;
}

export function SegmentReshootPanel({ zoom, mode, onClose }: SegmentReshootPanelProps) {
  const [selected, setSelected] = useState<string[]>(mode === "continue" ? ["24-28"] : []);
  const [intent, setIntent] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const isContinue = mode === "continue";
  const selectedSegments = useMemo(() => segments.filter((segment) => selected.includes(segment.id)), [selected]);
  const projectedPrompt = isContinue
    ? `对 视频 1 的 ${selectedSegments[0] ? `${time(selectedSegments[0].start)}-${time(selectedSegments[0].end)}` : "结尾片段"} 进行续写：`
    : selectedSegments.length > 0
      ? selectedSegments.map((segment) => `把 视频 1 中 ${time(segment.start)}-${time(segment.end)}`).join("；")
      : "未选择片段，将编辑整段视频";

  const toggle = (id: string) => {
    if (isContinue) {
      setSelected([id]);
      return;
    }
    setSelected((items) => items.includes(id) ? items.filter((item) => item !== id) : items.length >= 5 ? items : [...items, id]);
  };

  return (
    <div
      className="nodrag nowheel nopan absolute -bottom-4 left-1/2 z-30 w-[660px] -translate-x-1/2 translate-y-full origin-top"
      // Matches the original node-anchored, screen-size editor positioning contract.
      style={{ transform: `scale(${1 / zoom})` }}
    >
      <section className="flex h-[286px] flex-col overflow-hidden rounded-2xl border border-[#363636] bg-[#262626] shadow-[0_22px_60px_rgba(0,0,0,0.52)]">
        <header className="flex h-11 shrink-0 items-center border-b border-white/[0.07] px-3">
          {isContinue ? <TimerReset size={15} /> : <Scissors size={15} />}
          <span className="ml-2 text-sm font-medium text-white">{isContinue ? "智能续写" : "片段重拍"}</span>
          <span className="ml-auto text-xs text-[#8a8a8a]">{isContinue ? "选择续写前置片段" : `${selected.length}/5 个片段`}</span>
          <button type="button" onClick={onClose} aria-label={`关闭${isContinue ? "智能续写" : "片段重拍"}`} className="ml-2 flex size-7 items-center justify-center rounded-lg text-[#777] hover:bg-white/[0.07] hover:text-white"><X size={14} /></button>
        </header>

        <div className="px-3 pt-3">
          <div className="flex h-[62px] gap-1 overflow-hidden rounded-xl bg-[#191919] p-1">
            {segments.map((segment) => {
              const active = selected.includes(segment.id);
              return (
                <button key={segment.id} type="button" disabled={segment.disabled} onClick={() => toggle(segment.id)} className={cn("relative min-w-0 flex-1 overflow-hidden rounded-lg border", active ? "border-[#09caf5]" : "border-transparent", segment.disabled && "cursor-not-allowed opacity-35")}>
                  <Image src={segment.image} alt={`${time(segment.start)}-${time(segment.end)}`} fill sizes="80px" className="object-cover" unoptimized />
                  <span className="absolute inset-0 bg-black/15" />
                  <span className="absolute bottom-1 left-1 rounded bg-black/70 px-1 text-[10px] text-white">{segment.end - segment.start}.0s</span>
                  {active && <span className="absolute right-1 top-1 flex size-4 items-center justify-center rounded-full bg-[#09caf5] text-[#172126]"><Check size={10} /></span>}
                </button>
              );
            })}
          </div>
          <div className="mt-1 flex justify-between text-[10px] text-[#666]"><span>00:00</span><span>00:30</span></div>
        </div>

        <div className="mx-3 mt-2 flex min-h-0 flex-1 flex-col rounded-xl bg-[#1f1f1f] p-3">
          <p className="text-xs text-[#bababa]">{projectedPrompt}</p>
          <textarea value={intent} onChange={(event) => { setIntent(event.target.value); setSubmitted(false); }} placeholder={isContinue ? "请输入需要续写的内容" : "描述这段视频要如何修改"} className="mt-2 min-h-0 flex-1 resize-none bg-transparent text-sm leading-6 text-white outline-none placeholder:text-[#595959]" />
        </div>

        <footer className="flex h-12 shrink-0 items-center gap-2 border-t border-white/[0.07] px-3 text-xs text-[#cfcfcf]">
          <button type="button" className="flex h-8 items-center gap-1 rounded-lg px-2 hover:bg-white/[0.06]">Seedance 2.5 <ChevronDown size={12} /></button>
          <button type="button" className="flex h-8 items-center gap-1 rounded-lg px-2 hover:bg-white/[0.06]">720P · 1个 <ChevronDown size={12} /></button>
          {submitted && <span className="ml-auto text-[#09caf5]">已创建本地重拍预览</span>}
          <button type="button" onClick={() => setSubmitted(true)} disabled={!intent.trim()} aria-label={isContinue ? "提交智能续写" : "提交片段重拍"} className={cn("flex size-8 items-center justify-center rounded-xl bg-white text-[#202020] disabled:bg-white/[0.08] disabled:text-[#555]", !submitted && "ml-auto")}><ArrowUp size={15} /></button>
        </footer>
      </section>
    </div>
  );
}
