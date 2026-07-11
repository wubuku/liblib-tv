"use client";

import { useFrameosStore } from "@/store/frameosStore";
import { useStoreApi } from "@xyflow/react";
import { useCallback, useEffect, useRef, useState } from "react";

/**
 * FrameOS 节点对齐辅助线
 * - 订阅 xyflow store 的 nodeLookup, 事件驱动 (非 rAF polling)
 * - 当任一节点 dragging 状态变化时重算 guide
 * - 被拖动节点与其他节点中心/边 < 8px (画布坐标系) 时显示蓝色虚线
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
  const storeApi = useStoreApi();

  // 闭包中需要访问最新 nodes; 用 ref + effect 持有 (不在 render 中赋值)
  const nodesRef = useRef(nodes);

  // 缓存被拖动节点 id 集合, 订阅 store 时 diff
  const draggingRef = useRef<Set<string>>(new Set());

  // 计算辅助线 (useCallback 以便两个 effect 共享)
  const compute = useCallback(() => {
    const draggingIds = draggingRef.current;
    if (draggingIds.size === 0) {
      setGuides((prev) => (prev.length === 0 ? prev : []));
      return;
    }
    const ns = nodesRef.current;
    const newGuides: Guide[] = [];
    for (const dragged of ns) {
      if (!draggingIds.has(dragged.id)) continue;
      const w = (dragged.style?.width as number) ?? 300;
      const h = (dragged.style?.height as number) ?? 169;
      const draggedCx = dragged.position.x + w / 2;
      const draggedCy = dragged.position.y + h / 2;
      const draggedLeft = dragged.position.x;
      const draggedRight = dragged.position.x + w;
      const draggedTop = dragged.position.y;
      const draggedBottom = dragged.position.y + h;
      for (const other of ns) {
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
  }, []);

  // 订阅 xyflow 内部 store, 事件触发 (xyflow v12 subscribe: (state, prev) => void)
// compute() 在订阅回调与初始挂载中调用, 内部会 setGuides — 这是事件驱动的合法 setState
/* eslint-disable react-hooks/set-state-in-effect */
useEffect(() => {
  const unsubscribe = storeApi.subscribe((state) => {
    const lookup = state.nodeLookup as
      | Map<string, { id: string; internals?: { dragging?: boolean } }>
      | undefined;
    if (!lookup) return;
    const next = new Set<string>();
    for (const n of lookup.values()) {
      if (n.internals?.dragging) next.add(n.id);
    }
    const prev = draggingRef.current;
    if (
      next.size !== prev.size ||
      Array.from(next).some((id) => !prev.has(id))
    ) {
      draggingRef.current = next;
      compute();
    }
  });

  compute();
  return () => unsubscribe();
}, [storeApi, compute]);

// 兜底: 当 store 状态不变但外部 nodes 引用变化 (position 改变) 时也重算
// 这里依赖 nodes 引用触发一次, 仅影响 dragging 中节点
useEffect(() => {
  nodesRef.current = nodes;
  if (draggingRef.current.size === 0) return;
  compute();
}, [nodes, compute]);
/* eslint-enable react-hooks/set-state-in-effect */

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
