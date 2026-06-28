"use client";

import { useCallback, useEffect, useRef } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  addEdge,
  type Connection,
  type Edge,
  type Node,
  type NodeChange,
  type EdgeChange,
  BackgroundVariant,
  applyNodeChanges,
  applyEdgeChanges,
  SelectionMode,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { useCanvasStore } from "@/store/canvasStore";
import { useUIStore } from "@/store/uiStore";
import { TopNavBar } from "@/components/TopNavBar";
import { LeftSidebar } from "@/components/LeftSidebar";
import { BottomToolbar } from "@/components/BottomToolbar";
import { KeyboardShortcutsDialog } from "@/components/KeyboardShortcutsDialog";
import { ScriptNode } from "@/components/nodes/ScriptNode";
import { ImageNode } from "@/components/nodes/ImageNode";
import { TextNode } from "@/components/nodes/TextNode";
import { VideoNode } from "@/components/nodes/VideoNode";
import { ScriptExecutionNode } from "@/components/nodes/ScriptExecutionNode";
import { StoryboardGroupNode } from "@/components/nodes/StoryboardGroupNode";
import { DeletableEdge } from "@/components/nodes/DeletableEdge";
import { ScriptHeader } from "@/components/ScriptHeader";

const nodeTypes = {
  script: ScriptNode,
  image: ImageNode,
  text: TextNode,
  video: VideoNode,
  "script-execution": ScriptExecutionNode,
  "storyboard-group": StoryboardGroupNode,
};

const edgeTypes = {
  default: DeletableEdge,
};

export default function Home() {
  const {
    getActiveCanvas,
    setNodes: setStoreNodes,
    setEdges: setStoreEdges,
    addEdge: addStoreEdge,
    removeEdge,
    selectNode,
    setViewport,
    activeCanvasId,
  } = useCanvasStore();
  const {
    showMinimap,
    showGrid,
    snapToGrid,
    closeAllPanels,
    isShortcutsPanelOpen,
    toggleShortcutsPanel,
  } = useUIStore();

  const activeCanvas = getActiveCanvas();
  const nodes = activeCanvas?.nodes || [];
  const edges = activeCanvas?.edges || [];

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Delete selected node/edge
      if (e.key === 'Delete' || e.key === 'Backspace') {
        const { selectedNodeId, removeNode } = useCanvasStore.getState();
        if (selectedNodeId) {
          e.preventDefault();
          removeNode(selectedNodeId);
        }
      }
      // Escape - deselect and close panels
      if (e.key === 'Escape') {
        selectNode(null);
        closeAllPanels();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectNode, closeAllPanels]);

  // Use ref to track local changes and avoid store->flow sync loops
  const isLocalChange = useRef(false);
  const prevCanvasId = useRef(activeCanvasId);

  // Reset local change flag when canvas changes
  useEffect(() => {
    if (prevCanvasId.current !== activeCanvasId) {
      prevCanvasId.current = activeCanvasId;
      isLocalChange.current = false;
    }
  }, [activeCanvasId]);

  // Handle node changes (drag, select, etc.)
  const onNodesChange = useCallback(
    (changes: NodeChange[]) => {
      isLocalChange.current = true;
      const updatedNodes = applyNodeChanges(changes, nodes);
      setStoreNodes(updatedNodes);
    },
    [nodes, setStoreNodes]
  );

  // Handle edge changes
  const onEdgesChange = useCallback(
    (changes: EdgeChange[]) => {
      isLocalChange.current = true;
      const updatedEdges = applyEdgeChanges(changes, edges);
      setStoreEdges(updatedEdges);
    },
    [edges, setStoreEdges]
  );

  // Handle new connections
  const onConnect = useCallback(
    (params: Connection) => {
      const newEdge: Edge = {
        ...params,
        type: "default",
        animated: false,
        id: `e-${params.source}-${params.target}-${Date.now()}`,
        source: params.source || "",
        target: params.target || "",
        style: { stroke: "#86909c", strokeWidth: 2 },
      };
      addStoreEdge(newEdge);
    },
    [addStoreEdge]
  );

  // Handle node click
  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      selectNode(node.id);
    },
    [selectNode]
  );

  // Handle pane click (deselect)
  const onPaneClick = useCallback(() => {
    selectNode(null);
  }, [selectNode]);

  // Handle viewport changes
  const onViewportChange = useCallback(
    (viewport: { x: number; y: number; zoom: number }) => {
      setViewport(viewport);
    },
    [setViewport]
  );

  // Handle node drag end - save final position
  const onNodeDragStop = useCallback(
    (_: unknown, node: Node) => {
      const updatedNodes = nodes.map((n) =>
        n.id === node.id ? { ...n, position: node.position } : n
      );
      setStoreNodes(updatedNodes);
    },
    [nodes, setStoreNodes]
  );

  // Listen for delete-edge custom events from DeletableEdge component
  useEffect(() => {
    const handler = (e: Event) => {
      const detail = (e as CustomEvent<{ id: string }>).detail;
      if (detail?.id) {
        removeEdge(detail.id);
      }
    };
    window.addEventListener("delete-edge", handler);
    return () => window.removeEventListener("delete-edge", handler);
  }, [removeEdge]);

  return (
    <div className="h-screen w-screen flex flex-col overflow-hidden bg-[#141414]">
      {/* Top Navigation Bar */}
      <TopNavBar />

      {/* Script Header (compact title node above canvas) */}
      <ScriptHeader />

      {/* Main Content Area */}
      <div className="flex flex-1 overflow-hidden relative">
        {/* Left Sidebar */}
        <LeftSidebar />

        {/* Canvas Area */}
        <div className="flex-1 relative">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={onNodeClick}
            onPaneClick={onPaneClick}
            onNodeDragStop={onNodeDragStop}
            nodeTypes={nodeTypes}
            edgeTypes={edgeTypes}
            fitView
            className="bg-[#171717]"
            defaultEdgeOptions={{
              type: "default",
              animated: false,
              style: { stroke: "#86909c", strokeWidth: 2 },
            }}
            snapToGrid={snapToGrid}
            snapGrid={[20, 20]}
            onViewportChange={onViewportChange}
            // Pan and zoom settings
            panOnScroll
            zoomOnScroll
            panOnDrag
            selectionOnDrag={false}
            // Connection settings
            connectionLineStyle={{ stroke: "#09caf5", strokeWidth: 2 }}
            // Interaction options
            nodesDraggable
            nodesConnectable
            elementsSelectable
            selectNodesOnDrag={false}
            // Selection
            selectionMode={SelectionMode.Partial}
            // Min/Max zoom
            minZoom={0.1}
            maxZoom={2}
            // Delete key
            deleteKeyCode="Delete"
          >
            {showGrid && (
              <Background
                variant={BackgroundVariant.Dots}
                gap={20}
                size={1}
                color="#474747"
              />
            )}
          </ReactFlow>

          {/* Following Status - Top center, purple background */}
          <div className="absolute top-0 left-1/2 -translate-x-1/2 flex items-center gap-2 bg-[#8B25E4] border border-[#8B25E4] rounded-b-xl px-3 py-1.5 text-sm text-white z-50">
            <span>正在跟随</span>
            <button className="text-xs text-white/80 hover:text-white transition-colors">
              取消ESC
            </button>
          </div>
        </div>
      </div>

      {/* Bottom Toolbar */}
      <BottomToolbar />

      {/* Keyboard Shortcuts Dialog */}
      <KeyboardShortcutsDialog
        isOpen={isShortcutsPanelOpen}
        onClose={toggleShortcutsPanel}
      />
    </div>
  );
}
