"use client";

import { useState } from "react";
import { History, Search } from "lucide-react";

import { JimengLogo, VipDiamond } from "@/components/jimeng/icons";
import { JimengHelpMenu } from "@/components/jimeng/JimengHelpMenu";
import { JimengHistoryMenu } from "@/components/jimeng/JimengHistoryMenu";
import { JimengSearchOverlay } from "@/components/jimeng/JimengSearchOverlay";
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
  // Batch 70 (SOURCE_FACT): 节点计数随画布实时变化 (源站建 image/组 后
  // 顶栏 节点 2→3)
  // Batch 71 (SOURCE_FACT 63-after-group.png): 编组后 节点 3 = 2 卡片 +
  // 1 组节点 — 每个编组使计数 +1
  const nodeCount = useJimengStore((s) => {
    const groups = new Set(
      s.nodes.filter((n) => n.groupId).map((n) => n.groupId),
    );
    return s.nodes.length + groups.size;
  });
  const renameProject = useJimengStore((s) => s.renameProject);
  const [helpOpen, setHelpOpen] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
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
          节点{nodeCount}
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
              aria-label="搜索"
              data-testid="topbar-search"
              onClick={() => {
                setHistoryOpen(false);
                setSearchOpen((v) => !v);
              }}
              className={`flex size-7 items-center justify-center rounded-md ${
                searchOpen ? "bg-white/10 text-white" : "text-white/85 hover:bg-white/10"
              }`}
            >
              <Search size={16} />
            </button>
            {searchOpen ? (
              <JimengSearchOverlay onClose={() => setSearchOpen(false)} />
            ) : null}
          </div>
          <div className="relative">
            <button
              type="button"
              aria-label="生成历史"
              onClick={() => {
                setSearchOpen(false);
                setHistoryOpen((v) => !v);
              }}
              className={`flex size-7 items-center justify-center rounded-md ${
                historyOpen ? "bg-white/10 text-white" : "text-white/85 hover:bg-white/10"
              }`}
            >
              <History size={16} />
            </button>
            {historyOpen ? (
              <JimengHistoryMenu onClose={() => setHistoryOpen(false)} />
            ) : null}
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
              Batch 96: 源站该钮 aria 为 用户菜单，且展开的是个人资料弹层
              (西卡文案馆/积分详情，对齐留待后续批次)；帮助/? 钮已从源站
              顶栏移除，故本栏不再渲染 帮助。 */}
          <div className="relative ml-0.5">
            <button
              type="button"
              aria-label="用户菜单"
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
