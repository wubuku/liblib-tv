"use client";

import { Fragment, useEffect, useRef, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";
import {
  ArrowDownToLine,
  Clapperboard,
  HelpCircle,
  History,
  Image as ImageIcon,
  Sparkles,
  Proportions,
  Upload,
  UserRoundPlus,
  Layers,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useDirectorStore } from "@/store/directorStore";
import { DirectorAiImportModal } from "@/components/director/DirectorAiImportModal";

// Batch 536: 2026-09-27 源站采样（liblib-source-exploration-2026-09-25
// NOTES §8 + 截图 18）——3D 导演台最左窄图标栏（约 46px）。
// Batch 537: 同日 CDP DOM 补采修正——rail 实际七入口（aria-label 实证）：
// 场景 / 添加角色 / 添加机位 / 全景图 / 选择画幅比例 / AI 识图导入 +
// 底部帮助（? 圆钮）。仅场景（场景树）与添加角色 flyout 在 clone 有实现；
// 添加机位为直接动作（无面板采样），其余面板未采样（SOURCE_UNCERTAIN）
// 做视觉切换不导航（CLONE_DECISION）。
// Batch 538: 2026-09-27 已存截图转录——全景图 flyout = 本地上传/历史记录/
// AI生成（44-director-rail-25，batch 589 DOM 复核确认无空格）；选择画幅比例 =
// 自适应（默认激活）/
// 21:9/16:9/4:3/1:1/3:4/9:16 七卡单选（44-director-rail-26）。
// AI生成/AI 识图为付费 AI 动作，clone 仅可视不触发。
const railEntries = [
  { id: "scene", label: "场景", icon: Layers, kind: "panel" },
  { id: "add-character", label: "添加角色", icon: UserRoundPlus, kind: "panel" },
  { id: "add-camera", label: "添加机位", icon: Clapperboard, kind: "panel" },
  { id: "panorama", label: "全景图", icon: ImageIcon, kind: "flyout" },
  { id: "aspect-ratio", label: "选择画幅比例", icon: Proportions, kind: "flyout" },
  { id: "ai-import", label: "AI 识图导入", icon: ArrowDownToLine, kind: "modal" },
] as const;


// 全景图 flyout（源站 2026-10-01 DOM 复核：232×96 @(48,100)，三项行距
// 32px）。Batch 589 修正文案：逐字是「AI生成」——**无空格**，batch 538
// 从截图转录时记成了「AI 生成」。
const panoramaFlyout = [
  { id: "local-upload", label: "本地上传", icon: Upload },
  { id: "history", label: "历史记录", icon: History },
  { id: "ai-generate", label: "AI生成", icon: Sparkles },
] as const;

// 选择画幅比例（截图 44-director-rail-26 转录）：七卡单选，自适应默认。
const aspectRatios = [
  "自适应",
  "21:9",
  "16:9",
  "4:3",
  "1:1",
  "3:4",
  "9:16",
] as const;

// Batch 590（源站 2026-10-01 实测）：七张卡的示意框尺寸逐项对齐。
// 注意源站 `3:4` 与 `9:16` 实测**同为 8×16**（看起来是源站自身的取整
// 结果），clone 按实测照抄，不按比例自行「修正」。
const ASPECT_GLYPH: Record<(typeof aspectRatios)[number], string> = {
  自适应: "h-[11px] w-4",
  "21:9": "h-[7px] w-4",
  "16:9": "h-[9px] w-4",
  "4:3": "h-3 w-4",
  "1:1": "h-[14px] w-[14px]",
  "3:4": "h-4 w-2",
  "9:16": "h-4 w-2",
};




// Batch 589（源站 2026-10-01 实测）：三个 flyout 面板实测宽度**一致为
// 232px**（@(48,100)），且每个面板顶部都有一行 12px `truncate` 的标题
// （`添加角色` @(60,66) 48×20）。另注：rail 按钮 hover 会弹一个 Mantine
// `Tooltip-tooltip`（@(45,118) 64×28），与面板标题是两件事。
const FLYOUT_WIDTH = "w-[232px]";

// Batch 625: rail 里的五个浮层（全景图 / 画幅比例 / 添加角色 / 几何模型子菜单 /
// 群众弹窗）改为 portal 到 document.body。原本它们都是资源栏的后代，而资源栏
// 是 `absolute ... z-30` 且**创建层叠上下文** —— 于是这些元素写在类名里的
// z-40 / z-50 从未生效，它们在工作区那一层的**有效 z 是 30**，低于时间线的 40。
//
// 实测后果（verify-liblib-batch625.py，五个视口）：几何模型子菜单在 1280×720
// 埋掉 5 枚控件、1100×700 埋掉 6 枚（立方体/球体/圆柱体/环状体/圆锥/上传文件），
// 画幅比例 flyout 在 1100×700 埋掉 1 枚（9:16）。几何模型尤其惨：它的 z-50 还
// 被**再关一层** —— 它嵌套在添加角色 flyout（z-40）里，于是有效 z 是 30 而非 50。
//
// 为什么抬 rail 的 z 不行（试算后否掉）：rail 是 48px 宽通栏贴左，抬到 45 之后
// 它会反过来盖住时间线左侧的播放控件（总时长、时间单位那几枚），拿三个浮层换
// 一排活控件，不做。为什么把 rail 改成 z-auto 也不行：那样 rail 与时间线的
// 胜负就交给 DOM 顺序，比一个显式的 z 更脆弱。
//
// 所以照 batch 624 对 AI 导入模态的同一手法 portal 出去，z 取 **160**：高于
// 工作区的 z-100（时间线就在它里面）与场景树右键菜单的 z-120，低于视口底部条
// z-200 与 AI 导入模态 z-290。
const RAIL_FLYOUT_Z = 160;
const RAIL_FLYOUT_CLASS = `z-[${RAIL_FLYOUT_Z}]`;

const FLYOUT_CARD_CLASS =
  "rounded-xl border border-white/10 bg-[#242424] shadow-[0_16px_40px_rgba(0,0,0,0.5)]";
// 标题行在卡片**之外**（源站 `添加角色` 标题 @(60,66)，卡片从 y=100 起），
// 故外层定位容器同时承载标题与卡片。
const FLYOUT_TITLE_CLASS = "block truncate px-3 pb-2 text-xs text-[#8a8a8a]";

export function DirectorIconRail({
  onPanoramaSourceChange,
  onOpenShortcuts,
  onOpenTutorial,
  onOpenCameraPresets,
  onOpenCharacterPanel,
  panelView = "scene",
}: {
  onPanoramaSourceChange?: (sourceNodeId: string | null) => void;
  /** Batch 831：打开「快捷键」对话框（源站 rail 的 onOpenShortcuts） */
  onOpenShortcuts?: () => void;
  /** Batch 831：打开使用教程（源站 rail 的 onOpenTutorial） */
  onOpenTutorial?: () => void;
  /**
   * Batch 832：切到 / 切回「添加机位」机位预设面板视图。
   * 传 `false` 表示切回场景树（源站点「场景」条目即切回）。
   */
  onOpenCameraPresets?: (open?: boolean) => void;
  /**
   * Batch 858：切到 / 切回「添加角色」面板视图（源站逐字：左侧资源栏是
   * 一个**多视图**面板，`z` 在 scene / character / camera / panorama /
   * aspect 之间**互斥**切换）。传 `false` 表示切回场景树。
   */
  onOpenCharacterPanel?: (open?: boolean) => void;
  /**
   * Batch 858：左侧资源栏当前是**哪个面板模式**（源站逐字：`z`）。
   *
   * ★ 源站的 rail 按钮是 `aria-pressed={z===r.id}` ⟹ ⟹ **选中态完全由
   *   左侧面板模式派生**。clone 此前用自己的本地 `active` 状态 ⟹ ⟹
   *   两处真相：点「添加角色」把面板切走了、按钮却**不会亮**。
   *   现在统一由这个 prop 派生 ⟹ ⟹ 少一份状态、少一处漂移。
   *
   * 源站逐字（`ep=[scene,character,camera,panorama,aspect]`）⟹ ⟹ 五个模式
   * 一一对应 rail 的五枚条目。clone 目前只把 scene / character / camera
   * 做成左侧面板；panorama / aspect 仍是浮层（batch 859 整改）。
   */
  panelView?: "scene" | "character" | "camera" | "panorama" | "aspect";
} = {}) {
  const [active, setActive] = useState<string>("scene");
  const [openFlyout, setOpenFlyout] = useState<string | null>(null);
  const [aspectRatio, setAspectRatio] = useState<string>("自适应");
  // Batch 831：源站的「帮助」是一枚**向上弹的菜单**（不是页签）——
  //   role=menu、120px 宽、两枚 menuitem（快捷键 / 使用教程）。
  //   源站实测：菜单 120×78 @(8,954)，帮助按钮 32×32 @(8,1040)
  //   ⟹ 菜单底边 = 按钮顶边 − 8px（`bottom-full` + `pb-2`）。
  const [helpMenuOpen, setHelpMenuOpen] = useState(false);
  // Batch 539: AI 识图导入 打开居中模态。
  const [aiImportOpen, setAiImportOpen] = useState(false);
  // Batch 540 → 832：源站 rail「添加机位」**不是**直接加机位（那是 batch 540
  // 的旧读数，本批被推翻）⟹ 它把左侧资源栏切成一个**机位预设面板**视图
  // （标题条「添加机位」＋ 2 列 × 15 枚 104×72 的预设）。
  // ⟹ 故此处**不再**直接调 addDirectorCamera（那会跳过「选哪一枚」这一步）；
  //   场景树里的「新增机位」按钮仍走同一条 store 动作（见 DirectorObjectTree）。
  // Batch 587: rail「场景」兼作收起态的恢复入口（源站收起后浮层内唯一
  // 能把顶栏 + 左侧场景面板叫回来的控件）。
  const setViewportPanelsCollapsed = useDirectorStore(
    (state) => state.setViewportPanelsCollapsed,
  );

  // Batch 625: portal 之后定位不能再靠 CSS 的
  // `absolute left-[calc(100%+8px)] top-0`（那个包含块是 rail 里的
  // `div.relative`），必须自己量 anchor 的视口坐标注入。
  //
  // 为什么要重算而不是量一次就存着：原实现是 CSS 锚定，窗口一变就跟着重排；
  // 换成 JS 坐标后若只量一次，resize 就会让浮层停在旧位置。所以订阅 resize
  // 在同一个 effect 里重算。
  //
  // 坐标口径：三个 flyout 原本是 `left = anchor.left + anchor.width + 8`
  // （`left-[calc(100%+8px)]` 相对那个 32px 宽的 `div.relative`）、
  // `top = anchor.top`（`top-0`）。实测 x=48 与之吻合：rail 48 宽居中 32px
  // 按钮 → anchor 在 x=8，8+32+8=48。群众弹窗 anchor 的是**资源栏本身**
  // （`absolute left-[294px] top-0`，即 railRect + (294, 0)）。
  const useFlyoutAnchor = (
    anchorRef: { current: HTMLElement | null },
    active: boolean,
    offset: (r: DOMRect) => { left: number; top: number } = (r) => ({
      left: r.left + r.width + 8,
      top: r.top,
    }),
  ): { left: number; top: number } | null => {
    const [pos, setPos] = useState<{ left: number; top: number } | null>(null);
    useEffect(() => {
      if (!active) {
        setPos(null);
        return;
      }
      const measure = () => {
        const el = anchorRef.current;
        if (!el) return;
        setPos(offset(el.getBoundingClientRect()));
      };
      measure();
      window.addEventListener("resize", measure);
      return () => window.removeEventListener("resize", measure);
      // `offset` is an inline arrow at each call site, so it changes identity
      // every render; including it would tear the listener down and re-measure
      // on every parent render.  The rect it derives from is re-read inside
      // `measure` anyway, so the value stays correct across renders.
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [anchorRef, active]);
    return pos;
  };

  const panoramaAnchor = useRef<HTMLDivElement | null>(null);
  const aspectAnchor = useRef<HTMLDivElement | null>(null);
  const railRef = useRef<HTMLDivElement | null>(null);
  const panoramaPos = useFlyoutAnchor(panoramaAnchor, openFlyout === "panorama");
  const aspectPos = useFlyoutAnchor(aspectAnchor, openFlyout === "aspect-ratio");
  // ★ Batch 858：「添加角色」已改成**左侧面板模式**（源站逐字）⟹ ⟹ rail
  //   这里只留「全景图」「画幅比例」两个浮层 ⟹ ⟹ `useFlyoutAnchor` 只剩两处。

  // Batch 626：几何模型子菜单也要纵向钳制。
  //
  // 事实（探针 C，1440 宽 × 900…540 八档）：子菜单盒恒为 @(52,508) 204×270，
  // 底边恒 778 —— 因为它用 `top-[calc(100%+2px)]` 挂在**整张** flyout 卡片
  // 之下，而卡片顶由 rail 锚点决定、与视口高无关。于是 `视口高 < 778` 时末尾
  // 控件直接落到屏幕外：720 丢 2/8（棱锥、添加空对象），640 丢 4/8，540 丢 7/8。
  //
  // 否掉的替代方案记在这里，免得以后重犯：
  // - 「翻到卡片上方」不行 —— 卡片顶在 y=116，子菜单要 270，翻上去顶边是 -154，
  //   改从屏幕顶部出界，更糟；
  // - 「改成可滚动列表」被否 —— 623/625 的判据是「被自己的滚动容器裁掉不算缺陷、
  //   但要记录」；这里 8 项全可达是更好的结果，滚动等于把缺陷降级成妥协。
  //
  // 口径与时间轴那个下拉一致：8px 安全边，越界多少上移多少，不越界一个像素不动
  // （≥800 视口的读数与 590 之前的几何完全一致）。

  // ★★★ Batch 857（源站逐字）：源站的群众对话框**锚在「群众按钮」自己身上**：
  //   `W({left:Math.max(8,Math.min(t.right+8,window.innerWidth-r-8)),
  //      top:Math.max(8,Math.min(t.top,window.innerHeight-n-8))})`
  //   其中 t ＝ 按钮矩形、r/n ＝ 对话框自己的宽高（量不到时兜底 220）。
  //   ⟹ ⟹ clone 此前写死「rail 左边 + 294」⟹ ⟹ 那**不是**源站的规则
  //   （源站的对话框是**贴着按钮**的：按钮 right+8、按钮 top）。
  //   ⟹ ⟹ 改成按锚点算 ⟹ 顺带让「移动端那枚入口」也能把对话框放在自己旁边。

  // anchor, so the z in RAIL_FLYOUT_CLASS competes against the timeline instead
  // of being sealed inside the rail's z-30 context.
  //
  // **The wrapper carries the z-index too, and that is not redundant.** A first
  // version wrapped the flyout in `<div style={{position:"fixed", left, top}}>`
  // with no z-index — and `position: fixed` **creates a stacking context** (it is
  // not only positioned-with-z elements that do). The wrapper therefore sealed
  // the flyout's z-[160] at an effective z-auto, which sits *below* the
  // workspace's z-[100]: the flyout ended up under the scene tree at every
  // viewport, and Playwright refused to click 几何模型 / 群众 (3x3) because the
  // element was covered. Fixing "a child's z sealed inside its parent's context"
  // had created the same bug one level up — the fourth occurrence of this trap,
  // and the first one self-inflicted.
  const portalFlyout = (pos: { left: number; top: number }, node: ReactNode) => {
    if (typeof document === "undefined") return null;
    return createPortal(
      <div
        style={{
          position: "fixed",
          left: pos.left,
          top: pos.top,
          zIndex: RAIL_FLYOUT_Z,
        }}
      >
        {node}
      </div>,
      document.body,
    );
  };

  // ★ Batch 858（源站逐字）：源站的 rail 按钮 `aria-pressed={z===r.id}`
  //   ⟹ ⟹ 选中态**完全**由左侧面板模式派生 ⟹ ⟹ 不再有第二份真相。
  const isEntryPressed = (id: string) => {
    if (id === "scene") return panelView === "scene";
    if (id === "add-character") return panelView === "character";
    if (id === "add-camera") return panelView === "camera";
    // 全景图 / 画幅比例 目前仍是浮层（batch 859 面板化）⟹ ⟹ 选中态看浮层。
    if (id === "panorama") return openFlyout === "panorama";
    if (id === "aspect-ratio") return openFlyout === "aspect-ratio";
    // 「AI 识图导入」是 clone 自己的扩展（源站的 `ep` 里没有它）⟹ ⟹ 选中态
    // 只能由本地状态给。
    return active === id;
  };

  const select = (id: string) => {
    if (id === "ai-import") {
      setAiImportOpen(true);
      setActive(id);
      return;
    }
    if (id === "add-camera") {
      // Batch 832（源站 2026-10-21 活体实测）：源站的「添加机位」**不是**直接
      // 加一个机位 ⟹ 它把**左侧资源栏切成一个视图**：标题条「添加机位」
      // ＋ 2 列 × 15 枚机位预设（每枚 104×72）。
      // ⟹ 实测点「正面中景」**真的新建了一台机位**（机位2 / 位置 (0,1.5,4) /
      //    旋转 (4.29,180,0) / FOV 50 / 注视 (0,1.2,0)）。
      // ⟹ 本批把「选哪一枚预设」的**呈现**建出来；预设的**语义**（每枚的
      //    位置/朝向/FOV）另有一批逐枚实测 ⟹ 在那之前这里只切视图。
      setOpenFlyout(null);
      onOpenCameraPresets?.();
      return;
    }
    setOpenFlyout(null);
    // Batch 587（源站 2026-10-01 实测）：收起之后顶栏与「收起」按钮一并
    // 消失，浮层内没有第二个恢复按钮——点图标栏的「场景」条目即恢复
    // 顶栏与左侧场景面板。图标栏本身在收起态保留。
    if (id === "scene") {
      setViewportPanelsCollapsed(false);
      // ★ Batch 858：切回场景树 ⟹ ⟹ 「添加角色」面板随之关闭（源站逐字：
      //   左侧面板是**模式互斥**的，`"scene"===z?n:null,"character"===z?(…)`）。
      onOpenCharacterPanel?.(false);
      // Batch 832：源站的「场景」是把左侧资源栏**切回场景树**视图 ⟹
      // 若当前停在「添加机位」预设面板上，切回去。
      onOpenCameraPresets?.(false);
      return;
    }
    if (id === "add-character") {
      // ★ Batch 858：源站的「添加角色」**不是浮层** ⟹ ⟹ 它把左侧资源栏
      //   切成一个**面板视图**（与「添加机位」同一机制）⟹ ⟹ 场景树随之
      //   消失（源站逐字 `"scene"===z?n:null,"character"===z?(…)`）。
      setOpenFlyout(null);
      onOpenCharacterPanel?.();
      return;
    }
    if (id === "panorama" || id === "aspect-ratio") {
      // ★ Batch 858：源站逐字 —— rail 的每一枚条目都**改写左侧面板模式**
      //   （`onClick: () => { F(r.id), N(!1), O(null), … }`）⟹ ⟹ 点「全景图」
      //   时 `z` 变成 "panorama" ⟹ ⟹ 「添加角色」「添加机位」两个面板模式
      //   **必须让位** ⟹ ⟹ 否则两个面板会**同时**留在左侧。
      //   ⚠ 「全景图 / 画幅比例」目前仍是**浮层**（源站逐字它们也是面板模式，
      //   ⟹ ⟹ batch 859 整改）⟹ ⟹ 这里先让左侧面板**回到场景树**。
      onOpenCharacterPanel?.(false);
      onOpenCameraPresets?.(false);
      setOpenFlyout(id);
      return;
    }
    setActive(id);
  };

  return (
    <div
      ref={railRef}
      data-director-icon-rail
      aria-label="导演台资源栏"
      // Batch 613（源站实测 nav `[0,52,48,1098]`）：源站资源栏在 `aside` 里
      // 从 52（顶栏下沿）**纵贯到视口底**，`p-2` 把首枚推到 60、末枚
      // 「帮助」被 `mt-auto` 钉到 1110。clone 此前 `inset-y-0` 挂在中间
      // flex 子节点里，被 36px 高的镜头条顶到 88、下沿停在时间线上沿 968。
      // 现由 DirectorDesk 把它提到工作区根（`fixed`，即包含块）并改成
      // `top-[52px] bottom-0`，这里只需给出高度。z-30 保持低于时间线的
      // z-40 —— 与源站一致（源站「帮助」同样被时间线左簇盖住，见下）。
      //
      // Batch 623：`min-[900px]` → `min-[899px]`。原先这一对断点
      // （`max-[899px]` + `min-[900px]`）看上去互补，其实是**错开一像素的**：
      // Tailwind v4 把 `max-[899px]` 编译成 `@media (width < 899px)`（≤898）、
      // `min-[900px]` 编译成 `@media (width >= 900px)`（≥900），于是 **899
      // 落在两条都不生效的缝里**。缝里的资源栏塌成 `[0,0,0,0]` —— 7 枚活
      // 控件一起消失，而普查不把「零尺寸」算作遮挡，所以 899 的普查报
      // covered=0，看不出来。改成 `min-[899px]`（≥899）后与 `max-[899px]`
      // 严丝合缝：窄屏 ≤898 / 桌面 ≥899，无缝无叠，也与 622 对齐过的
      // `matchMedia('(max-width: 898px)')` 完全一致。
      className="absolute bottom-0 left-0 top-[52px] z-30 hidden w-12 shrink-0 flex-col items-center gap-2 border-r border-white/8 bg-[#171717] p-2 min-[899px]:flex"
    >
      {/* 源站节奏：gap-2（8px）。`场景` 与 `添加角色` 之间还夹一条
          `<div class="border-white/8 h-2 w-8 border-b">` 分隔线（32×8
          @(8,100)）——加上上下各 8px 的 gap，正好把 添加角色 顶到 y=116。 */}
      <div className="flex flex-col items-center gap-2">
        {railEntries.map((entry, index) => {
          const Icon = entry.icon;
          const isActive = isEntryPressed(entry.id);
          return (
            <Fragment key={entry.id}>
            <div
              className="relative"
              ref={entry.id === "panorama" ? panoramaAnchor
                   : entry.id === "aspect-ratio" ? aspectAnchor
                   : undefined}
            >
              <button
                type="button"
                data-director-rail-entry={entry.id}
                aria-label={entry.label}
                title={entry.label}
                aria-pressed={isActive}
                onClick={() => select(entry.id)}
                // 源站逐字：`text-white/72 hover:bg-white/8 flex size-8
                // items-center justify-center rounded-lg transition-colors
                // hover:text-white`，选中态叠 `bg-white/10 text-white`。
                className={cn(
                  "flex size-8 items-center justify-center rounded-lg text-white/72 transition-colors",
                  "hover:bg-white/8 hover:text-white",
                  isActive && "bg-white/10 text-white",
                )}
              >
                <Icon size={20} />
              </button>
              {entry.id === "panorama" && openFlyout === "panorama"
                && panoramaPos && portalFlyout(panoramaPos, (
                <div
                  data-director-panorama-flyout
                  aria-label="全景图"
                  className={cn(
                    "fixed",
                    RAIL_FLYOUT_CLASS,
                    FLYOUT_WIDTH,
                  )}
                >
                  <span
                    data-director-flyout-title="panorama"
                    className={FLYOUT_TITLE_CLASS}
                  >
                    全景图
                  </span>
                  <div className={cn(FLYOUT_CARD_CLASS, "p-1.5")}>
                  {panoramaFlyout.map((item) => {
                    const ItemIcon = item.icon;
                    return (
                      <button
                        key={item.id}
                        type="button"
                        data-director-panorama-option={item.id}
                        className="flex h-8 w-full items-center gap-2 rounded-lg px-2 text-left text-xs text-[#d8d8d8] hover:bg-white/[0.07]"
                      >
                        <ItemIcon size={13} className="shrink-0 text-[#9a9a9a]" />
                        <span className="truncate">{item.label}</span>
                      </button>
                    );
                  })}
                  </div>
                </div>
              ) )}
              {entry.id === "aspect-ratio" && openFlyout === "aspect-ratio"
                && aspectPos && portalFlyout(aspectPos, (
                <div
                  data-director-aspect-flyout
                  aria-label="选择画幅比例"
                  className={cn(
                    "fixed",
                    RAIL_FLYOUT_CLASS,
                    FLYOUT_WIDTH,
                  )}
                >
                  <span
                    data-director-flyout-title="aspect-ratio"
                    className={FLYOUT_TITLE_CLASS}
                  >
                    选择画幅比例
                  </span>
                  <div
                    data-director-aspect-grid
                    className={cn(
                      FLYOUT_CARD_CLASS,
                      // Batch 590（源站实测）：gap 8px、padding 0 8 12 →
                      // 4×72 + 3×8 + 12 = 324，与源站卡片高逐像素一致。
                      "grid grid-cols-2 gap-2 px-2 pb-3 pt-0",
                    )}
                  >
                  {aspectRatios.map((ratio) => (
                    <button
                      key={ratio}
                      type="button"
                      data-director-aspect-option={ratio}
                      aria-pressed={aspectRatio === ratio}
                      onClick={() => setAspectRatio(ratio)}
                      // Batch 590（源站实测 104×72 / radius 12px）：
                      // 选中态与未选中态的**文字色相同**（都是
                      // rgba(255,255,255,0.9)），唯一差别是按钮描边——
                      // 选中 0.85、未选中 0.1，背景两态皆透明。源站按钮
                      // 无 aria-pressed，clone 保留作 a11y 超集。
                      className={cn(
                        "flex h-[72px] flex-col items-center justify-center gap-1 rounded-xl border text-xs",
                        aspectRatio === ratio
                          ? "border-white/[0.85] text-white/90"
                          : "border-white/10 text-white/90 hover:border-white/25",
                      )}
                    >
                      <span
                        aria-hidden="true"
                        data-director-aspect-glyph
                        className={cn("block rounded-sm border border-white/90", ASPECT_GLYPH[ratio])}
                      />
                      {ratio}
                    </button>
                  ))}
                  </div>
                </div>
              ) )}
            </div>
            {/* 源站在 `场景` 与 `添加角色` 之间有一条
                `<div class="border-white/8 h-2 w-8 border-b">`（32×8 @(8,100)）。
                它是 nav 的直接子节点，所以要跟按钮的包裹 div 平级。 */}
            {index === 0 ? (
              <span
                aria-hidden="true"
                data-director-rail-divider
                className="block h-2 w-8 border-b border-white/8"
              />
            ) : null}
            </Fragment>
          );
        })}
      </div>
      {/* Batch 831（源站实测 + 源站代码）：「帮助」点开的是一枚**向上弹的
          role=menu**（120px、两枚 menuitem：快捷键 / 使用教程），不是页签。
          源站原文：`absolute bottom-full left-0 z-50 pb-2` 包一层，
          内层 `flex w-[120px] flex-col gap-1 rounded-xl border border-white/10
          bg-[rgba(31,31,31,0.94)] p-1 shadow-[0_8px_24px_rgba(0,0,0,0.35)]
          backdrop-blur-xl`。
          ★ 4317 的 Tailwind 扫描是冻结的（batch 824）⟹ `w-[120px]` 在 dev CSS
          里存在（仓库别处用过），但 `bg-[rgba(31,31,31,0.94)]` 与那串 shadow
          **不存在** ⟹ 颜色/阴影走 inline style（dev 与 prod 一致）。 */}
      <div className="relative mt-auto">
        <button
          type="button"
          data-director-rail-entry="help"
          aria-label="帮助"
          title="帮助"
          aria-haspopup="menu"
          aria-expanded={helpMenuOpen}
          // 源站的「帮助」与其它 rail 项同款：`rounded-lg`（不是 clone 的
          // rounded-full）+ `text-white/72 hover:bg-white/8 hover:text-white`，
          // 图标同为 20px。
          className="flex size-8 items-center justify-center rounded-lg text-white/72 transition-colors hover:bg-white/8 hover:text-white"
          onClick={() => {
            setHelpMenuOpen((open) => !open);
            setOpenFlyout(null);
          }}
        >
          <HelpCircle size={20} />
        </button>
        {helpMenuOpen ? (
          <div className="absolute bottom-full left-0 z-50 pb-2">
            <div
              role="menu"
              data-director-help-menu
              aria-label="帮助菜单"
              className="flex flex-col gap-1 rounded-xl border border-white/10 p-1 backdrop-blur-xl"
              style={{
                width: 120,
                background: "rgba(31,31,31,0.94)",
                boxShadow: "0 8px 24px rgba(0,0,0,0.35)",
              }}
            >
              <button
                type="button"
                role="menuitem"
                data-director-help-menu-item="shortcuts"
                className="flex h-8 w-full items-center rounded-lg px-3 text-left text-[13px] leading-none text-white/75 transition-colors hover:bg-white/10 hover:text-white"
                onClick={() => {
                  setHelpMenuOpen(false);
                  onOpenShortcuts?.();
                }}
              >
                快捷键
              </button>
              <button
                type="button"
                role="menuitem"
                data-director-help-menu-item="tutorial"
                className="flex h-8 w-full items-center rounded-lg px-3 text-left text-[13px] leading-none text-white/75 transition-colors hover:bg-white/10 hover:text-white"
                onClick={() => {
                  setHelpMenuOpen(false);
                  onOpenTutorial?.();
                }}
              >
                使用教程
              </button>
            </div>
          </div>
        ) : null}
      </div>
      {aiImportOpen && (
        <DirectorAiImportModal
          onClose={() => setAiImportOpen(false)}
          onPanoramaSourceChange={onPanoramaSourceChange}
        />
      )}
      {/* Batch 590（源站实测 220×204 @(280,388)）：`群众 (3x3)` 打开的是
          弹窗——标题「添加群众阵列」、右上角「共N人」计数、三个数字输入
          行数/列数/间距，页脚 取消 / 添加（添加为白底主按钮）。弹窗并排
          出现在 flyout 右侧（源站 x=280，flyout 占 48..280），flyout 保持
          打开。clone 此前是点一下直接按 3×3/1.2 出结果。 */}
    </div>
  );
}
