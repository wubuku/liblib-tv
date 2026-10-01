"use client";

import { Box, ChevronRight } from "lucide-react";
import type { NodeProps } from "@xyflow/react";

import { nodeRingShadow } from "@/components/jimeng/nodeChrome";
import type { JimengDirectorNodeData } from "@/types/jimeng";
import { JimengNodeTitle } from "@/components/jimeng/nodes/JimengNodeTitle";
import { JimengConnectHandles } from "@/components/jimeng/JimengConnectHandles";
import { useJimengStore } from "@/store/jimengStore";
import { FEEDBACK } from "@/components/jimeng/jimengFeedback";

/**
 * 导演台节点 (Batch 805 SOURCE_FACT @1680×826 实测 320×320)。
 *
 * 左栏「导演台」按钮点下去之后出现的东西（源站落点 `rf__node-*` role=group，
 * 在 viewport 内，顶栏节点计数 +1）—— 此前复刻当成"打开浮层"，所以是死按钮。
 *
 * 空态：3D 立方图标 +「在 3D 空间中设计角色、机位与镜头」+「进入导演台」按钮。
 * 源站把资源统计放在 sr-only（"No resources: 0 ready, 0 processing, 0 failed."），
 * 复刻同样不做成可见状态行（与 batch 794 的资源计数处理一致）。
 */
export function JimengDirectorNode({ id, data, selected }: NodeProps) {
  const d = data as JimengDirectorNodeData;
  const updateNodeData = useJimengStore((s) => s.updateNodeData);
  const pushToast = useJimengStore((s) => s.pushToast);
  const entered = d.entered === true;
  const ready = d.ready ?? 0;
  const processing = d.processing ?? 0;
  const failed = d.failed ?? 0;

  return (
    <div
      className="group relative"
      style={{ width: d.width, height: d.height }}
      data-jimeng-node-selected={selected || undefined}
      data-testid="director-node"
    >
      <div className="absolute inset-x-0 top-[-31px] z-10 flex h-8 items-start gap-1 text-left">
        <Box size={16} className="mt-1 shrink-0" />
        <JimengNodeTitle id={id} title={d.title} />
      </div>

      <div
        className="flex h-full w-full flex-col items-center justify-center gap-3 overflow-hidden rounded-lg px-6 text-center"
        style={{
          background: "rgb(32,32,32)",
          boxShadow: nodeRingShadow(selected === true),
        }}
      >
        <Box size={28} className="text-white/70" />
        <p className="text-[13px]/[20px] text-white/80" data-testid="director-caption">
          {entered ? "已进入导演台，场景为 3D 空间" : "在 3D 空间中设计角色、机位与镜头"}
        </p>
        <button
          type="button"
          data-testid="director-enter"
          onClick={() => {
            updateNodeData(id, { entered: !entered });
            pushToast(entered ? FEEDBACK.exitDirectorStage() : FEEDBACK.enterDirectorStage());
          }}
          className="flex h-8 items-center gap-1 rounded-lg bg-white/10 px-4 text-[13px] font-medium text-white hover:bg-white/20"
        >
          {entered ? "退出演讲台" : "进入导演台"}
          {!entered ? <ChevronRight size={14} /> : null}
        </button>
        <span className="sr-only">
          {ready + processing + failed === 0
            ? "No resources: 0 ready, 0 processing, 0 failed."
            : `${ready} ready, ${processing} processing, ${failed} failed.`}
        </span>
      </div>

      <JimengConnectHandles
        nodeId={id}
        title={d.title}
        size={{ width: d.width, height: d.height }}
        selected={selected === true}
      />
    </div>
  );
}
