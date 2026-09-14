"use client";

import { useCallback, useEffect, useState } from "react";
import {
  MiniMap,
  ReactFlow,
  ReactFlowProvider,
  useReactFlow,
  PanOnScrollMode,
  SelectionMode,
} from "@xyflow/react";
import type { NodeMouseHandler, OnMove } from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { useJimengStore } from "@/store/jimengStore";
import { JimengVideoNode } from "@/components/jimeng/nodes/JimengVideoNode";
import { JimengImageNode } from "@/components/jimeng/nodes/JimengImageNode";
import { JimengTextNode } from "@/components/jimeng/nodes/JimengTextNode";
import { JimengAudioNode } from "@/components/jimeng/nodes/JimengAudioNode";
import { JimengEdge } from "@/components/jimeng/JimengEdge";
import { JimengTopBar } from "@/components/jimeng/JimengTopBar";
import { JimengToolRail } from "@/components/jimeng/JimengToolRail";
import { JimengBottomDock } from "@/components/jimeng/JimengBottomDock";
import { JimengAiButton } from "@/components/jimeng/JimengAiButton";
import {
  JimengContextMenu,
} from "@/components/jimeng/JimengContextMenu";
import type { JimengContextMenuState } from "@/components/jimeng/JimengContextMenu";
import { JimengTaskToast } from "@/components/jimeng/JimengTaskToast";
import { JimengAiDrawer } from "@/components/jimeng/JimengAiDrawer";
import {
  JimengPaneContextMenu,
} from "@/components/jimeng/JimengPaneContextMenu";
import type { JimengPaneMenuState } from "@/components/jimeng/JimengPaneContextMenu";
import { JimengMultiSelectToolbar } from "@/components/jimeng/JimengMultiSelectToolbar";
import { JimengSelectionOutline } from "@/components/jimeng/JimengSelectionOutline";
import { JimengGroupFrames } from "@/components/jimeng/JimengGroupFrames";
import { JimengAssetsModal } from "@/components/jimeng/JimengAssetsModal";
import { JimengOfflineDialog } from "@/components/jimeng/JimengOfflineDialog";

/**
 * 即梦画布工作区编排。
 * 源站即 React Flow (xyflow v12)：初始视口 zoom 0.7299 / 平移 (-60.6, 1.3)
 * 与节点世界坐标均为提取证据 (SOURCE_FACT)。点阵网格在 jimeng-canvas.css 中实现。
 */
const nodeTypes = {
  video: JimengVideoNode,
  image: JimengImageNode,
  text: JimengTextNode,
  audio: JimengAudioNode,
};

const edgeTypes = {
  jimeng: JimengEdge,
};

const DEFAULT_VIEWPORT = { x: -60.6, y: 1.3, zoom: 0.7299 };

function JimengFlow() {
  const nodes = useJimengStore((s) => s.nodes);
  const edges = useJimengStore((s) => s.edges);
  const onNodesChange = useJimengStore((s) => s.onNodesChange);
  const onEdgesChange = useJimengStore((s) => s.onEdgesChange);
  const selectNode = useJimengStore((s) => s.selectNode);
  const setZoomPercent = useJimengStore((s) => s.setZoomPercent);
  const { fitView, zoomIn, zoomOut, getViewport, setViewport, screenToFlowPosition } =
    useReactFlow();
  const addNodeAt = useJimengStore((s) => s.addNodeAt);
  const copyNode = useJimengStore((s) => s.copyNode);
  const copyNodes = useJimengStore((s) => s.copyNodes);
  const duplicateNode = useJimengStore((s) => s.duplicateNode);
  const pasteNodes = useJimengStore((s) => s.pasteNodes);
  const removeNode = useJimengStore((s) => s.removeNode);
  const removeNodes = useJimengStore((s) => s.removeNodes);
  const pushToast = useJimengStore((s) => s.pushToast);
  const exitRepaint = useJimengStore((s) => s.exitRepaint);
  const exitEdit = useJimengStore((s) => s.exitEdit);
  const exitInfer = useJimengStore((s) => s.exitInfer);
  const exitFramePicker = useJimengStore((s) => s.exitFramePicker);
  const exitTrim = useJimengStore((s) => s.exitTrim);
  const undo = useJimengStore((s) => s.undo);
  const redo = useJimengStore((s) => s.redo);
  const past = useJimengStore((s) => s.past);
  const future = useJimengStore((s) => s.future);
  const selectedNodeId = useJimengStore((s) => s.selectedNodeId);
  const toolActive = useJimengStore((s) => s.toolActive);
  const setToolActive = useJimengStore((s) => s.setToolActive);
  const groupSelected = useJimengStore((s) => s.groupSelected);
  const ungroupSelected = useJimengStore((s) => s.ungroupSelected);
  const selectAll = useJimengStore((s) => s.selectAll);
  const closePreview = useJimengStore((s) => s.closePreview);
  const [contextMenu, setContextMenu] = useState<JimengContextMenuState | null>(
    null,
  );
  const [paneMenu, setPaneMenu] = useState<
    (JimengPaneMenuState & { flowX: number; flowY: number }) | null
  >(null);
  const clipboard = useJimengStore((s) => s.clipboard);
  const assetsOpen = useJimengStore((s) => s.assetsOpen);
  const setAssetsOpen = useJimengStore((s) => s.setAssetsOpen);
  const offlineDialogOpen = useJimengStore((s) => s.offlineDialogOpen);
  const setOfflineDialog = useJimengStore((s) => s.setOfflineDialog);
  const minimapOpen = useJimengStore((s) => s.minimapOpen);
  // Batch 66: 保存状态门控下载 (导出前请保存画布)
  const saved = useJimengStore((s) => s.project.saved);

  const onPaneClick = useCallback(() => {
    selectNode(null);
    exitRepaint();
    exitEdit();
    exitInfer();
    exitFramePicker();
    exitTrim();
    setContextMenu(null);
    setPaneMenu(null);
  }, [selectNode, exitRepaint, exitEdit, exitInfer, exitFramePicker, exitTrim]);

  // 空白右键菜单 (SOURCE_FACT batch 25): 记录屏幕坐标 + 对应画布坐标
  const onPaneContextMenu = useCallback(
    (event: React.MouseEvent | MouseEvent) => {
      event.preventDefault();
      const e = event as MouseEvent;
      const flow = screenToFlowPosition({ x: e.clientX, y: e.clientY });
      setPaneMenu({ x: e.clientX, y: e.clientY, flowX: flow.x, flowY: flow.y });
    },
    [screenToFlowPosition],
  );

  const onNodeContextMenu = useCallback<NodeMouseHandler>((event, node) => {
    const e = event as unknown as MouseEvent;
    e.preventDefault();
    setContextMenu({ x: e.clientX, y: e.clientY, nodeId: node.id });
  }, []);

  const onPaneInsert = useCallback(
    (kind: "video" | "image" | "text" | "audio") => {
      if (!paneMenu) return;
      addNodeAt(kind, { x: paneMenu.flowX, y: paneMenu.flowY });
    },
    [paneMenu, addNodeAt],
  );

  const onContextMenuAction = useCallback(
    (action: string) => {
      if (!contextMenu) return;
      // 多选判定 (Batch 64): 右键时选中数 >1 即多选菜单语义
      const selIds = nodes.filter((n) => n.selected).map((n) => n.id);
      const multi = selIds.length > 1;
      if (action === "copy") {
        // 多选时复制全部选中节点 (Batch 52)
        if (multi) copyNodes(selIds);
        else copyNode(contextMenu.nodeId);
      }
      if (action === "duplicate") {
        // 多选 复制副本 (Batch 64): 剪贴板中转 + 相对布局粘贴
        if (multi) {
          copyNodes(selIds);
          pasteNodes();
        } else {
          duplicateNode(contextMenu.nodeId);
        }
      }
      if (action === "group") groupSelected();
      if (action === "ungroup") ungroupSelected();
      if (action === "paste") pasteNodes();
      if (action === "delete") {
        // 多选时批量删除选中节点 (Batch 38)
        if (multi) removeNodes(selIds);
        else removeNode(contextMenu.nodeId);
      }
      if (action === "undo") undo();
      if (action === "redo") redo();
      if (action === "save-to-library") pushToast("已保存到主体库（mock）");
      if (action === "download") pushToast("视频下载已开始（mock）");
    },
    [contextMenu, copyNode, copyNodes, duplicateNode, pasteNodes, removeNode, removeNodes, undo, redo, groupSelected, ungroupSelected, nodes, pushToast],
  );

  // 键盘快捷键 (Batch 14): ⌘Z/⌘⇧Z/⌘C/⌘D/⌘V/Delete|Backspace
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      const mod = e.metaKey || e.ctrlKey;
      const target = e.target as HTMLElement | null;
      const inField =
        target &&
        (target.tagName === "INPUT" ||
          target.tagName === "TEXTAREA" ||
          target.isContentEditable);
      if (inField) return;
      if (mod && e.key.toLowerCase() === "z" && !e.shiftKey) {
        e.preventDefault();
        undo();
      } else if (mod && e.key.toLowerCase() === "z" && e.shiftKey) {
        e.preventDefault();
        redo();
      } else if (mod && e.key === "0") {
        // 快捷键面板证据: ⌘0 = 适配画布 (Batch 18)
        e.preventDefault();
        void fitView({ duration: 300 });
      } else if (!mod && e.key.toLowerCase() === "v" && !inField) {
        // 快捷键面板证据: V = 移动工具 (Batch 20)
        setToolActive(toolActive === "select" ? "move" : "select");
      } else if (!mod && e.key.toLowerCase() === "f" && !inField) {
        // 快捷键面板证据: F = 全屏 (Batch 20, CLONE_DECISION 浏览器全屏)
        e.preventDefault();
        if (document.fullscreenElement) {
          void document.exitFullscreen();
        } else {
          void document.documentElement.requestFullscreen().catch(() => {});
        }
      } else if (!mod && e.key === "1" && e.shiftKey && !inField) {
        // 快捷键面板证据: ⇧1 = 适配画布 (Batch 18/21)
        e.preventDefault();
        void fitView({ duration: 300 });
      } else if (mod && e.key === "1") {
        // 快捷键面板证据: ⌘1 = 缩放至 100% (Batch 21)
        e.preventDefault();
        const vp = getViewport();
        const el = document.querySelector(".jimeng-canvas");
        const w = el ? el.clientWidth / 2 : 0;
        const h = el ? el.clientHeight / 2 : 0;
        setViewport({
          x: w - (w - vp.x) * (1 / vp.zoom),
          y: h - (h - vp.y) * (1 / vp.zoom),
          zoom: 1,
        });
      } else if (e.key === "2" && e.shiftKey && !mod && !inField) {
        // 快捷键面板证据: ⇧2 = 缩放至选中项 (Batch 21)
        e.preventDefault();
        void fitView({ duration: 300, maxZoom: 1, padding: 0.4 });
      } else if (mod && (e.key === "+" || e.key === "=")) {
        // 快捷键面板证据: ⌘+ 放大 (Batch 21)
        e.preventDefault();
        void zoomIn({ duration: 200 });
      } else if (mod && (e.key === "-" || e.key === "_")) {
        // 快捷键面板证据: ⌘- 缩小 (Batch 21)
        e.preventDefault();
        void zoomOut({ duration: 200 });
      } else if (mod && e.key.toLowerCase() === "a") {
        // ⌘A 全选 (Batch 46)
        e.preventDefault();
        selectAll();
      } else if (e.key === "Escape") {
        selectNode(null);
        exitRepaint();
        exitEdit();
        exitInfer();
        exitFramePicker();
        exitTrim();
        closePreview();
        setAssetsOpen(false);
        setOfflineDialog(false);
      } else if (mod && e.key.toLowerCase() === "g" && e.shiftKey) {
        // 快捷键面板证据: ⌘⇧G = 取消编组 (Batch 39)
        e.preventDefault();
        ungroupSelected();
      } else if (mod && e.key.toLowerCase() === "g") {
        // 快捷键面板证据: ⌘G = 创建编组 (Batch 39)
        e.preventDefault();
        groupSelected();
      } else if (mod && e.key.toLowerCase() === "c" && selectedNodeId) {
        copyNode(selectedNodeId);
      } else if (mod && e.key.toLowerCase() === "d" && selectedNodeId) {
        e.preventDefault();
        duplicateNode(selectedNodeId);
      } else if (mod && e.key.toLowerCase() === "v") {
        pasteNodes();
      } else if (
        (e.key === "Delete" || e.key === "Backspace") &&
        selectedNodeId
      ) {
        e.preventDefault();
        removeNode(selectedNodeId);
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [
    undo,
    redo,
    copyNode,
    duplicateNode,
    pasteNodes,
    removeNode,
    selectedNodeId,
    toolActive,
    setToolActive,
    fitView,
    zoomIn,
    zoomOut,
    getViewport,
    setViewport,
    groupSelected,
    ungroupSelected,
    selectAll,
    selectNode,
    closePreview,
    setAssetsOpen,
    setOfflineDialog,
    exitRepaint,
    exitEdit,
    exitInfer,
    exitFramePicker,
    exitTrim,
  ]);

  const onMove = useCallback<OnMove>(
    (_event, viewport) => {
      setZoomPercent(viewport.zoom * 100);
    },
    [setZoomPercent],
  );

  return (
    <div className="jimeng-canvas relative h-full w-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        defaultEdgeOptions={{ type: "jimeng" }}
        multiSelectionKeyCode="Shift"
        /* 导航语义 (SOURCE_FACT, batch 21/55 提取): 空白左键拖拽 = 框选
           (marquee selection, 不平移)；普通滚轮 = 平移 (free)；
           ctrl+滚轮/触控 pinch = 缩放；中键拖拽平移 (CLONE_DECISION)。 */
        selectionOnDrag
        selectionMode={SelectionMode.Partial}
        elementsSelectable
        panOnDrag={[1]}
        panOnScroll
        panOnScrollMode={PanOnScrollMode.Free}
        zoomOnScroll={false}
        zoomOnPinch
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onPaneClick={onPaneClick}
        onPaneContextMenu={onPaneContextMenu}
        onNodeContextMenu={onNodeContextMenu}
        onMove={onMove}
        defaultViewport={DEFAULT_VIEWPORT}
        minZoom={0.1}
        maxZoom={4}
        proOptions={{ hideAttribution: true }}
        deleteKeyCode={null}
        zoomOnDoubleClick={false}
      >
        {/* 小地图 (Batch 91, SOURCE_FACT): dock 切换，位于 dock 上方 */}
        {minimapOpen ? (
          <div
            data-testid="jimeng-minimap-panel"
            className="absolute bottom-14 left-4 z-[30] rounded-lg p-2"
            style={{ background: "rgb(13,13,13)", width: 164, height: 154 }}
          >
            <MiniMap
              pannable
              zoomable={false}
              style={{
                width: 156,
                height: 114,
                background: "rgba(255,255,255,0.08)",
                borderRadius: 6,
              }}
              maskColor="rgba(0,0,0,0.45)"
              nodeColor={() => "#4a4a4a"}
              nodeStrokeColor="transparent"
              className="!rounded-md"
            />
          </div>
        ) : null}
      </ReactFlow>
      {contextMenu ? (
        <JimengContextMenu
          state={contextMenu}
          canUndo={past.length > 0}
          canRedo={future.length > 0}
          canDownload={saved}
          multi={nodes.filter((n) => n.selected).length > 1}
          grouped={(() => {
            const sel = nodes.filter((n) => n.selected);
            return sel.length > 1 && sel.every((n) => n.groupId);
          })()}
          onClose={() => setContextMenu(null)}
          onAction={onContextMenuAction}
        />
      ) : null}
      {/* 多选组合工具条 + 包围盒 + 编组卡片 (Batch 62/63) */}
      <JimengGroupFrames />
      <JimengSelectionOutline />
      <JimengMultiSelectToolbar />
      {assetsOpen ? <JimengAssetsModal onClose={() => setAssetsOpen(false)} /> : null}
      {offlineDialogOpen ? (
        <JimengOfflineDialog onClose={() => setOfflineDialog(false)} />
      ) : null}
      {paneMenu ? (
        <JimengPaneContextMenu
          state={paneMenu}
          canUndo={past.length > 0}
          canRedo={future.length > 0}
          clipboard={clipboard !== null}
          onClose={() => setPaneMenu(null)}
          onInsert={onPaneInsert}
          onPaste={pasteNodes}
          onUndo={undo}
          onRedo={redo}
        />
      ) : null}
      <JimengTaskToast />
    </div>
  );
}

export function JimengWorkspace() {
  const aiDrawerOpen = useJimengStore((s) => s.aiDrawerOpen);
  const setAiDrawerOpen = useJimengStore((s) => s.setAiDrawerOpen);

  // chrome 组件 (底栏缩放菜单) 需要 useReactFlow，整体包在 Provider 内
  return (
    <ReactFlowProvider>
      <div className="relative h-screen w-screen overflow-hidden">
        <JimengFlow />
        <JimengTopBar />
        <JimengToolRail />
        <JimengBottomDock />
        {aiDrawerOpen ? null : <JimengAiButton />}
        {aiDrawerOpen ? (
          <JimengAiDrawer onClose={() => setAiDrawerOpen(false)} />
        ) : null}
      </div>
    </ReactFlowProvider>
  );
}
