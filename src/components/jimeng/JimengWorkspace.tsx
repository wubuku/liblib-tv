"use client";

import { useCallback, useState } from "react";
import { ReactFlow, ReactFlowProvider } from "@xyflow/react";
import type { NodeMouseHandler, OnMove } from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { useJimengStore } from "@/store/jimengStore";
import { JimengVideoNode } from "@/components/jimeng/nodes/JimengVideoNode";
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
};

const DEFAULT_VIEWPORT = { x: -60.6, y: 1.3, zoom: 0.7299 };

function JimengFlow() {
  const nodes = useJimengStore((s) => s.nodes);
  const edges = useJimengStore((s) => s.edges);
  const onNodesChange = useJimengStore((s) => s.onNodesChange);
  const onEdgesChange = useJimengStore((s) => s.onEdgesChange);
  const selectNode = useJimengStore((s) => s.selectNode);
  const setZoomPercent = useJimengStore((s) => s.setZoomPercent);
  const copyNode = useJimengStore((s) => s.copyNode);
  const duplicateNode = useJimengStore((s) => s.duplicateNode);
  const pasteNode = useJimengStore((s) => s.pasteNode);
  const removeNode = useJimengStore((s) => s.removeNode);
  const exitRepaint = useJimengStore((s) => s.exitRepaint);
  const exitEdit = useJimengStore((s) => s.exitEdit);
  const exitInfer = useJimengStore((s) => s.exitInfer);
  const exitFramePicker = useJimengStore((s) => s.exitFramePicker);
  const exitTrim = useJimengStore((s) => s.exitTrim);
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
    },
    [contextMenu, copyNode, duplicateNode, pasteNode, removeNode],
  );

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
