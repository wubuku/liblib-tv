"use client";

import { useState } from "react";
import {
  ArrowUp,
  ChevronDown,
  Expand,
  RectangleHorizontal,
  Scissors,
} from "lucide-react";

export type VideoClipMode =
  | "讲解视频"
  | "批量广告"
  | "口播视频"
  | "素材混剪";

interface VideoClipEditPanelProps {
  zoom: number;
  mode: VideoClipMode | null;
}

export function VideoClipEditPanel({
  zoom,
  mode,
}: VideoClipEditPanelProps) {
  const [prompt, setPrompt] = useState("");
  const [status, setStatus] = useState("");

  return (
    <div
      data-video-clip-edit-panel
      className="nodrag nowheel nopan absolute -bottom-[17px] left-1/2 z-20 w-[660px] -translate-x-1/2 translate-y-full origin-top"
      // The bordered node shell needs 17 flow units to preserve the source's 16-unit outer gap.
      style={{ transform: `scale(${1 / zoom})` }}
    >
      <section className="relative flex h-[191px] w-full flex-col rounded-2xl border border-[#363636] bg-[#262626] p-3 shadow-[0_22px_60px_rgba(0,0,0,0.5)]">
        <button
          type="button"
          data-video-clip-reference
          onClick={() => setStatus("请先连接视频节点后添加参考")}
          className="flex h-[26px] w-fit items-center rounded-full bg-white/[0.06] px-2.5 text-xs text-[#a5a5a5] hover:bg-white/10 hover:text-white"
        >
          +参考
        </button>
        <button
          type="button"
          aria-label="展开智能剪辑编辑器"
          onClick={() => setStatus("本地原型：展开编辑器未连接")}
          className="absolute right-3 top-3 flex size-7 items-center justify-center rounded-lg text-[#8b8b8b] hover:bg-white/[0.07] hover:text-white"
        >
          <Expand size={15} />
        </button>

        <textarea
          data-video-clip-prompt
          aria-label="智能剪辑提示词"
          value={prompt}
          onChange={(event) => {
            setPrompt(event.target.value);
            setStatus("");
          }}
          placeholder="描述想剪成什么效果"
          className="mt-3 min-h-0 flex-1 resize-none bg-transparent text-sm leading-6 text-[#ededed] outline-none selection:bg-[#09caf5]/30 placeholder:text-[#5e5e5e]"
        />

        <footer className="mt-2 flex h-[41px] shrink-0 items-end gap-1 border-t border-white/[0.07] pt-2 text-xs text-[#dfdfdf]">
          <button
            type="button"
            data-video-clip-mode-setting
            className="flex h-8 items-center gap-1.5 rounded-md px-1.5 hover:bg-white/[0.06]"
          >
            <Scissors size={14} className="text-[#aaa]" />
            <span>{mode ?? "默认模式"}</span>
            <ChevronDown size={12} className="text-[#777]" />
          </button>
          <span className="h-4 w-px bg-white/10" />
          <button
            type="button"
            data-video-clip-output-setting
            className="flex h-8 items-center gap-1.5 rounded-md px-1.5 hover:bg-white/[0.06]"
          >
            <RectangleHorizontal size={14} className="text-[#aaa]" />
            <span>16:9 · 720P · 30s</span>
            <ChevronDown size={12} className="text-[#777]" />
          </button>
          <span className="ml-auto" />
          {status && (
            <span
              data-video-clip-status
              className="max-w-52 truncate pb-2 text-[11px] text-[#75d7e8]"
            >
              {status}
            </span>
          )}
          <button
            type="button"
            data-video-clip-submit
            aria-label="发送"
            disabled={!prompt.trim()}
            onClick={() => setStatus("已创建本地智能剪辑任务")}
            className="flex size-8 shrink-0 items-center justify-center rounded-full bg-[#d9d9d9] text-[#303030] hover:bg-white disabled:bg-white/[0.08] disabled:text-[#555]"
          >
            <ArrowUp size={17} />
          </button>
        </footer>
      </section>
    </div>
  );
}
