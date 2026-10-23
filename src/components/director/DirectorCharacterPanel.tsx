"use client";

// ★★★ Batch 858（源站逐字）：导演台左侧的「**添加角色**」**侧栏面板**。
//
// ★ ★★ 本组件存在的理由（= batch 857 登记的 D1）：
//
//   源站逐字（源站 chunk，`aU` 组件）：
//     `e?null:(0,i.jsxs)("div",{className:"flex w-[232px] min-w-0 flex-col bg-[#171717]",
//        children:["scene"===z?n:null,"character"===z?(…添加角色…)]})`
//     ⟹ ⟹ **左侧面板是「模式切换」**：`z` 只能是 `"scene"`（场景树）
//     **或** `"character"`（添加角色）⟹ ⟹ **两者互斥、永远不同时出现**。
//     ⟹ ⟹ 源站在「添加角色」模式下**根本看不到场景树**。
//
//   clone 此前把「添加角色」做成 **rail 上的浮层（portal 覆盖层）**
//     ⟹ ⟹ 场景树**仍然在浮层下面** ⟹ ⟹ 实测浮层矩形 x=48..280 与场景树
//     x=48..280 **完全重叠** ⟹ ⟹ 浮层里的选项**截走**落在组行上的点击
//     ⟹ ⟹ **场景树看着能点、其实点不动**（batch 857 的命中测试证据）。
//
// ★ 本组件把「添加角色」改成**左侧面板模式**（与源站逐字同构）：
//   ① 面板内容区宽度 **232px**、底色 `#171717`、纵向 flex；
//   ② 标题条 `flex h-12 shrink-0 items-center px-3 text-[12px] leading-5
//      text-white/90` ＋ 内层 `<span class="truncate">`（源站 `aO`）；
//   ③ 列表 `min-h-0 flex-1 overflow-y-auto px-2 pb-3`；
//   ④ 每一行 `flex h-8 w-full items-center gap-2 rounded-lg px-2 text-left
//      text-[13px] leading-5 text-white/88 transition-colors hover:bg-white/8`
//      （源站 `eu`，逐字照抄）；
//   ⑤ 「群众 (3x3)」带 `aria-haspopup="dialog"` ＋ `aria-expanded`
//      ＋ 展开态 `bg-white/8`；
//   ⑥ 「几何模型」**就地展开**（`border-white/8 ml-3 border-l pl-1`），
//      **不是**绝对定位的浮层（源站逐字就是就地展开）。
//
// ★ ★ 面板化之后，几何**逐字命中源站**（数字来自源站实测，不是估算）：
//   列表首行顶 ＝ 52（顶栏下沿）＋ 48（标题条）＝ 100
//   「群众 (3x3)」是第 **10** 行 ⟹ ⟹ 顶 ＝ 100 ＋ 9×32 ＝ **388**
//   ⟹ ⟹ 按钮 x ＝ 48 ＋ 8（px-2）＝ **56**、宽 ＝ 232 − 16 ＝ **216**
//   ⟹ ⟹ 对话框 ＝ 按钮 right+8 ＝ **280**、top ＝ **388**
//   ⟹ ⟹ 即 **220×204 @(280,388)** ⟹ ⟹ 与源站实测**逐字一致**（batch 857 实测）。
//   几何就地展开：x ＝ 56 ＋ 12（ml-3）＝ **68**、宽 ＝ 216 − 12 ＝ **204**
//   ⟹ ⟹ 与 batch 590 对源站的实测 **(68,452) 204×256** 逐字一致。
//
// ★ 源站的两个子菜单（crowd / geometry）**共用一个状态变量**（源站 `L`）：
//   `"crowd"===L` / `"geometry"===L` ⟹ ⟹ **互斥** ⟹ ⟹ 本组件用单一
//   `submenu` 状态复刻，而不是两个独立布尔量。
import { useCallback, useEffect, useLayoutEffect, useRef, useState, type ChangeEvent } from "react";
import { createPortal } from "react-dom";
import {
  Box,
  ChevronRight,
  Layers,
  Plus,
  Upload,
  UserRound,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useDirectorStore } from "@/store/directorStore";
import { readDirectorLocalModelFiles } from "@/components/director/directorLocalModelImport";

// ★ 源站逐字（`eu`）：行样式。`disabled:*` 两段源站也有，这里照抄。
const ROW_CLASS =
  "flex h-8 w-full items-center gap-2 rounded-lg px-2 text-left text-[13px] leading-5 text-white/88 transition-colors hover:bg-white/8 disabled:cursor-not-allowed disabled:opacity-45";

// ★ 添加角色列表（源站逐字顺序：本地上传 → 8 个体型 → 群众 (3x3) → 几何模型）
const characterItems = [
  { id: "local-upload", label: "本地上传", icon: Upload },
  { id: "standard-male", label: "标准男性", icon: UserRound },
  { id: "standard-female", label: "标准女性", icon: UserRound },
  { id: "muscular", label: "健硕", icon: UserRound },
  { id: "slim", label: "纤细", icon: UserRound },
  { id: "teen", label: "少年", icon: UserRound },
  { id: "child", label: "儿童", icon: UserRound },
  { id: "broad", label: "宽厚", icon: UserRound },
  { id: "chibi", label: "二头身", icon: UserRound },
  { id: "crowd-3x3", label: "群众 (3x3)", icon: UserRound },
  { id: "geometry", label: "几何模型", icon: Box },
] as const;

// ★ 几何模型子菜单（源站逐字：**就地展开**在父项下方）。
//   ⚠ 源站这 6 个几何体**共用同一个** `u.p.layers` 图标（不是各自不同的形状图），
//   最后一个「添加空对象」用 `u.p.Add` ⟹ ⟹ 这里照抄，别"好心"改成不同图标。
const geometryItems = [
  { id: "geometry-upload", label: "上传文件", icon: Upload },
  { id: "cube", label: "立方体", icon: Layers },
  { id: "sphere", label: "球体", icon: Layers },
  { id: "cylinder", label: "圆柱体", icon: Layers },
  { id: "torus", label: "环状体", icon: Layers },
  { id: "cone", label: "圆锥", icon: Layers },
  { id: "pyramid", label: "棱锥", icon: Layers },
  { id: "empty-object", label: "添加空对象", icon: Plus },
] as const;

// ★ 源站逐字：行/列 `min:1,max:10,step:1`、间距 `min:.1,max:10,step:.1`
const CROWD_LIMITS = {
  rows: { min: 1, max: 10 },
  columns: { min: 1, max: 10 },
  spacing: { min: 0.1, max: 10 },
} as const;

// ★ 源站逐字：对话框 `fixed z-[1800]` ⟹ ⟹ 4317 冻结 CSS 里**确实有**
//   `z-[1800]`（已用 scripts/check-tailwind-classes-in-css.py 实测）⟹ ⟹ 可直接用。
//   ⚠ `bg-[rgba(31,31,31,0.98)]` **不在**冻结 CSS 里（实测 MISS）⟹ ⟹ 走 inline style。

type AnchorRect = { left: number; top: number; right: number; bottom: number };

export function DirectorCharacterPanel({ active }: { active: boolean }) {
  const addCrowdArray = useDirectorStore((state) => state.addCrowdArray);
  const addLocalModelLibraryItem = useDirectorStore(
    (state) => state.addLocalModelLibraryItem,
  );

  const uploadInputRef = useRef<HTMLInputElement | null>(null);
  const crowdButtonRef = useRef<HTMLButtonElement | null>(null);
  const crowdDialogRef = useRef<HTMLDivElement | null>(null);

  const [ack, setAck] = useState<string | null>(null);
  // ★ 源站的 crowd 与 geometry **共用一个**状态变量 `L` ⟹ ⟹ 互斥。
  const [submenu, setSubmenu] = useState<"crowd" | "geometry" | null>(null);
  const [crowdDraft, setCrowdDraft] = useState({ rows: 3, columns: 3, spacing: 1.2 });
  const [crowdAnchor, setCrowdAnchor] = useState<AnchorRect | null>(null);
  const [crowdPos, setCrowdPos] = useState<{ left: number; top: number } | null>(
    null,
  );

  const flashAck = useCallback((message: string) => {
    setAck(message);
    window.setTimeout(() => setAck(null), 2000);
  }, []);

  // ★★★ 源站逐字：源站的群众对话框**锚在「群众按钮」自己身上**：
  //   `W({left:Math.max(8,Math.min(t.right+8,window.innerWidth-r-8)),
  //      top:Math.max(8,Math.min(t.top,window.innerHeight-n-8))})`
  //   ⟹ ⟹ r/n ＝ 对话框**自己**的宽高，量不到时兜底 **220**（源站同）⟹ ⟹ 两边 8px 安全边。
  const placeCrowdDialog = useCallback((anchor: AnchorRect) => {
    const box = crowdDialogRef.current?.getBoundingClientRect();
    const width = box?.width || 220;
    const height = box?.height || 220;
    setCrowdPos({
      left: Math.max(8, Math.min(anchor.right + 8, window.innerWidth - width - 8)),
      top: Math.max(8, Math.min(anchor.top, window.innerHeight - height - 8)),
    });
  }, []);

  const openCrowdDialog = useCallback((anchor: AnchorRect) => {
    setCrowdAnchor(anchor);
    setCrowdPos({
      left: Math.max(8, Math.min(anchor.right + 8, window.innerWidth - 220 - 8)),
      top: Math.max(8, Math.min(anchor.top, window.innerHeight - 220 - 8)),
    });
    setSubmenu("crowd");
  }, []);

  // 对话框挂上之后，用**实测**宽高再算一次（源站用 offsetWidth/offsetHeight）。
  useLayoutEffect(() => {
    if (submenu !== "crowd" || !crowdAnchor) return;
    placeCrowdDialog(crowdAnchor);
  }, [submenu, crowdAnchor, placeCrowdDialog]);

  // 视口变了要重算（源站监听 resize ＋ 捕获阶段的 scroll）。
  useEffect(() => {
    if (submenu !== "crowd" || !crowdAnchor) return;
    const onViewportChange = () => placeCrowdDialog(crowdAnchor);
    window.addEventListener("resize", onViewportChange);
    document.addEventListener("scroll", onViewportChange, true);
    return () => {
      window.removeEventListener("resize", onViewportChange);
      document.removeEventListener("scroll", onViewportChange, true);
    };
  }, [submenu, crowdAnchor, placeCrowdDialog]);

  // ★★★ 源站逐字：点在**群众按钮**或**对话框**之外 ⟹ ⟹ 关掉对话框。
  //   源站逐字：
  //     `en.current?.contains(t)||ea.current?.contains(t)||O(null)`
  //   ⟹ ⟹ ★ 「群众入口」有**两枚**（面板里的 ＋ 移动端视口工具条那枚）
  //   ⟹ ⟹ 两枚都算「入口自己」⟹ ⟹ 不然移动端那枚会被 mousedown 关掉、
  //   又被 click 打开 ⟹ ⟹ 净效果是「一直开着」⟹ ⟹ **不是开关**。
  useEffect(() => {
    if (submenu !== "crowd") return;
    const onMouseDown = (event: MouseEvent) => {
      const target = event.target as HTMLElement | null;
      if (!target) return;
      if (target.closest?.(
        "[data-director-character-option='crowd-3x3'], "
          + "[data-director-crowd-mobile-trigger]",
      )) {
        return;
      }
      if (crowdDialogRef.current?.contains(target)) return;
      setSubmenu(null);
    };
    document.addEventListener("mousedown", onMouseDown);
    return () => document.removeEventListener("mousedown", onMouseDown);
  }, [submenu]);

  // ★★★ 移动端那枚入口用事件把「自己的矩形」递进来（clone 自己的扩展）。
  //   ⚠ 本组件**必须常驻挂载**（哪怕面板本身不显示）⟹ ⟹ 否则这枚监听器
  //   不存在、移动端那枚入口就成了「点了没反应」的死按钮。
  useEffect(() => {
    const onOpenCrowd = (event: Event) => {
      const detail = (event as CustomEvent<{ rect?: AnchorRect }>).detail;
      if (!detail?.rect) return;
      // 源站的「群众 (3x3)」是**开关** ⟹ ⟹ 移动端那枚照同样的语义做。
      if (submenu === "crowd") {
        setSubmenu(null);
        return;
      }
      openCrowdDialog(detail.rect);
    };
    window.addEventListener("director:open-crowd-dialog", onOpenCrowd);
    return () =>
      window.removeEventListener("director:open-crowd-dialog", onOpenCrowd);
  });

  const handleUploadChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const input = event.currentTarget;
    try {
      const items = await readDirectorLocalModelFiles(input.files ?? []);
      if (items.length === 0) {
        flashAck("未选择可用模型文件");
        return;
      }
      items.forEach(addLocalModelLibraryItem);
      flashAck(`已导入 ${items.length} 个本地模型至模型库`);
    } finally {
      input.value = "";
    }
  };

  const handleItem = (itemId: string, label: string) => {
    if (itemId === "crowd-3x3") {
      // ★★★ 源站逐字：这一枚是**开关** ——
      //   `if("crowd"===L)return void O(null); … O("crowd")`
      if (submenu === "crowd") {
        setSubmenu(null);
        return;
      }
      const rect = crowdButtonRef.current?.getBoundingClientRect();
      if (rect) {
        openCrowdDialog({
          left: rect.left,
          top: rect.top,
          right: rect.right,
          bottom: rect.bottom,
        });
      }
      return;
    }
    if (itemId === "local-upload") {
      uploadInputRef.current?.click();
      return;
    }
    if (itemId === "geometry") {
      // ★ 源站逐字：`O(e => "geometry"===e ? null : "geometry")`
      setSubmenu((current) => (current === "geometry" ? null : "geometry"));
      return;
    }
    flashAck(`预设角色「${label}」为本地等效占位`);
  };

  const handleGeometryItem = (optionId: string, label: string) => {
    setSubmenu(null);
    if (optionId === "geometry-upload") {
      uploadInputRef.current?.click();
      return;
    }
    flashAck(`几何体「${label}」为本地等效占位`);
  };

  const confirmCrowdArray = () => {
    addCrowdArray(crowdDraft);
    setSubmenu(null);
    flashAck(
      `已加入群众 ${crowdDraft.rows}×${crowdDraft.columns}（间距 ${crowdDraft.spacing}）`,
    );
  };

  const dialog = submenu === "crowd" && crowdPos && typeof document !== "undefined"
    ? createPortal(
        <div
          ref={crowdDialogRef}
          data-director-crowd-dialog
          role="dialog"
          aria-label="添加群众阵列"
          // ★ 源站逐字：`fixed z-[1800] … shadow-[0_8px_24px_rgba(0,0,0,0.35)]`
          //   ⟹ ⟹ `bg-[rgba(31,31,31,0.98)]` 不在冻结 CSS 里 ⟹ ⟹ 走 inline style。
          className="fixed z-[1800] w-[220px] rounded-xl border border-white/10 p-3 text-white shadow-[0_8px_24px_rgba(0,0,0,0.35)] backdrop-blur-xl"
          style={{
            left: crowdPos.left,
            top: crowdPos.top,
            background: "rgba(31,31,31,0.98)",
          }}
        >
          {/* ★ 源站逐字：`mb-3 flex items-center justify-between gap-2` */}
          <div className="mb-3 flex items-center justify-between gap-2">
            <span className="text-[13px] font-medium text-white/90">添加群众阵列</span>
            <span data-director-crowd-count className="text-[11px] text-white/45">
              共{crowdDraft.rows * crowdDraft.columns}人
            </span>
          </div>
          {/* ★ 源站逐字：`grid grid-cols-2 gap-2` —— 间距那一格是
              `col-span-2`（**在** grid 里，不是另起一个块）。 */}
          <div className="grid grid-cols-2 gap-2">
            <label className="flex min-w-0 flex-col gap-1 text-[11px] leading-[1.55] text-white/55">
              <span>行数</span>
              <input
                type="number"
                data-director-crowd-input="rows"
                aria-label="行数"
                min={CROWD_LIMITS.rows.min}
                max={CROWD_LIMITS.rows.max}
                step={1}
                value={crowdDraft.rows}
                onChange={(event) =>
                  setCrowdDraft((draft) => ({
                    ...draft,
                    rows: Math.min(
                      CROWD_LIMITS.rows.max,
                      Math.max(CROWD_LIMITS.rows.min, Number(event.target.value)),
                    ),
                  }))
                }
                className="h-7 min-w-0 rounded-lg border border-white/10 bg-white/[0.06] px-2 text-[12px] text-white outline-none transition-colors focus:border-white/30"
              />
            </label>
            <label className="flex min-w-0 flex-col gap-1 text-[11px] leading-[1.55] text-white/55">
              <span>列数</span>
              <input
                type="number"
                data-director-crowd-input="columns"
                aria-label="列数"
                min={CROWD_LIMITS.columns.min}
                max={CROWD_LIMITS.columns.max}
                step={1}
                value={crowdDraft.columns}
                onChange={(event) =>
                  setCrowdDraft((draft) => ({
                    ...draft,
                    columns: Math.min(
                      CROWD_LIMITS.columns.max,
                      Math.max(CROWD_LIMITS.columns.min, Number(event.target.value)),
                    ),
                  }))
                }
                className="h-7 min-w-0 rounded-lg border border-white/10 bg-white/[0.06] px-2 text-[12px] text-white outline-none transition-colors focus:border-white/30"
              />
            </label>
            {/* ★ 源站逐字：`col-span-2` —— 间距占满整行。 */}
            <label className="col-span-2 flex min-w-0 flex-col gap-1 text-[11px] leading-[1.55] text-white/55">
              <span>间距</span>
              <input
                type="number"
                data-director-crowd-input="spacing"
                aria-label="间距"
                min={CROWD_LIMITS.spacing.min}
                max={CROWD_LIMITS.spacing.max}
                step={0.1}
                value={crowdDraft.spacing}
                onChange={(event) => {
                  // ★★★ Batch 857（源站逐字）：间距**保留 1 位小数**
                  //   `Number.isFinite(t=valueAsNumber)
                  //     ? Math.min(10,Math.max(.1,Math.round(10*t)/10)) : .1`
                  //   ⟹ ⟹ 源站**实测**（raw/source-857-crowd.json）：把间距填成
                  //   **1.55** ⟹ ⟹ 源站读回 **1.6** ⟹ ⟹ 行为证据，不是「读代码所以这么说」。
                  //   ⟹ ⟹ 源站在非数字时兜底成 **0.1**（＝量程下限），照抄。
                  const next = event.currentTarget.valueAsNumber;
                  setCrowdDraft((draft) => ({
                    ...draft,
                    spacing: Number.isFinite(next)
                      ? Math.min(
                          CROWD_LIMITS.spacing.max,
                          Math.max(
                            CROWD_LIMITS.spacing.min,
                            Math.round(next * 10) / 10,
                          ),
                        )
                      : CROWD_LIMITS.spacing.min,
                  }));
                }}
                className="h-7 min-w-0 rounded-lg border border-white/10 bg-white/[0.06] px-2 text-[12px] text-white outline-none transition-colors focus:border-white/30"
              />
            </label>
          </div>
          {/* ★ 源站逐字：`mt-3 flex justify-end gap-2` ＋ 两枚按钮的类名。 */}
          <div className="mt-3 flex justify-end gap-2">
            <button
              type="button"
              data-director-crowd-cancel
              onClick={() => setSubmenu(null)}
              className="flex h-7 items-center justify-center rounded-lg px-3 text-[12px] text-white/60 transition-colors hover:bg-white/10 hover:text-white"
            >
              取消
            </button>
            <button
              type="button"
              data-director-crowd-confirm
              onClick={confirmCrowdArray}
              className="flex h-7 items-center justify-center rounded-lg bg-white px-3 text-[12px] text-[#171717] transition-colors hover:bg-white/90"
            >
              添加
            </button>
          </div>
        </div>,
        document.body,
      )
    : null;

  return (
    <>
      {active ? (
        <div
          data-director-character-panel
          aria-label="添加角色"
          className="flex h-full min-h-0 w-full flex-col bg-[#171717]"
        >
          {/* ★ 源站逐字（`aO`）：`flex h-12 shrink-0 items-center px-3
              text-[12px] leading-5 text-white/90` ＋ `<span class="truncate">` */}
          <div
            data-director-panel-title="add-character"
            className="flex h-12 shrink-0 items-center px-3 text-[12px] leading-5 text-white/90"
          >
            <span className="truncate">添加角色</span>
          </div>
          {/* ★ 源站逐字：列表 `min-h-0 flex-1 overflow-y-auto px-2 pb-3`
              ＋ `[scrollbar-color:…] [scrollbar-width:thin]`
              ⟹ ⟹ 那两个任意值不在冻结 CSS 里 ⟹ ⟹ 走 inline style。 */}
          <div
            className="min-h-0 flex-1 overflow-y-auto px-2 pb-3"
            style={{
              scrollbarColor: "rgba(255,255,255,0.2) transparent",
              scrollbarWidth: "thin",
            }}
          >
            {characterItems.map((item) => {
              const ItemIcon = item.icon;
              const isSubmenu = item.id === "crowd-3x3" || item.id === "geometry";
              const open =
                item.id === "crowd-3x3"
                  ? submenu === "crowd"
                  : item.id === "geometry"
                    ? submenu === "geometry"
                    : false;
              return (
                <button
                  key={item.id}
                  type="button"
                  ref={item.id === "crowd-3x3" ? crowdButtonRef : undefined}
                  data-director-character-option={item.id}
                  // ★ 源站逐字：`"aria-haspopup":"dialog","aria-expanded":"crowd"===L`
                  aria-haspopup={item.id === "crowd-3x3" ? "dialog" : undefined}
                  aria-expanded={item.id === "crowd-3x3" ? open : undefined}
                  onClick={() => handleItem(item.id, item.label)}
                  className={cn(ROW_CLASS, open && "bg-white/8")}
                >
                  <ItemIcon className="size-3.5 shrink-0" aria-hidden="true" />
                  <span
                    className={cn(
                      isSubmenu ? "min-w-0 flex-1 truncate" : "truncate",
                    )}
                  >
                    {item.label}
                  </span>
                  {isSubmenu ? (
                    <span aria-hidden="true" className="shrink-0">
                      <ChevronRight className="size-3.5" />
                    </span>
                  ) : null}
                </button>
              );
            })}
            {/* ★ 源站逐字：几何模型是**就地展开**
                （`"geometry"===L?(… "border-white/8 ml-3 border-l pl-1" …)`）
                ⟹ ⟹ **不是**绝对定位的浮层。 */}
            {submenu === "geometry" ? (
              <div
                data-director-geometry-submenu
                aria-label="几何模型"
                className="border-white/8 ml-3 border-l pl-1"
              >
                {geometryItems.map((option) => {
                  const OptionIcon = option.icon;
                  return (
                    <button
                      key={option.id}
                      type="button"
                      data-director-geometry-option={option.id}
                      onClick={() => handleGeometryItem(option.id, option.label)}
                      className={ROW_CLASS}
                    >
                      <OptionIcon className="size-3.5" aria-hidden="true" />
                      <span className="truncate">{option.label}</span>
                    </button>
                  );
                })}
              </div>
            ) : null}
          </div>
          <input
            ref={uploadInputRef}
            type="file"
            accept=".glb,.gltf,.fbx,.obj"
            multiple
            aria-label="导入本地角色模型"
            className="hidden"
            onChange={handleUploadChange}
          />
          {ack ? (
            <span
              data-director-character-ack
              aria-live="polite"
              className="absolute bottom-14 left-3 whitespace-nowrap rounded-full bg-black/70 px-2.5 py-1 text-[11px] text-[#9ddbb9]"
            >
              {ack}
            </span>
          ) : null}
        </div>
      ) : null}
      {dialog}
    </>
  );
}
