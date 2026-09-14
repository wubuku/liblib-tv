"use client";

import { useEffect, useRef, useState } from "react";

import { useJimengStore } from "@/store/jimengStore";

/**
 * 多选包围盒 (Batch 62)。
 *
 * SOURCE_FACT (62b-multiselect-styles.json): 源站多选包围盒 = 选中卡片
 * 包围盒四周外扩 40px，bg rgba(255,255,255,0.04) + 1px dashed
 * rgba(255,255,255,0.2) + border-radius 40px（即 xyflow
 * nodesselection-rect 的样式覆写）。
 * CLONE_DECISION: xyflow v12 仅在 marquee 结束后渲染原生
 * nodesselection-rect，shift+click 多选不渲染（源站两种方式都有）——
 * 复刻侧以本组件补齐 shift+click 路径；仅视觉，pointer-events:none
 * （源站包围盒可拖拽整体移动，未复刻，见 README）。
 */
export function JimengSelectionOutline() {
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
  const [rect, setRect] = useState<{
    left: number;
    top: number;
    width: number;
    height: number;
  } | null>(null);
  const lastRef = useRef("");

  const visible = selectedCount >= 2 && !editingActive;

  useEffect(() => {
    if (!visible) {
      // 隐藏时清除矩形 (异步调度，避免 effect 内同步 setState)
      const id = window.setTimeout(() => {
        setRect(null);
        lastRef.current = "";
      }, 0);
      return () => window.clearTimeout(id);
    }
    let raf = 0;
    const PADDING = 40;
    const tick = () => {
      const rects = [
        ...document.querySelectorAll(".react-flow__node.selected"),
      ].map((n) => n.getBoundingClientRect());
      if (rects.length >= 2) {
        const rawLeft = Math.min(...rects.map((r) => r.x));
        const rawTop = Math.min(...rects.map((r) => r.y));
        const rawRight = Math.max(...rects.map((r) => r.x + r.width));
        const rawBottom = Math.max(...rects.map((r) => r.y + r.height));
        const left = rawLeft - PADDING;
        const top = rawTop - PADDING;
        const width = rawRight + PADDING - left;
        const height = rawBottom + PADDING - top;
        const key = `${Math.round(left)}:${Math.round(top)}:${Math.round(width)}:${Math.round(height)}`;
        if (key !== lastRef.current) {
          lastRef.current = key;
          setRect({ left, top, width, height });
        }
      }
      raf = window.requestAnimationFrame(tick);
    };
    raf = window.requestAnimationFrame(tick);
    return () => window.cancelAnimationFrame(raf);
  }, [visible]);

  if (!visible || !rect) return null;

  return (
    <div
      data-testid="jimeng-selection-outline"
      className="jimeng-selection-outline pointer-events-none fixed z-[5]"
      style={{
        left: rect.left,
        top: rect.top,
        width: rect.width,
        height: rect.height,
      }}
    />
  );
}
