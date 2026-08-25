"use client";

import { useState } from "react";
import Link from "next/link";
import { Bot, ChevronRight, Globe2, LayoutPanelTop, Link2, Share2, Workflow, Zap } from "lucide-react";
import { CanvasTabDropdown } from "./CanvasTabDropdown";
import { useUIStore } from "@/store/uiStore";
import { cn } from "@/lib/utils";

function LibTvMark() {
  return (
    <svg width="25" height="18" viewBox="0 0 25 18" fill="none" aria-hidden="true">
      <path d="M2.4 2h20.2L18 16H1L5.4 4.6h10.7l-1.3 3.2H7.7l-1.9 5h9.9l3-7.7H1.5L2.4 2Z" fill="currentColor" />
    </svg>
  );
}

function SharePanel() {
  const [status, setStatus] = useState("");

  return (
    <div data-liblib-overlay="share" className="pointer-events-auto absolute right-[164px] top-10 min-h-[166px] w-[360px] overflow-hidden rounded-2xl border border-white/10 bg-[#262626] p-2 shadow-[0_18px_50px_rgba(0,0,0,0.48)]">
      <h2 className="px-2 py-1 text-sm font-medium text-[#f2f2f2]">发布与分享</h2>
      <button
        type="button"
        data-share-action="publish"
        onClick={() => setStatus("本地原型：发布服务未连接")}
        className="flex min-h-[62px] w-full items-center gap-3 rounded-xl p-3 text-left hover:bg-white/[0.06]"
      >
        <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#343434] text-[#f7f7f7]">
          <Globe2 size={17} />
        </span>
        <span className="min-w-0 flex-1">
          <span className="block text-sm text-[#f7f7f7]">在LibTV上发布</span>
          <span className="mt-0.5 block text-xs text-[#8c8c8c]">发布你的作品和创作过程，让更多创作者看到。</span>
        </span>
        <ChevronRight size={16} className="text-[#737373]" />
      </button>
      <button
        type="button"
        data-share-action="link"
        onClick={() => setStatus("本地原型：分享链接服务未连接")}
        className="flex min-h-[62px] w-full items-center gap-3 rounded-xl p-3 text-left hover:bg-white/[0.06]"
      >
        <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#343434] text-[#f7f7f7]">
          <Link2 size={17} />
        </span>
        <span className="min-w-0 flex-1">
          <span className="block text-sm text-[#f7f7f7]">分享链接</span>
          <span className="mt-0.5 block text-xs text-[#8c8c8c]">拥有此链接的人可以查看并复制你的画布。</span>
        </span>
        <ChevronRight size={16} className="text-[#737373]" />
      </button>
      {status && <p data-share-status className="px-3 pb-1 text-[10px] text-[#75d7e8]">{status}</p>}
    </div>
  );
}

export function TopNavBar() {
  const [projectName, setProjectName] = useState("未命名项目");
  const [isEditing, setIsEditing] = useState(false);
  const {
    editorMode,
    setEditorMode,
    isSharePanelOpen,
    toggleSharePanel,
    isAgentOpen,
    toggleAgent,
  } = useUIStore();

  return (
    <nav className={cn("pointer-events-none fixed left-4 right-4 top-4 z-[70] flex h-8 items-center justify-between text-[#f7f7f7]", isAgentOpen && "sm:right-[356px]")}>
      <div className="pointer-events-auto flex h-8 items-center gap-1">
        <Link
          href="/frameos/canvas/demo"
          className="flex h-8 w-10 items-center justify-center rounded-lg bg-[#262626] text-white shadow-[0_4px_16px_rgba(0,0,0,0.25)] hover:bg-[#303030]"
          title="进入 FrameOS 画布"
        >
          <LibTvMark />
        </Link>
        <div className="hidden h-8 items-center rounded-lg bg-[#262626] px-2 lg:flex">
          {isEditing ? (
            <input
              autoFocus
              value={projectName}
              onChange={(event) => setProjectName(event.target.value)}
              onBlur={() => setIsEditing(false)}
              onKeyDown={(event) => event.key === "Enter" && setIsEditing(false)}
              className="w-28 bg-transparent text-xs outline-none"
            />
          ) : (
            <button className="max-w-28 truncate text-xs text-[#bcbcbc]" onClick={() => setIsEditing(true)}>
              {projectName}
            </button>
          )}
        </div>
        <div className="rounded-lg bg-[#262626] shadow-[0_4px_16px_rgba(0,0,0,0.25)]">
          <CanvasTabDropdown />
        </div>
        <div className="hidden h-8 items-center rounded-lg bg-[#262626] p-0.5 shadow-[0_4px_16px_rgba(0,0,0,0.25)] sm:flex">
          <button
            title="工作台"
            aria-label="工作台"
            aria-pressed={editorMode === "workbench"}
            onClick={() => setEditorMode("workbench")}
            className={cn(
              "flex h-7 w-7 items-center justify-center rounded-md text-[#8c8c8c] transition-colors",
              editorMode === "workbench" && "bg-[#404040] text-white",
            )}
          >
            <Workflow size={14} />
          </button>
          <button
            title="分镜"
            aria-label="分镜"
            aria-pressed={editorMode === "storyboard"}
            onClick={() => setEditorMode("storyboard")}
            className={cn(
              "flex h-7 w-7 items-center justify-center rounded-md text-[#8c8c8c] transition-colors",
              editorMode === "storyboard" && "bg-[#404040] text-white",
            )}
          >
            <LayoutPanelTop size={14} />
          </button>
        </div>
      </div>

      <div className="pointer-events-auto hidden h-8 items-center gap-2 sm:flex">
        <button
          aria-label="分享"
          aria-expanded={isSharePanelOpen}
          onClick={toggleSharePanel}
          className={cn(
            "flex h-8 w-8 items-center justify-center rounded-lg bg-[#262626] hover:bg-[#333]",
            isSharePanelOpen && "bg-[#3b3b3b]",
          )}
        >
          <Share2 size={15} />
        </button>
        <button className="flex h-8 items-center gap-1.5 rounded-lg bg-[#262626] px-3 text-xs hover:bg-[#333]">
          <Zap size={14} className="fill-white" />
          <span>20</span>
        </button>
        {!isAgentOpen && (
          <button
            aria-expanded={isAgentOpen}
            onClick={toggleAgent}
            className="flex h-8 items-center gap-2 rounded-lg bg-[#262626] px-3 text-sm hover:bg-[#333]"
          >
            <Bot size={16} />
            <span>Agent</span>
          </button>
        )}
      </div>

      {isSharePanelOpen && <SharePanel />}
    </nav>
  );
}
