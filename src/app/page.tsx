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
  type OnConnectEnd,
  type OnConnectStart,
  BackgroundVariant,
  SelectionMode,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { useCanvasStore, type GraphSnapshot } from "@/store/canvasStore";
import {
  getDirectorProjectRegistrySnapshot,
  useDirectorStore,
} from "@/store/directorStore";
import { useUIStore } from "@/store/uiStore";
import { TopNavBar } from "@/components/TopNavBar";
import { LeftSidebar } from "@/components/LeftSidebar";
import { BottomToolbar } from "@/components/BottomToolbar";
import { KeyboardShortcutsDialog } from "@/components/KeyboardShortcutsDialog";
import { ImagePreviewOverlay } from "@/components/ImagePreviewOverlay";
import { AssetManagerPanel } from "@/components/AssetManagerPanel";
import { AgentDrawer } from "@/components/AgentDrawer";
import { StoryboardBoard } from "@/components/StoryboardBoard";
import { CanvasEmptyState } from "@/components/CanvasEmptyState";
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
import {
  proposedLibTVConnectionFromEdge,
  validateLibTVGraphConnection,
} from "@/lib/libtvGraphConnection";
import {
  reconcileLibTVUiOwners,
  type LibTVUiOwnerSnapshot,
} from "@/lib/libtvUiOwnerReconciliation";
import {
  collectLiveDirectorProjectOwners,
  createDirectorOwnerReachabilitySignature,
  planDirectorOwnerReachability,
} from "@/lib/directorOwnerReconciliation";
import {
  isLibTVCanvasCommandKey,
  isLibTVEditableCommandTarget,
  resolveLibTVBlockingForegroundSurface,
} from "@/lib/libtvSelectionCommandContext";
import {
  getLibTVHostCenterClientPoint,
  getLibTVViewportForFlowAtHostCenter,
  isValidLibTVViewport,
  planLibTVResponsiveViewportProjection,
  type LibTVViewport,
  type LibTVViewportOwnership,
} from "@/lib/libtvViewportPlacement";

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

interface LibTVAssetLayoutLogEntry {
  operationId: number;
  canvasId: string;
  status: "committed" | "skipped";
  reason:
    | "committed"
    | "capture-unavailable"
    | "canvas-changed"
    | "instance-changed"
    | "operation-superseded"
    | "viewport-changed"
    | "host-unavailable"
    | "invalid-target"
    | "host-unchanged";
}

interface LibTVViewportOwnerLogEntry {
  canvasId: string;
  status: "committed" | "skipped";
  reason:
    | "bootstrap-applied"
    | "stable-restored"
    | "viewport-accepted"
    | "projection-echo"
    | "canvas-changed"
    | "invalid-viewport"
    | "canvas-unavailable";
  ownership: LibTVViewportOwnership | null;
  viewport: LibTVViewport | null;
}

interface LibTVViewportEventResult {
  status: "committed" | "skipped";
  reason: LibTVViewportOwnerLogEntry["reason"];
}

declare global {
  interface Window {
    __libtv_asset_layout_log: LibTVAssetLayoutLogEntry[];
    __libtv_viewport_owner_log: LibTVViewportOwnerLogEntry[];
    __libtv_apply_viewport_event?: (
      expectedCanvasId: string,
      viewport: LibTVViewport,
    ) => LibTVViewportEventResult;
    __libtv_get_viewport_ownership?: () => Record<
      string,
      LibTVViewportOwnership
    >;
  }
}

function sameViewport(left: LibTVViewport, right: LibTVViewport): boolean {
  return (
    Math.abs(left.x - right.x) <= 0.001 &&
    Math.abs(left.y - right.y) <= 0.001 &&
    Math.abs(left.zoom - right.zoom) <= 0.000001
  );
}

if (typeof window !== "undefined") {
  window.__libtv_asset_layout_log = [];
  window.__libtv_viewport_owner_log = [];
}

export default function Home() {
  const {
    getActiveCanvas,
    setNodes: setStoreNodes,
    addNodeAtFlowCenter,
    addEdge: addStoreEdge,
    removeEdge,
    selectNode,
    selectElements,
    selectedNodeIds,
    selectedEdgeIds,
    routeReactFlowChanges,
    groupSelectedNodes,
    ungroupSelectedNodes,
    removeSelectedNodes,
    undo,
    redo,
    duplicateSelectedNodes,
    setViewport: setStoreViewport,
    activeCanvasId,
    canvases,
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
    toggleAssetPanel,
    toggleCanvasDropdown,
    toggleAddNodePanel,
    isShortcutsPanelOpen,
    toggleShortcutsPanel,
    setCanvasTool,
    setZoomLevel,
    activeDirectorNodeId,
    activeDirectorCanvasId,
    closeDirectorDesk,
    imagePreview,
    closeImagePreview,
    imageAnnotate,
    closeImageAnnotate,
    imageElementEdit,
    closeImageElementEdit,
  } = useUIStore();

  const activeCanvas = getActiveCanvas();
  const nodes = activeCanvas?.nodes ?? emptyNodes;
  const edges = activeCanvas?.edges ?? emptyEdges;
  const flowRef = useRef<ReactFlowInstance<Node, Edge> | null>(null);
  const flowContainerRef = useRef<HTMLElement | null>(null);
  const assetLayoutOperationRef = useRef(0);
  const assetLayoutFrameRef = useRef<number | null>(null);
  const viewportOwnershipRef = useRef<Map<string, LibTVViewportOwnership>>(
    new Map([["canvas-2", "bootstrap"]]),
  );
  const [organizeSnapshot, setOrganizeSnapshot] = useState<{ nodes: Node[]; viewport: { x: number; y: number; zoom: number } } | null>(null);
  const [isSpacePressed, setIsSpacePressed] = useState(false);
  const dragHistorySnapshot = useRef<{ snapshot: GraphSnapshot; nodeIds: string[] } | null>(null);
  const connectionGesture = useRef<{
    nodeId: string | null;
    handleId: string | null;
    handleType: "source" | "target" | null;
  } | null>(null);
  const [flowViewport, setFlowViewport] = useState(() => {
    if (activeCanvasId !== "canvas-2") return activeCanvas?.viewport ?? { x: 0, y: 0, zoom: 1 };
    return typeof window !== "undefined" && window.innerWidth <= 768 ? compactViewport : desktopViewport;
  });
  const focusCanvasRoot = useCallback(() => {
    flowContainerRef.current?.focus({ preventScroll: true });
  }, []);

  const flowNodes = useMemo<Node[]>(
    () => {
      const selectedIds = new Set(selectedNodeIds);
      return nodes.map((node) => ({ ...node, selected: selectedIds.has(node.id) }));
    },
    [nodes, selectedNodeIds],
  );
  const flowEdges = useMemo<Edge[]>(() => {
    const selectedIds = new Set(selectedEdgeIds);
    return edges.map((edge) => ({
      ...edge,
      selected: selectedIds.has(edge.id),
    }));
  }, [edges, selectedEdgeIds]);
  const activeNodeIds = useMemo(() => nodes.map((node) => node.id), [nodes]);
  const directorOwnerReachabilitySignature = useMemo(
    () => createDirectorOwnerReachabilitySignature(canvases),
    [canvases],
  );
  const effectivePan = canvasTool === "pan" || isSpacePressed;

  useEffect(() => {
    const liveOwners = collectLiveDirectorProjectOwners(
      useCanvasStore.getState().canvases,
    );
    const registry = getDirectorProjectRegistrySnapshot();
    const plan = planDirectorOwnerReachability({
      liveOwners,
      registry,
    });
    if (plan.activeOwnerInvalidated) closeDirectorDesk();
    useDirectorStore.getState().reconcileProjectOwners(liveOwners);
    const invalidatedOwner = plan.activeOwnerInvalidated
      ? registry.activeSession?.owner ?? null
      : null;
    if (invalidatedOwner) {
      window.requestAnimationFrame(() => {
        window.requestAnimationFrame(() => {
          useDirectorStore
            .getState()
            .clearTombstonedProjectOwner(invalidatedOwner);
        });
      });
    }
  }, [closeDirectorDesk, directorOwnerReachabilitySignature]);

  useEffect(() => {
    const owners: LibTVUiOwnerSnapshot = {
      imagePreview: imagePreview
        ? { canvasId: imagePreview.canvasId, nodeId: imagePreview.nodeId }
        : null,
      imageAnnotate: imageAnnotate
        ? { canvasId: imageAnnotate.canvasId, nodeId: imageAnnotate.nodeId }
        : null,
      imageElementEdit: imageElementEdit
        ? { canvasId: imageElementEdit.canvasId, nodeId: imageElementEdit.nodeId }
        : null,
      director: activeDirectorNodeId
        ? {
            canvasId: activeDirectorCanvasId ?? "",
            nodeId: activeDirectorNodeId,
          }
        : null,
    };
    const result = reconcileLibTVUiOwners({
      activeCanvasId,
      activeNodeIds,
      owners,
    });
    const invalidOwners = new Set(result.invalidOwners);

    if (invalidOwners.has("imagePreview")) closeImagePreview();
    if (invalidOwners.has("imageAnnotate")) closeImageAnnotate();
    if (invalidOwners.has("imageElementEdit")) closeImageElementEdit();
    if (invalidOwners.has("director")) {
      if (owners.director) {
        useDirectorStore.getState().closeSession({
          route: "libtv",
          canvasId: owners.director.canvasId,
          sourceNodeId: owners.director.nodeId,
        });
      }
      closeDirectorDesk();
    }
  }, [
    activeCanvasId,
    activeDirectorCanvasId,
    activeDirectorNodeId,
    activeNodeIds,
    closeDirectorDesk,
    closeImageAnnotate,
    closeImageElementEdit,
    closeImagePreview,
    imageAnnotate,
    imageElementEdit,
    imagePreview,
  ]);

  useEffect(() => {
    if (activeDirectorNodeId !== null) return;
    useDirectorStore.getState().closeSession();
  }, [activeDirectorNodeId]);

  useEffect(() => {
    const imageOwner = imageAnnotate ?? imageElementEdit;
    if (!imageOwner) return;
    const ownsSelection =
      selectedNodeIds.length === 1 && selectedNodeIds[0] === imageOwner.nodeId;
    if (!ownsSelection) {
      closeImageAnnotate();
      closeImageElementEdit();
    }
  }, [
    closeImageAnnotate,
    closeImageElementEdit,
    imageAnnotate,
    imageElementEdit,
    selectedNodeIds,
  ]);

  const onNodesChange = useCallback(
    (changes: NodeChange[]) => {
      routeReactFlowChanges({
        expectedActiveCanvasId: activeCanvasId,
        nodeChanges: changes,
      });
    },
    [activeCanvasId, routeReactFlowChanges],
  );

  const onEdgesChange = useCallback(
    (changes: EdgeChange[]) => {
      routeReactFlowChanges({
        expectedActiveCanvasId: activeCanvasId,
        edgeChanges: changes,
      });
    },
    [activeCanvasId, routeReactFlowChanges],
  );

  const validateActiveConnection = useCallback((params: Connection | Edge) => {
    const canvas = useCanvasStore.getState().getActiveCanvas();
    return validateLibTVGraphConnection(
      proposedLibTVConnectionFromEdge(params, "react-flow"),
      canvas?.nodes ?? [],
      canvas?.edges ?? [],
    );
  }, []);

  const isValidConnection = useCallback(
    (params: Connection | Edge) =>
      validateActiveConnection(params).status === "allow",
    [validateActiveConnection],
  );

  const onConnect = useCallback(
    (params: Connection) => {
      const validation = validateActiveConnection(params);
      if (validation.status === "reject") return;
      const { connection } = validation;
      addStoreEdge({
        id: `e-${connection.sourceNodeId}-${connection.targetNodeId}-${Date.now()}`,
        source: connection.sourceNodeId,
        sourceHandle: connection.sourceHandleId,
        target: connection.targetNodeId,
        targetHandle: connection.targetHandleId,
        type: "default",
      });
    },
    [addStoreEdge, validateActiveConnection],
  );

  const onConnectStart = useCallback<OnConnectStart>((_, params) => {
    connectionGesture.current = params;
  }, []);

  const onConnectEnd = useCallback<OnConnectEnd<Node>>(() => {
    connectionGesture.current = null;
  }, []);

  const applyViewportEvent = useCallback(
    (
      expectedCanvasId: string,
      viewport: LibTVViewport,
    ): LibTVViewportEventResult => {
      const log = (
        status: LibTVViewportOwnerLogEntry["status"],
        reason: LibTVViewportOwnerLogEntry["reason"],
        ownership: LibTVViewportOwnership | null,
      ): LibTVViewportEventResult => {
        window.__libtv_viewport_owner_log.push({
          canvasId: expectedCanvasId,
          status,
          reason,
          ownership,
          viewport: isValidLibTVViewport(viewport) ? { ...viewport } : null,
        });
        return { status, reason };
      };

      if (useCanvasStore.getState().activeCanvasId !== expectedCanvasId) {
        return log("skipped", "canvas-changed", null);
      }
      if (!isValidLibTVViewport(viewport)) {
        return log("skipped", "invalid-viewport", null);
      }

      const ownership =
        viewportOwnershipRef.current.get(expectedCanvasId) ??
        (expectedCanvasId === "canvas-2" ? "bootstrap" : "stable");
      const bootstrapViewport =
        expectedCanvasId === "canvas-2"
          ? window.matchMedia("(max-width: 768px)").matches
            ? compactViewport
            : desktopViewport
          : null;
      if (
        ownership === "bootstrap" &&
        bootstrapViewport &&
        sameViewport(bootstrapViewport, viewport)
      ) {
        return log("committed", "projection-echo", ownership);
      }

      viewportOwnershipRef.current.set(expectedCanvasId, "stable");
      setFlowViewport(viewport);
      setStoreViewport(viewport);
      setZoomLevel(Math.round(viewport.zoom * 100));
      return log("committed", "viewport-accepted", "stable");
    },
    [setStoreViewport, setZoomLevel],
  );

  const onViewportChange = useCallback(
    (viewport: LibTVViewport) => {
      applyViewportEvent(activeCanvasId, viewport);
    },
    [activeCanvasId, applyViewportEvent],
  );

  useEffect(() => {
    window.__libtv_apply_viewport_event = applyViewportEvent;
    window.__libtv_get_viewport_ownership = () =>
      Object.fromEntries(viewportOwnershipRef.current.entries());
    return () => {
      delete window.__libtv_apply_viewport_event;
      delete window.__libtv_get_viewport_ownership;
    };
  }, [applyViewportEvent]);

  const addNodeAtHostCenter = useCallback(
    (type: string, data?: Record<string, unknown>) => {
      const instance = flowRef.current;
      const host =
        flowContainerRef.current?.querySelector<HTMLElement>(
          "[data-libtv-react-flow-host]",
        ) ?? null;
      if (!instance || !host) return;

      const hostRect = host.getBoundingClientRect();
      const clientCenter = getLibTVHostCenterClientPoint({
        left: hostRect.left,
        top: hostRect.top,
        width: hostRect.width,
        height: hostRect.height,
      });
      if (!clientCenter) return;

      try {
        addNodeAtFlowCenter(
          type,
          instance.screenToFlowPosition(clientCenter),
          data,
        );
      } catch {
        // A stale/unmounted React Flow instance must not create a misplaced node.
      }
    },
    [addNodeAtFlowCenter],
  );

  const runAssetHostLayoutAction = useCallback(
    (action: () => void) => {
      const operationId = ++assetLayoutOperationRef.current;
      if (assetLayoutFrameRef.current !== null) {
        window.cancelAnimationFrame(assetLayoutFrameRef.current);
        assetLayoutFrameRef.current = null;
      }

      const instance = flowRef.current;
      const host =
        flowContainerRef.current?.querySelector<HTMLElement>(
          "[data-libtv-react-flow-host]",
        ) ?? null;
      const capturedViewport = instance?.getViewport() ?? null;
      const oldHostRect = host?.getBoundingClientRect() ?? null;
      const oldClientCenter = oldHostRect
        ? getLibTVHostCenterClientPoint({
            left: oldHostRect.left,
            top: oldHostRect.top,
            width: oldHostRect.width,
            height: oldHostRect.height,
          })
        : null;
      let flowAnchor: { x: number; y: number } | null = null;

      if (instance && oldClientCenter) {
        try {
          flowAnchor = instance.screenToFlowPosition(oldClientCenter);
        } catch {
          flowAnchor = null;
        }
      }

      action();

      if (!instance || !oldHostRect || !capturedViewport || !flowAnchor) {
        window.__libtv_asset_layout_log.push({
          operationId,
          canvasId: activeCanvasId,
          status: "skipped",
          reason: "capture-unavailable",
        });
        return;
      }

      const capturedCanvasId = activeCanvasId;
      assetLayoutFrameRef.current = window.requestAnimationFrame(() => {
        assetLayoutFrameRef.current = window.requestAnimationFrame(() => {
          assetLayoutFrameRef.current = null;
          const log = (reason: LibTVAssetLayoutLogEntry["reason"]) => {
            window.__libtv_asset_layout_log.push({
              operationId,
              canvasId: capturedCanvasId,
              status: reason === "committed" ? "committed" : "skipped",
              reason,
            });
          };

          if (assetLayoutOperationRef.current !== operationId) {
            log("operation-superseded");
            return;
          }
          if (useCanvasStore.getState().activeCanvasId !== capturedCanvasId) {
            log("canvas-changed");
            return;
          }
          if (flowRef.current !== instance) {
            log("instance-changed");
            return;
          }
          if (!sameViewport(instance.getViewport(), capturedViewport)) {
            log("viewport-changed");
            return;
          }

          const nextHost =
            flowContainerRef.current?.querySelector<HTMLElement>(
              "[data-libtv-react-flow-host]",
            ) ?? null;
          if (!nextHost) {
            log("host-unavailable");
            return;
          }
          const nextHostRect = nextHost.getBoundingClientRect();
          if (
            Math.abs(nextHostRect.left - oldHostRect.left) <= 0.5 &&
            Math.abs(nextHostRect.top - oldHostRect.top) <= 0.5 &&
            Math.abs(nextHostRect.width - oldHostRect.width) <= 0.5 &&
            Math.abs(nextHostRect.height - oldHostRect.height) <= 0.5
          ) {
            log("host-unchanged");
            return;
          }

          const targetViewport = getLibTVViewportForFlowAtHostCenter(
            flowAnchor,
            {
              left: nextHostRect.left,
              top: nextHostRect.top,
              width: nextHostRect.width,
              height: nextHostRect.height,
            },
            capturedViewport.zoom,
          );
          if (!targetViewport) {
            log("invalid-target");
            return;
          }

          applyViewportEvent(capturedCanvasId, targetViewport);
          log("committed");
        });
      });
    },
    [activeCanvasId, applyViewportEvent],
  );

  const toggleAssetPanelWithAnchor = useCallback(() => {
    runAssetHostLayoutAction(toggleAssetPanel);
  }, [runAssetHostLayoutAction, toggleAssetPanel]);

  const openCanvasDropdownFromAsset = useCallback(() => {
    runAssetHostLayoutAction(toggleCanvasDropdown);
  }, [runAssetHostLayoutAction, toggleCanvasDropdown]);

  useEffect(
    () => () => {
      assetLayoutOperationRef.current += 1;
      if (assetLayoutFrameRef.current !== null) {
        window.cancelAnimationFrame(assetLayoutFrameRef.current);
      }
    },
    [],
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
    applyViewportEvent(activeCanvasId, organizedViewport);
  }, [
    activeCanvasId,
    applyViewportEvent,
    flowViewport,
    nodes,
    selectNode,
    setStoreNodes,
  ]);

  const restoreOrganize = () => {
    if (organizeSnapshot) {
      setStoreNodes(organizeSnapshot.nodes, { recordHistory: true });
      applyViewportEvent(activeCanvasId, organizeSnapshot.viewport);
    }
    setOrganizeSnapshot(null);
  };

  useEffect(() => {
    const media = window.matchMedia("(max-width: 768px)");
    let frame = 0;
    const applyResponsiveViewport = () => {
      window.cancelAnimationFrame(frame);
      const capturedCanvasId = activeCanvasId;
      frame = window.requestAnimationFrame(() => {
        const state = useCanvasStore.getState();
        if (state.activeCanvasId !== capturedCanvasId) {
          window.__libtv_viewport_owner_log.push({
            canvasId: capturedCanvasId,
            status: "skipped",
            reason: "canvas-changed",
            ownership: null,
            viewport: null,
          });
          return;
        }

        const canvas = state.canvases.find(
          (item) => item.id === capturedCanvasId,
        );
        if (!canvas) {
          window.__libtv_viewport_owner_log.push({
            canvasId: capturedCanvasId,
            status: "skipped",
            reason: "canvas-unavailable",
            ownership: null,
            viewport: null,
          });
          return;
        }

        const ownership =
          viewportOwnershipRef.current.get(capturedCanvasId) ??
          (capturedCanvasId === "canvas-2" ? "bootstrap" : "stable");
        viewportOwnershipRef.current.set(capturedCanvasId, ownership);
        const bootstrapViewport =
          capturedCanvasId === "canvas-2"
            ? media.matches
              ? compactViewport
              : desktopViewport
            : canvas.viewport;
        const plan = planLibTVResponsiveViewportProjection(
          canvas.viewport,
          bootstrapViewport,
          ownership,
        );
        if (!plan) {
          window.__libtv_viewport_owner_log.push({
            canvasId: capturedCanvasId,
            status: "skipped",
            reason: "invalid-viewport",
            ownership,
            viewport: null,
          });
          return;
        }

        setFlowViewport(plan.viewport);
        if (plan.shouldWriteStore) setStoreViewport(plan.viewport);
        setZoomLevel(Math.round(plan.viewport.zoom * 100));
        window.__libtv_viewport_owner_log.push({
          canvasId: capturedCanvasId,
          status: "committed",
          reason: plan.shouldWriteStore
            ? "bootstrap-applied"
            : "stable-restored",
          ownership: plan.ownership,
          viewport: { ...plan.viewport },
        });
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
    const handleActiveImageSurfaceKeyDown = (event: KeyboardEvent) => {
      const uiState = useUIStore.getState();
      const hasActiveImageSurface =
        Boolean(uiState.imagePreview) ||
        Boolean(uiState.imageAnnotate) ||
        Boolean(uiState.imageElementEdit);
      if (hasActiveImageSurface) {
        const modifier = event.metaKey || event.ctrlKey;
        const blocksBrowserDefault =
          event.key === "Escape" ||
          event.key === "Delete" ||
          event.key === "Backspace" ||
          event.key === "Tab" ||
          event.code === "Space" ||
          (modifier && ["z", "y", "d"].includes(event.key.toLowerCase()));
        if (blocksBrowserDefault) event.preventDefault();
        event.stopImmediatePropagation();

        if (event.key !== "Escape") return;
        if (uiState.imagePreview) uiState.closeImagePreview();
        else if (uiState.imageAnnotate) uiState.closeImageAnnotate();
        else uiState.closeImageElementEdit();
        return;
      }

      if (event.isComposing || isLibTVEditableCommandTarget(event.target)) return;
      if (!resolveLibTVBlockingForegroundSurface(uiState)) return;

      if (event.key === "Escape") {
        event.preventDefault();
        uiState.closeTopForegroundSurface();
        focusCanvasRoot();
        event.stopImmediatePropagation();
        return;
      }
      if (isLibTVCanvasCommandKey(event)) {
        event.preventDefault();
        event.stopImmediatePropagation();
      }
    };

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.isComposing || isLibTVEditableCommandTarget(event.target)) return;
      const uiState = useUIStore.getState();
      if (uiState.activeDirectorNodeId) return;
      if (resolveLibTVBlockingForegroundSurface(uiState)) return;

      const modifier = event.metaKey || event.ctrlKey;

      if (event.code === "Space") {
        event.preventDefault();
        if (!event.repeat) setIsSpacePressed(true);
        return;
      }
      if (event.key === "Delete" || event.key === "Backspace") {
        const selection = useCanvasStore.getState().getSelectionSnapshot();
        if (selection.nodeIds.length > 0) {
          event.preventDefault();
          removeSelectedNodes(selection.nodeIds);
        }
      }
      if (event.key === "Escape") {
        const selection = useCanvasStore.getState().getSelectionSnapshot();
        if (selection.kind !== "none") {
          event.preventDefault();
          selectElements({ nodeIds: [], edgeIds: [] });
          focusCanvasRoot();
        }
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
        const selection = useCanvasStore.getState().getSelectionSnapshot();
        if (selection.nodeIds.length > 0) {
          event.preventDefault();
          duplicateSelectedNodes(selection.nodeIds);
        }
      }
      if (event.key === "Tab") {
        event.preventDefault();
        toggleAddNodePanel();
      }
      if (!modifier && !event.altKey && event.key.toLowerCase() === "g") {
        event.preventDefault();
        const selection = useCanvasStore.getState().getSelectionSnapshot();
        if (event.shiftKey) ungroupSelectedNodes(selection.nodeIds);
        else groupSelectedNodes(selection.nodeIds);
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
      const uiState = useUIStore.getState();
      if (uiState.activeDirectorNodeId || uiState.imageAnnotate || uiState.imageElementEdit) {
        setIsSpacePressed(false);
        return;
      }
      if (event.code === "Space") setIsSpacePressed(false);
    };
    const resetTemporaryPan = () => setIsSpacePressed(false);
    const handleVisibilityChange = () => {
      if (document.hidden) resetTemporaryPan();
    };

    window.addEventListener("keydown", handleActiveImageSurfaceKeyDown, true);
    window.addEventListener("keydown", handleKeyDown);
    window.addEventListener("keyup", handleKeyUp);
    window.addEventListener("blur", resetTemporaryPan);
    document.addEventListener("visibilitychange", handleVisibilityChange);
    return () => {
      window.removeEventListener("keydown", handleActiveImageSurfaceKeyDown, true);
      window.removeEventListener("keydown", handleKeyDown);
      window.removeEventListener("keyup", handleKeyUp);
      window.removeEventListener("blur", resetTemporaryPan);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, [
    duplicateSelectedNodes,
    fitView,
    focusCanvasRoot,
    groupSelectedNodes,
    organize,
    removeSelectedNodes,
    redo,
    selectElements,
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

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#141414]">
      <TopNavBar />
      {isAssetPanelOpen && (
        <AssetManagerPanel
          onClose={toggleAssetPanelWithAnchor}
          onOpenCanvasDropdown={openCanvasDropdownFromAsset}
        />
      )}

      <main
        ref={flowContainerRef}
        data-libtv-canvas-focus-root
        tabIndex={-1}
        className="relative min-w-0 flex-1 overflow-hidden outline-none"
      >
        {editorMode === "storyboard" ? (
          <StoryboardBoard />
        ) : (
          <ReactFlow
            key={activeCanvasId}
            nodes={flowNodes}
            edges={showEdges ? flowEdges : []}
            onInit={(instance) => {
              flowRef.current = instance;
              setZoomLevel(Math.round(flowViewport.zoom * 100));
            }}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            isValidConnection={isValidConnection}
            onConnect={onConnect}
            onConnectStart={onConnectStart}
            onConnectEnd={onConnectEnd}
            onNodeClick={(event, node) => {
              if (!event.metaKey && !event.ctrlKey) selectNode(node.id);
            }}
            onPaneClick={() => {
              selectElements({ nodeIds: [], edgeIds: [] });
              focusCanvasRoot();
            }}
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
            data-libtv-react-flow-host
            data-canvas-tool={canvasTool}
            data-temporary-pan={isSpacePressed}
            defaultEdgeOptions={{ type: "default", animated: false, style: { stroke: "#7a8090", strokeWidth: 1.5 } }}
            snapToGrid={snapToGrid}
            snapGrid={[20, 20]}
            onViewportChange={onViewportChange}
            panOnScroll
            panOnScrollSpeed={1}
            zoomOnScroll
            panOnDrag={effectivePan ? [0, 1] : [1]}
            panActivationKeyCode={null}
            selectionOnDrag={false}
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
        {editorMode === "workbench" && flowNodes.length === 0 && <CanvasEmptyState />}
      </main>

      {isAgentOpen && <AgentDrawer />}

      <LeftSidebar onAddNode={addNodeAtHostCenter} />
      <BottomToolbar
        onToggleAssetPanel={toggleAssetPanelWithAnchor}
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
      {imagePreview && (
        <ImagePreviewOverlay
          preview={imagePreview}
          onClose={closeImagePreview}
        />
      )}
      {activeDirectorNodeId && activeDirectorCanvasId && (
        <DirectorDesk
          canvasId={activeDirectorCanvasId}
          sourceNodeId={activeDirectorNodeId}
          onClose={closeDirectorDesk}
        />
      )}
    </div>
  );
}
