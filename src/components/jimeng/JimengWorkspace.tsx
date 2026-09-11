"use client";

import { useCallback } from "react";
import { ReactFlow, ReactFlowProvider } from "@xyflow/react";
import type { OnMove } from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { useJimengStore } from "@/store/jimengStore";
import { JimengVideoNode } from "@/components/jimeng/nodes/JimengVideoNode";
import { JimengTopBar } from "@/components/jimeng/JimengTopBar";
import { JimengToolRail } from "@/components/jimeng/JimengToolRail";
import { JimengBottomDock } from "@/components/jimeng/JimengBottomDock";
import { JimengAiButton } from "@/components/jimeng/JimengAiButton";

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

  const onPaneClick = useCallback(() => selectNode(null), [selectNode]);

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
        onMove={onMove}
        defaultViewport={DEFAULT_VIEWPORT}
        minZoom={0.1}
        maxZoom={4}
        proOptions={{ hideAttribution: true }}
        deleteKeyCode={null}
        zoomOnDoubleClick={false}
      />
    </div>
  );
}

export function JimengWorkspace() {
  return (
    <div className="relative h-screen w-screen overflow-hidden">
      <ReactFlowProvider>
        <JimengFlow />
      </ReactFlowProvider>
      <JimengTopBar />
      <JimengToolRail />
      <JimengBottomDock />
      <JimengAiButton />
    </div>
  );
}
