"use client";

import { useCallback, useMemo, useRef, useEffect } from "react";
import {
  ReactFlow,
  Background,
  BackgroundVariant,
  applyNodeChanges,
  applyEdgeChanges,
  SelectionMode,
  useReactFlow,
  type Connection,
  type Edge,
  type EdgeChange,
  type NodeChange,
  ReactFlowProvider,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { useFrameosStore } from "@/store/frameosStore";
import { FrameosTextNode } from "@/components/frameos/nodes/FrameosTextNode";
import { FrameosImageNode } from "@/components/frameos/nodes/FrameosImageNode";
import { FrameosVideoNode } from "@/components/frameos/nodes/FrameosVideoNode";
import { DeletableEdge } from "@/components/nodes/DeletableEdge";
import { FrameosAppHeader } from "@/components/frameos/FrameosAppHeader";
import { FrameosHistoryDock } from "@/components/frameos/FrameosHistoryDock";
import { FrameosToolRail } from "@/components/frameos/FrameosToolRail";
import { FrameosMapDock } from "@/components/frameos/FrameosMapDock";
import { FrameosPromptBar } from "@/components/frameos/FrameosPromptBar";
import { FrameosBreadcrumb } from "@/components/frameos/FrameosBreadcrumb";
import { FrameosNodeEditPanel } from "@/components/frameos/FrameosNodeEditPanel";
import { FrameosNodeToolbar } from "@/components/frameos/FrameosNodeToolbar";
import { FrameosHelpPanel } from "@/components/frameos/FrameosHelpPanel";

const nodeTypes = {
  text: FrameosTextNode,
  image: FrameosImageNode,
  video: FrameosVideoNode,
};

const edgeTypes = {
  default: DeletableEdge,
};

function FrameosCanvasInner() {
  const nodes = useFrameosStore((s) => s.nodes);
  const edges = useFrameosStore((s) => s.edges);
  const setNodes = useFrameosStore((s) => s.setNodes);
  const setEdges = useFrameosStore((s) => s.setEdges);
  const addEdge = useFrameosStore((s) => s.addEdge);
  const removeEdge = useFrameosStore((s) => s.removeEdge);
  const removeNode = useFrameosStore((s) => s.removeNode);
  const duplicateNode = useFrameosStore((s) => s.duplicateNode);
  const selectNode = useFrameosStore((s) => s.selectNode);
  const isPromptFullscreen = useFrameosStore((s) => s.isPromptFullscreen);
  const undo = useFrameosStore((s) => s.undo);
  const redo = useFrameosStore((s) => s.redo);
  const toggleHelp = useFrameosStore((s) => s.toggleHelp);
  const { zoomIn, zoomOut, fitView } = useReactFlow();

  // 防止 store <-> flow 同步循环
  const isLocalChange = useRef(false);

  const onNodesChange = useCallback(
    (changes: NodeChange[]) => {
      isLocalChange.current = true;
      const updated = applyNodeChanges(changes, nodes);
      setNodes(updated as typeof nodes);
    },
    [nodes, setNodes]
  );

  const onEdgesChange = useCallback(
    (changes: EdgeChange[]) => {
      isLocalChange.current = true;
      const updated = applyEdgeChanges(changes, edges);
      setEdges(updated);
    },
    [edges, setEdges]
  );

  const onConnect = useCallback(
    (params: Connection) => {
      const newEdge: Edge = {
        ...params,
        id: `e-${params.source}-${params.target}-${Date.now()}`,
        source: params.source ?? "",
        target: params.target ?? "",
        type: "default",
        sourceHandle: params.sourceHandle ?? undefined,
        targetHandle: params.targetHandle ?? undefined,
      };
      addEdge(newEdge);
    },
    [addEdge]
  );

  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: { id: string }) => {
      selectNode(node.id);
    },
    [selectNode]
  );

  const onPaneClick = useCallback(() => {
    selectNode(null);
  }, [selectNode]);

  // 监听 DeletableEdge 的删除事件
  useEffect(() => {
    const handler = (e: Event) => {
      const detail = (e as CustomEvent<{ id: string }>).detail;
      if (detail?.id) removeEdge(detail.id);
    };
    window.addEventListener("delete-edge", handler);
    return () => window.removeEventListener("delete-edge", handler);
  }, [removeEdge]);

  // 完整键盘快捷键
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const state = useFrameosStore.getState();

      // 输入框中不触发快捷键
      const tag = (e.target as HTMLElement).tagName;
      const isInInput = tag === "INPUT" || tag === "TEXTAREA" ||
        (e.target as HTMLElement).isContentEditable;
      if (isInInput && e.key !== "Escape") return;

      // Escape - 多级退出
      if (e.key === "Escape") {
        if (state.isHelpOpen) {
          state.closeHelp();
          return;
        }
        if (state.isPromptFullscreen) {
          state.setPromptFullscreen(false);
          return;
        }
        if (state.isAddNodeMenuOpen) {
          state.closeAddNodeMenu();
          return;
        }
        if (state.isOrganizeMenuOpen) {
          state.closeOrganizeMenu();
          return;
        }
        selectNode(null);
        return;
      }

      // ? - 帮助面板
      if (e.key === "?" || (e.shiftKey && e.key === "/")) {
        e.preventDefault();
        toggleHelp();
        return;
      }

      // Cmd/Ctrl + Z - 撤销
      if ((e.metaKey || e.ctrlKey) && e.key === "z" && !e.shiftKey) {
        e.preventDefault();
        undo();
        return;
      }
      // Cmd/Ctrl + Shift + Z - 重做
      if ((e.metaKey || e.ctrlKey) && (e.key === "Z" || (e.key === "z" && e.shiftKey))) {
        e.preventDefault();
        redo();
        return;
      }

      // Cmd/Ctrl + D - 复制
      if ((e.metaKey || e.ctrlKey) && e.key === "d" && state.selectedNodeId) {
        e.preventDefault();
        duplicateNode(state.selectedNodeId);
        return;
      }

      // Delete / Backspace - 删除
      if ((e.key === "Delete" || e.key === "Backspace") && state.selectedNodeId) {
        e.preventDefault();
        removeNode(state.selectedNodeId);
        return;
      }

      // +/-/0 - 缩放控制
      if (e.key === "+" || e.key === "=") {
        zoomIn({ duration: 150 });
        return;
      }
      if (e.key === "-" || e.key === "_") {
        zoomOut({ duration: 150 });
        return;
      }
      if (e.key === "0") {
        fitView({ duration: 200, padding: 0.15 });
        return;
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [removeNode, duplicateNode, selectNode, undo, redo, toggleHelp, zoomIn, zoomOut, fitView]);

  // 给边一个默认样式（与 frameos 一致：深灰 2px）
  const styledEdges = useMemo<Edge[]>(
    () =>
      edges.map((e) => ({
        ...e,
        style: { stroke: "#86909c", strokeWidth: 2 },
      })),
    [edges]
  );

  return (
    <div className="frameos-canvas" style={{ position: "relative", width: "100vw", height: "100vh", overflow: "hidden" }}>
      <ReactFlow
        nodes={nodes}
        edges={styledEdges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={onNodeClick}
        onPaneClick={onPaneClick}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
        fitViewOptions={{ padding: 0.15, includeHiddenNodes: false, minZoom: 1, maxZoom: 1 }}
        minZoom={0.1}
        maxZoom={2}
        panOnScroll
        zoomOnScroll
        panOnDrag={[1, 2]}
        selectionOnDrag
        selectionMode={SelectionMode.Partial}
        nodesDraggable
        nodesConnectable
        elementsSelectable
        deleteKeyCode={["Delete", "Backspace"]}
        proOptions={{ hideAttribution: true }}
        defaultEdgeOptions={{
          type: "default",
          style: { stroke: "#86909c", strokeWidth: 2 },
        }}
        connectionLineStyle={{ stroke: "#3B82F6", strokeWidth: 2 }}
      >
        <Background
          variant={BackgroundVariant.Dots}
          gap={20}
          size={1}
          color="#222222"
        />
      </ReactFlow>

      {/* 顶部浮动元素 */}
      <FrameosAppHeader />
      <FrameosHistoryDock />
      <FrameosBreadcrumb />

      {/* 左侧浮动 rail */}
      <FrameosToolRail />

      {/* 左下 dock */}
      <FrameosMapDock />

      {/* 右侧节点编辑面板 */}
      <FrameosNodeEditPanel />

      {/* 选中节点的浮动工具条 (跟随节点位置 + 画布缩放) */}
      <FrameosNodeToolbar />

      {/* 底部 prompt */}
      <FrameosPromptBar />

      {/* 全屏编辑时的背景遮罩 */}
      {isPromptFullscreen && (
        <div
          style={{
            position: "absolute",
            inset: 0,
            background: "rgba(0,0,0,0.5)",
            backdropFilter: "blur(2px)",
            zIndex: 2999,
          }}
          onClick={() => useFrameosStore.getState().setPromptFullscreen(false)}
        />
      )}

      {/* 帮助面板 */}
      <FrameosHelpPanel />
    </div>
  );
}

export default function FrameosCanvasPage() {
  return (
    <ReactFlowProvider>
      <FrameosCanvasInner />
    </ReactFlowProvider>
  );
}
