"use client";

import Image from "next/image";
import type { Node } from "@xyflow/react";
import { ChevronDown, FileText, ImageIcon, Play, Workflow } from "lucide-react";
import { cn } from "@/lib/utils";
import { useCanvasStore } from "@/store/canvasStore";
import { useUIStore } from "@/store/uiStore";

type NodeRecord = Record<string, unknown>;

function nodeData(node: Node): NodeRecord {
  return node.data as NodeRecord;
}

function nodeLabel(node: Node): string {
  const data = nodeData(node);
  if (typeof data.filename === "string") return data.filename;
  if (typeof data.title === "string") return data.title;
  return node.type ?? "未命名节点";
}

function nodeDimension(node: Node): string | null {
  const data = nodeData(node);
  const width = typeof data.width === "number" ? data.width : null;
  const height = typeof data.height === "number" ? data.height : null;
  if (width && height) return `${width} × ${height}`;
  return null;
}

function imageUrl(node: Node): string | null {
  const data = nodeData(node);
  return typeof data.imageUrl === "string" ? data.imageUrl : null;
}

function posterUrl(node: Node): string | null {
  const data = nodeData(node);
  return typeof data.posterUrl === "string" ? data.posterUrl : null;
}

function references(node: Node): string[] {
  const value = nodeData(node).references;
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [];
}

function EmptyState({ label }: { label: string }) {
  return <div className="flex min-h-24 items-center justify-center rounded-lg border border-dashed border-white/[0.08] px-3 text-center text-[11px] text-[#666]">{label}</div>;
}

function KeyElementCard({
  node,
  selected,
  onSelect,
}: {
  node: Node;
  selected: boolean;
  onSelect: () => void;
}) {
  const src = imageUrl(node);
  const isScript = node.type === "script";

  return (
    <button
      type="button"
      data-storyboard-card={node.id}
      aria-pressed={selected}
      onClick={onSelect}
      className={cn(
        "flex w-full items-center gap-2 rounded-lg border p-1.5 text-left transition-colors",
        selected ? "border-[#09caf5]/70 bg-[#09caf5]/10" : "border-white/[0.07] bg-[#222] hover:bg-[#2a2a2a]",
      )}
    >
      <span className="flex size-10 shrink-0 items-center justify-center overflow-hidden rounded-md bg-[#303030] text-[#8d8d8d]">
        {src ? (
          <Image src={src} alt="" width={80} height={80} className="size-full object-cover" unoptimized />
        ) : isScript ? (
          <FileText size={15} />
        ) : (
          <ImageIcon size={15} />
        )}
      </span>
      <span className="min-w-0 truncate text-[11px] text-[#d7d7d7]">{nodeLabel(node)}</span>
    </button>
  );
}

function StoryboardMediaCard({
  node,
  selected,
  onSelect,
}: {
  node: Node;
  selected: boolean;
  onSelect: () => void;
}) {
  const src = imageUrl(node) ?? posterUrl(node);
  const isVideo = node.type === "video";
  const refs = references(node);
  const dimension = nodeDimension(node);

  return (
    <button
      type="button"
      data-storyboard-card={node.id}
      aria-pressed={selected}
      onClick={onSelect}
      className={cn(
        "w-full overflow-hidden rounded-lg border text-left transition-colors",
        selected ? "border-[#09caf5] bg-[#09caf5]/[0.06]" : "border-white/[0.08] bg-[#222] hover:border-white/[0.16]",
      )}
    >
      <div className="relative aspect-video overflow-hidden bg-[#1b1b1b]">
        {src ? (
          <Image src={src} alt="" width={420} height={236} className="size-full object-cover" unoptimized />
        ) : isVideo ? (
          <div className="flex size-full items-center justify-center text-xs text-[#dd5c65]">
            <Play size={14} className="mr-1.5" />
            生成失败
          </div>
        ) : (
          <div className="flex size-full items-center justify-center text-xs text-[#666]">暂无预览</div>
        )}
      </div>
      <div className="space-y-2 p-2.5">
        <div className="flex items-center justify-between gap-2">
          <span className="min-w-0 truncate text-xs text-[#e7e7e7]">{nodeLabel(node)}</span>
          {isVideo && <span className="shrink-0 text-[10px] text-[#dd5c65]">失败</span>}
        </div>
        <div className="flex items-center gap-1.5 text-[10px] text-[#777]">
          <span className="rounded bg-white/[0.06] px-1.5 py-0.5">{isVideo ? "Lib Video" : "Lib Image"}</span>
          {dimension && <span>{dimension}</span>}
        </div>
        {refs.length > 0 && (
          <div className="flex items-center gap-1.5">
            {refs.slice(0, 3).map((ref, index) => (
              <span key={`${ref}-${index}`} className="size-7 overflow-hidden rounded bg-[#303030]">
                <Image src={ref} alt="" width={56} height={56} className="size-full object-cover" unoptimized />
              </span>
            ))}
          </div>
        )}
      </div>
    </button>
  );
}

function StoryboardColumn({
  kind,
  title,
  icon,
  nodes,
  selectedNodeId,
  onSelect,
}: {
  kind: "image" | "video" | "script";
  title: string;
  icon: React.ReactNode;
  nodes: Node[];
  selectedNodeId: string | null;
  onSelect: (nodeId: string) => void;
}) {
  return (
    <section data-storyboard-column={kind} className="flex min-h-full w-[204px] shrink-0 flex-col border-l border-white/[0.08] pl-3 first:border-l-0 first:pl-0">
      <header className="mb-3 flex h-7 items-center gap-2 text-xs text-[#9b9b9b]">
        {icon}
        <span>{title}</span>
        {kind !== "script" && (
          <button
            type="button"
            data-storyboard-zoom={kind}
            title={`放大${title}`}
            aria-label={`放大${title}`}
            className="ml-auto flex h-6 items-center rounded-md px-1.5 text-[11px] text-[#8c8c8c] hover:bg-white/[0.07] hover:text-white"
          >
            放大{title}
          </button>
        )}
        {kind !== "script" && <span className="text-[#5f5f5f]">{nodes.length}</span>}
      </header>
      <div className="space-y-3">
        {nodes.length > 0 ? nodes.map((node) => (
          <StoryboardMediaCard
            key={node.id}
            node={node}
            selected={selectedNodeId === node.id}
            onSelect={() => onSelect(node.id)}
          />
        )) : <EmptyState label={`暂无${title}`} />}
      </div>
    </section>
  );
}

export function StoryboardBoard() {
  const { canvases, activeCanvasId, selectedNodeId, selectNode } = useCanvasStore();
  const setEditorMode = useUIStore((state) => state.setEditorMode);
  const activeCanvas = canvases.find((canvas) => canvas.id === activeCanvasId);
  const nodes = activeCanvas?.nodes ?? [];
  const imageNodes = nodes.filter((node) => node.type === "image");
  const videoNodes = nodes.filter((node) => node.type === "video");
  const scriptNodes = nodes.filter((node) => node.type === "script");

  const selectStoryboardNode = (nodeId: string) => selectNode(nodeId);

  return (
    <div data-storyboard-board className="h-full min-w-0 overflow-hidden bg-[#141414] px-4 pb-24 pt-14">
      <div className="flex h-full min-w-0 gap-3">
        <aside data-storyboard-key-elements className={cn(
          "w-[148px] shrink-0 flex-col overflow-y-auto border-r border-white/[0.08] pr-3",
          // Batch 104: 源站空画布故事板只有 文本/图片/视频 三组 banner，无侧栏。
          imageNodes.length === 0 && scriptNodes.length === 0 ? "hidden" : "flex",
        )}>
          <header className="mb-3 flex min-h-8 items-center justify-between gap-2 text-xs text-[#e4e4e4]">
            <span className="font-medium">关键元素 · 全部</span>
            <ChevronDown size={13} className="text-[#777]" />
          </header>

          <section data-storyboard-key-group="image" className="space-y-2">
            <div className="flex items-center gap-2 text-[11px] text-[#8c8c8c]">
              <ImageIcon size={13} />
              <span>图片</span>
              <span className="ml-auto text-[#5f5f5f]">{imageNodes.length}</span>
            </div>
            <div className="space-y-1.5">
              {imageNodes.length > 0 ? imageNodes.map((node) => (
                <KeyElementCard
                  key={node.id}
                  node={node}
                  selected={selectedNodeId === node.id}
                  onSelect={() => selectStoryboardNode(node.id)}
                />
              )) : <EmptyState label="暂无图片元素" />}
            </div>
          </section>

          <section data-storyboard-key-group="text" className="mt-5 space-y-2">
            <div className="flex items-center gap-2 text-[11px] text-[#8c8c8c]">
              <FileText size={13} />
              <span>文本</span>
              <span className="ml-auto text-[#5f5f5f]">{scriptNodes.length}</span>
            </div>
            <div className="space-y-1.5">
              {scriptNodes.length > 0 ? scriptNodes.map((node) => (
                <KeyElementCard
                  key={node.id}
                  node={node}
                  selected={selectedNodeId === node.id}
                  onSelect={() => selectStoryboardNode(node.id)}
                />
              )) : <EmptyState label="暂无文本元素" />}
            </div>
          </section>
        </aside>

        <section className="min-w-0 flex-1 overflow-x-auto overflow-y-auto">
          <div className="min-h-full min-w-[636px]">
            <header className="mb-3 flex h-8 items-center justify-between text-xs text-[#e4e4e4]">
              <span className="font-medium">故事板</span>
              <button
                type="button"
                data-storyboard-return
                onClick={() => setEditorMode("workbench")}
                className="flex h-7 items-center gap-1.5 rounded-lg px-2 text-[11px] text-[#8c8c8c] hover:bg-white/[0.07] hover:text-white"
              >
                <Workflow size={13} />
                返回工作台
              </button>
            </header>
            <div className="flex min-h-[calc(100%-44px)] gap-3">
              <StoryboardColumn
                kind="script"
                title="文本"
                icon={<FileText size={14} />}
                nodes={scriptNodes}
                selectedNodeId={selectedNodeId}
                onSelect={selectStoryboardNode}
              />
              <StoryboardColumn
                kind="image"
                title="图片"
                icon={<ImageIcon size={14} />}
                nodes={imageNodes}
                selectedNodeId={selectedNodeId}
                onSelect={selectStoryboardNode}
              />
              <StoryboardColumn
                kind="video"
                title="视频"
                icon={<Play size={14} />}
                nodes={videoNodes}
                selectedNodeId={selectedNodeId}
                onSelect={selectStoryboardNode}
              />
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
