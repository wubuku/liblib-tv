"use client";

import { useFrameosStore } from "@/store/frameosStore";
import { useViewport, useReactFlow } from "@xyflow/react";
import { useEffect, useState } from "react";

/**
 * FrameOS 节点对齐辅助线
 * - 拖节点时检测该节点与其他节点中心点
 * - 当 x 或 y 与其他节点中心/边 < 8px (画布坐标系) 时显示蓝色虚线
 * - 颜色 rgba(59,130,246,0.6) 蓝色
 */
const SNAP_THRESHOLD = 8;

interface Guide {
  orientation: "horizontal" | "vertical";
  position: number;
}

export function FrameosAlignmentGuides() {
  const nodes = useFrameosStore((s) => s.nodes);
  const { x: panX, y: panY, zoom } = useViewport();
  const rf = useReactFlow();
  const [guides, setGuides] = useState<Guide[]>([]);

  useEffect(() => {
    let raf = 0;
    let prevDraggingIds = "";
    const tick = () => {
      // 拿到 xyflow 内部 nodes (含 internals.dragging)
      const internalNodes = rf.getNodes() as Array<{
        id: string;
        internals?: { dragging?: boolean };
      }>;
      const draggingIds: string[] = [];
      for (const n of internalNodes) {
        if (n.internals?.dragging) draggingIds.push(n.id);
      }
      const draggingKey = draggingIds.sort().join(",");
      // 没人在拖 → 清空 guides (避免重叠 trigger)
      if (draggingIds.length === 0) {
        if (prevDraggingIds !== "") {
          prevDraggingIds = "";
          setGuides([]);
        }
        raf = requestAnimationFrame(tick);
        return;
      }
      prevDraggingIds = draggingKey;
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
          // 水平辅助线: 中心, top, bottom 任一 y 匹配
          for (const yc of [draggedCy, draggedTop, draggedBottom]) {
            for (const oc of [oCy, oTop, oBottom]) {
              if (Math.abs(yc - oc) < SNAP_THRESHOLD) {
                newGuides.push({ orientation: "horizontal", position: oc });
              }
            }
          }
          // 垂直辅助线: 中心, left, right 任一 x 匹配
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
          const top = g.position * zoom + panY;
          return (
            <div
              key={`h-${i}-${g.position}`}
              style={{
                position: "fixed",
                left: 0,
                right: 0,
                top,
                height: 0,
                borderTop: "1px dashed rgba(59,130,246,0.7)",
                pointerEvents: "none",
                zIndex: 5000,
              }}
            />
          );
        } else {
          const left = g.position * zoom + panX;
          return (
            <div
              key={`v-${i}-${g.position}`}
              style={{
                position: "fixed",
                top: 0,
                bottom: 0,
                left,
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
