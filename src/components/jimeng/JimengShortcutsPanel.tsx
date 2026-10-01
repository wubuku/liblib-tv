"use client";

import { useEffect, useRef } from "react";
import { X } from "lucide-react";

/**
 * 快捷键面板 (Batch 18 建；Batch 815 按源站逐字订正)。
 *
 * 证据 (SOURCE_FACT，batch 815 取证脚本逐字抓取，见
 * docs/research/jimeng-canvas/README.md §24)：
 *   面板 aside[aria-label="shortcut-panel"] 240×934 @ viewport(1680,1050) 的 [1428,56]，
 *   bg rgb(38,38,38)、圆角 16px、padding 0；滚动区 scrollH 1300 / clientH 878。
 *   分区四段：**通用操作 / 视图 / 时间线 / 文本编辑**，合计 28 行
 *   （通用 8 + 视图 6 + 时间线 4 + 文本编辑 10）。
 *   Batch 18 记的「时间线分区源站被截断 BLOCKED_BY_FIXTURE」已解除，
 *   文本编辑分区当时整段缺失。
 *   通用操作八行：打开/关闭 Agent ⌘/、撤销 ⌘Z、还原 ⌘⇧Z|⌘Y、移动工具 V、
 *   **预览视图 F**（不是 Batch 18 写的「全屏」）、**宫格视图 G**（Batch 18 漏行）、
 *   创建编组 ⌘G、取消编组 ⌘⇧G。
 *   一行两键的「还原」「适配画布」在源站是**两个 chip + 一条竖分隔线**同行，
 *   不是字面 "|"；此处按源站拆成两个 chip。
 *
 * 关于 V / F / G 三项 (CLONE_DECISION，均为**展示项**)：
 *   batch 815 对源站逐项做了状态指纹比对（画布背景、光标、testid 集合、视口
 *   transform），按 G / F / V 三次指纹**全部零变化**，二次按压亦无变化 —— 即源站
 *   自己也测不到可见响应。复刻不擅自实现源站测不到的行为，也不在面板上伪称可用；
 *   面板文案按源站逐字照抄，差异如实记在此处。
 *   编组 ⌘G / ⌘⇧G 早已接上 store.groupSelected / ungroupSelected，
 *   Batch 18 注释「编组…为展示项」已过时，本次删除。
 */
type Row = { label: string; keys: string[] };
const SECTIONS: { title: string; rows: Row[] }[] = [
  {
    title: "通用操作",
    rows: [
      { label: "打开/关闭 Agent", keys: ["⌘ /"] },
      { label: "撤销", keys: ["⌘ Z"] },
      { label: "还原", keys: ["⌘ ⇧ Z", "⌘ Y"] },
      { label: "移动工具", keys: ["V"] },
      { label: "预览视图", keys: ["F"] },
      { label: "宫格视图", keys: ["G"] },
      { label: "创建编组", keys: ["⌘ G"] },
      { label: "取消编组", keys: ["⌘ ⇧ G"] },
    ],
  },
  {
    title: "视图",
    rows: [
      { label: "放大视图", keys: ["⌘ +"] },
      { label: "缩小视图", keys: ["⌘ -"] },
      { label: "适配画布", keys: ["⇧ 1", "⌘ 0"] },
      { label: "缩放至 100%", keys: ["⌘ 1"] },
      { label: "缩放至选中项", keys: ["⇧ 2"] },
      { label: "缩放画布", keys: ["⌘ scroll"] },
    ],
  },
  {
    title: "时间线",
    rows: [
      { label: "分割片段", keys: ["⌘ B"] },
      { label: "向左裁剪", keys: ["Q"] },
      { label: "向右裁剪", keys: ["W"] },
      { label: "缩放时间线", keys: ["⌘ scroll"] },
    ],
  },
  {
    title: "文本编辑",
    rows: [
      { label: "加粗", keys: ["⌘ B"] },
      { label: "倾斜", keys: ["⌘ I"] },
      { label: "下划线", keys: ["⌘ U"] },
      { label: "删除线", keys: ["⌘ ⇧ X"] },
      { label: "一级标题", keys: ["⌘ ⌥ 1"] },
      { label: "二级标题", keys: ["⌘ ⌥ 2"] },
      { label: "三级标题", keys: ["⌘ ⌥ 3"] },
      { label: "普通文本", keys: ["⌘ ⌥ 0"] },
      { label: "无序列表", keys: ["⌘ ⇧ 8"] },
      { label: "有序列表", keys: ["⌘ ⇧ 7"] },
    ],
  },
];

export function JimengShortcutsPanel({ onClose }: { onClose: () => void }) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    const onDown = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose();
    };
        // 捕获阶段（batch 794 实测踩坑）：JimengFlow 的全局 Escape 监听注册更早，
        // 会先触发同步重渲染；重渲染使本 effect 清理并重新注册监听，
        // removeEventListener 会把该 listener 标记为 removed，浏览器在**同一次
        // 事件派发中**跳过它 → 冒泡监听收不到 Escape，浮层关不掉。
    window.addEventListener("keydown", onKey, true);
    window.addEventListener("mousedown", onDown, true);
    return () => {
      window.removeEventListener("keydown", onKey, true);
      window.removeEventListener("mousedown", onDown, true);
    };
  }, [onClose]);

  return (
    <div
      ref={ref}
      role="dialog"
      aria-label="快捷键"
      /* Batch 823 SOURCE_FACT 缺口：同 `topbar-history-menu` ——
         批 816 的锚点收口漏了这两块，它们只有可访问名、没有 testid，
         结果是 batch 822 的 fixed 普查到不了这一态。
         本块是 `fixed right-3 top-14`，正是最该被普查盯住的那类浮层。 */
      data-testid="topbar-shortcuts-panel"
      // 源站 240 宽 @[1428,56]（right=12、top=56、bottom 余 60）→ 240×934
      className="fixed right-3 top-14 z-[220] flex max-h-[calc(100vh-116px)] w-[240px] flex-col rounded-2xl"
      style={{ background: "rgb(38,38,38)" }}
    >
      <div className="flex h-14 shrink-0 items-center justify-between px-4">
        <p className="text-[14px] font-medium text-white">快捷键</p>
        <button
          type="button"
          aria-label="关闭快捷键面板"
          onClick={onClose}
          className="flex size-8 items-center justify-center rounded-lg text-white/60 hover:bg-white/10 hover:text-white"
        >
          <X size={14} />
        </button>
      </div>
      {/* 源站面板 padding 0，行相对面板左右各内缩 4px */}
      <div className="flex-1 overflow-y-auto px-1">
        {SECTIONS.map((section) => (
          <div key={section.title}>
            <p className="flex h-8 items-center text-[12px] text-white/35">
              {section.title}
            </p>
            {section.rows.map((row) => (
              <div
                key={row.label}
                className="mb-1 flex h-9 items-center justify-between rounded-md px-3 hover:bg-white/[0.06]"
              >
                <span className="text-[13px] text-white">{row.label}</span>
                <span className="flex items-center gap-2">
                  {row.keys.map((k, i) => (
                    <span key={k} className="flex items-center gap-2">
                      {/* 源站两键之间是一条竖分隔线，不是字面 "|" */}
                      {i > 0 ? (
                        <span aria-hidden className="h-3 w-px bg-white/25" />
                      ) : null}
                      <span className="text-[13px] text-white/60">{k}</span>
                    </span>
                  ))}
                </span>
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
