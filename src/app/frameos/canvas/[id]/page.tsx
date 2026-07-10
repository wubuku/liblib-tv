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
import { FrameosToolRail } from "@/components/frameos/FrameosToolRail";
import { FrameosMapDock } from "@/components/frameos/FrameosMapDock";
import { FrameosPromptBar } from "@/components/frameos/FrameosPromptBar";
import { FrameosNodeEditPanel } from "@/components/frameos/FrameosNodeEditPanel";
import { FrameosHelpPanel } from "@/components/frameos/FrameosHelpPanel";
import { FrameosMaterialLibrary } from "@/components/frameos/FrameosMaterialLibrary";
import { FrameosSidePanel } from "@/components/frameos/FrameosSidePanel";
import { FrameosConfirmDialog } from "@/components/frameos/FrameosConfirmDialog";
import {
  FrameosContextMenu,
  openContextMenu,
} from "@/components/frameos/FrameosContextMenu";
import { FrameosToast, showToast } from "@/components/frameos/FrameosToast";
import { FrameosNodeTooltip } from "@/components/frameos/FrameosNodeTooltip";
import { FrameosGenerationOverlay } from "@/components/frameos/FrameosGenerationOverlay";
import { FrameosAlignmentGuides } from "@/components/frameos/FrameosAlignmentGuides";
import { FrameosNodeFloatingToolbar } from "@/components/frameos/FrameosNodeFloatingToolbar";

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
  const { zoomIn, zoomOut, fitView } = useReactFlow();
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

      // Cmd/Ctrl + S - 保存 (mock)
      if ((e.metaKey || e.ctrlKey) && e.key === "s") {
        e.preventDefault();
        showToast("已保存当前画布", "success");
        return;
      }

      // Cmd/Ctrl + A - 全选 (mock, 留接口)
      if ((e.metaKey || e.ctrlKey) && e.key === "a") {
        // 阻止浏览器原生 select-all (画布不要求节点全选, 这是编辑器入口)
        // 这里直接 return 让浏览器原生效, 不开启节点全选
        return;
      }

      // 方向键 - 移动选中节点 (Shift = 10px, 默认 1px)
      if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(e.key) && state.selectedNodeId) {
        e.preventDefault();
        const step = e.shiftKey ? 10 : 1;
        const dx = e.key === "ArrowLeft" ? -step : e.key === "ArrowRight" ? step : 0;
        const dy = e.key === "ArrowUp" ? -step : e.key === "ArrowDown" ? step : 0;
        const selId = state.selectedNodeId;
        useFrameosStore.getState().setNodes(
          state.nodes.map(n => n.id === selId
            ? { ...n, position: { x: n.position.x + dx, y: n.position.y + dy } }
            : n)
        );
        return;
      }

      // Tab - 切换选中下一个节点
      if (e.key === "Tab" && state.nodes.length > 0) {
        e.preventDefault();
        const ids = state.nodes.map(n => n.id);
        const cur = ids.indexOf(state.selectedNodeId ?? "");
        const next = ids[(cur + 1 + ids.length) % ids.length];
        useFrameosStore.getState().selectNode(next);
        return;
      }

      // Delete / Backspace - 弹确认对话框
      if ((e.key === "Delete" || e.key === "Backspace") && state.selectedNodeId) {
        e.preventDefault();
        const node = state.nodes.find((n) => n.id === state.selectedNodeId);
        if (node) {
          state.requestConfirm({ kind: "node", id: node.id, name: node.data.title as string });
        }
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
      // M - 切换小地图 (frameos.cn 快捷键)
      if (e.key === "m" || e.key === "M") {
        e.preventDefault();
        useFrameosStore.getState().toggleMinimap();
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
            label: "复制",
            shortcut: "⌘C",
            onClick: () => {
              // mock 复制到剪贴板 (原站真实复用 ipc+navigator.clipboard)
              try {
                navigator.clipboard.writeText(
                  JSON.stringify({ kind: "frameos-node", node: n })
                );
              } catch {
                /* mock */
              }
              showToast(`已复制「${n.data.title}」`, "success");
            },
          },
          {
            label: "创建副本",
            shortcut: "⌘D",
            onClick: () => {
              duplicateNode(node.id);
              showToast(`已创建「${n.data.title}」副本`, "success");
            },
          },
          { separator: true, label: "" },
          {
            label: "删除",
            danger: true,
            shortcut: "⌫",
            onClick: () => {
              useFrameosStore.getState().requestConfirm({ kind: "node", id: node.id, name: n.data.title as string });
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
            onClick: () => fitView({ duration: 200, padding: 0.15 }),
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
        // 自绘 minimap (FrameosMapDock) 处理节点点击, ReactFlow 内置 minimap 已禁用.
        // v12 的 onMinimapNodeClick 既未定义又不支持, 删除避免 React 警告.
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
        multiSelectionKeyCode={["Shift", "Meta", "Control"]}
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
        {/* 画布底纹 (复刻原站 frameos.cn 双层点阵 + 暗角) */}
        <div
          aria-hidden
          style={{
            position: "absolute",
            inset: 0,
            zIndex: 0,
            pointerEvents: "none",
            backgroundImage:
              "radial-gradient(rgba(0, 0, 0, 0) 58%, rgba(0, 0, 0, 0.26) 100%)," +
              "radial-gradient(circle, rgba(255, 255, 255, 0.04) 1px, rgba(0, 0, 0, 0) 1.5px)," +
              "radial-gradient(circle, rgba(255, 255, 255, 0.07) 1px, rgba(0, 0, 0, 0) 1.5px)",
            backgroundSize: "cover, 16px 16px, 32px 32px",
            backgroundPosition: "center, center, center",
            backgroundRepeat: "no-repeat, repeat, repeat",
          }}
        />
        <Background
          variant={BackgroundVariant.Dots}
          gap={32}
          size={1}
          color="rgba(255,255,255,0.07)"
        />
      </ReactFlowAny>

      {/* 顶部浮动元素 */}
      <FrameosAppHeader />

      {/* 左侧浮动 rail */}
      <FrameosToolRail />

      {/* 左下 dock */}
      <FrameosMapDock />

      {/* 右侧节点编辑面板 */}
      <FrameosNodeEditPanel />

      {/* 选中节点的浮动工具条 (跟随节点位置 + 画布缩放) */}

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

      {/* 确认对话框 (删除节点/边) */}
      <FrameosConfirmDialogShell />

      {/* 素材库面板 (从 FrameosToolRail 触发) */}
      <FrameosMaterialLibrary />

      {/* 侧边面板 (展开菜单按钮控制) */}
      <FrameosSidePanel />

      {/* 历史记录面板 */}

      {/* 节点搜索面板 (Cmd+K) */}

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

      {/* 选中节点时的浮动工具条 (原站: 下载按钮) */}
      <FrameosNodeFloatingToolbar />

    </div>
  );
}

function FrameosConfirmDialogShell() {
  const pendingConfirm = useFrameosStore((s) => s.pendingConfirm);
  const requestConfirm = useFrameosStore((s) => s.requestConfirm);
  const removeNode = useFrameosStore((s) => s.removeNode);
  const removeEdge = useFrameosStore((s) => s.removeEdge);

  if (!pendingConfirm) return null;

  const handleConfirm = () => {
    if (pendingConfirm.kind === "node") {
      removeNode(pendingConfirm.id);
      window.dispatchEvent(
        new CustomEvent("frameos-toast", {
          detail: { message: `已删除「${pendingConfirm.name}」`, variant: "warning" },
        })
      );
    } else {
      removeEdge(pendingConfirm.id);
      window.dispatchEvent(
        new CustomEvent("frameos-toast", {
          detail: { message: "已删除连线", variant: "warning" },
        })
      );
    }
    requestConfirm(null);
  };

  return (
    <FrameosConfirmDialog
      open={!!pendingConfirm}
      title={pendingConfirm.kind === "node" ? "删除节点" : "删除连线"}
      message={
        pendingConfirm.kind === "node"
          ? `确认删除「${pendingConfirm.name}」？此操作可通过 Ctrl+Z 撤销。`
          : "确认删除这条连线？此操作可通过 Ctrl+Z 撤销。"
      }
      confirmLabel="删除"
      danger
      onConfirm={handleConfirm}
      onCancel={() => requestConfirm(null)}
    />
  );
}

export default function FrameosCanvasPage() {
  return (
    <ReactFlowProvider>
      <FrameosCanvasInner />
    </ReactFlowProvider>
  );
}
