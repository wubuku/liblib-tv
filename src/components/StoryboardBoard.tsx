"use client";

import { useState } from "react";
import Image from "next/image";
import type { Node } from "@xyflow/react";
import { AudioLines, ChevronDown, ImageIcon, Maximize2, MessageSquareText, Play, Scan } from "lucide-react";
import { cn } from "@/lib/utils";
import { useCanvasStore } from "@/store/canvasStore";

type NodeRecord = Record<string, unknown>;

function nodeData(node: Node): NodeRecord {
  return node.data as NodeRecord;
}

function str(value: unknown): string | null {
  return typeof value === "string" ? value : null;
}

function nodeLabel(node: Node): string {
  const data = nodeData(node);
  const filename = str(data.filename);
  if (filename) return filename;
  const title = str(data.title);
  if (title) return title;
  return node.type ?? "未命名节点";
}

// Batch 334: 源站 2026-09-11 故事板视图为全宽三栏资源总览
// （音频 | 图片 | 视频），无 batch 104 时代的关键元素侧栏与
// 返回工作台按钮——工作流/故事板切换由顶栏图标对承担
// （见 docs/research/liblib-canvas-batch334-2026-09-11/）。
function audioDuration(node: Node): string | null {
  return str(nodeData(node).duration);
}

function dimension(node: Node): string | null {
  const data = nodeData(node);
  const width = typeof data.width === "number" ? data.width : null;
  const height = typeof data.height === "number" ? data.height : null;
  if (width && height) return `${width} x ${height}`;
  return null;
}

function imageUrl(node: Node): string | null {
  const d = nodeData(node);
  const url = str(d.imageUrl);
  return url ?? str(d.posterUrl);
}

function references(node: Node): string[] {
  const value = nodeData(node).references;
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [];
}

function EmptyColumn({ kind, label }: { kind: string; label: string }) {
  return (
    <div
      data-storyboard-empty={kind}
      className="flex min-h-32 items-center justify-center rounded-lg border border-dashed border-white/[0.08] text-xs text-[#666]"
    >
      {label}
    </div>
  );
}

function VideoStatusOverlay({ status, onPlay }: { status: string | null; onPlay?: () => void }) {
  const label = status === "pending"
    ? "待确认后生成"
    : status === "failed"
      ? "生成失败"
      : status === "empty"
        ? "暂无预览"
        : null;
  if (status === "ready") {
    return (
      <span
        role="button"
        tabIndex={0}
        data-storyboard-play
        aria-label="播放视频"
        onClick={(event) => {
          event.stopPropagation();
          onPlay?.();
        }}
        className="flex size-11 cursor-pointer items-center justify-center rounded-full bg-black/55 text-white transition-colors hover:bg-black/75"
      >
        <Play size={16} fill="currentColor" className="ml-0.5" />
      </span>
    );
  }
  return (
    <span className="flex flex-col items-center gap-2 text-xs text-[#9d9d9d]">
      <Play size={18} className="text-[#c9c9c9]" />
      {label ?? "暂无预览"}
    </span>
  );
}

export function StoryboardBoard() {
  const { canvases, activeCanvasId, selectedNodeId, selectNode, updateNodeData } = useCanvasStore();
  const activeCanvas = canvases.find((canvas) => canvas.id === activeCanvasId);
  const nodes = activeCanvas?.nodes ?? [];
  const audioNodes = nodes.filter((node) => node.type === "audio");
  const imageNodes = nodes.filter((node) => node.type === "image");
  const videoNodes = nodes.filter((node) => node.type === "video");
  const select = (nodeId: string) => selectNode(nodeId);

  // Batch 336: 待确认生成 确认/取消——源站交互细节未采得（BLOCKED_MANUAL
  // → CLONE_DECISION）：选中 pending 卡片显示确认条，确认→本地置为
  // ready（生成完成态），取消→清为 empty。
  const setVideoStatus = (nodeId: string, status: "ready" | "empty") => {
    updateNodeData(nodeId, { status });
  };

  // Batch 337: 视频栏 全部 ∨ 过滤与 ready 播放灯箱——源站选项/行为未采得
  // （CLONE_DECISION）：过滤按生成状态四态（全部/待确认/已完成/失败），
  // ready 卡播放钮打开 <video> 灯箱（无源时显示本地原型提示）。
  const [statusFilter, setStatusFilter] = useState<"all" | "pending" | "ready" | "failed">("all");
  const [filterMenuOpen, setFilterMenuOpen] = useState(false);
  const [playingVideoId, setPlayingVideoId] = useState<string | null>(null);
  const filterLabel = statusFilter === "all" ? "全部" : statusFilter === "pending" ? "待确认" : statusFilter === "ready" ? "已完成" : "失败";
  const visibleVideoNodes = statusFilter === "all"
    ? videoNodes
    : videoNodes.filter((node) => (str(nodeData(node).status) ?? "empty") === statusFilter);
  const playingNode = playingVideoId ? videoNodes.find((node) => node.id === playingVideoId) : null;

  return (
    <div data-storyboard-board className="h-full min-w-0 overflow-hidden bg-[#141414] p-4 pt-16">
      <div className="flex h-full min-w-0 gap-4">
        {/* 音频栏 */}
        <section data-storyboard-column="audio" className="flex w-[19%] min-w-[264px] shrink-0 flex-col overflow-hidden rounded-xl border border-white/[0.06] bg-[#181818]">
          <header className="flex h-12 shrink-0 items-center px-4 text-[15px] text-[#ececec]">
            音频
          </header>
          <div className="flex-1 space-y-4 overflow-y-auto p-4 pt-1">
            {audioNodes.length > 0 ? audioNodes.map((node) => (
              <button
                key={node.id}
                type="button"
                data-storyboard-card={node.id}
                aria-pressed={selectedNodeId === node.id}
                onClick={() => select(node.id)}
                className={cn(
                  "block w-fit text-left transition-opacity",
                  selectedNodeId === node.id ? "opacity-100" : "opacity-90 hover:opacity-100",
                )}
              >
                <span className="flex size-24 flex-col items-center justify-center gap-1.5 rounded-xl bg-[#1f1f1f] text-[#b9b9b9]">
                  <AudioLines size={22} />
                  <span data-storyboard-audio-duration className="text-[10px] tabular-nums text-[#8b8b8b]">
                    {audioDuration(node) ?? "00:00"}
                  </span>
                </span>
                <span className="mt-2 block max-w-40 truncate text-xs text-[#c9c9c9]">{nodeLabel(node)}</span>
              </button>
            )) : <EmptyColumn kind="audio" label="暂无音频" />}
          </div>
        </section>

        {/* 图片栏 */}
        <section data-storyboard-column="image" className="flex w-[39%] min-w-[360px] shrink-0 flex-col overflow-hidden rounded-xl border border-white/[0.06] bg-[#181818]">
          <header className="flex h-12 shrink-0 items-center px-4 text-[15px] text-[#ececec]">
            图片
            <button
              type="button"
              data-storyboard-expand="image"
              aria-label="放大图片栏"
              className="ml-auto flex size-7 items-center justify-center rounded-md text-[#8c8c8c] hover:bg-white/[0.07] hover:text-white"
            >
              <Maximize2 size={14} />
            </button>
          </header>
          <div className="flex-1 overflow-y-auto p-4 pt-1">
            <div className="mb-3 flex items-center justify-between">
              <span className="flex items-center gap-1.5 text-xs text-[#8b8b8b]">
                <ImageIcon size={13} />
                图片
              </span>
              <button
                type="button"
                data-storyboard-dialog="image"
                className="flex h-7 items-center gap-1.5 rounded-md bg-[#262626] px-2 text-xs text-[#c9c9c9] hover:bg-[#303030]"
              >
                <MessageSquareText size={13} />
                对话
              </button>
            </div>
            <div className="flex flex-wrap gap-4">
              {imageNodes.length > 0 ? imageNodes.map((node) => {
                const dim = dimension(node);
                const src = imageUrl(node);
                return (
                  <button
                    key={node.id}
                    type="button"
                    data-storyboard-card={node.id}
                    aria-pressed={selectedNodeId === node.id}
                    onClick={() => select(node.id)}
                    className={cn(
                      "block w-fit text-left",
                      selectedNodeId === node.id ? "outline outline-1 outline-[#09caf5]" : "",
                    )}
                  >
                    <span className="block h-[132px] w-[99px] overflow-hidden rounded-lg bg-[#1f1f1f]">
                      {src ? (
                        <Image src={src} alt="" width={198} height={264} className="size-full object-cover" unoptimized />
                      ) : (
                        <span className="flex size-full items-center justify-center text-[#666]">
                          <ImageIcon size={16} />
                        </span>
                      )}
                    </span>
                    {dim && (
                      <span data-storyboard-dimension={node.id} className="mt-2 inline-block rounded bg-[#262626] px-1.5 py-0.5 text-[10px] text-[#9a9a9a]">
                        {dim}
                      </span>
                    )}
                  </button>
                );
              }) : <EmptyColumn kind="image" label="暂无图片" />}
            </div>
          </div>
        </section>

        {/* 视频栏 */}
        <section data-storyboard-column="video" className="flex min-w-0 flex-1 flex-col overflow-hidden rounded-xl border border-white/[0.06] bg-[#181818]">
          <header className="flex h-12 shrink-0 items-center px-4 text-[15px] text-[#ececec]">
            视频
            <span className="relative ml-auto">
              <button
                type="button"
                data-storyboard-filter={statusFilter}
                aria-expanded={filterMenuOpen}
                onClick={() => setFilterMenuOpen((open) => !open)}
                className="flex h-7 items-center gap-1 rounded-md px-2 text-xs text-[#c9c9c9] hover:bg-white/[0.07]"
              >
                {filterLabel}
                <ChevronDown size={13} className="text-[#8c8c8c]" />
              </button>
              {filterMenuOpen && (
                <span data-storyboard-filter-menu className="absolute right-0 top-8 z-30 flex w-28 flex-col rounded-lg border border-white/[0.08] bg-[#262626] p-1 shadow-[0_12px_32px_rgba(0,0,0,0.5)]">
                  {([
                    ["all", "全部"],
                    ["pending", "待确认"],
                    ["ready", "已完成"],
                    ["failed", "失败"],
                  ] as const).map(([value, label]) => (
                    <button
                      key={value}
                      type="button"
                      data-storyboard-filter-option={value}
                      aria-pressed={statusFilter === value}
                      onClick={() => {
                        setStatusFilter(value);
                        setFilterMenuOpen(false);
                      }}
                      className="flex h-8 items-center justify-between rounded-md px-2 text-left text-xs text-[#d4d4d4] hover:bg-white/[0.07]"
                    >
                      {label}
                      {statusFilter === value && <span className="text-[#09caf5]">✓</span>}
                    </button>
                  ))}
                </span>
              )}
            </span>
            <button
              type="button"
              data-storyboard-expand="video"
              aria-label="放大视频栏"
              className="ml-2 flex size-7 items-center justify-center rounded-md text-[#8c8c8c] hover:bg-white/[0.07] hover:text-white"
            >
              <Scan size={14} />
            </button>
          </header>
          <div className="flex-1 overflow-y-auto p-4 pt-1">
            <div className="mb-3 flex items-center gap-1.5 text-xs text-[#8b8b8b]">
              <Play size={13} />
              视频
            </div>
            <div className="flex flex-wrap gap-5">
              {visibleVideoNodes.length > 0 ? visibleVideoNodes.map((node) => {
                const data = nodeData(node);
                const model = str(data.model);
                const status = str(data.status);
                const refs = references(node);
                return (
                  <span key={node.id} className="block">
                    <button
                      type="button"
                      data-storyboard-card={node.id}
                      data-storyboard-video-status={status ?? "empty"}
                      aria-pressed={selectedNodeId === node.id}
                      onClick={() => select(node.id)}
                      className={cn(
                        "block w-fit overflow-hidden rounded-lg border text-left",
                        selectedNodeId === node.id ? "border-[#09caf5]" : "border-white/[0.07]",
                      )}
                    >
                      <span className="relative flex aspect-video w-[300px] items-center justify-center overflow-hidden bg-[#161616]">
                        {imageUrl(node) && (
                          <Image src={imageUrl(node) as string} alt="" width={600} height={338} className="absolute inset-0 size-full object-cover opacity-80" unoptimized />
                        )}
                        <span className="relative">
                          <VideoStatusOverlay status={status} onPlay={() => setPlayingVideoId(node.id)} />
                        </span>
                      </span>
                      <span className="flex flex-col gap-2 p-3">
                        {model && (
                          <span data-storyboard-model={node.id} className="inline-flex w-fit items-center gap-1.5 rounded bg-[#262626] px-2 py-1 text-[11px] text-[#d4d4d4]">
                            <span className="text-[#9a9a9a]">✦</span>
                            {model}
                          </span>
                        )}
                        {refs.length > 0 && (
                          <span className="flex items-center gap-1.5">
                            {refs.slice(0, 3).map((ref, index) => (
                              <span key={`${ref}-${index}`} className="size-8 overflow-hidden rounded bg-[#262626]">
                                <Image src={ref} alt="" width={64} height={64} className="size-full object-cover" unoptimized />
                              </span>
                            ))}
                          </span>
                        )}
                        <span className="max-w-[276px] truncate text-xs text-[#c9c9c9]">{nodeLabel(node)}</span>
                      </span>
                    </button>
                    {/* Batch 336: 确认条为卡片兄弟节点（button 不可嵌套）。 */}
                    {status === "pending" && selectedNodeId === node.id && (
                      <span className="mt-2 flex items-center gap-2" data-storyboard-pending-strip={node.id}>
                        <button
                          type="button"
                          data-storyboard-pending-confirm={node.id}
                          onClick={() => setVideoStatus(node.id, "ready")}
                          className="flex h-7 items-center rounded-md bg-[#09caf5] px-2.5 text-xs font-medium text-[#141414] hover:bg-[#2ad4f7]"
                        >
                          确认生成
                        </button>
                        <button
                          type="button"
                          data-storyboard-pending-cancel={node.id}
                          onClick={() => setVideoStatus(node.id, "empty")}
                          className="flex h-7 items-center rounded-md bg-[#262626] px-2.5 text-xs text-[#c9c9c9] hover:bg-[#303030]"
                        >
                          取消
                        </button>
                      </span>
                    )}
                  </span>
                );
              }) : <EmptyColumn kind="video" label={statusFilter === "all" ? "暂无视频" : "该状态下暂无视频"} />}
            </div>
          </div>
        </section>
      </div>
      {playingNode && (
        <div
          data-storyboard-lightbox
          className="fixed inset-0 z-[90] flex items-center justify-center bg-black/70"
          onClick={() => setPlayingVideoId(null)}
        >
          <div className="flex flex-col items-center gap-3" onClick={(event) => event.stopPropagation()}>
            {str(nodeData(playingNode).videoUrl) ? (
              <video
                data-storyboard-lightbox-player
                src={str(nodeData(playingNode).videoUrl) as string}
                controls
                autoPlay
                className="max-h-[80vh] w-[80vw] max-w-[960px] rounded-xl bg-black"
              />
            ) : (
              <div className="flex h-64 w-[560px] flex-col items-center justify-center gap-2 rounded-xl bg-[#1b1b1b] text-sm text-[#9a9a9a]">
                <Play size={22} />
                本地原型：该视频节点无视频源
              </div>
            )}
            <button
              type="button"
              data-storyboard-lightbox-close
              onClick={() => setPlayingVideoId(null)}
              className="rounded-lg bg-[#262626] px-3 py-1.5 text-xs text-[#d4d4d4] hover:bg-[#303030]"
            >
              关闭
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
