"use client";

import { Download, Maximize2, Play, Plus, Trash2, Upload, Volume2 } from "lucide-react";
import type { NodeProps } from "@xyflow/react";

import { nodeRingShadow } from "@/components/jimeng/nodeChrome";
import type { JimengTimelineNodeData } from "@/types/jimeng";
import { JimengNodeTitle } from "@/components/jimeng/nodes/JimengNodeTitle";
import { JimengConnectHandles } from "@/components/jimeng/JimengConnectHandles";
import { useJimengStore } from "@/store/jimengStore";
import { FEEDBACK } from "@/components/jimeng/jimengFeedback";

/**
 * 时间线节点 (Batch 805 SOURCE_FACT @1680×826，登录态)。
 *
 * 这是**左栏「时间线」按钮点下去之后出现的东西** —— 源站实测落点是
 * `data-testid="rf__node-*" role="group"`，位于 `.react-flow__viewport` 内，
 * 顶栏节点计数同步 +1。此前复刻把它当"打开浮层"理解，所以按钮点了没反应。
 *
 * 结构 (源站截图逐层量得)：
 *   顶行  导入 · 删除 | 播放 ▶ · "00:00 / 00:00" | 下载 · 全屏编辑
 *   刻度  00:00 → 00:30，每 5s 一个主刻度
 *   轨道  「+ 添加素材到时间线」虚线占位
 *   左侧槽 静音钮
 *
 * 真交互（不是静态图）：
 *   「添加素材到时间线」往轨道塞一个片段，标题栏的 时长/片段数 随之变化；
 *   删除钮移除当前节点；导入/下载/全屏编辑沿用既有 mock 语义。
 */
const TOTAL_SECONDS = 30;
const TICK_STEP = 5;

function fmt(sec: number): string {
  const s = Math.max(0, Math.floor(sec));
  return `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`;
}

export function JimengTimelineNode({ id, data, selected }: NodeProps) {
  const d = data as JimengTimelineNodeData;
  const updateNodeData = useJimengStore((s) => s.updateNodeData);
  const pushToast = useJimengStore((s) => s.pushToast);
  const removeNode = useJimengStore((s) => s.removeNode);
  const clips = d.clips ?? [];
  // 注意别写成 Math.max(..., 1)：空轨道时那个下限 1 会漏进显示值，
  // 空态就成了 "00:00 / 00:01" 而不是源站的 "00:00 / 00:00"。
  const ends = clips.map((c) => c.start + c.length);
  const span = ends.length ? Math.max(d.duration ?? 0, ...ends) : (d.duration ?? 0);

  const addClip = () => {
    const clip = {
      id: `clip-${Date.now()}`,
      label: `片段 ${clips.length + 1}`,
      start: clips.length ? Math.min(30, clips[clips.length - 1].start + clips[clips.length - 1].length) : 0,
      length: 5,
    };
    updateNodeData(id, { clips: [...clips, clip], duration: clip.start + clip.length });
    pushToast(FEEDBACK.addTimelineClip(clip.label));
  };

  const removeClip = (clipId: string) => {
    const rest = clips.filter((c) => c.id !== clipId);
    updateNodeData(id, {
      clips: rest,
      duration: rest.length ? rest[rest.length - 1].start + rest[rest.length - 1].length : 0,
    });
  };

  return (
    <div
      className="group relative"
      style={{ width: d.width, height: d.height }}
      data-jimeng-node-selected={selected || undefined}
      data-testid="timeline-node"
    >
      <div className="absolute inset-x-0 top-[-31px] z-10 flex h-8 items-start text-left">
        <JimengNodeTitle id={id} title={d.title} />
      </div>

      <div
        className="relative flex h-full w-full flex-col overflow-hidden rounded-lg"
        style={{
          background: "rgb(24,24,26)",
          boxShadow: nodeRingShadow(selected === true),
        }}
      >
        {/* 顶行：导入/删除 · 播放/时间码 · 下载/全屏编辑 */}
        <div className="flex h-12 shrink-0 items-center gap-1 px-3">
          <button
            type="button"
            aria-label="导入"
            onClick={addClip}
            className="flex size-8 items-center justify-center rounded-md text-white/70 hover:bg-white/10"
          >
            <Upload size={16} />
          </button>
          <button
            type="button"
            aria-label="删除时间线"
            onClick={() => removeNode(id)}
            className="flex size-8 items-center justify-center rounded-md text-white/70 hover:bg-white/10"
          >
            <Trash2 size={16} />
          </button>

          <div className="flex flex-1 items-center justify-center gap-2 text-white/80">
            <Play size={18} className="text-white/60" />
            <span className="text-[13px]/[20px] tabular-nums" data-testid="timeline-time">
              {fmt(0)} / {fmt(span)}
            </span>
          </div>

          <button
            type="button"
            aria-label="下载"
            className="flex size-8 items-center justify-center rounded-md text-white/70 hover:bg-white/10"
          >
            <Download size={16} />
          </button>
          <button
            type="button"
            aria-label="全屏编辑"
            className="flex h-8 items-center gap-1.5 whitespace-nowrap rounded-md px-2 text-[13px] text-white/85 hover:bg-white/10"
          >
            <Maximize2 size={15} />
            全屏编辑
          </button>
        </div>

        <div className="flex min-h-0 flex-1">
          {/* 左侧槽：静音 */}
          <div className="flex w-12 shrink-0 flex-col items-center gap-3 border-r border-white/[0.06] py-2">
            <button
              type="button"
              aria-label="静音"
              className="flex size-8 items-center justify-center rounded-full text-white/70 hover:bg-white/10"
            >
              <Volume2 size={16} />
            </button>
          </div>

          <div className="min-w-0 flex-1">
            {/* 刻度尺：SOURCE_FACT 00:00→00:30，每 5s 一格 */}
            <div
              className="relative h-6 border-b border-white/[0.06]"
              data-testid="timeline-ruler"
              aria-label="时间线刻度"
            >
              {Array.from({ length: TOTAL_SECONDS / TICK_STEP + 1 }, (_, i) => i * TICK_STEP).map((t) => (
                <span
                  key={t}
                  className="absolute top-0 flex h-full -translate-x-px flex-col items-start"
                  style={{ left: `${(t / TOTAL_SECONDS) * 100}%` }}
                >
                  <span className="h-2 w-px bg-white/20" />
                  <span className="text-[10px] leading-3 text-white/40 tabular-nums">{fmt(t)}</span>
                </span>
              ))}
            </div>

            {/* 轨道：片段 + 「+ 添加素材到时间线」 */}
            <div className="relative h-[76px] px-3 py-2">
              {clips.map((c) => (
                <div
                  key={c.id}
                  className="absolute top-2 flex h-[60px] items-center justify-between gap-2 rounded-md px-2 text-[12px] text-white/85"
                  style={{
                    left: `calc(12px + ${(c.start / TOTAL_SECONDS) * 100}% * (100% - 24px) / 100%)`,
                    width: `${(c.length / TOTAL_SECONDS) * 100}%`,
                    background: "rgba(255,255,255,0.10)",
                    border: "1px solid rgba(255,255,255,0.14)",
                  }}
                  data-testid="timeline-clip"
                >
                  <span className="truncate">{c.label}</span>
                  <button
                    type="button"
                    aria-label={`移除 ${c.label}`}
                    onClick={() => removeClip(c.id)}
                    className="shrink-0 text-white/50 hover:text-white"
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
              ))}
              {clips.length === 0 ? (
                <button
                  type="button"
                  onClick={addClip}
                  data-testid="timeline-add-clip"
                  className="flex h-[60px] w-full items-center justify-center gap-2 rounded-md border border-dashed border-white/20 text-[13px] text-white/50 hover:border-white/35 hover:text-white/80"
                >
                  <Plus size={15} />
                  添加素材到时间线
                </button>
              ) : (
                <button
                  type="button"
                  onClick={addClip}
                  aria-label="添加素材到时间线"
                  className="absolute bottom-2 right-3 flex h-7 items-center gap-1 rounded-md px-2 text-[12px] text-white/50 hover:bg-white/10 hover:text-white/80"
                >
                  <Plus size={14} />
                  添加素材
                </button>
              )}
            </div>
          </div>
        </div>

        {/* 源站把空态说明放在 sr-only，不渲染成可见行 */}
        <span className="sr-only">
          {clips.length === 0
            ? "No clips. Drag clips to reorder them. With the keyboard, press Shift to move."
            : `${clips.length} clips on the timeline.`}
        </span>
      </div>

      <JimengConnectHandles
        nodeId={id}
        title={d.title}
        size={{ width: d.width, height: d.height }}
        selected={selected === true}
      />
    </div>
  );
}
