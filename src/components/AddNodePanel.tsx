"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  ArrowRight,
  Clapperboard,
  FileText,
  Film,
  FolderOpen,
  ImageIcon,
  Library,
  Mic2,
  ScanLine,
  Search,
  Upload,
  Video,
} from "lucide-react";
import { useUIStore } from "@/store/uiStore";
import { useCanvasStore } from "@/store/canvasStore";
import type { LibTVLocalFileDescriptor } from "@/lib/libtvMediaIngress";
import {
  formatLibTVCommandStatus,
  projectLibTVCommandFeedback,
} from "@/lib/libtvCommandFeedback";

interface NodeEntry {
  type: string;
  label: string;
  icon: React.ComponentType<{ size?: number }>;
  badge?: string;
  action?: "create" | "material" | "script";
  arrow?: boolean;
}

const nodeEntries: NodeEntry[] = [
  { type: "text", label: "文本", icon: FileText },
  { type: "image", label: "图片", icon: ImageIcon },
  { type: "video", label: "视频", icon: Video },
  { type: "video-clip", label: "智能剪辑", icon: Film, badge: "Beta" },
  { type: "script-execution", label: "导演台", icon: Clapperboard, badge: "NEW" },
  { type: "shot-breakdown", label: "逐帧拉片", icon: ScanLine, badge: "SD 2.5" },
  { type: "audio", label: "音频", icon: Mic2 },
  { type: "script", label: "脚本", icon: FileText, action: "script", arrow: true },
  { type: "material", label: "素材库", icon: Library, action: "material", arrow: true },
];

interface AddNodePanelProps {
  onAddNode: (type: string, data?: Record<string, unknown>) => void;
}

export function AddNodePanel({ onAddNode }: AddNodePanelProps) {
  const { isAddNodePanelOpen, toggleAddNodePanel, setPrimaryPanel } = useUIStore();
  const panelRef = useRef<HTMLDivElement>(null);
  const [materialSubmenuOpen, setMaterialSubmenuOpen] = useState(false);
  const [scriptSubmenuOpen, setScriptSubmenuOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [status, setStatus] = useState<{ text: string; tone: "neutral" | "positive" | "diagnostic" }>({
    text: "",
    tone: "neutral",
  });
  const resourceInputRef = useRef<HTMLInputElement>(null);
  // Batch 478 (VR-021 Slice D): fixture generated-history assets — local
  // fixture data only, no account/backend claim (contract boundary).
  const historyAssets = [
    { assetId: "fixture-hist-0", renderUrl: "/images/scene-coffee-1.png", mediaFamily: "image" as const },
    { assetId: "fixture-hist-1", renderUrl: "/images/scene-coffee-4.png", mediaFamily: "image" as const },
  ];
  const [historyOpen, setHistoryOpen] = useState(false);
  const attachFixtureAsset = (index: number) => {
    const asset = historyAssets[index];
    if (!asset) return;
    const generation = useCanvasStore.getState().canvasGeneration;
    const result = useCanvasStore
      .getState()
      .attachAssetReferences("GENERATED_HISTORY_ATTACH", [asset], generation);
    if (result.status === "rejected") {
      setStatus({ text: result.reasons.join(" · "), tone: "diagnostic" });
    } else {
      setHistoryOpen(false);
      setStatus({ text: "已从生成历史添加资源", tone: "positive" });
    }
  };
  const closePanel = useCallback(() => {
    setMaterialSubmenuOpen(false);
    setScriptSubmenuOpen(false);
    setSearchOpen(false);
    setSearchQuery("");
    setStatus({ text: "", tone: "neutral" });
    toggleAddNodePanel();
  }, [toggleAddNodePanel]);

  useEffect(() => {
    if (!isAddNodePanelOpen) return;

    const handleClickOutside = (event: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(event.target as Node)) {
        closePanel();
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [closePanel, isAddNodePanelOpen]);

  if (!isAddNodePanelOpen) return null;

  const createNode = (type: string) => {
    // Batch 268: 源站 2026-09-10 截图——新建图片节点为空占位（山形图标），
    // 不带默认示例图；尝试建议行（图生图/图片高清）依赖空态渲染。
    if (type === "image") {
      onAddNode(type, { imageUrl: null, watermarkUrl: null });
    } else {
      onAddNode(type);
    }
    closePanel();
  };

  const openMaterialLibrary = () => {
    setPrimaryPanel("material");
  };

  // Batch 453 (VR-021 Slice C): Add Resource cohort entry — File objects
  // are reduced to LOCAL_FILE descriptors before touching the store; the
  // actual bytes never enter graph state.
  const submitResourceFiles = (files: FileList | null) => {
    if (!files || files.length === 0) return;
    const descriptors: LibTVLocalFileDescriptor[] = Array.from(files).map(
      (file) => ({
        kind: "LOCAL_FILE" as const,
        name: file.name,
        declaredMimeType: file.type,
        sizeBytes: file.size,
        lastModified: file.lastModified,
      }),
    );
    const generation = useCanvasStore.getState().canvasGeneration;
    const result = useCanvasStore
      .getState()
      .addResourceCohort(descriptors, generation);
    if (result.status === "accepted") {
      setStatus(
        formatLibTVCommandStatus(
          projectLibTVCommandFeedback("accepted"),
          `已添加 ${result.nodeIds.length} 个资源`,
        ),
      );
      window.setTimeout(closePanel, 600);
    } else {
      setStatus(
        formatLibTVCommandStatus(
          projectLibTVCommandFeedback("rejected"),
          result.reasons.join(" · "),
        ),
      );
    }
  };

  const normalizedQuery = searchQuery.trim().toLowerCase();
  const visibleEntries = normalizedQuery
    ? nodeEntries.filter((entry) => entry.label.toLowerCase().includes(normalizedQuery))
    : nodeEntries;

  return (
    <div
      ref={panelRef}
      data-liblib-overlay="add-node"
      /* Batch 150: 源站 2026-09-07 容器类——rounded-2xl + backdrop-blur-[32px] + hairline 边框。 */
      className="fixed bottom-[69px] left-[calc(50%-242px)] z-[62] h-[481px] w-[196px] rounded-2xl border border-white/[0.08] bg-[#262626]/85 p-2 shadow-[0_18px_48px_rgba(0,0,0,0.5)] backdrop-blur-[32px] max-sm:bottom-[109px] max-sm:left-3"
    >
      <div className="flex items-center justify-between px-2 pb-1.5 pt-1">
        <h3 className="text-xs font-medium text-[#9a9a9a]">添加节点</h3>
        <button
          type="button"
          data-add-node-search-toggle
          aria-label="搜索画布节点"
          title="搜索画布节点"
          onClick={() => {
            setSearchOpen((value) => !value);
            setSearchQuery("");
          }}
          className="flex size-6 items-center justify-center rounded-md text-[#9a9a9a] hover:bg-white/[0.07] hover:text-white"
        >
          <Search size={13} />
        </button>
      </div>
      {searchOpen && (
        <div className="px-1 pb-1.5">
          <input
            data-add-node-search
            value={searchQuery}
            onChange={(event) => setSearchQuery(event.target.value)}
            placeholder="搜索画布节点"
            aria-label="搜索画布节点"
            className="h-7 w-full rounded-lg border border-white/[0.1] bg-[#1f1f1f] px-2 text-xs text-[#eeeeee] outline-none placeholder:text-[#666] focus:border-white/25"
          />
        </div>
      )}
      <div className="space-y-1">
        {visibleEntries.map((entry) => {
          const Icon = entry.icon;
          return (
            <button
              key={entry.type}
              type="button"
              data-add-node-entry={entry.type}
              onClick={() => {
                if (entry.action === "material") {
                  setScriptSubmenuOpen(false);
                  setMaterialSubmenuOpen((value) => !value);
                  return;
                }
                if (entry.action === "script") {
                  setMaterialSubmenuOpen(false);
                  setScriptSubmenuOpen((value) => !value);
                  return;
                }
                createNode(entry.type);
              }}
              className="flex h-8 w-full items-center gap-2.5 rounded-lg px-2 text-left text-sm text-[#eeeeee] hover:bg-white/[0.07]"
            >
              <Icon size={15} />
              <span className="flex-1">{entry.label}</span>
              {entry.badge && (
                <span className="rounded bg-[#3b3b3b] px-1.5 py-0.5 text-[9px] text-[#bcbcbc]">
                  {entry.badge}
                </span>
              )}
              {entry.arrow && <ArrowRight data-add-node-arrow size={13} className="text-[#777]" />}
            </button>
          );
        })}
        {visibleEntries.length === 0 && (
          <p data-add-node-empty className="px-2 py-1.5 text-[11px] text-[#888]">
            无匹配节点
          </p>
        )}
      </div>

      {scriptSubmenuOpen && (
        <div
          data-add-node-submenu="script"
          className="absolute left-[calc(100%+8px)] top-[252px] w-44 rounded-xl border border-[#363636] bg-[#262626] p-1.5 shadow-[0_18px_48px_rgba(0,0,0,0.5)] max-sm:left-3 max-sm:top-[calc(100%+8px)]"
        >
          <p className="px-2 py-1.5 text-[11px] text-[#888]">脚本</p>
          <button
            type="button"
            data-add-node-entry="script-new"
            onClick={() => createNode("script-generator")}
            className="flex h-9 w-full items-center justify-between rounded-lg px-2 text-left text-xs text-[#e8e8e8] hover:bg-white/[0.07]"
          >
            脚本
            <span className="rounded bg-[#3b3b3b] px-1.5 py-0.5 text-[9px] text-[#bcbcbc]">NEW</span>
          </button>
          <button
            type="button"
            data-add-node-entry="script-legacy"
            onClick={() => createNode("script")}
            className="flex h-9 w-full items-center justify-between rounded-lg px-2 text-left text-xs text-[#e8e8e8] hover:bg-white/[0.07]"
          >
            脚本（旧版）
            <span className="rounded bg-[#3b3b3b] px-1.5 py-0.5 text-[9px] text-[#bcbcbc]">Beta</span>
          </button>
        </div>
      )}

      {materialSubmenuOpen && (
        <div
          data-add-node-submenu="material"
          className="absolute left-[calc(100%+8px)] top-[288px] w-44 rounded-xl border border-[#363636] bg-[#262626] p-1.5 shadow-[0_18px_48px_rgba(0,0,0,0.5)] max-sm:left-3 max-sm:top-[calc(100%+8px)]"
        >
          <p className="px-2 py-1.5 text-[11px] text-[#888]">素材库</p>
          <button type="button" data-add-node-entry="material-style" onClick={openMaterialLibrary} className="flex h-9 w-full items-center rounded-lg px-2 text-left text-xs text-[#e8e8e8] hover:bg-white/[0.07]">
            风格库
          </button>
          <button type="button" data-add-node-entry="material-effect" onClick={openMaterialLibrary} className="flex h-9 w-full items-center rounded-lg px-2 text-left text-xs text-[#e8e8e8] hover:bg-white/[0.07]">
            特效库
          </button>
        </div>
      )}

      <div className="my-2 h-px bg-white/[0.08]" />
      <h3 className="px-2 pb-1.5 text-xs font-medium text-[#9a9a9a]">添加资源</h3>
      <button type="button" data-add-node-resource="upload" onClick={() => resourceInputRef.current?.click()} className="flex h-8 w-full items-center gap-2.5 rounded-lg px-2 text-sm text-[#eeeeee] hover:bg-white/[0.07]">
        <Upload size={15} />
        <span>上传</span>
      </button>
      <input
        ref={resourceInputRef}
        type="file"
        multiple
        accept="image/png,image/jpeg,image/webp"
        data-add-resource-input
        className="sr-only"
        onChange={(event) => {
          submitResourceFiles(event.target.files);
          event.target.value = "";
        }}
      />
      <button type="button" data-add-node-resource="history" onClick={() => setHistoryOpen((open) => !open)} className="flex h-8 w-full items-center gap-2.5 rounded-lg px-2 text-sm text-[#eeeeee] hover:bg-white/[0.07]">
        <FolderOpen size={15} />
        <span>从生成历史选择</span>
      </button>
      {historyOpen && (
        <div
          data-add-node-submenu="history"
          className="absolute left-[calc(100%+8px)] top-[286px] w-44 rounded-xl border border-[#363636] bg-[#262626] p-1.5 shadow-[0_18px_48px_rgba(0,0,0,0.5)] max-sm:left-3 max-sm:top-[calc(100%+8px)]"
        >
          <p className="px-2 py-1.5 text-[11px] text-[#888]">生成历史（fixture 数据）</p>
          <button type="button" data-history-asset="0" onClick={() => attachFixtureAsset(0)} className="flex h-8 w-full items-center gap-2 rounded-lg px-2 text-left text-xs text-[#e8e8e8] hover:bg-white/[0.07]">
            <ImageIcon size={13} /> 咖啡馆漫步 · 成品
          </button>
          <button type="button" data-history-asset="1" onClick={() => attachFixtureAsset(1)} className="flex h-8 w-full items-center gap-2 rounded-lg px-2 text-left text-xs text-[#e8e8e8] hover:bg-white/[0.07]">
            <ImageIcon size={13} /> 城市夜景 · 成品
          </button>
        </div>
      )}
      {status && (
        <p
          data-add-node-status
          data-status-tone={status.tone}
          className={`mt-2 px-2 text-[10px] leading-4 ${
            status.tone === "diagnostic"
              ? "text-[#ff9c8e]"
              : status.tone === "positive"
                ? "text-[#8fe8b4]"
                : "text-[#75d7e8]"
          }`}
        >
          {status.text}
        </p>
      )}
    </div>
  );
}
