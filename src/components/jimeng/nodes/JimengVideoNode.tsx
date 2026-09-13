"use client";

import { useEffect, useState } from "react";
import {
  Ban,
  Camera,
  Maximize2,
  Pause,
  Play,
  Plus,
  Tag,
  Volume2,
  VolumeX,
  X,
} from "lucide-react";
import { Handle, Position } from "@xyflow/react";
import type { NodeProps } from "@xyflow/react";

import type { JimengVideoNodeData } from "@/types/jimeng";
import { FileBadgeIcon } from "@/components/jimeng/icons";
import { JimengNodeToolbar } from "@/components/jimeng/JimengNodeToolbar";
import { JimengGenPanel } from "@/components/jimeng/JimengGenPanel";
import { JimengInsertMenu } from "@/components/jimeng/JimengInsertMenu";
import { JimengInferPanel } from "@/components/jimeng/JimengInferPanel";
import { JimengFramePicker } from "@/components/jimeng/JimengFramePicker";
import { JimengRepaintPanel } from "@/components/jimeng/JimengRepaintPanel";
import { JimengTrimPanel } from "@/components/jimeng/JimengTrimPanel";
import { JimengVideoEditMode } from "@/components/jimeng/JimengVideoEditMode";
import { JimengVideoPreview } from "@/components/jimeng/JimengVideoPreview";
import { useJimengStore } from "@/store/jimengStore";

/**
 * 即梦视频节点 — 复刻重点 (本地上传视频)。
 *
 * 结构证据 (SOURCE_FACT, docs/research/jimeng-canvas/README.md):
 * - 标题行在卡片上方 32px：文件徽标 16×16 + 13px/22px rgba(255,255,255,0.7) 标题 + 右侧 Tag 图标
 * - 卡片 569×320 世界尺寸、8px 圆角；媒体 object-cover
 * - 有内容: 中央 32px 半透明播放圆钮 + 底部 播放/时间/静音/全屏 控制 + 底边 2px 进度条
 * - 空节点: 对角渐变占位 + 中央小图标
 * - 左右连接热区 60×120 (隐形)；"+ " 圆钮 24px：本地上传节点仅右侧，空节点两侧 (hover/选中显示)
 */
function formatTime(s: number): string {
  const m = Math.floor(s / 60);
  const sec = Math.floor(s % 60);
  return `${String(m).padStart(2, "0")}:${String(sec).padStart(2, "0")}`;
}

const HANDLE_BASE = {
  width: 60,
  height: 120,
  background: "transparent",
  border: "none",
  borderRadius: 0,
} as const;

export function JimengVideoNode({ id, data, selected }: NodeProps) {
  const d = data as JimengVideoNodeData;
  // 播放态由 data.playing 显式驱动 (mock 初始为暂停，与源站提取时一致)
  const playing = d.hasMedia && d.playing === true;
  const addVideoNodeAfter = useJimengStore((s) => s.addVideoNodeAfter);
  const repaintNodeId = useJimengStore((s) => s.repaintNodeId);
  const enterRepaint = useJimengStore((s) => s.enterRepaint);
  const exitRepaint = useJimengStore((s) => s.exitRepaint);
  const editNodeId = useJimengStore((s) => s.editNodeId);
  const enterEdit = useJimengStore((s) => s.enterEdit);
  const exitEdit = useJimengStore((s) => s.exitEdit);
  const inferNodeId = useJimengStore((s) => s.inferNodeId);
  const enterInfer = useJimengStore((s) => s.enterInfer);
  const exitInfer = useJimengStore((s) => s.exitInfer);
  const framePickerNodeId = useJimengStore((s) => s.framePickerNodeId);
  const framePickerMode = useJimengStore((s) => s.framePickerMode);
  const enterFramePicker = useJimengStore((s) => s.enterFramePicker);
  const exitFramePicker = useJimengStore((s) => s.exitFramePicker);
  const trimNodeId = useJimengStore((s) => s.trimNodeId);
  const enterTrim = useJimengStore((s) => s.enterTrim);
  const exitTrim = useJimengStore((s) => s.exitTrim);
  const tasks = useJimengStore((s) => s.tasks);
  const startTask = useJimengStore((s) => s.startTask);
  const addNodeAt = useJimengStore((s) => s.addNodeAt);
  const [insertMenu, setInsertMenu] = useState<
    "left" | "right" | "title" | null
  >(null);

  const [tagPickerOpen, setTagPickerOpen] = useState(false);
  const repaintMode = repaintNodeId === id;
  const editMode = editNodeId === id;
  const inferMode = inferNodeId === id;
  const pickerMode = framePickerNodeId === id;
  const trimMode = trimNodeId === id;
  const task = tasks.find((t) => t.nodeId === id);
  const groupId = useJimengStore((s) =>
    s.nodes.find((n) => n.id === id)?.groupId,
  );
  const togglePlay = useJimengStore((s) => s.togglePlay);
  const restartPlay = useJimengStore((s) => s.restartPlay);
  const tickPlay = useJimengStore((s) => s.tickPlay);
  const toggleMute = useJimengStore((s) => s.toggleMute);
  const updateNodeData = useJimengStore((s) => s.updateNodeData);
  const seek = useJimengStore((s) => s.seek);
  const applyTrim = useJimengStore((s) => s.applyTrim);
  const onToggleMute = toggleMute;
  const previewNodeId = useJimengStore((s) => s.previewNodeId);
  const openPreview = useJimengStore((s) => s.openPreview);
  const closePreview = useJimengStore((s) => s.closePreview);
  const previewOpen = previewNodeId === id;

  // 节点颜色标记 (SOURCE_FACT batch 31: 禁止 + 青/蓝/紫/橙/黄 五色)
  const TAG_COLORS = ["#3BE8E8", "#3D7BFF", "#9C5BFF", "#F79022", "#FFE14D"];

  // 播放中 mock 时间走动 (Batch 15)；播完自停
  useEffect(() => {
    if (!playing) return;
    const timer = window.setInterval(() => tickPlay(id, 0.25), 250);
    return () => window.clearInterval(timer);
  }, [playing, id, tickPlay]);

  // 插入菜单 Escape 关闭 (Batch 24)
  useEffect(() => {
    if (!insertMenu) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setInsertMenu(null);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [insertMenu]);

  return (
    <div
      className="group relative"
      style={{ width: d.width, height: d.height }}
      data-jimeng-node-selected={selected || undefined}
      data-group-id={groupId}
    >
      {/* 选中后弹出的操作工具条 / 编辑态 / 反推面板 / 空节点生成面板 */}
      {d.hasMedia && repaintMode ? (
        <JimengRepaintPanel
          visible
          data={d}
          onSubmit={() => exitRepaint()}
        />
      ) : d.hasMedia && editMode ? (
        <JimengVideoEditMode onSubmit={() => exitEdit()} />
      ) : d.hasMedia && inferMode ? (
        <JimengInferPanel visible data={d} onClose={() => exitInfer()} />
      ) : d.hasMedia && pickerMode ? (
        <JimengFramePicker
          visible
          data={d}
          mode={framePickerMode}
          onConfirm={(frameTime) => {
            updateNodeData(id, {
              currentTime: frameTime,
              capturedFrame: frameTime,
            });
            exitFramePicker();
          }}
        />
      ) : d.hasMedia && trimMode ? (
        <JimengTrimPanel
          visible
          data={d}
          onConfirm={(trimmedDuration, startOffset) => {
            applyTrim(id, trimmedDuration, startOffset);
            exitTrim();
          }}
        />
      ) : d.hasMedia ? (
        <JimengNodeToolbar
          visible={selected === true}
          onAction={(label) => {
            if (label === "局部重拍") enterRepaint(id);
            if (label === "视频编辑") enterEdit(id);
            if (label === "提示词反推") enterInfer(id);
            if (label === "视频修剪") enterTrim(id);
            if (label === "智能超清") startTask(id, "upscale");
            if (label === "补帧") startTask(id, "interpolate");
            if (label === "全屏预览") openPreview(id);
            if (label === "截取帧:自定义") enterFramePicker(id, "custom");
            if (label === "截取帧:首帧") enterFramePicker(id, "first");
            if (label === "截取帧:尾帧") enterFramePicker(id, "last");
          }}
        />
      ) : null}
      {!d.hasMedia ? <JimengGenPanel visible={selected === true} /> : null}
      {/* 标题行 (卡片上方 32px)：文件徽标 + 标题 + 右侧图标；编辑态隐藏。
          双击标题 = 「添加节点」菜单 extended 版 (SOURCE_FACT batch 24) */}
      {!repaintMode &&
      !editMode &&
      !inferMode &&
      !pickerMode &&
      !trimMode ? (
        <div
          className="absolute inset-x-0 bottom-full z-10 flex h-8 items-center justify-between text-left"
          onDoubleClick={(e) => {
            e.stopPropagation();
            setInsertMenu((cur) => (cur === "title" ? null : "title"));
          }}
        >
          <div className="flex min-w-0 items-center gap-1.5 text-white/70">
            <FileBadgeIcon size={16} />
            <span
              className="max-w-full truncate whitespace-nowrap text-[13px] leading-[22px]"
              title={d.title}
            >
              {d.title}
            </span>
          </div>
          {d.hasMedia ? (
            <span className="relative">
              <button
                type="button"
                aria-label="节点颜色标记"
                onClick={(e) => {
                  e.stopPropagation();
                  setTagPickerOpen((v) => !v);
                }}
                className="flex size-4 items-center justify-center"
              >
                {d.tagColor ? (
                  <span
                    className="size-3 rounded-full"
                    style={{ background: d.tagColor }}
                  />
                ) : (
                  <Tag size={16} className="text-white/40" />
                )}
              </button>
              {tagPickerOpen ? (
                <span
                  className="nodrag absolute right-0 top-[calc(100%+6px)] z-[130] flex items-center gap-2 rounded-full border border-white/10 bg-[#262626] px-2.5 py-1.5"
                  role="menu"
                  onMouseDown={(e) => e.stopPropagation()}
                >
                  <button
                    type="button"
                    aria-label="清除颜色标记"
                    onClick={(e) => {
                      e.stopPropagation();
                      updateNodeData(id, { tagColor: null });
                      setTagPickerOpen(false);
                    }}
                    className="flex size-4 items-center justify-center rounded-full border border-white/40 text-white/70"
                  >
                    <Ban size={10} />
                  </button>
                  {TAG_COLORS.map((color) => (
                    <button
                      key={color}
                      type="button"
                      aria-label={`颜色标记 ${color}`}
                      onClick={(e) => {
                        e.stopPropagation();
                        updateNodeData(id, { tagColor: color });
                        setTagPickerOpen(false);
                      }}
                      className="size-4 rounded-full"
                      style={{ background: color }}
                    />
                  ))}
                </span>
              ) : null}
            </span>
          ) : null}
        </div>
      ) : null}

      {/* 卡片主体；双击 = 从头重播 (SOURCE_FACT batch 24) */}
      <div
        className="relative h-full w-full overflow-hidden rounded-lg"
        style={{
          background:
            "linear-gradient(to right bottom, rgb(34,34,34), rgb(20,20,20))",
          boxShadow:
            selected === true
              ? "0 0 0 1.5px rgba(255,255,255,0.92)"
              : undefined,
        }}
        onDoubleClick={() => {
          if (d.hasMedia) restartPlay(id);
        }}
      >
        {d.hasMedia && d.poster ? (
          <>
            {/* eslint-disable-next-line @next/next/no-img-element -- 本地 data URI mock 海报 */}
            <img
              src={d.poster}
              alt={d.title}
              className="absolute inset-0 h-full w-full object-cover"
            />
            {/* 截取帧徽章 (Batch 35/36): 点击跳转到截取帧，× 清除 */}
            {d.capturedFrame != null ? (
              <span
                className="absolute left-2 top-2 z-[2] flex items-center overflow-hidden rounded bg-black/60 text-[11px] text-white"
                data-testid="captured-frame-badge"
              >
                <button
                  type="button"
                  aria-label="跳转到截取帧"
                  onClick={(e) => {
                    e.stopPropagation();
                    seek(id, (d.capturedFrame ?? 0) / (d.duration || 1));
                  }}
                  className="flex items-center gap-1 px-1.5 py-0.5 hover:bg-black/40"
                >
                  <Camera size={10} />
                  {formatTime(d.capturedFrame)}
                </button>
                <button
                  type="button"
                  aria-label="清除截取帧"
                  onClick={(e) => {
                    e.stopPropagation();
                    updateNodeData(id, { capturedFrame: null });
                  }}
                  className="px-1 py-0.5 hover:bg-black/40"
                >
                  <X size={10} />
                </button>
              </span>
            ) : null}
            {/* 中央播放/暂停圆钮 32px rgba(0,0,0,0.6) SOURCE_FACT；点击切换播放 */}
            <button
              type="button"
              aria-label={playing ? "暂停" : "播放"}
              onClick={(e) => {
                e.stopPropagation();
                togglePlay(id);
              }}
              className="absolute left-1/2 top-1/2 z-[1] flex size-8 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full bg-black/60 text-white hover:bg-black/75"
            >
              {playing ? (
                <Pause size={14} fill="currentColor" />
              ) : (
                <Play size={14} fill="currentColor" />
              )}
            </button>
            {/* 底部控制条 */}
            <div className="absolute inset-x-0 bottom-0 z-[1] flex items-center gap-1.5 bg-gradient-to-t from-black/55 to-transparent px-2.5 pb-2 pt-5 text-white">
              <button
                type="button"
                aria-label={playing ? "底部暂停" : "底部播放"}
                onClick={(e) => {
                  e.stopPropagation();
                  togglePlay(id);
                }}
                className="flex items-center"
              >
                {playing ? (
                  <Pause size={12} fill="currentColor" />
                ) : (
                  <Play size={12} fill="currentColor" />
                )}
              </button>
              <span className="text-[11px] leading-none tabular-nums">
                {formatTime(d.currentTime ?? 0)} / {formatTime(d.duration ?? 0)}
              </span>
              <span className="flex-1" />
              <button
                type="button"
                aria-label={d.muted ? "取消静音" : "静音"}
                onClick={(e) => {
                  e.stopPropagation();
                  onToggleMute(id);
                }}
                className="flex items-center"
              >
                {d.muted ? <VolumeX size={13} /> : <Volume2 size={13} />}
              </button>
              <button
                type="button"
                aria-label="全屏预览"
                onClick={(e) => {
                  e.stopPropagation();
                  openPreview(id);
                }}
                className="flex items-center"
              >
                <Maximize2 size={13} />
              </button>
            </div>
            {/* 底边进度条 2px；点击 seek (Batch 32)、按住拖拽 scrub (Batch 37)。
                nodrag: 阻止 xyflow 节点拖拽抢占指针 (否则 scrub 中途失效) */}
            <div
              className="nodrag absolute inset-x-0 bottom-0 z-[2] h-[8px] cursor-pointer bg-transparent"
              data-testid="video-progress"
              onPointerDown={(e) => {
                e.stopPropagation();
                (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
                const r = e.currentTarget.getBoundingClientRect();
                seek(id, (e.clientX - r.left) / r.width);
              }}
              onPointerMove={(e) => {
                if (!(e.buttons & 1)) return;
                e.stopPropagation();
                const r = e.currentTarget.getBoundingClientRect();
                seek(id, (e.clientX - r.left) / r.width);
              }}
            >
              <div className="absolute inset-x-0 bottom-0 h-[2px] bg-white/25">
                <div
                  className="h-full bg-white/90"
                  style={{
                    width: `${Math.min(100, ((d.currentTime ?? 0) / (d.duration || 1)) * 100)}%`,
                  }}
                />
              </div>
            </div>
          </>
        ) : (
          <span className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 text-white/45">
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden>
              <rect
                x="2"
                y="2"
                width="14"
                height="14"
                rx="3"
                stroke="currentColor"
                strokeWidth="1.3"
              />
              <rect x="6.5" y="6.5" width="5" height="5" rx="1" fill="currentColor" />
            </svg>
          </span>
        )}

        {/* mock 任务处理中遮罩 (Batch 11, CLONE_DECISION) */}
        {task ? (
          <div className="absolute inset-0 z-[3] flex flex-col items-center justify-center gap-2 rounded-lg bg-black/55">
            <span className="size-6 animate-spin rounded-full border-2 border-white/25 border-t-white" />
            <span className="text-[12px] text-white/85">
              {task.kind === "upscale" ? "智能超清" : "补帧"}处理中…
            </span>
          </div>
        ) : null}
      </div>

      {/* 连接热区 (隐形) + "+" 圆钮 (hover/选中显示；点击弹「添加节点」菜单) */}
      <Handle
        type="target"
        position={Position.Left}
        className="!z-10"
        style={{ ...HANDLE_BASE, left: -30, top: "50%", transform: "translateY(-50%)" }}
      >
        {/* 证据: 本地上传节点左侧无 "+" (SOURCE_FACT §5)，仅空节点两侧都有 */}
        {d.source === "empty" ? (
          <span
            role="button"
            aria-label="左侧添加节点"
            className="absolute left-1/2 top-1/2 hidden size-6 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full border border-white/50 bg-[#0D0D0D] text-white group-hover:flex group-data-[jimeng-node-selected]:flex"
            onClick={(e) => {
              e.stopPropagation();
              setInsertMenu((cur) => (cur === "left" ? null : "left"));
            }}
            onMouseDown={(e) => e.stopPropagation()}
          >
            <Plus size={14} />
          </span>
        ) : null}
      </Handle>
      <Handle
        type="source"
        position={Position.Right}
        className="!z-10"
        style={{ ...HANDLE_BASE, right: -30, top: "50%", transform: "translateY(-50%)" }}
      >
        <span
          role="button"
          aria-label="右侧添加节点"
          className="absolute left-1/2 top-1/2 hidden size-6 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full border border-white/50 bg-[#0D0D0D] text-white group-hover:flex group-data-[jimeng-node-selected]:flex"
          onClick={(e) => {
            e.stopPropagation();
            setInsertMenu((cur) => (cur === "right" ? null : "right"));
          }}
          onMouseDown={(e) => e.stopPropagation()}
        >
          <Plus size={14} />
        </span>
      </Handle>
      {insertMenu ? (
        <div
          className="absolute z-[130]"
          style={
            insertMenu === "right"
              ? { left: "100%", top: "50%", marginLeft: 22 }
              : insertMenu === "left"
                ? { right: "100%", top: "50%", marginRight: 22 }
                : { left: "18%", top: 8 }
          }
        >
          <JimengInsertMenu
            extended={insertMenu === "title"}
            onPick={(label) => {
              if (label === "视频") addVideoNodeAfter(id);
              if (label === "图片")
                addNodeAt("image", { x: d.width + 200, y: 0 });
              if (label === "文本")
                addNodeAt("text", { x: d.width + 200, y: 120 });
              if (label === "音频")
                addNodeAt("audio", { x: d.width + 200, y: 240 });
            }}
            onClose={() => setInsertMenu(null)}
          />
        </div>
      ) : null}
      {/* 全屏播放器 (Batch 27) */}
      {previewOpen ? (
        <JimengVideoPreview
          nodeId={id}
          data={d}
          onClose={() => closePreview()}
        />
      ) : null}
    </div>
  );
}
