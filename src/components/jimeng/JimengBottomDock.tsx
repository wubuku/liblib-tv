"use client";

import { useState } from "react";
import { Map, MousePointer2, Spline } from "lucide-react";

import { JimengZoomMenu, ZOOM_MENU_TRIGGER_ID } from "@/components/jimeng/JimengZoomMenu";
import { useJimengStore } from "@/store/jimengStore";

/**
 * 左下角画布导航 dock — 164×36 (SOURCE_FACT)。
 * Batch 91 (SOURCE_FACT 91-minimap.json): dock 演进为 [选择工具][小地图] |
 * 缩放百分比 (布局 已并入多选工具条、同步 由自动保存取代——均站点演进)；
 * 小地图 点击切换左上 MiniMap 面板 (164×154 rgb(13,13,13) r8，内
 * 156×114 white/8% r6)。
 * Batch 796 (SOURCE_FACT 1680×826 实测): 壳体 @[12,774] 164×36、bg rgb(13,13,13)、
 * radius 8、padding 4、gap 4 —— 与 rail 一样贴 **12px** 左缘（此前误为 16px，
 * 导致三个图标钮与缩放钮整体右移 4px）。缩放钮 aria-label 逐字对齐源站
 * "Zoom options, {n}%"（含实时百分比），故另给 data-testid 供稳定选择。
 */
export function JimengBottomDock() {
  const zoomPercent = useJimengStore((s) => s.zoomPercent);
  const toolActive = useJimengStore((s) => s.toolActive);
  const setToolActive = useJimengStore((s) => s.setToolActive);
  const minimapOpen = useJimengStore((s) => s.minimapOpen);
  const setMinimapOpen = useJimengStore((s) => s.setMinimapOpen);
  const edgesVisible = useJimengStore((s) => s.edgesVisible);
  const setEdgesVisible = useJimengStore((s) => s.setEdgesVisible);
  const [zoomMenuOpen, setZoomMenuOpen] = useState(false);

  return (
    <div className="absolute bottom-4 left-3 z-30">
      <div className="jimeng-bottom-dock relative flex h-9 w-[164px] items-center gap-1 p-1">
        <button
          type="button"
          aria-label="选择工具"
          // Batch 816 SOURCE_FACT: testid `canvas-pointer-tool-toggle`
          data-testid="canvas-pointer-tool-toggle"
          onClick={() => setToolActive("select")}
          // Batch 810 (SOURCE_FACT 2026-10-03 重测 @1512): 三枚 28×28 图标钮
          // 圆角 **8px**（此前 rounded-md = 6px）；选中底色 **white/8**
          // （此前 white/10）。缩放钮源站实测同为 6px，不动。
          className={`flex size-7 items-center justify-center rounded-lg ${
            toolActive === "select"
              ? "bg-white/[0.08] text-white"
              : "text-white/85 hover:bg-white/[0.08]"
          }`}
        >
          <MousePointer2 size={16} />
        </button>
        <button
          type="button"
          aria-label="小地图"
          data-testid="canvas-display-toggle-minimap"
          onClick={() => setMinimapOpen(!minimapOpen)}
          className={`flex size-7 items-center justify-center rounded-lg ${
            minimapOpen ? "bg-white/[0.08] text-white" : "text-white/85 hover:bg-white/[0.08]"
          }`}
        >
          <Map size={16} />
        </button>
        {/* Batch 93 (SOURCE_FACT canvas-dock-lines): 连线显隐开关 */}
        <button
          type="button"
          aria-label="显示连线"
          data-testid="canvas-display-toggle-connections"
          onClick={() => setEdgesVisible(!edgesVisible)}
          className={`flex size-7 items-center justify-center rounded-lg ${
            edgesVisible ? "bg-white/[0.08] text-white" : "text-white/85 hover:bg-white/[0.08]"
          }`}
        >
          <Spline size={16} />
        </button>
        <span className="mx-1 h-3 w-px shrink-0 bg-white/10" />
        <button
          type="button"
          // Batch 796 (SOURCE_FACT): 无障碍名逐字 = "Zoom options, {n}%"
          aria-label={`Zoom options, ${zoomPercent}%`}
          // 批 828：源站的缩放菜单用 aria-labelledby 指向这个触发器，复刻照此接线
          id={ZOOM_MENU_TRIGGER_ID}
          data-testid="canvas-zoom-percent"
          onClick={() => setZoomMenuOpen((v) => !v)}
          className="flex h-7 w-12 items-center justify-center rounded-md text-[13px] text-white/85 hover:bg-white/10"
        >
          {zoomPercent}%
        </button>
        {zoomMenuOpen ? <JimengZoomMenu onClose={() => setZoomMenuOpen(false)} /> : null}
      </div>
    </div>
  );
}
