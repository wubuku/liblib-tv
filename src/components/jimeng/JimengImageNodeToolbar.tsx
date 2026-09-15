"use client";

import {
  ChevronDown,
  Expand,
  Lasso,
  Rotate3d,
  Sparkles,
  WandSparkles,
  Wrench,
} from "lucide-react";
import { NodeToolbar, Position } from "@xyflow/react";

import { VipDiamond } from "@/components/jimeng/icons";

/**
 * 选中图片节点后上方弹出的操作工具条 (Batch 195)。
 *
 * 证据 (SOURCE_FACT, docs/research/jimeng-canvas/README.md §6, 195 源站提取):
 * - 面板与节点同宽 (569×40)，复用视频工具条深色药丸 (.jimeng-node-toolbar,
 *   rgb(32,32,32) r12 h40)
 * - 条目: 智能改图✦ / 扩图 / 智能超清 / 抠图 / 多角度 / 工具∨；
 *   仅智能改图带 14×14 VIP 菱标，工具带 12×12 下拉箭头；
 *   智能超清此处无 VIP 标 (与视频工具条不同)
 * - 与视频工具条差异: 无分隔线、无全屏/下载尾钮
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
  return (
    <NodeToolbar isVisible={visible} position={Position.Top} offset={36}>
      <div className="jimeng-node-toolbar flex h-10 select-none items-center gap-0.5 px-1.5">
        {ITEMS.map((item) => {
          const Icon = item.icon;
          return (
            <button
              key={item.label}
              type="button"
              onClick={() => onAction?.(item.label)}
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
      </div>
    </NodeToolbar>
  );
}
