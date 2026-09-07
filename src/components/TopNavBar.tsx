"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Bot, ChevronDown, ChevronRight, Globe2, LayoutPanelTop, Link2, Share2, Workflow, Zap } from "lucide-react";
import { CanvasTabDropdown } from "./CanvasTabDropdown";
import { useUIStore } from "@/store/uiStore";
import { useCanvasStore } from "@/store/canvasStore";
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
  // Batch 170: 源站 2026-09-07 顶栏画布芯片左侧有工作区名内联输入（min-w-30 max-w-100 cursor-text）。
  const { projectName, setProjectName } = useCanvasStore();
  const {
    editorMode,
    setEditorMode,
    isSharePanelOpen,
    toggleSharePanel,
    isAgentOpen,
    toggleAgent,
    isAssetPanelOpen,
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
        <ProjectMenu />
        <input
          data-workspace-name
          value={projectName}
          onChange={(event) => setProjectName(event.target.value)}
          aria-label="工作区名称"
          className="h-[21px] min-w-[30px] max-w-[100px] cursor-text truncate rounded border border-white/[0.12] bg-transparent px-1 text-[13px] text-[#ededed] outline-none hover:border-white/[0.25] focus:border-white/[0.3]"
        />
        {!isAssetPanelOpen && (
          <div className="rounded-lg bg-[#262626] shadow-[0_4px_16px_rgba(0,0,0,0.25)]">
            <CanvasTabDropdown />
          </div>
        )}
        <div className={cn(
          "hidden h-8 items-center rounded-lg bg-[#262626] p-0.5 shadow-[0_4px_16px_rgba(0,0,0,0.25)] sm:flex",
          isAssetPanelOpen && "ml-[204px]",
        )}>
          <button
            title="工作流"
            aria-label="工作流" /* Batch 103: 2026-09-05 源站顶栏为 工作流/故事板 */
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
            title="故事板"
            aria-label="故事板"
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

      <div data-liblib-topnav-actions className="pointer-events-auto hidden h-8 items-center gap-2 sm:flex">
        <button
          aria-label="发布与分享"
          aria-expanded={isSharePanelOpen}
          onClick={toggleSharePanel}
          className={cn(
            "flex h-8 w-8 items-center justify-center rounded-lg bg-[#262626] hover:bg-[#333]",
            isSharePanelOpen && "bg-[#3b3b3b]",
          )}
        >
          <Share2 size={15} />
        </button>
        {/* Batch 139: 源站顶栏 积分超市 与 积分余额 为两个独立入口。 */}
        <button
          type="button"
          aria-label="积分超市"
          title="积分超市"
          className="flex h-8 items-center gap-1.5 rounded-lg bg-[#262626] px-3 text-xs hover:bg-[#333]"
        >
          <span className="text-[#f5c451]">🏆</span>
          <span className="hidden text-[#f5c451] lg:inline">积分超市</span>
        </button>
        <button
          type="button"
          aria-label="积分余额"
          title="积分余额"
          className="flex h-8 items-center gap-1.5 rounded-lg bg-[#262626] px-3 text-xs hover:bg-[#333]"
        >
          <Zap size={14} className="fill-white" />
          <span>100</span>
        </button>
        <button
          type="button"
          aria-label="开通会员 限时 45 折"
          title="开通会员 限时 45 折"
          className="flex h-8 items-center gap-1.5 rounded-lg bg-[#262626] px-3 text-xs hover:bg-[#333]"
        >
          <span className="text-[#f5c451]">♦</span>
          <span className="hidden text-[#f5c451] md:inline">开通会员</span>
          <span className="rounded bg-[#f5c451]/15 px-1 py-0.5 text-[10px] text-[#f5c451]">限时 45 折</span>
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

// Batch 106: 2026-09-05 源站 logo 下拉为 回到主页/全部项目/创建新项目/删除项目；
// 四项在 clone 中均为本地 status（无路由/项目服务）。
function ProjectMenu() {
  const [open, setOpen] = useState(false);
  const [status, setStatus] = useState("");
  const router = useRouter();
  const menuRef = useRef<HTMLDivElement>(null);
  const items = ["回到主页", "全部项目", "创建新项目", "删除项目"];

  useEffect(() => {
    if (!open) return;
    const handleMouseDown = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setOpen(false);
        setStatus("");
      }
    };
    document.addEventListener("mousedown", handleMouseDown);
    return () => document.removeEventListener("mousedown", handleMouseDown);
  }, [open]);

  return (
    <div className="relative" ref={menuRef}>
      <button
        type="button"
        data-project-menu-trigger
        aria-label="项目菜单"
        aria-expanded={open}
        title="项目菜单"
        onClick={() => setOpen((value) => !value)}
        className="flex h-8 w-5 items-center justify-center rounded-lg text-[#8c8c8c] hover:text-white"
      >
        <ChevronDown size={12} />
      </button>
      {open && (
        <div
          data-project-menu
          className="absolute left-0 top-9 w-40 rounded-xl border border-white/[0.08] bg-[#262626] p-1.5 shadow-[0_18px_48px_rgba(0,0,0,0.5)]"
        >
          {items.map((item, index) => (
            <div key={item}>
              {(index === 2) && <div className="my-1 h-px bg-white/[0.08]" />}
              <button
                type="button"
                data-project-menu-item={item}
                onClick={() => {
                  // Batch 119: 全部项目 → /project 列表页（源站路由 /project）。
                  if (item === "全部项目") {
                    setOpen(false);
                    router.push("/project");
                    return;
                  }
                  setStatus(`本地原型：${item}未接入`);
                }}
                className="flex h-9 w-full items-center rounded-lg px-2.5 text-left text-xs text-[#e8e8e8] hover:bg-white/[0.07]"
              >
                {item}
              </button>
            </div>
          ))}
          {status && <p data-project-menu-status className="px-2.5 pb-1 pt-1 text-[10px] leading-4 text-[#75d7e8]">{status}</p>}
        </div>
      )}
    </div>
  );
}
