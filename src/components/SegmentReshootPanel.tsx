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
  Gem,
  Images,
  Languages,
  Volume2,
  Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface SegmentReshootPanelProps {
  zoom: number;
  mode: "reshoot" | "continue";
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

export function SegmentReshootPanel({ zoom, mode }: SegmentReshootPanelProps) {
  const [selected, setSelected] = useState<string[]>(mode === "continue" ? ["24-28"] : []);
  const [intent, setIntent] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const isContinue = mode === "continue";
  const selectedSegments = useMemo(() => segments.filter((segment) => selected.includes(segment.id)), [selected]);
  const status = isContinue
    ? "已创建本地续写任务"
    : selectedSegments.length === 0
      ? "已创建本地整段重跑任务"
      : "已创建本地片段重拍任务";

  const toggle = (id: string) => {
    setSubmitted(false);
    if (isContinue) {
      setSelected([id]);
      return;
    }
    setSelected((items) => items.includes(id) ? items.filter((item) => item !== id) : items.length >= 5 ? items : [...items, id]);
  };

  return (
    <div
      data-segment-reshoot-panel
      data-segment-mode={mode}
      className="nodrag nowheel nopan absolute -bottom-[17px] left-1/2 z-20 flex w-[660px] -translate-x-1/2 translate-y-full origin-top flex-col gap-2"
      // The bordered node is the containing block, so 17 flow units produce the source's 16-unit outer gap.
      style={{ transform: `scale(${1 / zoom})` }}
    >
      <section
        data-segment-filmstrip
        className="flex h-[56px] shrink-0 items-center gap-2 rounded-xl border border-[#343434] bg-[#262626] p-1.5 shadow-[0_12px_32px_rgba(0,0,0,0.38)]"
      >
        <div className="flex h-full min-w-0 flex-1 overflow-hidden rounded-lg bg-[#191919]">
          {segments.map((segment) => {
            const active = selected.includes(segment.id);
            const duration = segment.end - segment.start;
            return (
              <button
                key={segment.id}
                data-segment-option={segment.id}
                type="button"
                disabled={segment.disabled}
                aria-pressed={active}
                onClick={() => toggle(segment.id)}
                className={cn(
                  "relative min-w-0 overflow-hidden border-r border-black/25 last:border-r-0",
                  segment.disabled && "cursor-not-allowed opacity-35",
                )}
                // Each range occupies its actual duration share of the continuous 30-second strip.
                style={{ flexBasis: 0, flexGrow: duration }}
              >
                <Image
                  src={segment.image}
                  alt={`${time(segment.start)}-${time(segment.end)}`}
                  fill
                  sizes="80px"
                  className="object-cover"
                  unoptimized
                />
                <span className="absolute inset-0 bg-black/15" />
                {active && (
                  <>
                    <span className="absolute inset-0 border-2 border-[#2b9cff]" />
                    <span className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 rounded bg-black/75 px-1.5 py-1 text-[10px] font-medium text-white">
                      {duration}.0s
                    </span>
                    <span className="absolute right-1 top-1 flex size-4 items-center justify-center rounded-full bg-[#2b9cff] text-white">
                      <Check size={10} />
                    </span>
                  </>
                )}
              </button>
            );
          })}
        </div>
        <span data-segment-count className="w-[92px] shrink-0 text-center text-xs text-[#858585]">
          {isContinue ? "选择前置片段" : `${selected.length}/5 个片段`}
        </span>
      </section>

      <section
        data-segment-editor
        className={cn(
          "relative flex h-[252px] flex-col overflow-hidden rounded-2xl border border-[#363636] bg-[#262626] p-2 shadow-[0_22px_60px_rgba(0,0,0,0.52)]",
          expanded && "h-[320px]",
        )}
      >
        <div className="flex h-8 shrink-0 items-center gap-1">
          {[
            { label: "参考", icon: Images },
            { label: "标记", icon: AtSign },
            { label: "角色库", icon: Box },
          ].map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.label}
                type="button"
                className="flex h-7 items-center gap-1.5 rounded-full bg-white/[0.05] px-2.5 text-xs text-[#aaa] hover:bg-white/[0.09] hover:text-white"
              >
                <Icon size={12} />
                {item.label}
              </button>
            );
          })}
          <button
            type="button"
            aria-label={expanded ? "收起片段重拍编辑器" : "展开片段重拍编辑器"}
            aria-pressed={expanded}
            onClick={() => setExpanded((value) => !value)}
            className="ml-auto flex size-7 items-center justify-center rounded-lg text-[#777] hover:bg-white/[0.07] hover:text-white"
          >
            <Expand size={14} />
          </button>
        </div>

        <div className="mt-1 flex h-[47px] shrink-0 items-center">
          <div
            data-segment-source
            className="relative h-[47px] w-[38px] overflow-hidden rounded-lg border border-white/10"
          >
            <Image
              src="/images/scene-coffee-4.png"
              alt="视频 1"
              fill
              sizes="38px"
              className="object-cover"
              unoptimized
            />
            <span className="absolute left-0.5 top-0.5 flex size-4 items-center justify-center rounded-full bg-black/75 text-[9px] text-white">
              1
            </span>
            <span className="absolute bottom-0.5 left-0.5 rounded bg-black/75 px-1 text-[8px] text-white">
              30.1s
            </span>
          </div>
        </div>

        <div className="mt-1 flex min-h-0 flex-1 flex-col rounded-xl bg-black/10 px-2.5 py-2">
          {selectedSegments.length > 0 ? (
            <div className="flex flex-wrap items-center gap-1 text-xs text-[#d8d8d8]">
              <span>{isContinue ? "对" : "把"}</span>
              <span
                data-segment-video-token
                className="inline-flex h-6 items-center gap-1 rounded-md bg-white/[0.09] px-1.5 text-[#ededed]"
              >
                <span className="relative size-4 overflow-hidden rounded">
                  <Image src="/images/scene-coffee-4.png" alt="" fill sizes="16px" className="object-cover" unoptimized />
                </span>
                视频 1
              </span>
              <span>{isContinue ? "的" : "中"}</span>
              {selectedSegments.map((segment) => (
                <span
                  key={segment.id}
                  data-segment-range-token={segment.id}
                  className="inline-flex h-6 items-center rounded-md bg-white/[0.12] px-1.5 tabular-nums text-[#e5e5e5]"
                >
                  {time(segment.start)}-{time(segment.end)}
                </span>
              ))}
              <span>{isContinue ? "进行续写：" : ""}</span>
            </div>
          ) : (
            <p className="text-xs leading-5 text-[#777]">
              未选择片段，将编辑整段视频。留空 = 原样重跑一次。
            </p>
          )}
          <textarea
            data-segment-intent
            value={intent}
            onChange={(event) => {
              setIntent(event.target.value);
              setSubmitted(false);
            }}
            placeholder={isContinue ? "请输入需要续写的内容" : "描述这段视频要如何修改"}
            className="mt-1 min-h-0 flex-1 resize-none bg-transparent text-sm leading-6 text-white outline-none placeholder:text-[#595959]"
          />
        </div>

        <footer className="mt-1 flex h-9 shrink-0 items-center gap-1 border-t border-white/[0.07] pt-1 text-xs text-[#dfdfdf]">
          <button type="button" className="flex h-8 items-center gap-1.5 rounded-lg px-2 hover:bg-white/[0.06]">
            <span className="font-semibold">2.5</span>
            <Gem size={11} fill="currentColor" className="text-[#f3b74c]" />
            <ChevronDown size={12} className="text-[#777]" />
          </button>
          <button type="button" className="flex h-8 items-center gap-1 rounded-lg px-2 hover:bg-white/[0.06]">
            720P · 1个
            <Volume2 size={13} className="text-[#aaa]" />
            <ChevronDown size={12} className="text-[#777]" />
          </button>
          {submitted && (
            <span data-segment-status className="ml-auto text-[#09caf5]">
              {status}
            </span>
          )}
          {!submitted && (
            <span className="ml-auto flex shrink-0 items-center gap-1 text-[#777]">
              <Zap size={11} />
              本地预览
            </span>
          )}
          <button
            type="button"
            aria-label="翻译片段重拍提示词"
            className="flex size-8 shrink-0 items-center justify-center rounded-lg text-[#aaa] hover:bg-white/[0.06]"
          >
            <Languages size={14} />
          </button>
          <button
            data-segment-submit
            type="button"
            onClick={() => setSubmitted(true)}
            disabled={isContinue && !intent.trim()}
            aria-label={isContinue ? "提交智能续写" : "提交片段重拍"}
            className="flex size-8 shrink-0 items-center justify-center rounded-full bg-white text-[#202020] disabled:bg-white/[0.08] disabled:text-[#555]"
          >
            {submitted ? <Check size={15} /> : <ArrowUp size={15} />}
          </button>
        </footer>
      </section>
    </div>
  );
}
