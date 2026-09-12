"use client";

import { useState } from "react";
import { CircleHelp, Search } from "lucide-react";

import { JimengLogo, VipDiamond } from "@/components/jimeng/icons";
import { JimengHelpMenu } from "@/components/jimeng/JimengHelpMenu";
import { JimengHistoryMenu } from "@/components/jimeng/JimengHistoryMenu";
import { JimengMemberModal } from "@/components/jimeng/JimengMemberModal";
import { JimengShortcutsPanel } from "@/components/jimeng/JimengShortcutsPanel";
import { useJimengStore } from "@/store/jimengStore";

/**
 * 顶栏 — 绝对定位 left-3 top-[10px] h-10 z-30 (SOURCE_FACT)。
 * 左: Logo + 项目名(13px/500) + 节点数 + 已保存
 * 右: 生成历史(⌕)/帮助药丸(68px) + 会员药丸(161px) + 头像(36px)
 * Batch 13: ⌕ 打开生成历史下拉；会员药丸打开订阅页浮层。
 * mock: 会员积分数值为静态展示。
 */
export function JimengTopBar() {
  const project = useJimengStore((s) => s.project);
  const renameProject = useJimengStore((s) => s.renameProject);
  const [helpOpen, setHelpOpen] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [memberOpen, setMemberOpen] = useState(false);
  const [shortcutsOpen, setShortcutsOpen] = useState(false);
  // 单击项目名 = 行内重命名 (SOURCE_FACT batch 29)
  const [editingName, setEditingName] = useState(false);

  return (
    <>
      <header className="pointer-events-none absolute inset-x-3 top-[10px] z-30 flex h-10 items-center">
      {/* 左侧项目信息 */}
      <div className="pointer-events-auto flex min-w-0 flex-1 items-center gap-4">
        <div className="flex items-center gap-2.5">
          <JimengLogo />
          {editingName ? (
            <input
              autoFocus
              defaultValue={project.name}
              aria-label="项目名"
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  const v = (e.target as HTMLInputElement).value.trim();
                  if (v) renameProject(v);
                  setEditingName(false);
                }
                if (e.key === "Escape") setEditingName(false);
              }}
              onBlur={(e) => {
                const v = e.target.value.trim();
                if (v) renameProject(v);
                setEditingName(false);
              }}
              className="w-32 rounded-md border border-[#009EFA]/70 bg-transparent px-1.5 py-0.5 text-[13px] font-medium text-white outline-none"
            />
          ) : (
            <button
              type="button"
              onClick={() => setEditingName(true)}
              className="text-[13px] font-medium leading-[22px] text-white"
            >
              {project.name}
            </button>
          )}
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
          <div className="relative">
            <button
              type="button"
              aria-label="生成历史"
              onClick={() => setHistoryOpen((v) => !v)}
              className="flex size-7 items-center justify-center rounded-md text-white/85 hover:bg-white/10"
            >
              <Search size={16} />
            </button>
            {historyOpen ? (
              <JimengHistoryMenu onClose={() => setHistoryOpen(false)} />
            ) : null}
          </div>
          <div className="relative">
            <button
              type="button"
              aria-label="帮助"
              onClick={() => setHelpOpen((v) => !v)}
              className="flex size-7 items-center justify-center rounded-md text-white/85 hover:bg-white/10"
            >
              <CircleHelp size={16} />
            </button>
          </div>
        </div>

        <div className="jimeng-chrome-pill pointer-events-auto flex h-9 items-center gap-1 p-1">
          <div className="relative flex h-7 items-center gap-1 rounded-md px-2 hover:bg-white/10">
            <button
              type="button"
              aria-label="会员订阅"
              onClick={() => setMemberOpen(true)}
              className="flex items-center gap-1"
            >
              <VipDiamond size={14} />
              <span className="text-[13px] font-medium text-[#009EFA]">745</span>
              <span className="ml-1 text-[13px] text-white/90">基础会员</span>
            </button>
          </div>
          {/* 头像 (mock)；点击展开与帮助菜单同构的账号菜单 (SOURCE_FACT batch 22)。
              单一菜单实例锚定在头像下方，帮助/? 与头像共用 helpOpen。 */}
          <div className="relative ml-0.5">
            <button
              type="button"
              aria-label="账号菜单"
              onClick={() => setHelpOpen((v) => !v)}
              className="flex size-7 items-center justify-center overflow-hidden rounded-full bg-gradient-to-br from-[#FF8A7A] to-[#E4489B] text-[11px] text-white"
            >
              梦
            </button>
          </div>
        </div>
        {helpOpen ? (
          <div className="absolute right-3 top-[46px]">
            <JimengHelpMenu
              onClose={() => setHelpOpen(false)}
              onOpenShortcuts={() => setShortcutsOpen(true)}
            />
          </div>
        ) : null}
      </div>
      </header>
      {memberOpen ? <JimengMemberModal onClose={() => setMemberOpen(false)} /> : null}
      {shortcutsOpen ? (
        <JimengShortcutsPanel onClose={() => setShortcutsOpen(false)} />
      ) : null}
    </>
  );
}
