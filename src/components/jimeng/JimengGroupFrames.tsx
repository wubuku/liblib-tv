"use client";

import { useEffect, useRef, useState } from "react";
import { Group } from "lucide-react";

import { useJimengStore } from "@/store/jimengStore";

/**
 * 编组卡片视觉层 (Batch 63)。
 *
 * 证据 (SOURCE_FACT, docs/research/jimeng-canvas/README.md §6 batch 63,
 * 63-after-group.png / 63-group-deselected.png):
 * - 源站编组生成真实 group 节点卡片：标题「编组 N」在卡片左上方，
 *   面板比成员卡片包围盒大一圈 (~64px 边距)，圆角，bg 略亮于画布
 * - 选中时白色描边 + 四角圆形手柄；失焦时面板与标题仍可见
 * CLONE_DECISION: 我方编组采用 groupId 标记模型 (batch 39)，本组件以
 * 视觉层近似源站 group 卡片 (面板绘制在画布之上，pointer-events:none，
 * 成员卡片上的着色极浅)；排列/尺寸动画未复刻。背景色 tint 以 16% 透明度
 * 混合 (源站实色混合比例未提取)。
 */
const GROUP_PANEL_PADDING = 64;

interface FrameRect {
  gid: string;
  title: string;
  tint?: string;
  left: number;
  top: number;
  width: number;
  height: number;
  selected: boolean;
}

export function JimengGroupFrames() {
  const groupCount = useJimengStore(
    (s) =>
      Object.keys(
        s.nodes.reduce<Record<string, boolean>>((acc, n) => {
          if (n.groupId) acc[n.groupId] = true;
          return acc;
        }, {}),
      ).length,
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
  const [frames, setFrames] = useState<FrameRect[]>([]);
  const lastRef = useRef("");

  const visible = groupCount > 0 && !editingActive;

  useEffect(() => {
    if (!visible) {
      const id = window.setTimeout(() => {
        setFrames([]);
        lastRef.current = "";
      }, 0);
      return () => window.clearTimeout(id);
    }
    let raf = 0;
    const tick = () => {
      const { nodes, groupNames, groupColors } = useJimengStore.getState();
      const buckets = new Map<string, typeof nodes>();
      for (const n of nodes) {
        if (!n.groupId) continue;
        const list = buckets.get(n.groupId) ?? [];
        list.push(n);
        buckets.set(n.groupId, list);
      }
      const next: FrameRect[] = [];
      for (const [gid, members] of buckets) {
        if (members.length < 2) continue;
        const domRects = members
          .map(
            (m) =>
              document
                .querySelector(`[data-id="${m.id}"]`)
                ?.getBoundingClientRect() ?? null,
          )
          .filter((r): r is DOMRect => r !== null);
        if (domRects.length < 2) continue;
        const left =
          Math.min(...domRects.map((r) => r.x)) - GROUP_PANEL_PADDING;
        const top = Math.min(...domRects.map((r) => r.y)) - GROUP_PANEL_PADDING;
        const width =
          Math.max(...domRects.map((r) => r.x + r.width)) +
          GROUP_PANEL_PADDING -
          left;
        const height =
          Math.max(...domRects.map((r) => r.y + r.height)) +
          GROUP_PANEL_PADDING -
          top;
        next.push({
          gid,
          title: groupNames[gid] ?? "编组",
          tint: groupColors[gid],
          left,
          top,
          width,
          height,
          selected: members.some((m) => m.selected),
        });
      }
      const key = next
        .map(
          (f) =>
            `${f.gid}:${Math.round(f.left)}:${Math.round(f.top)}:${Math.round(f.width)}:${Math.round(f.height)}:${f.selected}:${f.tint ?? ""}`,
        )
        .join("|");
      if (key !== lastRef.current) {
        lastRef.current = key;
        setFrames(next);
      }
      raf = window.requestAnimationFrame(tick);
    };
    raf = window.requestAnimationFrame(tick);
    return () => window.cancelAnimationFrame(raf);
  }, [visible]);

  if (!visible) return null;

  return (
    <>
      {frames.map((f) => (
        <div
          key={f.gid}
          data-group-frame={f.gid}
          data-group-tint={f.tint ?? ""}
          className="jimeng-group-frame pointer-events-none fixed z-[4] rounded-3xl"
          style={{
            left: f.left,
            top: f.top,
            width: f.width,
            height: f.height,
            background: f.tint
              ? `${f.tint}29`
              : "rgba(255, 255, 255, 0.035)",
            boxShadow:
              f.selected === true
                ? "0 0 0 1.5px rgba(255,255,255,0.92)"
                : undefined,
          }}
        >
          <span className="absolute -top-7 left-2 flex items-center gap-1.5 text-[13px] leading-[22px] text-white/70">
            <Group size={14} className="shrink-0" />
            {f.title}
          </span>
          {f.selected
            ? ([
                "left-[-5px] top-[-5px]",
                "right-[-5px] top-[-5px]",
                "left-[-5px] bottom-[-5px]",
                "right-[-5px] bottom-[-5px]",
              ] as const).map((pos) => (
                <span
                  key={pos}
                  className={`absolute ${pos} size-2.5 rounded-full border border-black/40 bg-white`}
                />
              ))
            : null}
        </div>
      ))}
    </>
  );
}
