"use client";

import { useEffect, useMemo, useState } from "react";
import { AudioLines, ChevronRight, Image as ImageIcon, Play, SquareUser } from "lucide-react";
import type { LucideIcon } from "lucide-react";

import { useJimengStore } from "@/store/jimengStore";

/**
 * @ 提及面板 —— 「可能@的内容」（Batch 1032-②b-3）。
 *
 * ⭐⭐⭐⭐⭐ **源站取证**（不是设计，是实测）：
 *   手册 `docs/user-manual/jimeng-canvas/20-reference.md` §「参考输入的两条入口
 *   + `@` 提及面板（2026-10-01 批次 33 全量复测）」逐字记着：
 *
 *   | 元素 | 实测 |
 *   |---|---|
 *   | `[data-testid="generation-mention-panel"]` | 240×244，**渲染在 form 内部** |
 *   | `[role="listbox"]` | aria 逐字 **`可能@的内容`** |
 *   | `[role="group"]` | 232×236 |
 *   | 顶部「添加参考」行 | div 232×32，**分组标题**（无 role、不可点） |
 *   | 4 个 `role="option"` | 各 232×48：`主体` / `图片` / `视频` / `音频` |
 *   | 二级子菜单 | `[data-testid="generation-mention-submenu"]` 240×76（空）/ 240×56（1 条） |
 *   | 二级空态 | 逐字 **`暂无相关节点`**（`role="status"` 232×68，0 svg） |
 *
 *   🔴 **两级定步选择器，不是搜索框**：先点类别（主体/图片/视频/音频），
 *   再在右侧二级菜单点具体节点。手册 90-troubleshooting §「在「@」面板里打了字，
 *   列表反而整个不见了」明确写：**面板打开时键入「主」→ 面板立即关闭、
 *   占位符消失、提示词变字面量 `@主`；列表既不收窄也不选中。**
 *   ⇒ ⇒ 本组件**不做输入过滤**，照抄这个行为。
 *
 *   🔴 **只列有可用资源的节点**（批次 114 查明）：空节点被排除。
 *   ⇒ ⇒ 本组件的候选集按「该类型**有资源**」过滤，与 114 一致。
 *
 *   ⭐ **类别集合随宿主节点类型变化**（批次 34 四类对照）：
 *   视频 4 项（主体/图片/视频/音频）｜图片 2 项（主体/图片）｜音频 3 项（主体/图片/音频）
 *   ⇒ ⇒ 本组件按 `hostKind` 决定列出哪几类，不硬编 4 类。
 *
 * ⭐ **为什么复刻侧用 chip 而不是结构化 mention**：
 *   源站打开面板时往提示词写 `@` + 占位符（`<span data-slot=
 *   "generation-prompt-mention-placeholder">搜索主体、图片、视频</span>`），
 *   选中后变成一个**引用 chip**（手册批次 792：48×48 缩略图 + 名称 + Remove 角标）。
 *   本组件的产出形态是 **chip 列表**（由调用方渲染），与复刻侧既有的
 *   `JimengGenPanel` 的引用 chip 行同一套形态。
 */

/** 宿主节点类型 ⇒ 面板列出哪几类（SOURCE_FACT 批次 34 四类对照） */
export type MentionHostKind = "video" | "image" | "audio";

/** 四类候选的键 */
export type MentionCategory = "主体" | "图片" | "视频" | "音频";

const CATEGORIES_BY_HOST: Record<MentionHostKind, MentionCategory[]> = {
  // 批次 34：视频 4 项
  video: ["主体", "图片", "视频", "音频"],
  // 批次 34：图片 2 项（图片引不了视频/音频）
  image: ["主体", "图片"],
  // 批次 34：音频 3 项（无「视频」）
  audio: ["主体", "图片", "音频"],
};

const CATEGORY_ICONS: Record<MentionCategory, LucideIcon> = {
  主体: SquareUser,
  图片: ImageIcon,
  视频: Play,
  音频: AudioLines,
};

/** 一条候选（宿主面板按 nodeId 消费） */
export interface MentionCandidate {
  id: string;
  /** 展示名 */
  name: string;
  /** 归到哪一类 */
  category: MentionCategory;
  /** 缩略图（可空） */
  poster?: string;
  /** 视频时长徽标（秒） */
  duration?: number;
}

export function formatMentionDuration(seconds: number): string {
  const s = Math.max(0, Math.floor(seconds));
  const mm = Math.floor(s / 60);
  const ss = s % 60;
  return `${mm}:${ss.toString().padStart(2, "0")}`;
}

/**
 * 候选集：**只列有可用资源的节点**（批次 114）。
 *
 * ⭐ 复刻侧的「有资源」判据（按节点类型分别定义，因为源站的资源形态各不相同）：
 * · 主体  → `imported` 非空（主体节点内已导入的素材）
 * · 图片  → 有 `poster`（图片节点有画面）
 * · 视频  → `hasMedia` 为真
 * · 音频  → `source === "generated"`（有产出的音频才算有资源）
 *
 * ⚠️ 主体这一条是 **CLONE_DECISION**：源站的「主体」是账号级主体库里的条目
 * （手册批次 114：画布上该类型节点 0 个 ⇒ 二级子菜单逐字「暂无相关节点」），
 * 复刻侧的主体是**画布上的主体节点** ⇒ 判据只能自己定。
 * ⇒ 记在这里，别让后人以为这是源站实测。
 */
export function collectMentionCandidates(
  hostKind: MentionHostKind,
): MentionCandidate[] {
  const nodes = useJimengStore.getState().nodes;
  const categories = CATEGORIES_BY_HOST[hostKind];
  const out: MentionCandidate[] = [];
  for (const n of nodes) {
    const data = n.data as Record<string, unknown>;
    const title = typeof data.title === "string" ? data.title : n.id;
    if (n.type === "subject") {
      if (!categories.includes("主体")) continue;
      const imported = Array.isArray(data.imported) ? (data.imported as string[]) : [];
      if (imported.length === 0) continue;
      out.push({ id: n.id, name: title, category: "主体" });
      continue;
    }
    if (n.type === "image") {
      if (!categories.includes("图片")) continue;
      if (typeof data.poster !== "string" || !data.poster) continue;
      out.push({
        id: n.id,
        name: title,
        category: "图片",
        poster: data.poster as string,
      });
      continue;
    }
    if (n.type === "video") {
      if (!categories.includes("视频")) continue;
      if (data.hasMedia !== true) continue;
      out.push({
        id: n.id,
        name: title,
        category: "视频",
        poster: typeof data.poster === "string" ? data.poster : undefined,
        duration: typeof data.duration === "number" ? data.duration : undefined,
      });
      continue;
    }
    if (n.type === "audio") {
      if (!categories.includes("音频")) continue;
      if (data.source !== "generated") continue;
      out.push({
        id: n.id,
        name: title,
        category: "音频",
        duration: typeof data.duration === "number" ? data.duration : undefined,
      });
    }
  }
  return out;
}

/**
 * 面板本体。
 *
 * @param hostKind  宿主节点类型 ⇒ 决定列出哪几类（批次 34）
 * @param onPick    选中一条候选（宿主面板据此插 chip）
 * @param onClose   关闭
 */
export function JimengMentionPanel({
  hostKind,
  onPick,
  onClose,
  anchorClassName,
}: {
  hostKind: MentionHostKind;
  onPick: (candidate: MentionCandidate) => void;
  onClose: () => void;
  /** 锚点容器的类名（决定浮层贴哪一侧） */
  anchorClassName?: string;
}) {
  const [category, setCategory] = useState<MentionCategory | null>(null);
  // ⭐ 候选集是**读 store 的快照**：面板打开时取一次即可（源站也是打开时求值）。
  const candidates = useMemo(() => collectMentionCandidates(hostKind), [hostKind]);
  const categories = CATEGORIES_BY_HOST[hostKind];
  const inCategory = category
    ? candidates.filter((c) => c.category === category)
    : [];

  // ⭐ Esc 关闭面板（SOURCE_FACT 手册 20-reference「退出路径」表：
  //   `Esc` → 面板关、**提示词保留**）⇒ 面板自己收 Esc，不让它冒泡去关整个编辑态。
  useEffect(() => {
    if (!onClose) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.stopPropagation();
        onClose();
      }
    };
    window.addEventListener("keydown", onKey, true);
    return () => window.removeEventListener("keydown", onKey, true);
  }, [onClose]);

  return (
    <div
      className={
        anchorClassName ??
        "absolute bottom-[calc(100%+8px)] left-0 z-[140] w-[240px] rounded-[10px] border border-white/[0.06] p-1.5"
      }
      style={{ background: "rgb(38,38,38)" }}
      role="listbox"
      aria-label="可能@的内容"
      data-testid="mention-panel"
    >
      {/* 一级：类别列表（批次 33：顶部「添加参考」行是**分组标题**，无 role、不可点） */}
      <div className="min-w-0" data-testid="mention-primary">
        <div className="px-2.5 pb-1 pt-1.5 text-[12px] text-white/40">添加参考</div>
        {categories.map((cat) => {
          const Icon = CATEGORY_ICONS[cat];
          return (
            <button
              key={cat}
              type="button"
              role="option"
              aria-selected={category === cat}
              aria-label={`可能@的内容: ${cat}`}
              onClick={() => setCategory((cur) => (cur === cat ? null : cat))}
              className={`flex h-12 w-full items-center gap-2 rounded-lg px-2.5 text-left text-[13px] text-white/90 hover:bg-white/10 ${
                category === cat ? "bg-white/[0.10]" : ""
              }`}
            >
              <Icon size={15} className="shrink-0 text-white/70" />
              <span className="min-w-0 flex-1 truncate">{cat}</span>
              <ChevronRight size={14} className="shrink-0 text-white/40" />
            </button>
          );
        })}
      </div>

      {/* 二级：具体节点（批次 33：`generation-mention-submenu` **紧贴一级右缘，
          间隙 4px**；空态逐字「暂无相关节点」，role=status）。
          ⭐⭐⭐ **必须是绝对定位**：若把它放进一级的 flex 流里 ⇒ ⇒ 一级会被
          压成 20px 宽（`flex-1` 被固定宽的兄弟挤掉）⇒ ⇒ 而二级**盖在**一级上面
          ⇒ ⇒ 「视频」那一行**点不动**（实测 `elementFromPoint` 命中的是二级容器）。
          ⇒ ⇒ 这不是门的判据错，是**真缺陷**：源站的二级本来就是**浮在右侧**的。 */}
      {category ? (
        <div
          className="absolute left-[calc(100%+4px)] top-0 flex w-[240px] flex-col rounded-[10px] border border-white/[0.06] p-1.5"
          style={{ background: "rgb(38,38,38)" }}
          role="listbox"
          aria-label={category}
          data-testid="mention-submenu"
        >
          {inCategory.length > 0 ? (
            inCategory.map((c) => (
              <button
                key={c.id}
                type="button"
                role="option"
                aria-selected={false}
                aria-label={`可能@的内容: ${c.name}`}
                onClick={() => onPick(c)}
                className="flex h-12 w-full items-center gap-2 rounded-lg px-1.5 text-left hover:bg-white/10"
              >
                {c.poster ? (
                  // eslint-disable-next-line @next/next/no-img-element -- 本地 data URI mock 缩略图
                  <img
                    src={c.poster}
                    alt=""
                    className="size-8 shrink-0 rounded-md object-cover"
                  />
                ) : (
                  <span className="flex size-8 shrink-0 items-center justify-center rounded-md bg-white/[0.08] text-white/55">
                    {c.category === "图片" ? (
                      <ImageIcon size={14} />
                    ) : c.category === "视频" ? (
                      <Play size={14} />
                    ) : c.category === "音频" ? (
                      <AudioLines size={14} />
                    ) : (
                      <SquareUser size={14} />
                    )}
                  </span>
                )}
                <span className="min-w-0 flex-1 truncate text-[13px] text-white/90">
                  {c.name}
                </span>
                {c.category === "视频" && typeof c.duration === "number" ? (
                  <span className="shrink-0 rounded bg-black/70 px-1 text-[9px] leading-[14px] text-white/90">
                    {formatMentionDuration(c.duration)}
                  </span>
                ) : null}
              </button>
            ))
          ) : (
            <div
              role="status"
              className="flex h-16 items-center justify-center text-[13px] text-white/45"
            >
              暂无相关节点
            </div>
          )}
        </div>
      ) : null}
    </div>
  );
}

/** 给宿主面板用的闭包：把「选中候选」接到「插 chip」上。 */
export function useMentionPicker(
  hostKind: MentionHostKind,
  onPick: (candidate: MentionCandidate) => void,
) {
  const [open, setOpen] = useState(false);
  const setMentionPanelOpen = useJimengStore((s) => s.setMentionPanelOpen);
  // ⭐⭐⭐ 把「面板开着」这件事**同步到 store** ⇒ workspace 的 Esc 分支
  //   才知道「Esc 只关面板、不退出编辑态」（源站退出路径表：Esc → 面板关、
  //   提示词保留）。详见 store 里 `mentionPanelOpen` 的注释。
  useEffect(() => {
    setMentionPanelOpen(open);
    return () => setMentionPanelOpen(false);
  }, [open, setMentionPanelOpen]);
  return {
    open,
    toggle: () => setOpen((v) => !v),
    close: () => setOpen(false),
    panel: open ? (
      <JimengMentionPanel
        hostKind={hostKind}
        onPick={(c) => {
          onPick(c);
          setOpen(false);
        }}
        onClose={() => setOpen(false)}
      />
    ) : null,
  };
}
