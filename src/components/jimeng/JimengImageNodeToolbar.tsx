"use client";

import { useState } from "react";
import {
  Box,
  ChevronDown,
  ChevronRight,
  Crop,
  Download,
  Eraser,
  Expand,
  FileSearch,
  Film,
  LayoutGrid,
  Lasso,
  Maximize2,
  Rotate3d,
  Scan,
  Smile,
  Sparkles,
  User,
  WandSparkles,
  Wrench,
} from "lucide-react";
import { NodeToolbar, Position } from "@xyflow/react";

import { VipDiamond } from "@/components/jimeng/icons";
import { useJimengStore } from "@/store/jimengStore";

/**
 * 选中图片节点后上方弹出的操作工具条 (Batch 195/208/209)。
 *
 * 证据 (SOURCE_FACT, README §6 + 208-source-image-toolbar.png /
 * 209-menu-crop2.png):
 * - 面板与节点同宽 (569×40)，复用视频工具条深色药丸 (.jimeng-node-toolbar,
 *   rgb(32,32,32) r12 h40)
 * - 条目: 智能改图✦ / 扩图 / 智能超清 / 抠图 / 多角度 / 工具∨；
 *   仅智能改图带 14×14 VIP 菱标，智能超清此处无 VIP 标 (与视频工具条不同)
 * - 尾部: 分隔线 + 全屏预览 + 下载 32×32 图标钮 (208 截图修正 195 误判；
 *   下载沿用保存门控为 CLONE_DECISION)
 * - 工具∨ 菜单 (批 209 采样): 232px 面板，两组——「编辑」消除笔/构图/
 *   宫格切分(›)/提示词反推，「预设」场景俯视图/连续分镜图/多机位九宫格/
 *   人物三视图/面部三视图/产品三视图；行 38px 图标+13px 白字，
 *   分组标签 12px white/40；展开时箭头朝上
 * mock: 菜单项与各按钮 pushToast。
 */

type ToolbarItem = { label: string; icon: typeof Expand; vip?: boolean; chevron?: boolean };

/**
 * ⭐⭐⭐⭐⭐ Batch 1032-④-B（C01）：**每一项都必须诚实**。
 *
 * 此前这 18 项（6 主项 + 10 工具菜单项 + 全屏预览 + 下载）**全部**走同一条
 * `onAction(label) => pushToast(mockMsg(`${label}已执行`))` ⇒ ⇒ 画面零变化，
 * 而文案恰恰在说「已经做完了」。
 *
 * 处置分两类，**不许有第三类**：
 *  · **能做** ⇒ 接**真动作**（store 的真实状态变更）；
 *  · **做不了** ⇒ **真禁用态 + 可见理由**（`disabled` + `title` + 面板里
 *    逐字写明为什么），而不是「亮着但点了什么也不会发生」。
 *
 * ⚠️ 「不可用理由」必须**是这句能力本身的原因**，不是「（mock）」这种标注 ——
 *   标注只说明「这是原型」，不告诉用户**为什么这个按钮不能按**。
 */
const ITEMS: ToolbarItem[] = [
  { label: "智能改图", icon: WandSparkles, vip: true },
  { label: "扩图", icon: Expand },
  { label: "智能超清", icon: Sparkles },
  { label: "抠图", icon: Lasso },
  { label: "多角度", icon: Rotate3d },
  { label: "工具", icon: Wrench, chevron: true },
];

/** 本原型**做不了**的那些项 —— 键是项的文案，值是**用户看得见的理由**。 */
const UNAVAILABLE_REASON: Record<string, string> = {
  智能改图: "智能改图需要后端图像编辑服务，本原型只提供画布交互，未接入该能力",
  扩图: "扩图需要后端生成服务，本原型只提供画布交互，未接入该能力",
  抠图: "抠图需要后端图像编辑服务，本原型只提供画布交互，未接入该能力",
  多角度: "多角度需要后端生成服务，本原型只提供画布交互，未接入该能力",
  消除笔: "消除笔需要后端图像编辑服务，本原型只提供画布交互，未接入该能力",
  构图: "构图需要后端图像编辑服务，本原型只提供画布交互，未接入该能力",
  宫格切分: "宫格切分需要后端生成服务，本原型只提供画布交互，未接入该能力",
  场景俯视图: "预设生成需要后端生成服务，本原型只提供画布交互，未接入该能力",
  连续分镜图: "预设生成需要后端生成服务，本原型只提供画布交互，未接入该能力",
  多机位九宫格: "预设生成需要后端生成服务，本原型只提供画布交互，未接入该能力",
  人物三视图: "预设生成需要后端生成服务，本原型只提供画布交互，未接入该能力",
  面部三视图: "预设生成需要后端生成服务，本原型只提供画布交互，未接入该能力",
  产品三视图: "预设生成需要后端生成服务，本原型只提供画布交互，未接入该能力",
};

const TOOL_MENU_GROUPS: { group: string; items: { label: string; icon: typeof Expand; sub?: boolean }[] }[] = [
  {
    group: "编辑",
    items: [
      { label: "消除笔", icon: Eraser },
      { label: "构图", icon: Crop },
      { label: "宫格切分", icon: LayoutGrid, sub: true },
      { label: "提示词反推", icon: FileSearch },
    ],
  },
  {
    group: "预设",
    items: [
      { label: "场景俯视图", icon: Scan },
      { label: "连续分镜图", icon: Film },
      { label: "多机位九宫格", icon: LayoutGrid },
      { label: "人物三视图", icon: User },
      { label: "面部三视图", icon: Smile },
      { label: "产品三视图", icon: Box },
    ],
  },
];

export function JimengImageNodeToolbar({
  visible,
  onAction,
}: {
  visible: boolean;
  onAction?: (label: string) => void;
}) {
  const saved = useJimengStore((s) => s.project.saved);
  const [toolsOpen, setToolsOpen] = useState(false);
  const run = (label: string) => {
    setToolsOpen(false);
    onAction?.(label);
  };

  return (
    <NodeToolbar isVisible={visible} position={Position.Top} offset={36}>
      <div className="jimeng-node-toolbar flex h-10 select-none items-center gap-0.5 px-1.5">
        {ITEMS.map((item) => {
          const Icon = item.icon;
          const isTools = item.label === "工具";
          /* ⭐⭐⭐ Batch 1032-④-B（C01）：本原型做不了的项 ⇒ **真禁用态**。
             ⚠️ 「禁用」用 `disabled` 属性（而不是 `aria-disabled` + 仍可点）
             ⇒ ⇒ 浏览器与辅助技术都会把它当成不可用；
             ⚠️ 理由用 `title` ⇒ **鼠标悬停可见**（不是隐藏的 aria-describedby），
             因为「用户看得见为什么不能按」是这条整改的验收点。 */
          const reason = UNAVAILABLE_REASON[item.label];
          const unavailable = reason !== undefined && !isTools;
          return (
            <div key={item.label} className="relative">
              <button
                type="button"
                disabled={unavailable}
                title={reason}
                onClick={() => (isTools ? setToolsOpen((v) => !v) : run(item.label))}
                className={`jimeng-node-toolbar-item flex h-8 items-center gap-1 whitespace-nowrap px-2 text-[13px] leading-none text-white ${
                  unavailable ? "cursor-not-allowed text-white/35" : ""
                } ${isTools && toolsOpen ? "bg-white/10" : ""}`}
              >
                <Icon size={16} className="shrink-0" />
                {item.label}
                {item.vip ? <VipDiamond size={14} /> : null}
                {item.chevron ? (
                  <ChevronDown
                    size={12}
                    className={`ml-0.5 shrink-0 text-white/70 transition-transform ${
                      isTools && toolsOpen ? "rotate-180" : ""
                    }`}
                  />
                ) : null}
              </button>

              {/* 工具∨ 菜单 (批 209 SOURCE_FACT): 锚在按钮下方、右对齐面板右缘 */}
              {isTools && toolsOpen ? (
                <div
                  className="absolute right-0 top-full z-[130] mt-2 w-[232px] rounded-xl p-1.5"
                  style={{ background: "rgb(38,38,38)" }}
                  role="menu"
                  aria-label="工具菜单"
                  data-testid="image-tools-menu"
                >
                  {TOOL_MENU_GROUPS.map((g, gi) => (
                    <div key={g.group}>
                      {gi > 0 ? <div className="mx-1 my-1 h-px bg-white/10" aria-hidden /> : null}
                      <p className="px-2.5 pb-0.5 pt-1 text-[12px] text-white/40">{g.group}</p>
                      {g.items.map((it) => {
                        const ItIcon = it.icon;
                        /* ⭐⭐⭐ 同上：工具菜单里的项也逐条判可用性。 */
                        const itReason = UNAVAILABLE_REASON[it.label];
                        const itUnavailable = itReason !== undefined;
                        return (
                          <button
                            key={it.label}
                            type="button"
                            role="menuitem"
                            disabled={itUnavailable}
                            title={itReason}
                            onClick={() => run(`${it.label}`)}
                            className={`flex h-[38px] w-full items-center gap-2.5 whitespace-nowrap rounded-lg px-2.5 text-[13px] ${
                              itUnavailable
                                ? "cursor-not-allowed text-white/35"
                                : "text-white hover:bg-white/10"
                            }`}
                          >
                            <ItIcon size={16} className="shrink-0 text-white/85" />
                            {it.label}
                            {it.sub ? (
                              <ChevronRight size={13} className="ml-auto shrink-0 text-white/50" />
                            ) : null}
                          </button>
                        );
                      })}
                    </div>
                  ))}
                </div>
              ) : null}
            </div>
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
