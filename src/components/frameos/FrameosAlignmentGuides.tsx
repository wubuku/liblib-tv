"use client";

import { useFrameosStore } from "@/store/frameosStore";
import { useReactFlow } from "@xyflow/react";
import { useEffect, useState } from "react";

/**
 * FrameOS 节点对齐辅助线
 * - 通过 rAF tick 监听 xyflow 内部 nodes 的 internals.dragging 状态
 * - 当被拖动节点与其他节点中心/边 < 8px (画布坐标系) 时显示蓝色虚线
 * - 与原站 frameos.cn 拖动时显示对齐线一致
 */
const SNAP_THRESHOLD = 8;

interface Guide {
  orientation: "horizontal" | "vertical";
  position: number;
}

export function FrameosAlignmentGuides() {
  const nodes = useFrameosStore((s) => s.nodes);
  const [guides, setGuides] = useState<Guide[]>([]);
  const rf = useReactFlow();

  useEffect(() => {
    let raf = 0;
    const tick = () => {
      const internal = rf.getNodes() as Array<{
        id: string;
        internals?: { dragging?: boolean };
      }>;
      const draggingIds: string[] = [];
      for (const n of internal) {
        if (n.internals?.dragging) draggingIds.push(n.id);
      }
      if (draggingIds.length === 0) {
        setGuides((prev) => (prev.length === 0 ? prev : []));
        raf = requestAnimationFrame(tick);
        return;
      }
      const newGuides: Guide[] = [];
      for (const dragged of nodes) {
        if (!draggingIds.includes(dragged.id)) continue;
        const w = (dragged.style?.width as number) ?? 300;
        const h = (dragged.style?.height as number) ?? 169;
        const draggedCx = dragged.position.x + w / 2;
        const draggedCy = dragged.position.y + h / 2;
        const draggedLeft = dragged.position.x;
        const draggedRight = dragged.position.x + w;
        const draggedTop = dragged.position.y;
        const draggedBottom = dragged.position.y + h;
        for (const other of nodes) {
          if (other.id === dragged.id) continue;
          const ow = (other.style?.width as number) ?? 300;
          const oh = (other.style?.height as number) ?? 169;
          const oCx = other.position.x + ow / 2;
          const oCy = other.position.y + oh / 2;
          const oLeft = other.position.x;
          const oRight = other.position.x + ow;
          const oTop = other.position.y;
          const oBottom = other.position.y + oh;
          for (const yc of [draggedCy, draggedTop, draggedBottom]) {
            for (const oc of [oCy, oTop, oBottom]) {
              if (Math.abs(yc - oc) < SNAP_THRESHOLD) {
                newGuides.push({ orientation: "horizontal", position: oc });
              }
            }
          }
          for (const xc of [draggedCx, draggedLeft, draggedRight]) {
            for (const oc of [oCx, oLeft, oRight]) {
              if (Math.abs(xc - oc) < SNAP_THRESHOLD) {
                newGuides.push({ orientation: "vertical", position: oc });
              }
            }
          }
        }
      }
      setGuides(newGuides);
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [nodes, rf]);

  return (
    <>
      {guides.map((g, i) => {
        if (g.orientation === "horizontal") {
          return (
            <div
              key={`h-${i}-${g.position}`}
              style={{
                position: "fixed",
                left: 0,
                right: 0,
                top: g.position,
                height: 0,
                borderTop: "1px dashed rgba(59,130,246,0.7)",
                pointerEvents: "none",
                zIndex: 5000,
              }}
            />
          );
        } else {
          return (
            <div
              key={`v-${i}-${g.position}`}
              style={{
                position: "fixed",
                top: 0,
                bottom: 0,
                left: g.position,
                width: 0,
                borderLeft: "1px dashed rgba(59,130,246,0.7)",
                pointerEvents: "none",
                zIndex: 5000,
              }}
            />
          );
        }
      })}
    </>
  );
}
