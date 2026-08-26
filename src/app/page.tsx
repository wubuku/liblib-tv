"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import dynamic from "next/dynamic";
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
import { ShotBreakdownResultNode } from "@/components/nodes/ShotBreakdownResultNode";
import { VideoClipNode } from "@/components/nodes/VideoClipNode";
import { AudioNode } from "@/components/nodes/AudioNode";
import { LongVideoProcessNode } from "@/components/nodes/LongVideoProcessNode";
import { DeletableEdge } from "@/components/nodes/DeletableEdge";
import { getLiblibOrganizeViewport, organizeLiblibNodes } from "@/lib/liblibOrganize";

const DirectorDesk = dynamic(() => import("@/components/director/DirectorDesk"), {
  ssr: false,
  loading: () => (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-[#111] text-sm text-[#a9a9a9]">
      正在载入导演台…
    </div>
  ),
});

const nodeTypes = {
  script: ScriptNode,
  image: ImageNode,
  text: TextNode,
  video: VideoNode,
  "script-execution": ScriptExecutionNode,
  "storyboard-group": StoryboardGroupNode,
  "shot-breakdown": ShotBreakdownNode,
  "shot-breakdown-result": ShotBreakdownResultNode,
  "video-clip": VideoClipNode,
  audio: AudioNode,
  "long-video-process": LongVideoProcessNode,
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
    activeDirectorNodeId,
    closeDirectorDesk,
  } = useUIStore();

  const activeCanvas = getActiveCanvas();
  const nodes = activeCanvas?.nodes ?? emptyNodes;
  const edges = activeCanvas?.edges ?? emptyEdges;
  const flowRef = useRef<ReactFlowInstance<Node, Edge> | null>(null);
  const flowContainerRef = useRef<HTMLElement | null>(null);
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
    const currentViewport = flowRef.current?.getViewport() ?? flowViewport;
    const organized = organizeLiblibNodes(nodes);
    const organizedViewport = getLiblibOrganizeViewport(
      organized,
      flowContainerRef.current?.clientWidth ?? window.innerWidth,
    );

    setOrganizeSnapshot({ nodes, viewport: currentViewport });
    selectNode(null);
    setStoreNodes(organized, { recordHistory: true });
    setFlowViewport(organizedViewport);
    setStoreViewport(organizedViewport);
    setZoomLevel(Math.round(organizedViewport.zoom * 100));
  }, [flowViewport, nodes, selectNode, setStoreNodes, setStoreViewport, setZoomLevel]);

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
      if (useUIStore.getState().activeDirectorNodeId) return;

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
        if (useUIStore.getState().activeDirectorNodeId) return;
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
      if (useUIStore.getState().activeDirectorNodeId) {
        setIsSpacePressed(false);
        return;
      }
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

      <main ref={flowContainerRef} className="relative min-w-0 flex-1 overflow-hidden">
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
                position="bottom-left"
                className="liblib-minimap"
                // xyflow reads style width/height to calculate the minimap viewBox.
                style={{ width: 150, height: 110 }}
                ariaLabel="画布缩略图"
                bgColor="#262626"
                maskColor="rgba(20,20,20,0.56)"
                maskStrokeColor="#747474"
                maskStrokeWidth={0.75}
                nodeColor="#626262"
                nodeStrokeColor="#707070"
                nodeStrokeWidth={1}
                nodeBorderRadius={3}
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
        <div
          data-organize-confirmation
          className="fixed bottom-[53px] left-[49px] z-[72] flex min-h-[88px] w-[168px] flex-col rounded-[10px] border border-white/[0.08] bg-[#262626] p-3 text-xs text-[#dedede] shadow-[0_14px_40px_rgba(0,0,0,0.5)] max-sm:bottom-[106px] max-sm:left-3"
        >
          <span className="leading-5">是否保留此次整理结果？</span>
          <div className="mt-2 flex items-center justify-end gap-1">
            <button type="button" onClick={restoreOrganize} className="h-8 min-w-12 rounded-lg px-2 text-[#b7b7b7] hover:bg-white/[0.07] hover:text-white">还原</button>
            <button type="button" onClick={() => setOrganizeSnapshot(null)} className="h-8 min-w-12 rounded-lg bg-[#e5e5e7] px-2 text-[#202020] hover:bg-white">保留</button>
          </div>
        </div>
      )}

      <KeyboardShortcutsDialog isOpen={isShortcutsPanelOpen} onClose={toggleShortcutsPanel} />
      {activeDirectorNodeId && (
        <DirectorDesk
          sourceNodeId={activeDirectorNodeId}
          onClose={closeDirectorDesk}
        />
      )}
    </div>
  );
}
