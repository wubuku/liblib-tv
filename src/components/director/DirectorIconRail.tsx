"use client";

import { Fragment, useState } from "react";
import {
  ArrowDownToLine,
  Clapperboard,
  HelpCircle,
  Image as ImageIcon,
  Proportions,
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
  // ★ Batch 859（源站逐字）：源站左侧那个 232px 面板是**五模式互斥容器**
  //   （`"scene"===z?n:null,"character"===z?(…),"camera"===z?(…),
  //   "panorama"===z?(…),"aspect"===z?(…)`）⟹ ⟹ **全景图与画幅比例也是
  //   面板模式** ⟹ ⟹ 这两枚从「浮层」改成「面板」。
  { id: "panorama", label: "全景图", icon: ImageIcon, kind: "panel" },
  { id: "aspect-ratio", label: "选择画幅比例", icon: Proportions, kind: "panel" },
  { id: "ai-import", label: "AI 识图导入", icon: ArrowDownToLine, kind: "modal" },
] as const;


// ★ Batch 859：全景图的三行与画幅比例的七卡**都搬走了** ⟹ ⟹ 它们现在是
//   **左侧面板模式**（源站逐字：`"panorama"===z?(…)` / `"aspect"===z?(…)`
//   是同一个 232px 面板里的两个分支）⟹ ⟹ 数据与样式随之搬到：
//   · `DirectorPanoramaPanel.tsx`（标题条 ＋ `px-2` ＋ 三枚行类 `eu`）
//   · `DirectorAspectPanel.tsx`（标题条 ＋ `grid grid-cols-2 gap-2 px-2 pb-3`
//     ＋ 七枚 104×72 的卡片 ＋ 比例字形表）
//   ★ 逐字文本（源站实测）：「本地上传」「历史记录」「AI生成」（**无空格**，
//     batch 538 从截图转录时记成「AI 生成」，batch 589 已改对）。




// ★ Batch 859：rail 上**最后一个浮层**也走了 ⟹ ⟹ 下面这一整套 portal 机制
//   （`FLYOUT_WIDTH`／`FLYOUT_CARD_CLASS`／`FLYOUT_TITLE_CLASS`／
//   `RAIL_FLYOUT_Z`／`useFlyoutAnchor`／`portalFlyout`）随之**全部删除**。
//
// ★ ★ **留在这里的知识（别再踩）**：
//   ① rail 是 `absolute ... z-30` 且**创建层叠上下文** ⟹ ⟹ 它的后代里
//      写的 z-40／z-50 **从未生效**，有效 z 是 30 ⟹ ⟹ 低于时间线的 40
//      ⟹ ⟹ 当年几何子菜单与画幅比例浮层就是这样把控件埋掉的（batch 625）。
//   ② `position: fixed` **也会创建层叠上下文** ⟹ ⟹ 包裹层不带 z-index 时
//      会把里面的 z-160 封成 z-auto ⟹ ⟹ 浮层反而掉到工作区 z-100 之下
//      ⟹ ⟹ Playwright 会报「元素被覆盖」（这是同一个陷阱的第 4 次出现）。
//   ③ 现在 rail 里**不再有任何 portal 浮层** ⟹ ⟹ 这两条约束只在
//      「往 rail 里加浮层」时才需要重新想起。
//   ④ 源站逐字：crowd 对话框**是** portal（`createPortal` ＋ `z-[1800]`），
//      那是 `DirectorCharacterPanel` 里的事，不在本文件。

export function DirectorIconRail({
  onPanoramaSourceChange,
  onOpenShortcuts,
  onOpenTutorial,
  onSelectLeftPanelView,
  panelView = "scene",
}: {
  onPanoramaSourceChange?: (sourceNodeId: string | null) => void;
  /** Batch 831：打开「快捷键」对话框（源站 rail 的 onOpenShortcuts） */
  onOpenShortcuts?: () => void;
  /** Batch 831：打开使用教程（源站 rail 的 onOpenTutorial） */
  onOpenTutorial?: () => void;
  /**
   * Batch 832/858/859：**切左侧资源栏的模式**。
   * 源站逐字：rail 的每一枚条目 onClick 都是 `F(r.id)` ⟹ ⟹ **一个**动作
   * 把左侧面板切成那个模式（**互斥**：切走别的面板自然关闭）。
   *
   * ★ clone 此前用两个「开/关」回调（`onOpenCameraPresets(open?)` ＋
   *   `onOpenCharacterPanel(open?)`）⟹ ⟹ 每次切模式要「先关别人、再开自己」
   *   ⟹ ⟹ **顺序一错就会两个面板同时在** ⟹ ⟹ 现在合并成**一个**语义。
   */
  onSelectLeftPanelView?: (
    view: "scene" | "character" | "camera" | "panorama" | "aspect",
  ) => void;
  /**
   * Batch 858：左侧资源栏当前是**哪个面板模式**（源站逐字：`z`）。
   *
   * ★ 源站的 rail 按钮是 `aria-pressed={z===r.id}` ⟹ ⟹ **选中态完全由
   *   左侧面板模式派生**。clone 此前用自己的本地 `active` 状态 ⟹ ⟹
   *   两处真相：点「添加角色」把面板切走了、按钮却**不会亮**。
   *   现在统一由这个 prop 派生 ⟹ ⟹ 少一份状态、少一处漂移。
   *
   * 源站逐字（`ep=[scene,character,camera,panorama,aspect]`）⟹ ⟹ 五个模式
   * 一一对应 rail 的五枚条目。★ Batch 859：五枚**全部**是左侧面板模式
   * （panorama / aspect 从浮层搬过来了）⟹ ⟹ 选中态对五枚**全部**由
   * 这个 prop 派生。
   */
  panelView?: "scene" | "character" | "camera" | "panorama" | "aspect";
} = {}) {
  const [active, setActive] = useState<string>("scene");
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


  // ★ Batch 858（源站逐字）：源站的 rail 按钮 `aria-pressed={z===r.id}`
  //   ⟹ ⟹ 选中态**完全**由左侧面板模式派生 ⟹ ⟹ 不再有第二份真相。
  const isEntryPressed = (id: string) => {
    if (id === "scene") return panelView === "scene";
    if (id === "add-character") return panelView === "character";
    if (id === "add-camera") return panelView === "camera";
    // ★ Batch 859（源站逐字）：全景图 / 画幅比例**也是**左侧面板模式
    //   ⟹ ⟹ 选中态同样由 `panelView` 派生 ⟹ ⟹ 五枚**全部**只有一份真相。
    if (id === "panorama") return panelView === "panorama";
    if (id === "aspect-ratio") return panelView === "aspect";
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
    // ★ ★★ Batch 859（源站逐字）：源站 rail 的每一枚条目 onClick 都是
    //   `F(r.id)` ⟹ ⟹ **一个**动作把左侧面板切成那个模式 ⟹ ⟹ 互斥。
    //   clone 此前是「先关掉别的面板、再打开自己」两段式 ⟹ ⟹ 顺序一错
    //   就会两个面板同时在 ⟹ ⟹ 现在是**一次调用**、没有中间态。
    //
    //   源站逐字（`aU` 的 nav onClick）：`onClick: () => { F(r.id), N(!1),
    //   O(null), … }` ⟹ ⟹ 顺带把子菜单（`O(null)`）与别的状态清掉。
    if (id === "scene") {
      // Batch 587（源站 2026-10-01 实测）：收起之后顶栏与「收起」按钮一并
      // 消失，浮层内没有第二个恢复按钮——点图标栏的「场景」条目即恢复
      // 顶栏与左侧场景面板。图标栏本身在收起态保留。
      setViewportPanelsCollapsed(false);
      onSelectLeftPanelView?.("scene");
      return;
    }
    if (id === "add-character") {
      // Batch 858（源站逐字）：「添加角色」把左侧资源栏切成一个**面板视图**
      // ⟹ ⟹ 场景树随之消失（源站逐字 `"scene"===z?n:null,"character"===z?(…)`）。
      onSelectLeftPanelView?.("character");
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
      onSelectLeftPanelView?.("camera");
      return;
    }
    if (id === "panorama") {
      // ★ Batch 859（源站逐字）：`"panorama"===z` 是**左侧面板的一个分支**
      //   ⟹ ⟹ 不是浮层 ⟹ ⟹ 切过去时场景树让位。
      onSelectLeftPanelView?.("panorama");
      return;
    }
    if (id === "aspect-ratio") {
      // ★ Batch 859（源站逐字）：`"aspect"===z` 同上。
      onSelectLeftPanelView?.("aspect");
      return;
    }
    setActive(id);
  };

  return (
    <div
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
