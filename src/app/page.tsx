"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  ReactFlow,
  Background,
  MiniMap,
  type Connection,
  type Edge,
  type Node,
  type NodeChange,
  type EdgeChange,
  type ReactFlowInstance,
  BackgroundVariant,
  applyNodeChanges,
  applyEdgeChanges,
  SelectionMode,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { useCanvasStore, type GraphSnapshot } from "@/store/canvasStore";
import { useUIStore } from "@/store/uiStore";
import { TopNavBar } from "@/components/TopNavBar";
import { LeftSidebar } from "@/components/LeftSidebar";
import { BottomToolbar } from "@/components/BottomToolbar";
import { KeyboardShortcutsDialog } from "@/components/KeyboardShortcutsDialog";
import { AssetManagerPanel } from "@/components/AssetManagerPanel";
import { AgentDrawer } from "@/components/AgentDrawer";
import { StoryboardBoard } from "@/components/StoryboardBoard";
import { ScriptNode } from "@/components/nodes/ScriptNode";
import { ImageNode } from "@/components/nodes/ImageNode";
import { TextNode } from "@/components/nodes/TextNode";
import { VideoNode } from "@/components/nodes/VideoNode";
import { ScriptExecutionNode } from "@/components/nodes/ScriptExecutionNode";
import { StoryboardGroupNode } from "@/components/nodes/StoryboardGroupNode";
import { ShotBreakdownNode } from "@/components/nodes/ShotBreakdownNode";
import { VideoClipNode } from "@/components/nodes/VideoClipNode";
import { DeletableEdge } from "@/components/nodes/DeletableEdge";

const nodeTypes = {
  script: ScriptNode,
  image: ImageNode,
  text: TextNode,
  video: VideoNode,
  "script-execution": ScriptExecutionNode,
  "storyboard-group": StoryboardGroupNode,
  "shot-breakdown": ShotBreakdownNode,
  "video-clip": VideoClipNode,
};

const edgeTypes = { default: DeletableEdge };
const emptyNodes: Node[] = [];
const emptyEdges: Edge[] = [];
const desktopViewport = { x: -583.8, y: 260.8, zoom: 0.526 };
const compactViewport = { x: 17, y: 128, zoom: 0.28 };

export default function Home() {
  const {
    getActiveCanvas,
    setNodes: setStoreNodes,
    setEdges: setStoreEdges,
    addEdge: addStoreEdge,
    removeEdge,
    selectNode,
    selectNodes,
    selectedNodeIds,
    groupSelectedNodes,
    ungroupSelectedNodes,
    removeSelectedNodes,
    undo,
    redo,
    duplicateSelectedNodes,
    setViewport: setStoreViewport,
    activeCanvasId,
  } = useCanvasStore();
  const {
    showMinimap,
    showGrid,
    showEdges,
    snapToGrid,
    canvasTool,
    editorMode,
    isAssetPanelOpen,
    isAgentOpen,
    closeAllPanels,
    toggleAddNodePanel,
    isShortcutsPanelOpen,
    toggleShortcutsPanel,
    setCanvasTool,
    setZoomLevel,
  } = useUIStore();

  const activeCanvas = getActiveCanvas();
  const nodes = activeCanvas?.nodes ?? emptyNodes;
  const edges = activeCanvas?.edges ?? emptyEdges;
  const flowRef = useRef<ReactFlowInstance<Node, Edge> | null>(null);
  const [organizeSnapshot, setOrganizeSnapshot] = useState<{ nodes: Node[]; viewport: { x: number; y: number; zoom: number } } | null>(null);
  const [isSpacePressed, setIsSpacePressed] = useState(false);
  const dragHistorySnapshot = useRef<{ snapshot: GraphSnapshot; nodeIds: string[] } | null>(null);
  const [flowViewport, setFlowViewport] = useState(() => {
    if (activeCanvasId !== "canvas-2") return activeCanvas?.viewport ?? { x: 0, y: 0, zoom: 1 };
    return typeof window !== "undefined" && window.innerWidth <= 768 ? compactViewport : desktopViewport;
  });

  const flowNodes = useMemo<Node[]>(
    () => {
      const selectedIds = new Set(selectedNodeIds);
      return nodes.map((node) => ({ ...node, selected: selectedIds.has(node.id) }));
    },
    [nodes, selectedNodeIds],
  );
  const effectivePan = canvasTool === "pan" || isSpacePressed;

  const onNodesChange = useCallback(
    (changes: NodeChange[]) => {
      const currentNodes = useCanvasStore.getState().getActiveCanvas()?.nodes ?? [];
      const selectionChanges = changes.filter((change) => change.type === "select");
      const graphChanges = changes.filter((change) => change.type !== "select");
      if (selectionChanges.length > 0) {
        const selectionNodes = applyNodeChanges(selectionChanges, flowNodes);
        selectNodes(selectionNodes.filter((node) => node.selected).map((node) => node.id));
      }
      if (graphChanges.length === 0) return;
      const nextNodes = applyNodeChanges(graphChanges, currentNodes);
      setStoreNodes(
        nextNodes.map((node) => {
          const storedNode = { ...node };
          delete storedNode.selected;
          return storedNode;
        }),
      );
    },
    [flowNodes, selectNodes, setStoreNodes],
  );

  const onEdgesChange = useCallback(
    (changes: EdgeChange[]) => setStoreEdges(applyEdgeChanges(changes, edges)),
    [edges, setStoreEdges],
  );

  const onConnect = useCallback(
    (params: Connection) => {
      if (!params.source || !params.target) return;
      addStoreEdge({
        ...params,
        id: `e-${params.source}-${params.target}-${Date.now()}`,
        source: params.source,
        target: params.target,
        type: "default",
      });
    },
    [addStoreEdge],
  );

  const onViewportChange = useCallback(
    (viewport: { x: number; y: number; zoom: number }) => {
      setFlowViewport(viewport);
      setStoreViewport(viewport);
      setZoomLevel(Math.round(viewport.zoom * 100));
    },
    [setStoreViewport, setZoomLevel],
  );

  const fitView = useCallback(() => {
    void flowRef.current?.fitView({ padding: 0.12, duration: 260 });
  }, []);

  const zoomBy = useCallback((delta: number) => {
    const instance = flowRef.current;
    if (!instance) return;
    const viewport = instance.getViewport();
    void instance.setViewport({ ...viewport, zoom: Math.min(8, Math.max(0.1, viewport.zoom + delta)) }, { duration: 160 });
  }, []);

  const zoomTo = useCallback((zoom: number) => {
    void flowRef.current?.zoomTo(zoom, { duration: 180 });
  }, []);

  const organize = useCallback(() => {
    setOrganizeSnapshot({ nodes, viewport: flowRef.current?.getViewport() ?? flowViewport });
    const regularNodes = nodes.filter((node) => node.type !== "storyboard-group");
    const groupNodes = nodes.filter((node) => node.type === "storyboard-group");
    const organized = [
      ...regularNodes.map((node, index) => ({
        ...node,
        position: { x: (index % 3) * 760, y: Math.floor(index / 3) * 460 },
      })),
      ...groupNodes.map((node, index) => ({
        ...node,
        position: { x: 2280 + index * 760, y: index * 40 },
      })),
    ];
    setStoreNodes(organized, { recordHistory: true });
    window.setTimeout(fitView, 40);
  }, [fitView, flowViewport, nodes, setStoreNodes]);

  const restoreOrganize = () => {
    if (organizeSnapshot) {
      setStoreNodes(organizeSnapshot.nodes, { recordHistory: true });
      setFlowViewport(organizeSnapshot.viewport);
      setStoreViewport(organizeSnapshot.viewport);
      setZoomLevel(Math.round(organizeSnapshot.viewport.zoom * 100));
    }
    setOrganizeSnapshot(null);
  };

  useEffect(() => {
    const media = window.matchMedia("(max-width: 768px)");
    let frame = 0;
    const applyResponsiveViewport = () => {
      window.cancelAnimationFrame(frame);
      frame = window.requestAnimationFrame(() => {
        const viewport = activeCanvasId === "canvas-2"
          ? media.matches ? compactViewport : desktopViewport
          : useCanvasStore.getState().getActiveCanvas()?.viewport ?? { x: 0, y: 0, zoom: 1 };
        setFlowViewport(viewport);
        setStoreViewport(viewport);
        setZoomLevel(Math.round(viewport.zoom * 100));
      });
    };
    applyResponsiveViewport();
    media.addEventListener("change", applyResponsiveViewport);
    return () => {
      window.cancelAnimationFrame(frame);
      media.removeEventListener("change", applyResponsiveViewport);
    };
  }, [activeCanvasId, setStoreViewport, setZoomLevel]);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      const isEditableTarget = Boolean(
        target?.closest("input, textarea, [contenteditable='true'], [contenteditable='plaintext-only']"),
      );
      if (isEditableTarget) return;

      const modifier = event.metaKey || event.ctrlKey;

      if (event.code === "Space") {
        event.preventDefault();
        if (!event.repeat) setIsSpacePressed(true);
        return;
      }
      if (event.key === "Delete" || event.key === "Backspace") {
        const { selectedNodeIds: nodeIds, selectedNodeId: nodeId } = useCanvasStore.getState();
        if (nodeIds.length > 0 || nodeId) {
          event.preventDefault();
          removeSelectedNodes();
        }
      }
      if (event.key === "Escape") {
        selectNode(null);
        closeAllPanels();
      }
      if (modifier && event.key.toLowerCase() === "z") {
        event.preventDefault();
        if (event.shiftKey) redo();
        else undo();
      }
      if (modifier && event.key.toLowerCase() === "y") {
        event.preventDefault();
        redo();
      }
      if (modifier && event.key.toLowerCase() === "d") {
        const { selectedNodeIds: nodeIds, selectedNodeId: nodeId } = useCanvasStore.getState();
        if (nodeIds.length > 0 || nodeId) {
          event.preventDefault();
          duplicateSelectedNodes();
        }
      }
      if (event.key === "Tab") {
        event.preventDefault();
        toggleAddNodePanel();
      }
      if (!modifier && !event.altKey && event.key.toLowerCase() === "g") {
        event.preventDefault();
        if (event.shiftKey) ungroupSelectedNodes();
        else groupSelectedNodes();
      }
      if (event.altKey && event.shiftKey && event.key.toLowerCase() === "f") {
        event.preventDefault();
        organize();
      }
      if (!modifier && !event.altKey && event.key.toLowerCase() === "v") setCanvasTool("select");
      if (!modifier && !event.altKey && event.key.toLowerCase() === "h") setCanvasTool("pan");
      if (modifier && event.key === "0") {
        event.preventDefault();
        fitView();
      }
      if (modifier && (event.key === "+" || event.key === "=")) {
        event.preventDefault();
        zoomBy(0.1);
      }
      if (modifier && event.key === "-") {
        event.preventDefault();
        zoomBy(-0.1);
      }
    };
    const handleKeyUp = (event: KeyboardEvent) => {
      if (event.code === "Space") setIsSpacePressed(false);
    };
    const resetTemporaryPan = () => setIsSpacePressed(false);
    const handleVisibilityChange = () => {
      if (document.hidden) resetTemporaryPan();
    };

    window.addEventListener("keydown", handleKeyDown);
    window.addEventListener("keyup", handleKeyUp);
    window.addEventListener("blur", resetTemporaryPan);
    document.addEventListener("visibilitychange", handleVisibilityChange);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      window.removeEventListener("keyup", handleKeyUp);
      window.removeEventListener("blur", resetTemporaryPan);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, [
    closeAllPanels,
    duplicateSelectedNodes,
    fitView,
    groupSelectedNodes,
    organize,
    removeSelectedNodes,
    redo,
    selectNode,
    ungroupSelectedNodes,
    setCanvasTool,
    toggleAddNodePanel,
    undo,
    zoomBy,
  ]);

  useEffect(() => {
    const handler = (event: Event) => {
      const detail = (event as CustomEvent<{ id: string }>).detail;
      if (detail?.id) removeEdge(detail.id);
    };
    window.addEventListener("delete-edge", handler);
    return () => window.removeEventListener("delete-edge", handler);
  }, [removeEdge]);

  const onSelectionChange = useCallback(
    ({ nodes: selectedNodes }: { nodes: Node[] }) => {
      selectNodes(selectedNodes.map((node) => node.id));
    },
    [selectNodes],
  );

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#141414]">
      <TopNavBar />
      {isAssetPanelOpen && <AssetManagerPanel />}

      <main className="relative min-w-0 flex-1 overflow-hidden">
        {editorMode === "storyboard" ? (
          <StoryboardBoard />
        ) : (
          <ReactFlow
            key={activeCanvasId}
            nodes={flowNodes}
            edges={showEdges ? edges : []}
            onInit={(instance) => {
              flowRef.current = instance;
              setZoomLevel(Math.round(flowViewport.zoom * 100));
            }}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={(event, node) => {
              if (!event.metaKey && !event.ctrlKey) selectNode(node.id);
            }}
            onPaneClick={() => selectNode(null)}
            onSelectionChange={onSelectionChange}
            onNodeDragStart={(_, node) => {
              const currentCanvas = useCanvasStore.getState().getActiveCanvas();
              if (!currentCanvas) {
                dragHistorySnapshot.current = null;
                return;
              }
              const { selectedNodeIds: selectedIds } = useCanvasStore.getState();
              dragHistorySnapshot.current = {
                snapshot: { nodes: currentCanvas.nodes, edges: currentCanvas.edges },
                nodeIds: selectedIds.includes(node.id) ? selectedIds : [node.id],
              };
            }}
            onNodeDragStop={(_, node) => {
              const currentNodes = useCanvasStore.getState().getActiveCanvas()?.nodes ?? [];
              const transaction = dragHistorySnapshot.current;
              if (transaction) {
                const moved = transaction.nodeIds.some((id) => {
                  const before = transaction.snapshot.nodes.find((item) => item.id === id);
                  const after = currentNodes.find((item) => item.id === id);
                  return Boolean(
                    before &&
                      after &&
                      (before.position.x !== after.position.x || before.position.y !== after.position.y),
                  );
                });
                if (moved) {
                  setStoreNodes(currentNodes, {
                    recordHistory: true,
                    historySnapshot: transaction.snapshot,
                  });
                }
              } else {
                setStoreNodes(
                  currentNodes.map((item) => (item.id === node.id ? { ...item, position: node.position } : item)),
                  { recordHistory: true },
                );
              }
              dragHistorySnapshot.current = null;
            }}
            nodeTypes={nodeTypes}
            edgeTypes={edgeTypes}
            viewport={flowViewport}
            className={effectivePan ? "cursor-grab bg-[#141414]" : "bg-[#141414]"}
            data-canvas-tool={canvasTool}
            data-temporary-pan={isSpacePressed}
            defaultEdgeOptions={{ type: "default", animated: false, style: { stroke: "#7a8090", strokeWidth: 1.5 } }}
            snapToGrid={snapToGrid}
            snapGrid={[20, 20]}
            onViewportChange={onViewportChange}
            panOnScroll
            zoomOnScroll
            panOnDrag={effectivePan}
            panActivationKeyCode={null}
            selectionOnDrag={canvasTool === "select" && !effectivePan}
            connectionLineStyle={{ stroke: "#09caf5", strokeWidth: 1.5 }}
            nodesDraggable={canvasTool === "select" && !effectivePan}
            nodesConnectable
            elementsSelectable
            selectNodesOnDrag={false}
            selectionMode={SelectionMode.Partial}
            minZoom={0.1}
            maxZoom={8}
            deleteKeyCode={[]}
          >
            {showGrid && <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="#303030" />}
            {showMinimap && (
              <MiniMap
                position="bottom-right"
                style={{ width: 150, height: 110, background: "#202020", borderRadius: 12 }}
                maskColor="rgba(10,10,10,0.48)"
                nodeColor="#666"
                nodeStrokeColor="#8d8d8d"
              />
            )}
          </ReactFlow>
        )}
      </main>

      {isAgentOpen && <AgentDrawer />}

      <LeftSidebar />
      <BottomToolbar
        onOrganize={organize}
        onFitView={fitView}
        onZoomBy={zoomBy}
        onZoomTo={zoomTo}
      />

      {organizeSnapshot && (
        <div className="fixed bottom-[70px] left-1/2 z-[72] flex -translate-x-1/2 items-center gap-3 rounded-xl border border-white/10 bg-[#262626] p-2 pl-3 text-xs text-[#dedede] shadow-[0_14px_40px_rgba(0,0,0,0.5)] max-sm:bottom-[110px]">
          <span>是否保留此次整理结果？</span>
          <button onClick={restoreOrganize} className="h-7 rounded-lg px-3 text-[#aaa] hover:bg-white/[0.07] hover:text-white">还原</button>
          <button onClick={() => setOrganizeSnapshot(null)} className="h-7 rounded-lg bg-[#eceff3] px-3 text-[#202020] hover:bg-white">保留</button>
        </div>
      )}

      <KeyboardShortcutsDialog isOpen={isShortcutsPanelOpen} onClose={toggleShortcutsPanel} />
    </div>
  );
}
