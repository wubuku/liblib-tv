"use client";

import Image from "next/image";
import type { Node } from "@xyflow/react";
import {
  ArrowDownAZ,
  ChevronDown,
  Clapperboard,
  FileText,
  Folder,
  ImageIcon,
  Play,
  Search,
  X,
} from "lucide-react";
import { useState } from "react";
import { useCanvasStore } from "@/store/canvasStore";
import { cn } from "@/lib/utils";

type AssetManagerTab = "canvas" | "assets";
type NodeFilter = "all" | "image" | "video" | "text" | "group";
type SortMode = "graph" | "name";

interface AssetManagerPanelProps {
  onClose: () => void;
  onOpenCanvasDropdown: () => void;
}

const filterOptions: Array<{ value: NodeFilter; label: string }> = [
  { value: "all", label: "全部" },
  { value: "image", label: "图片" },
  { value: "video", label: "视频" },
  { value: "text", label: "文本" },
  { value: "group", label: "分组" },
];

const sourceNodeOrder = [
  "i-YDfWhFlthe",
  "b-bTLLuU4w5q",
  "t-9j2MoccxBj",
  "i-dnwoZQ7jsG",
  "i-vxeeCnxySa",
  "i-1FQ9tErTcC",
  "i-lBzmo67AHv",
  "g-245IDFh8sB",
  "g-EFbbHpwq5w",
  "v-UGQZzZOpbv",
];

function nodeLabel(node: Node) {
  const data = node.data as Record<string, unknown>;
  if (node.type === "script-execution") return "3D导演台";
  if (typeof data.filename === "string") return data.filename;
  if (typeof data.title === "string") return data.title;
  return "未命名节点";
}

function NodeTypeIcon({ type }: { type: string | undefined }) {
  if (type === "image") return <ImageIcon size={14} />;
  if (type === "video") return <Play size={14} />;
  if (type === "storyboard-group") return <Folder size={14} />;
  if (type === "script-execution") return <Clapperboard size={14} />;
  return <FileText size={14} />;
}

function matchesFilter(node: Node, filter: NodeFilter) {
  if (filter === "all") return true;
  if (filter === "image" || filter === "video") return node.type === filter;
  if (filter === "text") return node.type === "script" || node.type === "text";
  return node.type === "storyboard-group";
}

function sourceRank(node: Node, fallbackIndex: number) {
  const rank = sourceNodeOrder.findIndex((id) => node.id.startsWith(id));
  return rank >= 0 ? rank : sourceNodeOrder.length + fallbackIndex;
}

function buildTreeRows(nodes: Node[], sortMode: SortMode) {
  const originalIndexes = new Map(nodes.map((node, index) => [node.id, index]));
  const sorted = [...nodes].sort((left, right) => {
    if (sortMode === "name") {
      return nodeLabel(left).localeCompare(nodeLabel(right), "zh-CN");
    }
    return sourceRank(left, originalIndexes.get(left.id) ?? 0)
      - sourceRank(right, originalIndexes.get(right.id) ?? 0);
  });
  const visibleIds = new Set(sorted.map((node) => node.id));
  const topLevel = sorted.filter((node) => !node.parentId || !visibleIds.has(node.parentId));
  const rows: Array<{ node: Node; depth: 0 | 1 }> = [];

  for (const node of topLevel) {
    rows.push({ node, depth: 0 });
    for (const child of sorted) {
      if (child.parentId === node.id) rows.push({ node: child, depth: 1 });
    }
  }
  return rows;
}

export function AssetManagerPanel({
  onClose,
  onOpenCanvasDropdown,
}: AssetManagerPanelProps) {
  const {
    projectName,
    canvases,
    activeCanvasId,
    selectedNodeId,
    selectNode,
  } = useCanvasStore();
  const [activeTab, setActiveTab] = useState<AssetManagerTab>("canvas");
  const [filter, setFilter] = useState<NodeFilter>("all");
  const [filterOpen, setFilterOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [sortMode, setSortMode] = useState<SortMode>("graph");
  const activeCanvas = canvases.find((canvas) => canvas.id === activeCanvasId);
  const nodes = activeCanvas?.nodes ?? [];
  const assetNodes = nodes.filter((node) => node.type === "image" || node.type === "video");
  const baseNodes = activeTab === "assets" ? assetNodes : nodes;
  const normalizedQuery = query.trim().toLocaleLowerCase("zh-CN");
  const filteredNodes = baseNodes.filter((node) => {
    if (!matchesFilter(node, filter)) return false;
    if (!normalizedQuery) return true;
    return nodeLabel(node).toLocaleLowerCase("zh-CN").includes(normalizedQuery);
  });
  const visibleRows = buildTreeRows(filteredNodes, sortMode);
  const activeFilterLabel = filterOptions.find((option) => option.value === filter)?.label ?? "全部";

  return (
    <aside data-liblib-overlay="asset" className="relative z-50 flex h-screen w-60 shrink-0 flex-col border-r border-white/[0.07] bg-[#171717] pt-12 text-[#e7e7e7]">
      <div data-asset-manager-context className="flex h-11 items-center gap-2 border-b border-white/[0.07] px-3 text-xs">
        <span data-asset-manager-project className="min-w-0 truncate text-[#e4e4e4]">{projectName}</span>
        <span className="h-3 w-px shrink-0 bg-white/10" />
        <button
          type="button"
          data-asset-manager-canvas
          onClick={onOpenCanvasDropdown}
          className="flex min-w-0 items-center gap-1 text-[#d0d0d0] hover:text-white"
        >
          <span className="truncate">{activeCanvas?.name ?? "画布"}</span>
          <ChevronDown size={12} className="shrink-0" />
        </button>
      </div>

      <div className="flex h-12 items-center border-b border-white/[0.07] px-2">
        <button
          type="button"
          data-asset-manager-tab="canvas"
          aria-pressed={activeTab === "canvas"}
          onClick={() => {
            setActiveTab("canvas");
            setFilter("all");
          }}
          className={cn(
            "h-7 rounded-md px-2 text-xs transition-colors",
            activeTab === "canvas" ? "bg-white/[0.09] text-white" : "text-[#777] hover:text-[#bbb]",
          )}
        >
          画布
        </button>
        <button
          type="button"
          data-asset-manager-tab="assets"
          aria-pressed={activeTab === "assets"}
          onClick={() => {
            setActiveTab("assets");
            setFilter("all");
          }}
          className={cn(
            "ml-1 h-7 rounded-md px-2 text-xs transition-colors",
            activeTab === "assets" ? "bg-white/[0.09] text-white" : "text-[#777] hover:text-[#bbb]",
          )}
        >
          资产
        </button>
        <button
          type="button"
          onClick={onClose}
          className="ml-auto flex h-7 w-7 items-center justify-center rounded-md text-[#777] hover:bg-white/[0.07] hover:text-white"
          aria-label="关闭资产管理"
        >
          <X size={14} />
        </button>
      </div>

      <div className="relative flex h-11 items-center border-b border-white/[0.05] px-3">
        <span data-asset-manager-heading className="text-xs text-[#929292]">
          {activeTab === "assets" ? "画布资产" : "画布元素"}
        </span>
        <button
          type="button"
          data-asset-manager-sort={sortMode}
          title={sortMode === "graph" ? "按名称排序" : "恢复画布顺序"}
          aria-label={sortMode === "graph" ? "按名称排序" : "恢复画布顺序"}
          onClick={() => setSortMode((mode) => (mode === "graph" ? "name" : "graph"))}
          className={cn(
            "ml-1 flex h-6 w-6 items-center justify-center rounded text-[#777] hover:bg-white/[0.07] hover:text-white",
            sortMode === "name" && "text-[#d7d7d7]",
          )}
        >
          <ArrowDownAZ size={13} />
        </button>
        <div className="relative ml-auto">
          <button
            type="button"
            data-asset-manager-filter={filter}
            aria-expanded={filterOpen}
            onClick={() => setFilterOpen((open) => !open)}
            className="flex h-7 items-center gap-1 rounded-md px-2 text-xs text-[#d0d0d0] hover:bg-white/[0.07]"
          >
            {activeFilterLabel}
            <ChevronDown size={11} />
          </button>
          {filterOpen && (
            <div className="absolute right-0 top-8 z-20 w-24 rounded-lg border border-white/10 bg-[#262626] p-1 shadow-xl">
              {filterOptions.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  data-asset-manager-filter-option={option.value}
                  onClick={() => {
                    setFilter(option.value);
                    setFilterOpen(false);
                  }}
                  className={cn(
                    "h-8 w-full rounded-md px-2 text-left text-xs hover:bg-white/[0.07]",
                    option.value === filter ? "text-white" : "text-[#a0a0a0]",
                  )}
                >
                  {option.label}
                </button>
              ))}
            </div>
          )}
        </div>
        <button
          type="button"
          data-asset-manager-search
          aria-expanded={searchOpen}
          aria-label="搜索画布元素"
          onClick={() => {
            setSearchOpen((open) => !open);
            if (searchOpen) setQuery("");
          }}
          className={cn(
            "ml-1 flex h-7 w-7 items-center justify-center rounded-md text-[#9a9a9a] hover:bg-white/[0.07] hover:text-white",
            searchOpen && "bg-white/[0.07] text-white",
          )}
        >
          <Search size={14} />
        </button>
      </div>

      {searchOpen && (
        <div className="border-b border-white/[0.05] px-3 py-2">
          <div className="flex h-8 items-center gap-2 rounded-md bg-[#242424] px-2">
            <Search size={13} className="text-[#686868]" />
            <input
              data-asset-manager-search-input
              autoFocus
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="搜索当前画布"
              className="min-w-0 flex-1 bg-transparent text-xs text-[#e0e0e0] outline-none placeholder:text-[#626262]"
            />
          </div>
        </div>
      )}

      <div data-asset-manager-list={activeTab} className="min-h-0 flex-1 overflow-y-auto px-2 py-2">
        {visibleRows.length > 0 ? (
          <div className="space-y-1">
            {visibleRows.map(({ node, depth }) => {
              const data = node.data as Record<string, unknown>;
              const imageUrl = typeof data.imageUrl === "string" ? data.imageUrl : null;
              const isGroup = node.type === "storyboard-group";
              return (
                <button
                  key={node.id}
                  type="button"
                  data-asset-manager-item={node.id}
                  data-asset-manager-depth={depth}
                  onClick={() => selectNode(node.id)}
                  className={cn(
                    "flex h-10 w-full items-center gap-2 rounded-lg pr-2 text-left hover:bg-white/[0.06]",
                    depth === 1 ? "pl-7" : "pl-2",
                    selectedNodeId === node.id && "bg-white/[0.09]",
                  )}
                >
                  {isGroup && <ChevronDown size={12} className="shrink-0 text-[#686868]" />}
                  {imageUrl ? (
                    <Image src={imageUrl} alt="" width={28} height={28} className="h-7 w-7 shrink-0 rounded object-cover" unoptimized />
                  ) : (
                    <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded bg-[#292929] text-[#929292]">
                      <NodeTypeIcon type={node.type} />
                    </span>
                  )}
                  <span className="min-w-0 flex-1 truncate text-xs text-[#cfcfcf]">{nodeLabel(node)}</span>
                </button>
              );
            })}
          </div>
        ) : (
          <div data-asset-manager-empty className="px-2 py-8 text-center text-xs text-[#666]">
            {activeTab === "assets" ? "当前画布暂无媒体资产" : "当前画布暂无节点"}
          </div>
        )}
      </div>

      <div className="h-10 border-t border-white/[0.07] px-4 text-xs leading-10 text-[#777]">
        {activeTab === "assets" ? `共 ${assetNodes.length} 项资产` : `共 ${nodes.length} 节点`}
      </div>
    </aside>
  );
}
