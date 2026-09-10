"use client";

import Image from "next/image";
import type { Node } from "@xyflow/react";
import {
  ArrowDownAZ,
  ArrowLeft,
  ChevronDown,
  Clapperboard,
  FileText,
  Folder,
  ImageIcon,
  List,
  MoreHorizontal,
  Play,
  Search,
  Send,
  X,
} from "lucide-react";
import { useState } from "react";
import { useCanvasStore } from "@/store/canvasStore";
import { cn } from "@/lib/utils";

type AssetManagerTab = "canvas" | "assets";
// Batch 205: 扩展至源站类型菜单的十项（type→node 类型映射见 matchesFilter）。
type NodeFilter =
  | "all"
  | "image"
  | "video"
  | "text"
  | "group"
  | "audio"
  | "video-clip"
  | "script-execution"
  | "shot-breakdown"
  | "script"
  | "script-generator";
type SortMode = "graph" | "name";

interface AssetManagerPanelProps {
  onClose: () => void;
  onOpenCanvasDropdown: () => void;
}

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
  if (node.type === "script-execution") return "导演台";
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
  if (filter === "image") return node.type === "image";
  if (filter === "video") return node.type === "video";
  if (filter === "text") return node.type === "script" || node.type === "text";
  if (filter === "audio") return node.type === "audio";
  if (filter === "video-clip") return node.type === "video-clip";
  if (filter === "script-execution") return node.type === "script-execution";
  if (filter === "shot-breakdown") return node.type === "shot-breakdown";
  if (filter === "script") return node.type === "script";
  if (filter === "script-generator") return node.type === "script-generator";
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
  const [searchOpen, setSearchOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [sortMode, setSortMode] = useState<SortMode>("graph");
  // Batch 264: 源站工具行右端的列表视图切换（菜单语义未采样，视觉开关）。
  const [listView, setListView] = useState(false);
  // Batch 102: 源站有 所有评级/展示设置 控件；其菜单语义未采样，clone 给诚实本地 hint。
  // Batch 203: 源站直采评级筛选菜单（6 项：所有评级/1-5）。clipPath 用近似负一星。
  const [ratingsOpen, setRatingsOpen] = useState(false);
  // Batch 204: 源站直采节点类型筛选菜单（10 项，滑杆图标触发）。
  const [typeMenuOpen, setTypeMenuOpen] = useState(false);
  const [typeFilter, setTypeFilter] = useState("全部");
  // Batch 298: 源站 2026-09-10 直采——展示设置实为视图布局菜单（列表展示/
  // 宫格展示/展开全部分组/收起全部分组）；类型筛选菜单迁至 筛选 按钮。
  const [viewMenuOpen, setViewMenuOpen] = useState(false);
  const [viewMode, setViewMode] = useState<"list" | "grid">("list");
  const [groupsExpanded, setGroupsExpanded] = useState(true);
  const [minRating, setMinRating] = useState<number | null>(null);
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
  const visibleRows = buildTreeRows(filteredNodes, sortMode)
    .filter((row) => groupsExpanded || row.depth === 0);

  return (
    <aside data-liblib-overlay="asset" // Batch 264: 源站 2026-09-10 重采抽屉宽 320（batch 202 的 ~280 已漂移）。
      className="relative z-50 flex h-screen w-[320px] shrink-0 flex-col border-r border-white/[0.07] bg-[#171717] pt-12 text-[#e7e7e7]">
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
          data-asset-manager-listview
          aria-pressed={listView}
          title="列表视图"
          onClick={() => setListView((view) => !view)}
          className={cn(
            "flex h-6 w-6 items-center justify-center rounded text-[#777] hover:bg-white/[0.07] hover:text-white",
            listView && "text-[#d7d7d7]",
          )}
        >
          <List size={13} />
        </button>
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
            aria-label={`筛选：${typeFilter}`}
            aria-expanded={typeMenuOpen}
            onClick={() => setTypeMenuOpen((open) => !open)}
            className="flex h-7 items-center gap-1 rounded-md px-2 text-xs text-[#d0d0d0] hover:bg-white/[0.07]"
          >
            {typeFilter}
            <ChevronDown size={11} />
          </button>
          {typeMenuOpen && (
            /* Batch 204: 源站节点类型筛选菜单直采（180×369，10 项）。
               Batch 298: 菜单自 展示设置 迁至 筛选 按钮（源站 2026-09-10
               对照：展示设置实为视图布局菜单）。
               Batch 305: 源站筛选选择后并不过滤列表（混合类型全显，
               batch 304 直采）——clone 的类型过滤联动为超出源站的
               CLONE_DECISION 附加行为，保留以维持本地 mock 可用性。 */
            <div data-asset-manager-typemenu className="absolute left-0 top-8 z-50 w-[180px] rounded-xl border border-white/[0.08] bg-[#262626] p-1.5 shadow-[var(--canvas-shadow-menu)]">
              {["全部", "文本", "图片", "视频", "智能剪辑", "导演台", "逐帧拉片", "音频", "脚本", "脚本（旧版）"].map((label) => (
                <button
                  key={label}
                  type="button"
                  data-asset-manager-type-option={label}
                  aria-pressed={typeFilter === label}
                  onClick={() => {
                    setTypeFilter(label);
                    const mapped: NodeFilter =
                      label === "全部" ? "all"
                      : label === "文本" ? "text"
                      : label === "图片" ? "image"
                      : label === "视频" ? "video"
                      : label === "智能剪辑" ? "video-clip"
                      : label === "导演台" ? "script-execution"
                      : label === "逐帧拉片" ? "shot-breakdown"
                      : label === "音频" ? "audio"
                      : label === "脚本" ? "script-generator"
                      : "script";
                    setFilter(mapped);
                    setTypeMenuOpen(false);
                  }}
                  className={cn(
                    "flex h-8 w-full items-center rounded-lg px-2 text-left text-xs transition-colors",
                    typeFilter === label ? "bg-white/[0.1] text-white" : "text-[#ccc] hover:bg-white/[0.06]",
                  )}
                >
                  {label}
                </button>
              ))}
            </div>
          )}
        </div>
        <div className="relative shrink-0">
          <button
            type="button"
            data-asset-manager-rating
            onClick={() => setRatingsOpen(!ratingsOpen)}
            className="flex h-7 shrink-0 items-center rounded-md px-1.5 text-xs text-[#9a9a9a] hover:bg-white/[0.07] hover:text-white"
          >
            {minRating ? String(minRating) : "所有评级"}
          </button>
          {ratingsOpen && (
            /* Batch 203: 源站菜单直采（180×225，6 项：所有评级/1-5）。 */
            <div data-asset-manager-rating-menu className="absolute left-0 top-8 z-50 w-[180px] rounded-xl border border-white/[0.08] bg-[#262626] p-1.5 shadow-[var(--canvas-shadow-menu)]">
              {[null, 1, 2, 3, 4, 5].map((value) => (
                <button
                  key={value ?? "all"}
                  type="button"
                  data-asset-manager-rating-option={value ?? "all"}
                  aria-pressed={minRating === value}
                  onClick={() => {
                    setMinRating(value);
                    setRatingsOpen(false);
                  }}
                  className={cn(
                    "flex h-8 w-full items-center rounded-lg px-2 text-left text-xs transition-colors",
                    minRating === value ? "bg-white/[0.1] text-white" : "text-[#ccc] hover:bg-white/[0.06]",
                  )}
                >
                  {value ?? "所有评级"}
                </button>
              ))}
            </div>
          )}
        </div>
        <div className="relative shrink-0">
          <button
            type="button"
            data-asset-manager-display
            aria-expanded={viewMenuOpen}
            onClick={() => setViewMenuOpen((open) => !open)}
            className="flex h-7 shrink-0 items-center rounded-md px-1.5 text-xs text-[#9a9a9a] hover:bg-white/[0.07] hover:text-white"
          >
            展示设置
          </button>
          {viewMenuOpen && (
            /* Batch 297/298: 源站 2026-09-10 直采（180×167，4 项）——展示设置
               为视图布局菜单：列表/宫格展示 + 分组展开/收起。类型筛选菜单
               已迁至 筛选 按钮（batch 204 采样内容保留）。 */
            <div data-asset-manager-viewmenu className="absolute right-0 top-8 z-50 w-[180px] rounded-xl border border-white/[0.08] bg-[#262626] p-1 shadow-[var(--canvas-shadow-menu)]">
              {[
                { label: "列表展示", value: "list" as const },
                { label: "宫格展示", value: "grid" as const },
              ].map((option) => (
                <button
                  key={option.value}
                  type="button"
                  data-asset-manager-view-option={option.value}
                  aria-pressed={viewMode === option.value}
                  onClick={() => {
                    setViewMode(option.value);
                    setViewMenuOpen(false);
                  }}
                  className={cn(
                    "flex h-8 w-full items-center rounded-lg px-2 text-left text-xs transition-colors",
                    viewMode === option.value ? "bg-white/[0.1] text-white" : "text-[#ccc] hover:bg-white/[0.06]",
                  )}
                >
                  {option.label}
                </button>
              ))}
              <button
                type="button"
                data-asset-manager-expand-groups
                onClick={() => {
                  setGroupsExpanded(true);
                  setViewMenuOpen(false);
                }}
                className="flex h-8 w-full items-center rounded-lg px-2 text-left text-xs text-[#ccc] transition-colors hover:bg-white/[0.06]"
              >
                展开全部分组
              </button>
              <button
                type="button"
                data-asset-manager-collapse-groups
                onClick={() => {
                  setGroupsExpanded(false);
                  setViewMenuOpen(false);
                }}
                className="flex h-8 w-full items-center rounded-lg px-2 text-left text-xs text-[#ccc] transition-colors hover:bg-white/[0.06]"
              >
                收起全部分组
              </button>
            </div>
          )}
        </div>
        <button
          type="button"
          data-asset-manager-search
          aria-expanded={searchOpen}
          aria-label="搜索节点"
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
              placeholder="搜索节点"
              className="min-w-0 flex-1 bg-transparent text-xs text-[#e0e0e0] outline-none placeholder:text-[#626262]"
            />
          </div>
        </div>
      )}

      <div data-asset-manager-list={activeTab} className="min-h-0 flex-1 overflow-y-auto px-2 py-2">
        {visibleRows.length > 0 ? (
          <div className={cn(viewMode === "grid" ? "flex flex-wrap gap-2" : "space-y-1")}>
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
                    "group flex h-10 items-center gap-2 rounded-lg pr-2 text-left hover:bg-white/[0.06]",
                    viewMode === "grid" ? "w-[144px] flex-col justify-center" : "w-full",
                    depth === 1 && viewMode === "list" ? "pl-7" : "pl-2",
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
                  {/* Batch 264: 源站条目悬停操作（… 菜单 / 发送）；点击行为未采样，视觉呈现。 */}
                  <span className="hidden shrink-0 items-center gap-1 text-[#9a9a9a] group-hover:flex">
                    <MoreHorizontal size={13} />
                    <Send size={12} />
                  </span>
                </button>
              );
            })}
          </div>
        ) : (
          <div data-asset-manager-empty className="px-2 py-8 text-center text-xs text-[#666]">
            {/* Batch 295: 源站 2026-09-10 直采——搜索无匹配有专属文案。 */}
            {normalizedQuery
              ? "当前画布没有相关搜索结果"
              : activeTab === "assets"
                ? "当前画布暂无媒体资产"
                : "画布暂无节点"}
          </div>
        )}
      </div>

      <div className="flex h-10 items-center gap-3 border-t border-white/[0.07] px-4 text-xs text-[#777]">
        <button
          type="button"
          data-asset-manager-collapse
          aria-label="收起节点侧栏"
          onClick={onClose}
          className="rounded p-1 hover:text-white"
        >
          <ArrowLeft size={14} />
        </button>
        <span data-asset-manager-count>
          {activeTab === "assets" ? `共 ${assetNodes.length} 项资产` : `共 ${nodes.length} 节点`}
        </span>
      </div>
    </aside>
  );
}
