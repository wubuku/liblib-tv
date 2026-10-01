"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Scan, X } from "lucide-react";
import {
  MiniMap,
  ReactFlow,
  ReactFlowProvider,
  useReactFlow,
  PanOnScrollMode,
  SelectionMode,
} from "@xyflow/react";
import type { NodeMouseHandler, OnConnectEnd, OnMove } from "@xyflow/react";
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

/** Batch 799 SOURCE_FACT: 源站点阵网格的世界点距 18px（截图逐像素实测）。 */
const GRID_WORLD_PX = 18;

function JimengFlow() {
  // SOURCE_FACT (batch 801): 源站画布根 `.react-flow` 带 aria-label="Canvas"
  // + role="application"（testid=rf__wrapper）。xyflow v12 未开放这两个属性的 prop：
  // <ReactFlow ref> 拿到的是 ReactFlowInstance（fitView 等实例 API），**不是 DOM
  // 节点**，不能直接 setAttribute。故挂外层真实容器 ref，再从中查 .react-flow。
  const canvasBoxRef = useRef<HTMLDivElement | null>(null);
  useEffect(() => {
    const el = canvasBoxRef.current?.querySelector(".react-flow");
    if (!el) return;
    el.setAttribute("aria-label", "Canvas");
    if (!el.getAttribute("role")) el.setAttribute("role", "application");
  }, []);

  const nodes = useJimengStore((s) => s.nodes);
  const edges = useJimengStore((s) => s.edges);
  const onNodesChange = useJimengStore((s) => s.onNodesChange);
  const onEdgesChange = useJimengStore((s) => s.onEdgesChange);
  const selectNode = useJimengStore((s) => s.selectNode);
  const aiDrawerOpen = useJimengStore((s) => s.aiDrawerOpen);
  const setAiDrawerOpen = useJimengStore((s) => s.setAiDrawerOpen);
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
  const edgesVisible = useJimengStore((s) => s.edgesVisible);
  // Batch 793 SOURCE_FACT: 引用参考「从画布选择」点选模式
  const refPicking = useJimengStore((s) => s.refPicking);
  const pickRefNode = useJimengStore((s) => s.pickRefNode);
  const cancelRefPicking = useJimengStore((s) => s.cancelRefPicking);
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

  // 批 230 SOURCE_FACT: 无效连接尝试 → toast「无法连接这些节点」
  const onConnectEndHandler = useCallback<OnConnectEnd>((_event, state) => {
    if (state.isValid === false) {
      useJimengStore.getState().pushToast("无法连接这些节点");
    }
  }, []);

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
        // 批 398 SOURCE_FACT: Agent 面板常驻——Escape 不关闭 (381 实测)
        selectNode(null);
        exitRepaint();
        exitEdit();
        exitInfer();
        exitFramePicker();
        exitTrim();
        closePreview();
        setAssetsOpen(false);
        setOfflineDialog(false);
        cancelRefPicking();
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
    aiDrawerOpen,
    setAiDrawerOpen,
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
    cancelRefPicking,
  ]);

  // Batch 799 SOURCE_FACT: 点阵网格是**世界锚定**的 —— 源站实测 100% 缩放下
  // 屏幕点距 18px，缩到 48% 后变 8.6px（≈18×0.48），即点距随 zoom 缩放。
  // 而复刻的 .react-flow__pane **不在** .react-flow__viewport 内（是屏幕层，
  // 实测 paneInsideViewport=false），CSS background 不会被 viewport 变换缩放，
  // 于是网格会固定在 18px 屏幕间距 —— 缩放时与源站不符。
  // 这里把网格尺寸与相位按真实 viewport 变换写进 CSS 变量，让屏幕层的
  // background 复现世界锚定：tile = 18×zoom，偏移 = pan mod tile。
  const applyGridVars = useCallback((zoom: number, x: number, y: number) => {
    const el = document.querySelector<HTMLElement>(".jimeng-canvas");
    if (!el) return;
    const tile = GRID_WORLD_PX * zoom;
    if (!(tile > 0)) return;
    el.style.setProperty("--jm-grid-tile", `${tile}px`);
    el.style.setProperty("--jm-grid-x", `${x % tile}px`);
    el.style.setProperty("--jm-grid-y", `${y % tile}px`);
  }, []);

  const onMove = useCallback<OnMove>(
    (_event, viewport) => {
      setZoomPercent(viewport.zoom * 100);
      applyGridVars(viewport.zoom, viewport.x, viewport.y);
    },
    [setZoomPercent, applyGridVars],
  );

  // Batch 793 SOURCE_FACT: 点选模式下点击节点 = 选中为引用 (不改变画布选择)
  const onNodeClick = useCallback<NodeMouseHandler>(
    (_event, node) => {
      if (refPicking) {
        pickRefNode(node.id);
      }
    },
    [refPicking, pickRefNode],
  );

  return (
    <div
      ref={canvasBoxRef}
      className={`jimeng-canvas relative h-full w-full ${
        refPicking ? "ring-2 ring-inset ring-[#0A5CD6]" : ""
      }`}
      // Batch 799: 首屏也要有网格变量。onMove 不保证在挂载时触发，
      // 缺了这层 fallback 会导致「不移动就不显示网格」。
      style={
        {
          "--jm-grid-tile": `${GRID_WORLD_PX * DEFAULT_VIEWPORT.zoom}px`,
          "--jm-grid-x": `${DEFAULT_VIEWPORT.x % (GRID_WORLD_PX * DEFAULT_VIEWPORT.zoom)}px`,
          "--jm-grid-y": `${DEFAULT_VIEWPORT.y % (GRID_WORLD_PX * DEFAULT_VIEWPORT.zoom)}px`,
        } as React.CSSProperties
      }
    >
      <ReactFlow
        nodes={nodes}
        edges={edgesVisible ? edges : []}
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
        onConnectEnd={onConnectEndHandler}
        onPaneClick={onPaneClick}
        onNodeClick={onNodeClick}
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
        {/* 小地图 (Batch 91/92, SOURCE_FACT): dock 切换，位于 dock 上方；
            拖拽平移画布、滚轮缩放画布 (92-minimap-sem.json)
            Batch 802 SOURCE_FACT 复测（源站 @1680×826，点「小地图」后量得）：
              导航 dock 面板 @[12,656] **164×154**、padding 4、gap 4、flex column、
              bg rgb(13,13,13)、radius 8；子元素 = 小地图 @[16,660] **156×114**
              + 原 dock 行 @[16,778] 156×28（**与底栏原位重合**）。
              ⇒ 源站是「同一个 dock 变高、小地图插在上方」，不是另浮一个面板。
            复刻是分离浮层，故按**可实现的等价**对齐：把小地图面板落成
            @[12,656] 164×118（4+114+4），其下缘正好贴住底栏顶边 774，
            两者同底色 → 视觉上连成一整条，与源站一致。
            bottom = 826 − 774 = 52；left 12；padding 4（此前 bottom-14 left-4
            p-2 ⇒ 面板 @[16,616]、内层 @[9,641]，整体偏高 40px 且横向错位）。
            残留差异：源站是单一元素统一 8px 圆角，复刻是两块相接，
            接缝处圆角会略有断点（已记入台账）。 */}
        {minimapOpen ? (
          <div
            data-testid="jimeng-minimap-panel"
            className="absolute bottom-[52px] left-3 z-[30] rounded-lg p-1"
            style={{ background: "rgb(13,13,13)", width: 164, height: 118 }}
          >
            <MiniMap
              pannable
              zoomable
              style={{
                width: 156,
                height: 114,
                background: "rgba(255,255,255,0.08)",
                borderRadius: 6,
                // Batch 802: 必须压成**常规流**且清零 margin。`.react-flow__minimap`
                // 被本仓样式表设成 position:absolute + top:-26px / left:-22px +
                // margin:15px（实测 computed），使小地图跑到壳外左侧 @[5,645]；
                // 只改 position 会停在 @[31,675]（差值恰为那 15px margin）。
                // 两者都改后它是外壳 padding(4px) 内的常规块，正好落在
                // @[16,660] 156×114，与源站一致。外壳本身 absolute，定位不受影响。
                position: "static",
                margin: 0,
              }}
              maskColor="rgba(0,0,0,0.45)"
              nodeColor={() => "#4a4a4a"}
              nodeStrokeColor="transparent"
            />
          </div>
        ) : null}
      </ReactFlow>
      {/* Batch 793 SOURCE_FACT: 点选模式顶部 pill「从画布选择 ×」 */}
      {refPicking ? (
        <div
          data-testid="canvas-pick-banner"
          className="absolute left-1/2 top-5 z-[200] flex h-10 -translate-x-1/2 items-center gap-2 rounded-full px-4 text-[14px] text-white"
          style={{ background: "#0A5CD6" }}
        >
          <Scan size={16} />
          从画布选择
          <button
            type="button"
            aria-label="取消从画布选择"
            onClick={cancelRefPicking}
            className="ml-1 flex size-5 items-center justify-center rounded-full hover:bg-white/20"
          >
            <X size={14} />
          </button>
        </div>
      ) : null}
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
  const aiDrawerPrefill = useJimengStore((s) => s.aiDrawerPrefill);

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
          <JimengAiDrawer
            key={aiDrawerPrefill ?? "drawer"}
            onClose={() => setAiDrawerOpen(false)}
          />
        ) : null}
      </div>
    </ReactFlowProvider>
  );
}
