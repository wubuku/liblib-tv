"use client";

import { useCallback, useEffect, useState } from "react";
import {
  ReactFlow,
  ReactFlowProvider,
  useReactFlow,
  PanOnScrollMode,
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
  const { fitView, zoomIn, zoomOut, getViewport, setViewport } = useReactFlow();
  const copyNode = useJimengStore((s) => s.copyNode);
  const duplicateNode = useJimengStore((s) => s.duplicateNode);
  const pasteNode = useJimengStore((s) => s.pasteNode);
  const removeNode = useJimengStore((s) => s.removeNode);
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
  const [contextMenu, setContextMenu] = useState<JimengContextMenuState | null>(
    null,
  );

  const onPaneClick = useCallback(() => {
    selectNode(null);
    exitRepaint();
    exitEdit();
    exitInfer();
    exitFramePicker();
    exitTrim();
    setContextMenu(null);
  }, [selectNode, exitRepaint, exitEdit, exitInfer, exitFramePicker, exitTrim]);

  const onNodeContextMenu = useCallback<NodeMouseHandler>((event, node) => {
    const e = event as unknown as MouseEvent;
    e.preventDefault();
    setContextMenu({ x: e.clientX, y: e.clientY, nodeId: node.id });
  }, []);

  const onContextMenuAction = useCallback(
    (action: string) => {
      if (!contextMenu) return;
      if (action === "copy") copyNode(contextMenu.nodeId);
      if (action === "duplicate") duplicateNode(contextMenu.nodeId);
      if (action === "paste") pasteNode();
      if (action === "delete") removeNode(contextMenu.nodeId);
      if (action === "undo") undo();
      if (action === "redo") redo();
    },
    [contextMenu, copyNode, duplicateNode, pasteNode, removeNode, undo, redo],
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
      } else if (mod && e.key.toLowerCase() === "c" && selectedNodeId) {
        copyNode(selectedNodeId);
      } else if (mod && e.key.toLowerCase() === "d" && selectedNodeId) {
        e.preventDefault();
        duplicateNode(selectedNodeId);
      } else if (mod && e.key.toLowerCase() === "v") {
        pasteNode();
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
    pasteNode,
    removeNode,
    selectedNodeId,
    toolActive,
    setToolActive,
    fitView,
    zoomIn,
    zoomOut,
    getViewport,
    setViewport,
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
        /* 导航语义 (SOURCE_FACT, batch 21 提取): 空白左键拖拽不平移；
           普通滚轮 = 平移 (free)；ctrl+滚轮/触控 pinch = 缩放；
           中键拖拽平移 (CLONE_DECISION，源站中键行为未验证)。 */
        panOnDrag={[1]}
        panOnScroll
        panOnScrollMode={PanOnScrollMode.Free}
        zoomOnScroll={false}
        zoomOnPinch
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onPaneClick={onPaneClick}
        onNodeContextMenu={onNodeContextMenu}
        onMove={onMove}
        defaultViewport={DEFAULT_VIEWPORT}
        minZoom={0.1}
        maxZoom={4}
        proOptions={{ hideAttribution: true }}
        deleteKeyCode={null}
        zoomOnDoubleClick={false}
      />
      {contextMenu ? (
        <JimengContextMenu
          state={contextMenu}
          canUndo={past.length > 0}
          canRedo={future.length > 0}
          onClose={() => setContextMenu(null)}
          onAction={onContextMenuAction}
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
