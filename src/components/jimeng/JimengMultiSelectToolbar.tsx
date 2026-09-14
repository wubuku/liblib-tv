"use client";

import { useEffect, useRef, useState } from "react";
import { ChevronDown, Download, Group, LayoutGrid } from "lucide-react";

import { useJimengStore } from "@/store/jimengStore";

/**
 * 多选组合工具条 (Batch 62)。
 *
 * 证据 (SOURCE_FACT, docs/research/jimeng-canvas/README.md §6 batch 62):
 * - ≥2 节点选中时出现在选区包围盒上方 36px 居中：rgb(32,32,32) r12 h40
 *   (与单选工具条同族载体)
 * - 条目: 「N 节点」标签 rgba(255,255,255,0.5) 13px ｜分隔线｜ 编组 (图标+文字)
 *   布局 (图标+文字+下拉箭头) ｜分隔线｜ 下载图标钮 32×32 禁用态
 *   rgba(255,255,255,0.2)，隐藏提示文案「导出前请保存画布」
 * - 选区包围盒本身为 xyflow nodesselection-rect (样式覆写见 jimeng-canvas.css)
 * CLONE_DECISION: 布局下拉内容源站未提取，复刻提供「自动排列」mock 项；
 * 下载禁用原因为导出需先保存画布 (隐藏提示文案为源站提取)。
 */
export function JimengMultiSelectToolbar() {
  const selectedCount = useJimengStore(
    (s) => s.nodes.filter((n) => n.selected).length,
  );
  const editingActive = useJimengStore((s) =>
    Boolean(
      s.repaintNodeId ||
        s.editNodeId ||
        s.inferNodeId ||
        s.framePickerNodeId ||
        s.trimNodeId ||
        s.previewNodeId,
    ),
  );
  const groupSelected = useJimengStore((s) => s.groupSelected);
  const arrangeSelected = useJimengStore((s) => s.arrangeSelected);

  const [center, setCenter] = useState<{ x: number; top: number } | null>(null);
  const [layoutOpen, setLayoutOpen] = useState(false);
  const lastRef = useRef<string>("");

  const visible = selectedCount >= 2 && !editingActive;

  // 选区包围盒跟随: rAF 轮测选中节点的屏幕矩形 (视口平移/缩放/拖拽均适用)，
  // 仅在多选可见期间运行
  useEffect(() => {
    if (!visible) {
      // 隐藏时复位下拉/坐标 (异步调度，避免 effect 内同步 setState)
      const id = window.setTimeout(() => {
        setLayoutOpen(false);
        setCenter(null);
        lastRef.current = "";
      }, 0);
      return () => window.clearTimeout(id);
    }
    let raf = 0;
    const tick = () => {
      const rects = [
        ...document.querySelectorAll(".react-flow__node.selected"),
      ].map((n) => n.getBoundingClientRect());
      if (rects.length >= 2) {
        const left = Math.min(...rects.map((r) => r.x));
        const right = Math.max(...rects.map((r) => r.x + r.width));
        const top = Math.min(...rects.map((r) => r.y));
        const key = `${Math.round(left)}:${Math.round(right)}:${Math.round(top)}`;
        if (key !== lastRef.current) {
          lastRef.current = key;
          setCenter({ x: (left + right) / 2, top });
        }
      }
      raf = window.requestAnimationFrame(tick);
    };
    raf = window.requestAnimationFrame(tick);
    return () => window.cancelAnimationFrame(raf);
  }, [visible]);

  // 布局下拉 Escape 关闭
  useEffect(() => {
    if (!layoutOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setLayoutOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [layoutOpen]);

  if (!visible || !center) return null;

  return (
    <div
      data-testid="jimeng-multi-toolbar"
      className="jimeng-node-toolbar fixed z-[60] flex h-10 select-none items-center gap-0.5 px-1.5"
      style={{
        left: center.x,
        top: center.top - 36,
        transform: "translate(-50%, -100%)",
      }}
    >
      <span
        data-testid="multi-count"
        className="whitespace-nowrap px-1.5 text-[13px] leading-none text-white/50"
      >
        {selectedCount} 节点
      </span>
      <span className="jimeng-node-toolbar-divider mx-0.5" aria-hidden />
      <button
        type="button"
        data-testid="multi-group"
        onClick={() => groupSelected()}
        className="jimeng-node-toolbar-item flex h-8 items-center gap-1.5 whitespace-nowrap px-2 text-[13px] leading-none text-white"
      >
        <Group size={16} className="shrink-0" />
        编组
      </button>
      <div className="relative">
        <button
          type="button"
          data-testid="multi-layout"
          onClick={() => setLayoutOpen((v) => !v)}
          className={`jimeng-node-toolbar-item flex h-8 items-center gap-1.5 whitespace-nowrap px-2 text-[13px] leading-none text-white ${
            layoutOpen ? "bg-white/10" : ""
          }`}
        >
          <LayoutGrid size={16} className="shrink-0" />
          布局
          <ChevronDown size={12} className="ml-0.5 shrink-0 text-white/70" />
        </button>
        {layoutOpen ? (
          <div
            className="absolute left-1/2 top-full z-[120] mt-2 -translate-x-1/2 rounded-xl p-1"
            style={{ background: "rgb(38,38,38)" }}
          >
            <button
              type="button"
              data-testid="multi-arrange"
              onClick={() => {
                arrangeSelected();
                setLayoutOpen(false);
              }}
              className="flex h-10 w-full items-center gap-2 whitespace-nowrap rounded-lg px-2.5 text-[13px] text-white hover:bg-white/10"
            >
              <LayoutGrid size={16} className="shrink-0 text-white/85" />
              自动排列
            </button>
          </div>
        ) : null}
      </div>
      <span className="jimeng-node-toolbar-divider mx-0.5" aria-hidden />
      <button
        type="button"
        data-testid="multi-download"
        disabled
        aria-label="下载"
        title="导出前请保存画布"
        className="jimeng-node-toolbar-item flex size-8 cursor-not-allowed items-center justify-center text-white/20"
      >
        <Download size={16} />
      </button>
    </div>
  );
}
