"use client";

import { CircleHelp, Search } from "lucide-react";

import { JimengLogo, VipDiamond } from "@/components/jimeng/icons";
import { useJimengStore } from "@/store/jimengStore";

/**
 * 顶栏 — 绝对定位 left-3 top-[10px] h-10 z-30 (SOURCE_FACT)。
 * 左: Logo + 项目名(13px/500) + 节点数 + 已保存
 * 右: 搜索/帮助药丸(68px) + 会员药丸(161px) + 头像(36px)
 * mock: 会员积分数值为静态展示。
 */
export function JimengTopBar() {
  const project = useJimengStore((s) => s.project);

  return (
    <header className="pointer-events-none absolute inset-x-3 top-[10px] z-30 flex h-10 items-center">
      {/* 左侧项目信息 */}
      <div className="pointer-events-auto flex min-w-0 flex-1 items-center gap-4">
        <div className="flex items-center gap-2.5">
          <JimengLogo />
          <span className="text-[13px] font-medium leading-[22px] text-white">
            {project.name}
          </span>
        </div>
        <span className="text-[13px] leading-[22px] text-white/40">
          节点{project.nodeCount}
        </span>
        <span className="text-[13px] leading-[22px] text-white/40">
          {project.saved ? "已保存" : "保存中…"}
        </span>
      </div>

      {/* 右侧控制区 */}
      <div className="pointer-events-auto flex h-10 shrink-0 items-center gap-2">
        <div className="jimeng-chrome-pill pointer-events-auto flex h-9 items-center gap-1 p-1">
          <button
            type="button"
            aria-label="搜索"
            className="flex size-7 items-center justify-center rounded-md text-white/85 hover:bg-white/10"
          >
            <Search size={16} />
          </button>
          <button
            type="button"
            aria-label="帮助"
            className="flex size-7 items-center justify-center rounded-md text-white/85 hover:bg-white/10"
          >
            <CircleHelp size={16} />
          </button>
        </div>

        <div className="jimeng-chrome-pill pointer-events-auto flex h-9 items-center gap-1 p-1">
          <div className="flex h-7 items-center gap-1 rounded-md px-2 hover:bg-white/10">
            <VipDiamond size={14} />
            <span className="text-[13px] font-medium text-[#009EFA]">745</span>
            <span className="ml-1 text-[13px] text-white/90">基础会员</span>
          </div>
          {/* 头像 (mock) */}
          <button
            type="button"
            aria-label="账号"
            className="ml-0.5 flex size-7 items-center justify-center overflow-hidden rounded-full bg-gradient-to-br from-[#FF8A7A] to-[#E4489B] text-[11px] text-white"
          >
            梦
          </button>
        </div>
      </div>
    </header>
  );
}
