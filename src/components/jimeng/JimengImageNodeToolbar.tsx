"use client";

import { useState } from "react";
import {
  ChevronDown,
  Download,
  Expand,
  Lasso,
  Maximize2,
  Rotate3d,
  Sparkles,
  WandSparkles,
  Wrench,
} from "lucide-react";
import { NodeToolbar, Position } from "@xyflow/react";

import { VipDiamond } from "@/components/jimeng/icons";
import { useJimengStore } from "@/store/jimengStore";

/**
 * 选中图片节点后上方弹出的操作工具条 (Batch 195；Batch 208 截图修正)。
 *
 * 证据 (SOURCE_FACT, README §6 + 208-source-image-toolbar.png):
 * - 面板与节点同宽 (569×40)，复用视频工具条深色药丸 (.jimeng-node-toolbar,
 *   rgb(32,32,32) r12 h40)
 * - 条目: 智能改图✦ / 扩图 / 智能超清 / 抠图 / 多角度 / 工具∨；
 *   仅智能改图带 14×14 VIP 菱标，工具带 12×12 下拉箭头；
 *   智能超清此处无 VIP 标 (与视频工具条不同)
 * - 尾部 (208 截图修正，195 误判「无尾钮」——图标钮无文字曾被 rawText
 *   漏采): 分隔线 + 全屏预览 + 下载 32×32 图标钮 (与视频工具条同族；
 *   下载沿用保存门控为 CLONE_DECISION)
 * - 工具∨ 菜单项源站未捕获 (单击未展开, BLOCKED_BY_EXTRACTION)
 * mock: 各按钮 pushToast。
 */

type ToolbarItem = { label: string; icon: typeof Expand; vip?: boolean; chevron?: boolean };

const ITEMS: ToolbarItem[] = [
  { label: "智能改图", icon: WandSparkles, vip: true },
  { label: "扩图", icon: Expand },
  { label: "智能超清", icon: Sparkles },
  { label: "抠图", icon: Lasso },
  { label: "多角度", icon: Rotate3d },
  { label: "工具", icon: Wrench, chevron: true },
];

export function JimengImageNodeToolbar({
  visible,
  onAction,
}: {
  visible: boolean;
  onAction?: (label: string) => void;
}) {
  const saved = useJimengStore((s) => s.project.saved);
  const run = (label: string) => onAction?.(label);

  return (
    <NodeToolbar isVisible={visible} position={Position.Top} offset={36}>
      <div className="jimeng-node-toolbar flex h-10 select-none items-center gap-0.5 px-1.5">
        {ITEMS.map((item) => {
          const Icon = item.icon;
          return (
            <button
              key={item.label}
              type="button"
              onClick={() => run(item.label)}
              className="jimeng-node-toolbar-item flex h-8 items-center gap-1 whitespace-nowrap px-2 text-[13px] leading-none text-white"
            >
              <Icon size={16} className="shrink-0" />
              {item.label}
              {item.vip ? <VipDiamond size={14} /> : null}
              {item.chevron ? (
                <ChevronDown size={12} className="ml-0.5 shrink-0 text-white/70" />
              ) : null}
            </button>
          );
        })}

        <span className="jimeng-node-toolbar-divider mx-0.5" aria-hidden />

        <button
          type="button"
          aria-label="全屏预览"
          onClick={() => run("全屏预览")}
          className="jimeng-node-toolbar-item flex size-8 items-center justify-center text-white"
        >
          <Maximize2 size={16} />
        </button>
        <button
          type="button"
          aria-label="下载"
          title={saved ? undefined : "导出前请保存画布"}
          disabled={!saved}
          onClick={() => {
            if (saved) run("下载");
          }}
          className={`jimeng-node-toolbar-item flex size-8 items-center justify-center ${
            saved ? "text-white" : "cursor-not-allowed text-white/20"
          }`}
        >
          <Download size={16} />
        </button>
      </div>
    </NodeToolbar>
  );
}
