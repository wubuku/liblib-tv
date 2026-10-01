"use client";

import { useEffect, useState } from "react";
import { Plus } from "lucide-react";
import { Handle, Position } from "@xyflow/react";

import { JimengInsertMenu } from "@/components/jimeng/JimengInsertMenu";
import { useJimengStore } from "@/store/jimengStore";

/**
 * 节点连接手柄 (Batch 804)。
 *
 * 结构证据 (SOURCE_FACT, 2026-10-03 登录态实测
 * docs/research/jimeng-canvas-batch804-2026-10-03/handle2-source.json)：
 *
 * 1. **实名** = `Create connected node before {节点标题}` /
 *    `Create connected node after {节点标题}`。标题动态插值，实测过
 *    「视频 1」「音频 4」「音频 5」三个节点，串长随标题变化。
 *    此前复刻用中文「左侧添加节点/右侧添加节点」，与源站对不上。
 * 2. **命中盒** = `<button>` **36×36**，`rounded-lg`(8px)，
 *    `border border-transparent`、`p-2` —— 自身**无底色无边框**。
 * 3. **外观**（像素级 804-source-plus-left.png，36×36 盒内 ASCII 亮度图）：
 *    盒中是一个**空心圆环**，外径 ≈24px、1px 描边，环内**完全透明**
 *    （露出画布底 rgb(13,13,13)），中心一个 ≈8×11 的 `+` 字形。
 *    复刻此前是 36px **实心**深色圆盘（`bg-[#0D0D0D]` + `border-white/50`），
 *    环径与填充两处都偏大。
 * 4. **位置** = 垂直居中于节点；水平方向**紧贴节点缘外侧**，间隙
 *    2~3px（视频节点实测左 3 / 右 2，音频节点 4）。故 36px 命中盒的
 *    左缘落在 `-39px`（= -36 盒宽 - 3 间隙），圆心因此在缘外 21px。
 *    复刻此前把圆钮**骑在节点缘上**
 *    （圆心偏移 0），是 21px 的实差。
 * 5. **出现时机** = **仅节点选中时挂载**。三次定向验证：未选中时
 *    分别悬停在左侧 60×120 热区、节点边缘、节点中心，各等 900ms，
 *    `document.querySelectorAll('[aria-label*="onnected"]')` 恒为 0
 *    —— 不是 CSS 隐藏，是**根本不在 DOM 里**。这条同时**推翻**台账
 *    批 380「DOM 常驻 hover 显示」与 §5「hover/选中显示」。
 * 6. **两侧都有**：选中带媒体的视频节点时 before/after 同时出现，
 *    音频节点同理。**推翻**台账 §5「本地上传节点仅右侧有，空节点
 *    两侧都有」——真实规则与 source 无关，四类节点一律两侧。
 *
 * 不动的部分：60×120 隐形热区。源站类名
 * `react-flow__handle-left nodrag nopan !top-1/2 !z-10 !rounded-none
 * !border-0 !bg-transparent !p-0`，transform `matrix(1,0,0,1,∓30,-60)`
 * —— 圆心正落在节点缘上，与复刻的 `left/right: -30 + translateY(-50%)`
 * 完全一致，本批保持原样。
 */

/** 隐形热区：源站 60×120，圆心压在节点左右缘上（批 17 起既有契约）。 */
const HOT_ZONE = {
  width: 60,
  height: 120,
  background: "transparent",
  border: "none",
  borderRadius: 0,
  top: "50%",
  transform: "translateY(-50%)",
} as const;

/** 命中盒与节点缘的间隙（源站实测 2~3px，取 3）。 */
const GAP = 3;

export function JimengConnectHandles({
  nodeId,
  title,
  size,
  selected,
}: {
  nodeId: string;
  /** 节点标题，进入无障碍名（源站同名字段）。 */
  title: string;
  /** 节点世界尺寸，决定插入新节点的落点。 */
  size: { width: number; height: number };
  selected: boolean;
}) {
  const [side, setSide] = useState<"left" | "right" | null>(null);
  const addNodeAt = useJimengStore((s) => s.addNodeAt);
  const addVideoNodeAfter = useJimengStore((s) => s.addVideoNodeAfter);
  const origin = useJimengStore(
    (s) => s.nodes.find((n) => n.id === nodeId)?.position,
  );

  // Escape 关闭 (沿用批 794 的捕获阶段写法：冒泡监听会被工作区的
  // 同步重渲染跳过)
  useEffect(() => {
    if (!side) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setSide(null);
    };
    window.addEventListener("keydown", onKey, true);
    return () => window.removeEventListener("keydown", onKey, true);
  }, [side]);

  const onPick = (label: string) => {
    if (label === "视频") {
      addVideoNodeAfter(nodeId);
      return;
    }
    // 落点与 addVideoNodeAfter 同一套算式（源点右侧 +160、垂直 +44），
    // 三类依次下移 120px。批 804 顺带修掉的既有缺陷：此前这里直接传
    // `{x: size.width + 200, y: 0|120|240}` 当**绝对**世界坐标用，
    // 新节点一律落在画布原点附近，与源节点毫无关系。
    const at = (dy: number) => ({
      x: (origin?.x ?? 0) + size.width + 160,
      y: (origin?.y ?? 0) + 44 + dy,
    });
    if (label === "图片") addNodeAt("image", at(0));
    if (label === "文本") addNodeAt("text", at(120));
    if (label === "音频") addNodeAt("audio", at(240));
  };

  const plus = (which: "left" | "right") => (
    <button
      key={which}
      type="button"
      aria-label={`Create connected node ${which === "left" ? "before" : "after"} ${title}`}
      data-testid={`jimeng-connect-${which}`}
      className="nodrag absolute top-1/2 z-20 flex size-9 -translate-y-1/2 items-center justify-center"
      style={
        which === "left" ? { left: -(36 + GAP) } : { right: -(36 + GAP) }
      }
      onClick={(e) => {
        e.stopPropagation();
        setSide((cur) => (cur === which ? null : which));
      }}
      onMouseDown={(e) => e.stopPropagation()}
    >
      {/* 空心环：外径 24px、无填充；+ 字形约 10px */}
      <span className="flex size-6 items-center justify-center rounded-full border border-white/50 text-white">
        <Plus size={10} strokeWidth={2.5} />
      </span>
    </button>
  );

  return (
    <>
      <Handle
        type="target"
        position={Position.Left}
        className="!z-10"
        style={{ ...HOT_ZONE, left: -30 }}
      />
      <Handle
        type="source"
        position={Position.Right}
        className="!z-10"
        style={{ ...HOT_ZONE, right: -30 }}
      />
      {selected ? plus("left") : null}
      {selected ? plus("right") : null}
      {side ? (
        <div
          className="nodrag absolute z-[130]"
          style={
            side === "right"
              ? { left: "100%", top: "50%", marginLeft: 22 }
              : { right: "100%", top: "50%", marginRight: 22 }
          }
          onMouseDown={(e) => e.stopPropagation()}
        >
          <JimengInsertMenu
            onPick={(label) => {
              setSide(null);
              onPick(label);
            }}
            onClose={() => setSide(null)}
          />
        </div>
      ) : null}
    </>
  );
}
