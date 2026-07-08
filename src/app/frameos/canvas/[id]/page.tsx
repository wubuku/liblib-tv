"use client";

import { useCallback, useMemo, useRef, useEffect, useState } from "react";
import {
  ReactFlow as ReactFlowAny,
  Background,
  BackgroundVariant,
  applyNodeChanges,
  applyEdgeChanges,
  SelectionMode,
  useReactFlow,
  useViewport,
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
import { FrameosEdge } from "@/components/frameos/FrameosEdge";
import { FrameosAppHeader } from "@/components/frameos/FrameosAppHeader";
import { FrameosHistoryDock } from "@/components/frameos/FrameosHistoryDock";
import { FrameosToolRail } from "@/components/frameos/FrameosToolRail";
import { FrameosMapDock } from "@/components/frameos/FrameosMapDock";
import { FrameosPromptBar } from "@/components/frameos/FrameosPromptBar";
import { FrameosBreadcrumb } from "@/components/frameos/FrameosBreadcrumb";
import { FrameosNodeEditPanel } from "@/components/frameos/FrameosNodeEditPanel";
import { FrameosNodeToolbar } from "@/components/frameos/FrameosNodeToolbar";
import { FrameosHelpPanel } from "@/components/frameos/FrameosHelpPanel";
import { FrameosDebugToggle } from "@/components/frameos/FrameosDebugToggle";
import {
  FrameosContextMenu,
  openContextMenu,
} from "@/components/frameos/FrameosContextMenu";
import { FrameosToast, showToast } from "@/components/frameos/FrameosToast";
import { FrameosNodeTooltip } from "@/components/frameos/FrameosNodeTooltip";
import { FrameosGenerationOverlay } from "@/components/frameos/FrameosGenerationOverlay";
import { FrameosAlignmentGuides } from "@/components/frameos/FrameosAlignmentGuides";
import { FrameosImportExport } from "@/components/frameos/FrameosImportExport";

const nodeTypes = {
  text: FrameosTextNode,
  image: FrameosImageNode,
  video: FrameosVideoNode,
};

const edgeTypes = {
  default: FrameosEdge,
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
  const selectedNodeId = useFrameosStore((s) => s.selectedNodeId);
  const isPromptFullscreen = useFrameosStore((s) => s.isPromptFullscreen);
  const undo = useFrameosStore((s) => s.undo);
  const redo = useFrameosStore((s) => s.redo);
  const toggleHelp = useFrameosStore((s) => s.toggleHelp);
  const { x: panX, y: panY, zoom } = useViewport();
  const { zoomIn, zoomOut, fitView, setViewport, getViewport } = useReactFlow();
  const rf = useReactFlow();
  const [isConnecting, setIsConnecting] = useState(false);
  const [hoveredTargetId, setHoveredTargetId] = useState<string | null>(null);

  // 防止 store <-> flow 同步循环
  const isLocalChange = useRef(false);

  const onNodesChange = useCallback(
    (changes: NodeChange[]) => {
      isLocalChange.current = true;
      const updated = applyNodeChanges(changes, nodes) as typeof nodes;
      // 重新应用 store 的 selected 状态 (xyflow 的 applyNodeChanges 会清掉 selected)
      const selectedId = useFrameosStore.getState().selectedNodeId;
      setNodes(
        updated.map((n) => (n.id === selectedId ? { ...n, selected: true } : n))
      );
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

  // 拖动节点到 viewport 边缘时, 自动 pan 画布
  useEffect(() => {
    let raf = 0;
    const tick = () => {
      const pane = document.querySelector(".react-flow__pane") as HTMLElement | null;
      if (pane && (pane as any).__draggingNodeId) {
        const rect = pane.getBoundingClientRect();
        // 鼠标位置 (用最近 mousemove 记录)
        const mouse = (window as any).__lastMousePos || { x: 0, y: 0 };
        const EDGE = 60; // 离边缘 60px 触发 pan
        const SPEED = 8; // 每次 pan 像素
        const vp = useFrameosStore.getState();
        const { setViewport, getViewport } = rf;
        const cur = getViewport();
        let dx = 0, dy = 0;
        if (mouse.x < rect.left + EDGE) dx = -SPEED;
        if (mouse.x > rect.right - EDGE) dx = SPEED;
        if (mouse.y < rect.top + EDGE) dy = -SPEED;
        if (mouse.y > rect.bottom - EDGE) dy = SPEED;
        if (dx || dy) {
          setViewport({ x: cur.x + dx / cur.zoom, y: cur.y + dy / cur.zoom, zoom: cur.zoom }, { duration: 0 });
        }
      }
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, []);

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
        showToast("已撤销", "info");
        return;
      }
      // Cmd/Ctrl + Shift + Z - 重做
      if ((e.metaKey || e.ctrlKey) && (e.key === "Z" || (e.key === "z" && e.shiftKey))) {
        e.preventDefault();
        redo();
        showToast("已重做", "info");
        return;
      }

      // Cmd/Ctrl + D - 复制
      if ((e.metaKey || e.ctrlKey) && e.key === "d" && state.selectedNodeId) {
        e.preventDefault();
        const node = state.nodes.find((n) => n.id === state.selectedNodeId);
        duplicateNode(state.selectedNodeId);
        if (node) showToast(`已复制「${node.data.title}」`, "success");
        return;
      }

      // Delete / Backspace - 删除
      if ((e.key === "Delete" || e.key === "Backspace") && state.selectedNodeId) {
        e.preventDefault();
        const node = state.nodes.find((n) => n.id === state.selectedNodeId);
        removeNode(state.selectedNodeId);
        if (node) showToast(`已删除「${node.data.title}」`, "warning");
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
        fitView({ duration: 200, padding: 0.2 });
        return;
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [removeNode, duplicateNode, selectNode, undo, redo, toggleHelp, zoomIn, zoomOut, fitView]);

  // 给边一个默认样式（与 frameos 一致：蓝色虚线 2px，dasharray 7,5）
  // 注意：实际样式在 FrameosEdge 组件中按 hover/selected 切换
  const styledEdges = useMemo<Edge[]>(() => edges, [edges]);

  // 右键菜单：节点 / 画布空白处
  const onNodeContextMenu = useCallback(
    (event: React.MouseEvent, node: { id: string }) => {
      event.preventDefault();
      const n = nodes.find((x) => x.id === node.id);
      if (!n) return;
      openContextMenu({
        x: event.clientX,
        y: event.clientY,
        items: [
          {
            label: "复制节点",
            shortcut: "⌘D",
            onClick: () => {
              duplicateNode(node.id);
              showToast(`已复制「${n.data.title}」`, "success");
            },
          },
          { separator: true, label: "" },
          {
            label: "删除节点",
            danger: true,
            shortcut: "Del",
            onClick: () => {
              removeNode(node.id);
              showToast(`已删除「${n.data.title}」`, "warning");
            },
          },
        ],
      });
    },
    [nodes, duplicateNode, removeNode]
  );

  const onPaneContextMenu = useCallback(
    (event: React.MouseEvent | MouseEvent) => {
      event.preventDefault();
      const opts = {
        panX,
        panY,
        zoom,
        viewportWidth: window.innerWidth,
        viewportHeight: window.innerHeight,
      };
      openContextMenu({
        x: (event as React.MouseEvent).clientX,
        y: (event as React.MouseEvent).clientY,
        items: [
          {
            label: "添加文本节点",
            onClick: () => useFrameosStore.getState().addNode("text", opts),
          },
          {
            label: "添加图片节点",
            onClick: () => useFrameosStore.getState().addNode("image", opts),
          },
          {
            label: "添加视频节点",
            onClick: () => useFrameosStore.getState().addNode("video", opts),
          },
          { separator: true, label: "" },
          {
            label: "适应画布",
            shortcut: "0",
            onClick: () => fitView({ duration: 200, padding: 0.2 }),
          },
        ],
      });
    },
    [fitView, panX, panY, zoom]
  );

  return (
    <div
      className={`frameos-canvas${isConnecting ? " is-connecting" : ""}`}
      style={{ position: "relative", width: "100vw", height: "100vh", overflow: "hidden" }}
    >
      <ReactFlowAny
        nodes={nodes.map((n) => {
          // 连接拖拽时: 当前 hover 的目标 = 有效目标, 其他 = 无效目标
          let cls = "";
          if (isConnecting) {
            if (hoveredTargetId && n.id === hoveredTargetId) {
              cls = "is-valid-target";
            } else if (hoveredTargetId) {
              cls = "is-invalid-target";
            }
            // 源节点 (selectedNodeId) 标 connecting-source
            if (selectedNodeId && n.id === selectedNodeId) {
              cls = (cls + " is-connecting-source").trim();
            }
          }
          return { ...n, className: cls };
        })}
        edges={styledEdges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onConnectStart={() => setIsConnecting(true)}
        onConnectEnd={() => {
          setIsConnecting(false);
          setHoveredTargetId(null);
        }}
        // @ts-expect-error xyflow v12 缺失此 prop 类型但运行时支持
        onMinimapNodeClick={(_e, node) => {
          // 点击 minimap 节点 → 选中 + fitView 跳到该节点
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          const n = node as any;
          selectNode(n.id);
          setTimeout(() => {
            fitView({
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              nodes: [{ id: n.id, position: n.position, width: n.measured?.width ?? n.style?.width ?? 300, height: n.measured?.height ?? n.style?.height ?? 169 }] as any,
              duration: 400,
              padding: 0.2,
            });
          }, 50);
        }}
        onNodeClick={onNodeClick}
        onNodeMouseEnter={(_, n) => {
          if (isConnecting) setHoveredTargetId(n.id);
        }}
        onNodeMouseLeave={() => {
          if (isConnecting) setHoveredTargetId(null);
        }}
        onPaneClick={onPaneClick}
        onNodeContextMenu={onNodeContextMenu}
        onPaneContextMenu={onPaneContextMenu}
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
      </ReactFlowAny>

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

      {/* 调试模式开关 */}
      <FrameosDebugToggle />

      {/* 全局右键菜单 */}
      <FrameosContextMenu />

      {/* Toast 通知 */}
      <FrameosToast />

      {/* 节点 hover tooltip */}
      <FrameosNodeTooltip />

      {/* 生成动画覆盖层 */}
      <FrameosGenerationOverlay />

      {/* 节点拖动时的对齐辅助线 */}
      <FrameosAlignmentGuides />

      {/* 导入/导出按钮 */}
      <FrameosImportExport />
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
