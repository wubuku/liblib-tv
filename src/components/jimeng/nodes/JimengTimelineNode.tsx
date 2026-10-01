"use client";

import { useState } from "react";
import { Download, Maximize2, Play, Plus, Trash2, Upload, Volume2, VolumeX, X } from "lucide-react";
import type { NodeProps } from "@xyflow/react";

import { nodeRingShadow } from "@/components/jimeng/nodeChrome";
import type { JimengTimelineNodeData } from "@/types/jimeng";
import { JimengNodeTitle } from "@/components/jimeng/nodes/JimengNodeTitle";
import { JimengConnectHandles } from "@/components/jimeng/JimengConnectHandles";
import { useJimengStore } from "@/store/jimengStore";
import { FEEDBACK, mockMsg } from "@/components/jimeng/jimengFeedback";

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
/** Batch 813 SOURCE_FACT：点「导出时间线」弹出的菜单，逐字取自源站 */
const EXPORT_ITEMS = {
  mp4: { label: "导出为 MP4", blocked: "当前时间线暂不支持此操作" },
  xml: { label: "导出为 XML", hint: "批量导出时间线素材 · 请选择至少一个组、文本、图片或视频项" },
} as const;
/** SOURCE_FACT: 源站原文「导出到剪映」无空格、「导出到 DaVinci Resolve」有空格 ——
 *  CJK 名与拉丁名在源站就是不同排法，所以显示名逐条写死，不靠拼接。 */
const EXPORT_TARGETS = [
  { name: "剪映", label: "导出到剪映" },
  { name: "DaVinci Resolve", label: "导出到 DaVinci Resolve" },
  { name: "Premiere", label: "导出到 Premiere" },
  { name: "Final Cut Pro", label: "导出到 Final Cut Pro" },
] as const;

/** Batch 813 SOURCE_FACT：点「全屏编辑」打开的编辑器，逐字取自源站 */
const FS_SOURCES = ["已导入资产", "画布资产", "全部"] as const;
const FS_KINDS = ["图片", "视频", "音频"] as const;
const FS_SUBTITLE = "Edit the main visual track and multiple audio tracks";

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
  // Batch 813 SOURCE_FACT（源站逐个按钮实测）：
  //   导出时间线 42×42 → 弹导出菜单（MP4/XML + 导出到剪映/DaVinci/Premiere/Final Cut）
  //   全屏编辑   126×42 → 打开全屏时间线编辑器
  //   静音       42×42  data-testid="timeline-mute-button"
  // 这三个此前全是死按钮：只画了图标没挂行为。
  const [muted, setMuted] = useState(false);
  const [exportOpen, setExportOpen] = useState(false);
  const [fullscreen, setFullscreen] = useState(false);
  const [fsSource, setFsSource] = useState<(typeof FS_SOURCES)[number]>("已导入资产");
  const [fsKind, setFsKind] = useState<(typeof FS_KINDS)[number]>("图片");
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

          {/* 源站这一枚的 aria 是「导出时间线」不是「下载」 */}
          <button
            type="button"
            aria-label="导出时间线"
            data-testid="timeline-export-trigger"
            onClick={() => setExportOpen((v) => !v)}
            className="flex size-8 items-center justify-center rounded-md text-white/70 hover:bg-white/10"
          >
            <Download size={16} />
          </button>
          {exportOpen ? (
            <div
              className="absolute right-3 top-11 z-[150] w-[260px] rounded-xl p-1.5"
              style={{ background: "rgb(38,38,38)" }}
              role="menu"
              aria-label="导出时间线"
              data-testid="timeline-export-menu"
            >
              <button
                type="button"
                role="menuitem"
                onClick={() => {
                  setExportOpen(false);
                  pushToast(
                    mockMsg(
                      EXPORT_ITEMS.mp4.blocked
                        ? `导出为 MP4：${EXPORT_ITEMS.mp4.blocked}`
                        : EXPORT_ITEMS.mp4.label,
                    ),
                  );
                }}
                className="flex w-full flex-col items-start rounded-md px-2 py-1.5 text-left hover:bg-white/10"
              >
                <span className="text-[13px] text-white/85">{EXPORT_ITEMS.mp4.label}</span>
                {/* SOURCE_FACT: 空时间线点 MP4 导出，源站附「当前时间线暂不支持此操作」 */}
                <span className="text-[11px] text-white/45">{EXPORT_ITEMS.mp4.blocked}</span>
              </button>
              <button
                type="button"
                role="menuitem"
                onClick={() => {
                  setExportOpen(false);
                  pushToast(mockMsg(EXPORT_ITEMS.xml.label));
                }}
                className="flex w-full flex-col items-start rounded-md px-2 py-1.5 text-left hover:bg-white/10"
              >
                <span className="text-[13px] text-white/85">{EXPORT_ITEMS.xml.label}</span>
                <span className="text-[11px] text-white/45">{EXPORT_ITEMS.xml.hint}</span>
              </button>
              <div className="my-1 h-px bg-white/[0.08]" />
              {EXPORT_TARGETS.map((t) => (
                <button
                  key={t.name}
                  type="button"
                  role="menuitem"
                  onClick={() => {
                    setExportOpen(false);
                    pushToast(mockMsg(t.label));
                  }}
                  className="flex h-8 w-full items-center rounded-md px-2 text-left text-[13px] text-white/85 hover:bg-white/10"
                >
                  {t.label}
                </button>
              ))}
            </div>
          ) : null}
          <button
            type="button"
            aria-label="全屏编辑"
            data-testid="timeline-fullscreen-trigger"
            onClick={() => setFullscreen(true)}
            className="flex h-8 items-center gap-1.5 whitespace-nowrap rounded-md px-2 text-[13px] text-white/85 hover:bg-white/10"
          >
            <Maximize2 size={15} />
            全屏编辑
          </button>
        </div>

        <div className="flex min-h-0 flex-1">
          {/* 左侧槽：静音。
              宽度 96px 不是随便取的 —— 节点的左侧连接手柄命中盒实测
              44×88，从节点左缘往里吞掉约 30px（世界像素）。槽若只有 w-12(48)，
              静音钮就整个落在手柄命中盒里：Playwright 报
              `handle intercepts pointer events`，**用户同样点不到**。
              源站那枚钮是从节点左缘内缩约 36px 放置的，正是为了避开手柄。
              128px → 钮心离左缘 64px，实测余量 ~14px（96px 时只剩 1px，太险）。
              （手柄几何是 batch 806 的地盘，不去动那边。） */}
          <div className="flex w-32 shrink-0 flex-col items-center gap-3 border-r border-white/[0.06] py-2">
            <button
              type="button"
              aria-label={muted ? "取消静音" : "静音"}
              data-testid="timeline-mute-button"
              aria-pressed={muted}
              onClick={() => setMuted((v) => !v)}
              className="flex size-8 items-center justify-center rounded-full text-white/70 hover:bg-white/10"
            >
              {muted ? <VolumeX size={16} /> : <Volume2 size={16} />}
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

      {/* Batch 813 SOURCE_FACT：全屏时间线编辑器。此前「全屏编辑」是死按钮。
          源站结构：标题 + 副标题 + 来源/类型两排筛选 + 资产区 + 底部 playhead */}
      {fullscreen ? (
        <div
          className="fixed inset-0 z-[300] flex flex-col"
          style={{ background: "rgb(20,20,22)" }}
          role="dialog"
          aria-label="时间线"
          data-testid="timeline-fullscreen"
        >
          <div className="flex h-14 shrink-0 items-center gap-3 border-b border-white/[0.08] px-4">
            <span className="text-[15px] font-medium text-white">{d.title}</span>
            <span className="text-[12px] text-white/45">{FS_SUBTITLE}</span>
            <span className="flex-1" />
            <button
              type="button"
              aria-label="导出"
              onClick={() => pushToast(mockMsg("导出时间线"))}
              className="flex h-8 items-center rounded-md px-2.5 text-[13px] text-white/80 hover:bg-white/10"
            >
              导出
            </button>
            <button
              type="button"
              aria-label="关闭全屏编辑"
              data-testid="timeline-fullscreen-close"
              onClick={() => setFullscreen(false)}
              className="flex size-8 items-center justify-center rounded-md text-white/70 hover:bg-white/10"
            >
              <X size={16} />
            </button>
          </div>

          <div className="flex min-h-0 flex-1">
            <div className="w-[260px] shrink-0 border-r border-white/[0.08] p-3">
              <div className="mb-2 flex flex-wrap gap-1">
                {FS_SOURCES.map((sname) => (
                  <button
                    key={sname}
                    type="button"
                    data-testid={`timeline-fs-source-${sname}`}
                    onClick={() => setFsSource(sname)}
                    className={`h-7 rounded-md px-2 text-[12px] ${
                      fsSource === sname ? "bg-white/15 text-white" : "text-white/60 hover:bg-white/10"
                    }`}
                  >
                    {sname}
                  </button>
                ))}
              </div>
              <div className="mb-2 flex flex-wrap gap-1">
                {FS_KINDS.map((k) => (
                  <button
                    key={k}
                    type="button"
                    data-testid={`timeline-fs-kind-${k}`}
                    onClick={() => setFsKind(k)}
                    className={`h-7 rounded-md px-2 text-[12px] ${
                      fsKind === k ? "bg-white/15 text-white" : "text-white/60 hover:bg-white/10"
                    }`}
                  >
                    {k}
                  </button>
                ))}
              </div>
              <div
                className="flex h-[120px] items-center justify-center rounded-md border border-dashed border-white/15 px-3 text-center text-[12px] leading-[18px] text-white/40"
                data-testid="timeline-fs-asset-empty"
              >
                {clips.length === 0
                  ? "没有媒体可供预览 · 将文件拖至此处添加"
                  : clips.map((c) => c.label).join(" / ")}
              </div>
              <button
                type="button"
                data-testid="timeline-fs-import"
                onClick={() => pushToast(mockMsg("请选择要导入的文件"))}
                className="mt-2 flex h-8 w-full items-center justify-center rounded-md bg-white/10 text-[13px] text-white hover:bg-white/20"
              >
                导入
              </button>
            </div>

            <div className="flex min-w-0 flex-1 flex-col">
              <div className="flex-1 p-4 text-[13px] text-white/40">Timeline preview</div>
              <div className="flex h-12 shrink-0 items-center gap-3 border-t border-white/[0.08] px-4">
                <span className="text-[12px] text-white/55" data-testid="timeline-fs-playhead">
                  Timeline playhead 00:00:00 / 00:00:{String(Math.floor(span)).padStart(2, "0")}
                </span>
              </div>
            </div>
          </div>
        </div>
      ) : null}

      <JimengConnectHandles
        nodeId={id}
        title={d.title}
        size={{ width: d.width, height: d.height }}
        selected={selected === true}
      />
    </div>
  );
}
