"use client";

import { useMemo, useState } from "react";
import {
  ChevronDown,
  History,
  MoreHorizontal,
  Search,
  Share2,
} from "lucide-react";

import { JimengLogo, VipDiamond } from "@/components/jimeng/icons";
import { JimengHelpMenu } from "@/components/jimeng/JimengHelpMenu";
import { JimengHistoryMenu } from "@/components/jimeng/JimengHistoryMenu";
import { JimengMoreMenu } from "@/components/jimeng/JimengMoreMenu";
import { JimengNodeSummaryPopover } from "@/components/jimeng/JimengNodeSummaryPopover";
import { JimengProjectInfoModal } from "@/components/jimeng/JimengProjectInfoModal";
import { JimengProjectPanel } from "@/components/jimeng/JimengProjectPanel";
import { JimengSearchOverlay } from "@/components/jimeng/JimengSearchOverlay";
import { JimengSharePanel } from "@/components/jimeng/JimengSharePanel";
import { JimengMemberModal } from "@/components/jimeng/JimengMemberModal";
import { JimengShortcutsPanel } from "@/components/jimeng/JimengShortcutsPanel";
import { useJimengStore } from "@/store/jimengStore";

/**
 * 顶栏 — absolute left-3 top-[10px] h-10 z-30，两簇 justify-between、间距 24px。
 *
 * Batch 794 全面对齐源站实测 (SOURCE_FACT 2026-10-01 @1680×826，登录态)：
 *
 * 左簇 230×40 (r8)：
 *   返回首页 logo      40×40 @[12,10]   svg 40×40
 *   项目名标题         68×28 @[52,16]   13px/22px w500，radius 6/2/2/6
 *   项目箭头           20×28 @[120,16]  svg 16，radius 2/6/6/2（与标题拼成一体）
 *   节点摘要           28×28 @[156,16]  10px/18px white/60，距箭头 16px
 * 右簇（间距 16px）：
 *   搜索 28×28 r12 / 生成历史 28×28 r12（同药丸内 4px 缝）
 *   分享   60×28 @[1388,16] 16px/24 w500，padding 0 10px 0 8px
 *   更多   28×28 @[1465,16]
 *   积分   111×28 @[1509,16] 12px 品牌色数字 + 基础会员，border 1px transparent
 *   用户菜单 28×28 @[1636,16]
 *
 * 积分数值为 mock (CLONE_DECISION)：源站读数随账号/时间变化，源站样本为 805，
 * 复刻沿用既有 745 以与 JimengMemberModal 的「积分详情 745」保持一致。
 */
const CANVAS_URL =
  "https://jimeng.jianying.com/ai-tool/ai-canvas/" +
  "64b58cd5-7b04-4312-890a-09f2d1d3399f?enter_from=noew_canvas_shared_link";
const CREDITS = 745;

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
  // Batch 794: 节点摘要弹层按节点标题列出 (SOURCE_FACT 实测为「视频 1」)
  // 注意：selector 必须返回**稳定引用**。直接 map 出新数组会让 zustand 的
  // Object.is 快照比较永远为 false，触发 "getServerSnapshot should be cached"
  // 无限重渲染（整页白屏）。故取 nodes 引用后再 useMemo 派生。
  const nodes = useJimengStore((s) => s.nodes);
  const nodeLabels = useMemo(
    () =>
      nodes.map((n) =>
        typeof n.data?.title === "string" ? n.data.title : "节点",
      ),
    [nodes],
  );
  // Batch 795 SOURCE_FACT: Agent 面板展开时，源站顶栏**向左让位**而非被遮挡 ——
  // 顶栏 right 内边距由 12 变为 424（= 1680 - 1208(积分右缘) - 48(药丸右内边距4 + 头像28 + 药丸内 gap16)）。
  // 复测源站展开态：积分入口右缘 1208、用户菜单右缘 1252、面板左缘 1268。
  const aiDrawerOpen = useJimengStore((s) => s.aiDrawerOpen);
  const renameProject = useJimengStore((s) => s.renameProject);
  const [helpOpen, setHelpOpen] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [memberOpen, setMemberOpen] = useState(false);
  const [shortcutsOpen, setShortcutsOpen] = useState(false);
  const [shareOpen, setShareOpen] = useState(false);
  const [moreOpen, setMoreOpen] = useState(false);
  const [projectOpen, setProjectOpen] = useState(false);
  const [nodeSummaryOpen, setNodeSummaryOpen] = useState(false);
  const [projectInfoOpen, setProjectInfoOpen] = useState(false);
  // Batch 799: 复制项目需要 pushToast / 剪贴板
  const pushToast = useJimengStore((s) => s.pushToast);
  // 单击项目名 = 行内重命名 (SOURCE_FACT batch 29)
  const [editingName, setEditingName] = useState(false);

  const closeAll = () => {
    setShareOpen(false);
    setMoreOpen(false);
    setProjectOpen(false);
    setNodeSummaryOpen(false);
    setProjectInfoOpen(false);
  };

  // Batch 799 SOURCE_FACT: 「复制项目」把画布链接写入剪贴板并弹顶部 toast
  // 「复制画布中…」(127×44 @[776,24] 顶部居中，13px，
  // scripts/jimeng_probe797_copytoast.py)。复刻复用既有全局 toast
  // (JimengTaskToast)，文案逐字沿用源站。
  const copyProject = () => {
    pushToast("复制画布中…");
    const url = CANVAS_URL.split("?")[0];
    void navigator.clipboard?.writeText(url).catch(() => {
      /* 剪贴板不可用时静默降级，源站在无头环境亦未能验证终态 */
    });
  };

  return (
    <>
      {/* 面板展开时收缩右边界，把右簇让到面板左侧 (SOURCE_FACT batch 795) */}
      <header
        className="pointer-events-none absolute left-3 top-[10px] z-30 flex h-10 items-center justify-between gap-6"
        style={{ right: aiDrawerOpen ? 424 : 12 }}
      >
      {/* ── 左簇：logo + 项目名/箭头拼接段 + 节点摘要 ── */}
      <div
        data-testid="topbar-left"
        className="pointer-events-auto flex h-10 min-w-0 items-center rounded-lg"
      >
        <button
          type="button"
          aria-label="返回首页"
          data-testid="canvas-project-logo"
          className="flex size-10 shrink-0 items-center justify-center rounded-lg text-white hover:bg-white/10"
        >
          <JimengLogo size={40} />
        </button>

        {/* 标题与箭头拼成一个整体：左侧圆角归标题，右侧圆角归箭头 */}
        <div className="flex shrink-0 items-center">
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
              className="h-7 w-[68px] rounded-l-md border border-[#009EFA]/70 bg-transparent px-2 text-[13px] font-medium leading-[22px] text-white outline-none"
            />
          ) : (
            <button
              type="button"
              aria-label={`Canvas title: ${project.name}`}
              data-testid="canvas-project-title-trigger"
              onClick={() => setEditingName(true)}
              style={{ borderRadius: "6px 2px 2px 6px" }}
              className="flex h-7 items-center gap-1 whitespace-nowrap px-2 py-[3px] text-[13px] font-medium leading-[22px] text-white hover:bg-white/10"
            >
              {project.name}
            </button>
          )}
          <button
            type="button"
            aria-label="项目"
            data-testid="canvas-project-trigger"
            onClick={() => {
              closeAll();
              setProjectOpen((v) => !v);
            }}
            style={{ borderRadius: "2px 6px 6px 2px" }}
            className="flex h-7 w-5 shrink-0 items-center justify-center px-0.5 text-white hover:bg-white/10"
          >
            <ChevronDown size={16} />
          </button>
          {projectOpen ? (
            <JimengProjectPanel
              projectName={project.name}
              onClose={() => setProjectOpen(false)}
            />
          ) : null}
        </div>

        {/* 节点摘要：距箭头 16px，28×28 内 10px 小字 */}
        <div className="relative ml-4 shrink-0">
          <button
            type="button"
            aria-label={`Canvas node summary: 节点 ${nodeCount}`}
            data-testid="canvas-node-summary-trigger"
            onClick={() => {
              closeAll();
              setNodeSummaryOpen((v) => !v);
            }}
            className="flex size-7 items-center justify-center rounded-md text-[10px]/[18px] font-normal text-white/60 hover:bg-white/10"
          >
            节点 {nodeCount}
          </button>
          {nodeSummaryOpen ? (
            <JimengNodeSummaryPopover
              nodeLabels={nodeLabels}
              onClose={() => setNodeSummaryOpen(false)}
            />
          ) : null}
        </div>

        <span className="ml-3 text-[13px]/[22px] text-white/40">
          {project.saved ? "已保存" : "保存中…"}
        </span>
      </div>

      {/* ── 右簇：搜索/历史药丸 + 分享 + 更多 + 积分 + 用户菜单 ── */}
      {/* SOURCE_FACT (batch 795): 药丸之间 8px；按钮到按钮 = 8 + 4 + 4 = 16 */}
      <div className="pointer-events-auto flex h-10 shrink-0 items-center gap-2">
        <div className="jimeng-chrome-pill flex h-9 items-center gap-1 p-1">
          <div className="relative">
            <button
              type="button"
              aria-label="搜索"
              data-testid="topbar-search"
              onClick={() => {
                setHistoryOpen(false);
                setSearchOpen((v) => !v);
              }}
              className={`flex size-7 items-center justify-center rounded-full ${
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
              className={`flex size-7 items-center justify-center rounded-full ${
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

        {/* SOURCE_FACT (batch 795 复查): 分享的 chrome 药丸是 70×36 @[1383,12]，
            60×28 的按钮内缩 4px 在其中 —— 药丸背景属于外层，不属于按钮本身。 */}
        <div className="jimeng-chrome-pill flex h-9 shrink-0 items-center p-1">
        <button
          type="button"
          aria-label="分享"
          data-testid="canvas-share-trigger"
          onClick={() => {
            closeAll();
            setShareOpen((v) => !v);
          }}
          // Batch 798 SOURCE_FACT 复测（源站 @1680×826 逐层量得）：
          //   按钮   60×28  padding 0 10px 0 8px  gap 4px
          //   svg    16×16 @[1395,22]
          //   标签   span 24×20 @[1415,20]  **12px / line-height 20px / w500**
          //   关键   按钮 `white-space: nowrap`
          // 此前缺 nowrap：CJK 可在任意两字之间断行，标签被挤到 42px 内容盒里
          // 就叠成「分/享」两行（截图可见）。源站同样 44px 内容 > 42px 内容盒，
          // 靠 nowrap 保持单行——所以这不是"宽度算错"，是**缺 nowrap**。
          // 注释里"按我们的字体度量会到 70px"是旧账（那时标签还是 16px），
          // 实际 8+16+4+24+10 = 62。
          className="flex h-7 w-[60px] shrink-0 items-center justify-center gap-1 whitespace-nowrap rounded-md py-0 pl-2 pr-2.5 text-[16px] leading-6 font-medium text-[#FAFAFA] hover:bg-white/10"
        >
          <Share2 size={16} className="shrink-0" />
          <span className="shrink-0 text-[12px] leading-5">分享</span>
        </button>
        </div>
        {shareOpen ? (
          <JimengSharePanel
            canvasUrl={CANVAS_URL}
            onClose={() => setShareOpen(false)}
          />
        ) : null}

        <div className="jimeng-chrome-pill relative flex h-9 shrink-0 items-center p-1">
          <button
            type="button"
            aria-label="更多"
            data-testid="canvas-more-trigger"
            onClick={() => {
              closeAll();
              setMoreOpen((v) => !v);
            }}
            className="flex size-7 items-center justify-center rounded-md text-[#FAFAFA] hover:bg-white/10"
          >
            <MoreHorizontal size={16} />
          </button>
          {moreOpen ? (
            <JimengMoreMenu
              onClose={() => setMoreOpen(false)}
              onOpenProjectInfo={() => setProjectInfoOpen(true)}
              onCopyProject={copyProject}
            />
          ) : null}
        </div>

        {/* SOURCE_FACT (batch 795 复查): 积分入口与用户菜单**同处一个 163×36
            药丸** [1505,12]，两者自身背景透明（积分 111×28@1509，头像 28×28@1636，
            药丸内 gap 16，右内边距 4 → 头像右缘 1664 而非 1668）。 */}
        <div className="jimeng-chrome-pill flex h-9 shrink-0 items-center gap-4 p-1">
        <button
          type="button"
          aria-label={`Credits: ${CREDITS} · 基础会员`}
          data-testid="canvas-commerce-entry"
          onClick={() => setMemberOpen(true)}
          className="flex h-7 shrink-0 items-center gap-1 whitespace-nowrap rounded-md px-2 py-1 hover:bg-white/10"
        >
          <VipDiamond size={12} />
          <span className="text-[12px]/5 font-medium text-[#009EFA]">
            {CREDITS}
          </span>
          <span className="text-[13px] leading-5 text-white/90">基础会员</span>
        </button>

        {/* 头像 (mock)；点击展开与帮助菜单同构的账号菜单 (SOURCE_FACT batch 22)。
            Batch 96: 源站该钮 aria 为 用户菜单，且展开的是个人资料弹层
            (西卡文案馆/积分详情，对齐留待后续批次)；帮助/? 钮已从源站
            顶栏移除，故本栏不再渲染 帮助。 */}
        <div className="relative shrink-0">
          <button
            type="button"
            aria-label="用户菜单"
            data-testid="canvas-user-menu-trigger"
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
      {projectInfoOpen ? (
        <JimengProjectInfoModal onClose={() => setProjectInfoOpen(false)} />
      ) : null}
      {memberOpen ? <JimengMemberModal onClose={() => setMemberOpen(false)} /> : null}
      {shortcutsOpen ? (
        <JimengShortcutsPanel onClose={() => setShortcutsOpen(false)} />
      ) : null}
    </>
  );
}
