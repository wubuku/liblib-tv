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
  const toggleToolActive = useJimengStore((s) => s.toggleToolActive);
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
          /* Batch 837 SOURCE_FACT（2026-10-04 dock 普查实测）：源站这枚是
             **二态**开关 —— 初始 `aria-pressed="false"`，点一下变 **true**。
             复刻此前 onClick 是 `setToolActive("select")`（强制置位），
             于是「已经是 select 时点它」什么都不会发生；本批改成与 V 键
             共用 toggleToolActive。
             ⚠ 取值方向**故意与源站相反**并记档（台账 §52 的 837-a）：源站
             默认 false、点一下 true，这暗示它的第二态才是「被按下的那个」，
             语义无法从 aria 推出。复刻按**自己的**状态模型给
             `toolActive === "select"` —— 宁可让序列反一次，也不发一个
             语义颠倒的 aria-pressed（读屏会念「选择工具，已按下」而实际在
             移动模式）。 */
          aria-pressed={toolActive === "select"}
          onClick={toggleToolActive}
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
          /* Batch 837 SOURCE_FACT：源站带 aria-pressed，初值 **false**（与复刻
             store 的 minimapOpen=false 一致）。此前复刻一个都没发这个信号。 */
          aria-pressed={minimapOpen}
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
          /* Batch 837 SOURCE_FACT：源站带 aria-pressed，初值 **true**（与复刻
             store 的 edgesVisible=true 一致）—— 这枚默认就是「开」。 */
          aria-pressed={edgesVisible}
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
          /* Batch 837 SOURCE_FACT：源站这枚**有** aria-expanded（实测 "false"），
             但**没有** aria-pressed（实测 None）—— 别给错信号。 */
          aria-expanded={zoomMenuOpen}
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
