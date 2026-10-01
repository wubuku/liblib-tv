"use client";

import { Fragment, useEffect, useRef } from "react";
import { useReactFlow } from "@xyflow/react";

import {
  MENU_PANEL_BG,
  MENU_PANEL_CLASS,
  MenuItem,
  MenuSeparator,
} from "@/components/jimeng/jimengMenuChrome";
import { useJimengStore } from "@/store/jimengStore";

/** 源站给「缩放至选中项」配的禁用提示文案（藏在 1×1 隐藏 span 里）。 */
const DISABLED_TITLE = "请先选择至少一个画布元素";

/** 批 828：源站的缩放菜单用 aria-labelledby 指向缩放触发器，复刻照此给个稳定 id。 */
export const ZOOM_MENU_TRIGGER_ID = "jimeng-zoom-menu-trigger";

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

  // MenuItem 只负责调 onSelect，关闭菜单由各行自己收尾（此前是按钮 onClick 里
  // 统一 onClose，抽出 MenuItem 后必须显式带上，否则放大/缩小/适配画布点了不关）
  const rows: {
    label: string;
    shortcut?: string;
    disabled?: boolean;
    run: () => void;
  }[] = [
    { label: "放大视图", shortcut: "⌘ +", run: () => { void zoomIn({ duration: 200 }); onClose(); } },
    { label: "缩小视图", shortcut: "⌘ -", run: () => { void zoomOut({ duration: 200 }); onClose(); } },
    { label: "适配画布", shortcut: "⇧ 1", run: () => { void fitView({ duration: 300 }); onClose(); } },
    {
      label: "缩放至选中项",
      shortcut: "⇧ 2",
      disabled: !selectedNodeId,
      run: () => { void fitView({ duration: 300, maxZoom: 1 }); onClose(); },
    },
    // setZoom 内部已收尾
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
      // 批 828：源站实测 @1680×826 —— `data-testid="canvas-zoom-menu"`，
      // aria-label 为空但用 **aria-labelledby 指向缩放触发器**（与账号菜单同型），
      // 200×292 static，七项与本复刻逐字一致。几何本来就是对的，缺的只是
      // 可指名 + 可定位，于是它对任何按 role 枚举的普查都是隐形的。
      aria-labelledby={ZOOM_MENU_TRIGGER_ID}
      data-testid="canvas-zoom-menu"
      // 外观收口到 jimengMenuChrome（batch 814）：与画布右键菜单同一套 ——
      // 200 宽、padding 4、行高 36、行间隙 4。此前本文件自带一份，
      // 右键菜单又自带一份，两份已经开始漂移（右键那份还是 192/p-2/行高 44）。
      className={`absolute bottom-[calc(100%+8px)] left-0 ${MENU_PANEL_CLASS}`}
      style={{ background: MENU_PANEL_BG }}
    >
      {rows.map((row, i) => (
        // 必须是「分隔线 + 项」**并存**。曾写成 `has(i) ? <Separator/> : <MenuItem/>`
        // 的二选一，结果第 5 项（缩放至50%）被分隔线顶掉，菜单只剩 6 项 ——
        // 是 811 的验收脚本点不到「缩放至50%」才暴露的。
        <Fragment key={row.label}>
          {dividerBefore.has(i) ? <MenuSeparator /> : null}
          <MenuItem
            label={row.label}
            shortcut={row.shortcut}
            disabled={row.disabled}
            disabledReason={row.disabled ? DISABLED_TITLE : undefined}
            onSelect={row.run}
          />
        </Fragment>
      ))}
    </div>
  );
}
