"use client";

import { Fragment, useEffect, useRef } from "react";
import { useReactFlow } from "@xyflow/react";

import { useJimengStore } from "@/store/jimengStore";

/**
 * 缩放百分比菜单 (Batch 7)。
 *
 * SOURCE_FACT batch 811 (2026-10-03 @1512×950 实测，扁平化菜单子树逐元素量得):
 * 菜单 200×292 @[16,599]、padding **4px**、radius 12、bg rgb(38,38,38)。
 * 共 **7 项**（此前复刻只做了 5 项，且文件头曾断言「放大/缩小视图 已不在源站菜单中」
 * —— batch 811 实测证明**该断言错误**，两枚都在，且排在最前）:
 *   放大视图 ⌘ + ｜缩小视图 ⌘ - ｜适配画布 ⇧ 1 ｜缩放至选中项 ⇧ 2
 *   ｜role=separator｜缩放至50% ｜缩放至100% ⌘ 1 ｜缩放至200%
 * 竖向账：4(上边距) + 36 + 4 + 36 + 4 + 36 + 4 + 36 + 4(分隔线) + 36 + 4 + 36 + 4 + 36
 *       + 4(下边距) = 292 ✓ 行高 **36**（此前 40）、行距 4。
 * 横竖细节：行 padding 9px 12px、圆角 8、左右各 12px 内缩 → 行宽 192 @x=4；
 * 文案 13px/20px **纯白 rgb(255,255,255)**（此前 white/85）；
 * 快捷键 13px/20px **white/60 且右缘对齐到 180**（此前 12px/white 45、px 2.5）；
 * hover 底色 **white/8**（此前 white/10）；
 * 分隔线 = margin 0 12px + 1px 线，1px 伪元素 top:2px，**高 4px**，
 * 颜色实测 rgb(47,47,47) = white/4（在 rgb(38,38,38) 上叠加得 46.7）；
 * 「缩放至选中项」无选中时禁用，且源站在其上挂了 tooltip 文案
 * 「请先选择至少一个画布元素」（藏在 1×1 的 span 里，1.6s 内未能截到浮层，
 * 故复刻用原生 title 兜底，不臆造浮层几何）。
 *
 * 功能接 xyflow: zoomIn/zoomOut/fitView/setViewport，1.2 步长与源站实测一致
 * （50 →⌘-→ 83.3、83.3 →⌘+→ 100）。
 *
 * OPEN_QUESTION 811-a：源站**没有** ⌘0 / ⇧1 绑定（先把缩放设到 50% 再按，两次
 * 均无变化，而同条件下 ⌘1 / ⌘- / ⌘+ 全部生效），但菜单上仍印着 ⇧1 / ⇧2，
 * 且源站已无快捷键面板入口（按钮普查 0 命中）。复刻侧的 Batch 18/21 绑定
 * 据称来自那个已消失的面板。此批**保留**复刻侧绑定（多一个可用快捷键，
 * 优于照抄源站的无响应），差异如实记账。
 */
export function JimengZoomMenu({ onClose }: { onClose: () => void }) {
  const ref = useRef<HTMLDivElement>(null);
  const selectedNodeId = useJimengStore((s) => s.selectedNodeId);
  const {
    fitView,
    zoomIn,
    zoomOut,
    setViewport,
    getViewport,
  } = useReactFlow();

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    const onDown = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose();
    };
    // 捕获阶段（batch 794 实测）：冒泡监听会被工作区先触发的同步重渲染跳过。
    window.addEventListener("keydown", onKey, true);
    window.addEventListener("mousedown", onDown, true);
    return () => {
      window.removeEventListener("keydown", onKey, true);
      window.removeEventListener("mousedown", onDown, true);
    };
  }, [onClose]);

  const setZoom = (zoom: number) => {
    const vp = getViewport();
    // 以视口中心为缩放中心
    const el = document.querySelector(".jimeng-canvas");
    const w = el ? el.clientWidth / 2 : 0;
    const h = el ? el.clientHeight / 2 : 0;
    setViewport({ x: w - (w - vp.x) * (zoom / vp.zoom), y: h - (h - vp.y) * (zoom / vp.zoom), zoom });
    onClose();
  };

  const rows: {
    label: string;
    shortcut?: string;
    disabled?: boolean;
    title?: string;
    run: () => void;
  }[] = [
    { label: "放大视图", shortcut: "⌘ +", run: () => void zoomIn({ duration: 200 }) },
    { label: "缩小视图", shortcut: "⌘ -", run: () => void zoomOut({ duration: 200 }) },
    { label: "适配画布", shortcut: "⇧ 1", run: () => void fitView({ duration: 300 }) },
    {
      label: "缩放至选中项",
      shortcut: "⇧ 2",
      disabled: !selectedNodeId,
      title: "请先选择至少一个画布元素",
      run: () => void fitView({ duration: 300, maxZoom: 1 }),
    },
    { label: "缩放至50%", run: () => setZoom(0.5) },
    { label: "缩放至100%", shortcut: "⌘ 1", run: () => setZoom(1) },
    { label: "缩放至200%", run: () => setZoom(2) },
  ];

  // 分隔线在第 4 项（缩放至选中项）之后 —— SOURCE_FACT batch 811。
  const dividerBefore = new Set([4]);

  return (
    <div
      ref={ref}
      role="menu"
      // padding 4px（此前 8px）、行高 36（此前 40）、**flex 列 + gap-1**（此前行间 0 间隙）。
      // 竖向账：8(上下边距) + 7×36 + 4(分隔线) + 7×4(间隙) = 292 ✓（此前 225）
      className="absolute bottom-[calc(100%+8px)] left-0 flex w-[200px] flex-col gap-1 rounded-xl p-1"
      style={{ background: "rgb(38,38,38)" }}
    >
      {rows.map((row, i) => (
        <Fragment key={row.label}>
          {dividerBefore.has(i) ? (
            // 盒高 4px（h-1），1px 线在盒内垂直居中 → 落在盒顶 +2px，
            // 与源站 `::before { top:2px }` 等价。左右 margin 12 → 宽 168。
            <div role="separator" className="mx-3 flex h-1 items-center">
              <div className="h-px w-full bg-white/[0.04]" />
            </div>
          ) : null}
          <button
            type="button"
            role="menuitem"
            disabled={row.disabled}
            title={row.title}
            onClick={() => {
              if (row.disabled) return;
              row.run();
              onClose();
            }}
            // h-9 = 36px、px-3 = 12px、rounded-lg = 8px；
            // 文案纯白、快捷键 13px white/60、hover white/8 —— 均按 batch 811 实测
            className={`flex h-9 w-full shrink-0 items-center justify-between rounded-lg px-3 text-[13px] leading-5 ${
              row.disabled
                ? "cursor-default text-white/30"
                : "text-white hover:bg-white/[0.08]"
            }`}
          >
            {/*
              文案与快捷键都各自是 span（源站 DOM 实测如此），且**快捷键 span 始终渲染**
              —— 无快捷键时它是一个 0 宽的空 span，右缘仍停在 180。
            */}
            <span>{row.label}</span>
            <span className="text-white/60">{row.shortcut ?? ""}</span>
          </button>
        </Fragment>
      ))}
    </div>
  );
}
