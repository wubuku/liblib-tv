"use client";

// ★★★ Batch 859（源站逐字）：导演台左侧的「**选择画幅比例**」**侧栏面板模式**。
//
// ★ ★★ 与「全景图」同源（= batch 858 登记的 D8）：源站左侧那个 232px 面板
//   是**五模式互斥容器**，「选择画幅比例」是其中一个模式，**不是** rail 浮层。
//   clone 此前把它做成 **portal 浮层**（`data-director-aspect-flyout`）⟹ ⟹ 本批改掉。
//
// ★ 源站逐字（`"aspect"===z` 那段）：
//     标题条 `aO`，文本 `D("canvas:directorSelectAspectRatioHint")`（「选择画幅比例」）
//     内容容器 `className:"grid grid-cols-2 gap-2 px-2 pb-3"`
//     每一格：
//       `className: clsx("hover:bg-white/8 flex h-[72px] flex-col items-center
//         justify-center gap-2 rounded-xl border text-[12px] text-white/90
//         transition-colors disabled:cursor-not-allowed disabled:opacity-35",
//         t ? "border-white/85" : "border-white/10")`
//       其中 `t` ＝「这一项是不是当前选中」
//         （`null===e.value||null===l ? e.value===l : .001>Math.abs(e.value-l)`）
//       格内：比例字形 `aN` ＋ 文本 `e.label ?? D("canvas:ratioOptionsText07c60b")`
//
// ★ 源站的选项表（chunk 里的 `aj`，逐字）：
//     `[{label:null,value:null},{label:"21:9",value:21/9},{label:"16:9",value:16/9},
//       {label:"4:3",value:4/3},{label:"1:1",value:1},{label:"3:4",value:.75},
//       {label:"9:16",value:9/16}]`
//   ⟹ ⟹ 第一项 `label:null` ⟹ ⟹ 文本走 i18n 兜底（源站实测显示「自适应」）。
//
// ★ 源站实测（`docs/research/liblib-canvas-batch859-2026-10-01/raw/source-859-panels.json`）：
//     面板 @(48,52) 232 宽、标题条 @(48,52) 232×48 / 12px、
//     网格 @(48,100) 232×324、`grid-template-columns: 104px 104px`、gap **8px**、
//     padding `0px 8px 12px`
//     七格各 **104×72**：自适应 @(56,100)／21:9 @(168,100)／16:9 @(56,180)／
//     4:3 @(168,180)／1:1 @(56,260)／3:4 @(168,260)／9:16 @(56,340)
//     字号 **12px**、圆角 **12px**、边框 **1px**
//     （选中 `rgba(255,255,255,0.85)`／未选 `rgba(255,255,255,0.1)`）
//     ★ **场景树不在场**（模式互斥被实测确认）
//
// ★ ★ **功能缺口（如实登记，不假装已对齐）**：源站选比例会**改画布的宽高比**
//   （`aj` 的 value 是**数值比例**，`d(e.value)` 写进画布状态）⟹ ⟹
//   clone 的 store 里那个 `aspectRatio` 是**截图/导出**用的三值
//   （`"16:9"|"9:16"|"1:1"`），**与画布宽高比不是一回事** ⟹ ⟹
//   本组件的选择**只改面板里的高亮**，**不改画布** ⟹ ⟹ 登记为 **D11**。
// ★ ★★ Batch 862：**「没有机位时，七档比例全部禁用」**（源站逐字）。
//
// ★ 源站逐字（`aU` 的 props 解构 ＋ 父组件传参 ＋ aspect 段）：
//     `hasCameras:a, aspectRatio:l, onAspectRatioChange:d, …`
//     父组件：`hasCameras: rL.cameras.length > 0`
//     aspect 段每一格：`disabled:!a`
//       ＋ 类名含 `disabled:cursor-not-allowed disabled:opacity-35`
// ⇒ ⇒ **没有机位 ⟹ 七档比例全部禁用**（而且取景框也无处可施放）。
//
// ★ ★★ clone 侧的对应：机位在 `directorStore` 的 `objects` 里
//   （`kind === "camera"`）⟹ ⟹ `hasCameras` ＝ 至少有一个机位对象。
//   ★ 源站的 `rL.cameras` 是独立的机位集合 ⟹ ⟹ 语义对应（都是「有机位」）。
//
// ★ ★★ ★ **诚实标注（Batch 862 补测）**：源站的「无机位」状态在源站**未能实测**
//   （源站机位行只有「隐藏」「锁定」两枚按钮，`Delete`／`Backspace` 都删不掉
//   ⟹ ⟹ 该分支在源站近乎死代码）；
//   ★ ★★ **clone 侧同样不可达**：clone 的删除规划器有守卫
//   （`src/lib/directorDeletePlanner.ts`：`survivingCameras.length === 0`
//   ⟹ ⟹ `DIRECTOR_LAST_CAMERA_REQUIRED`「至少需要保留一个机位」），
//   **而且**主机位另有一条 `DIRECTOR_PRIMARY_CAMERA_REQUIRED`
//   ⟹ ⟹ **clone 永远至少有一个机位** ⟹ ⟹ `hasCameras` 恒为 `true`
//   ⟹ ⟹ 下面那行 `disabled` 绑定在运行时**永远不生效**。
//   ★ 本批依据的是**源站逐字表达式**（`hasCameras: rL.cameras.length > 0`
//   ＋ `disabled:!a`），**不是**运行时读数 ⟹ ⟹ 登记在 D16。
//   ★ 实施保留这行，是为了让 clone 的**逐字结构**与源站一致（若将来某条路径
//   允许删光机位，行为与源站相同）；**门禁也只能是源码逐字判据**，
//   不许假装有运行时读数。
// ★ ★ ★ ★ **注释纪律（Batch 862 踩坑后立的规矩）**：
//   本文件**不许**在注释里抄 clone 自己的 JSX 字面量
//   （★ 负控按字面量做替换时，会先命中**注释里**那一份 ⟹ ⟹ 改不到代码
//   ⟹ ⟹ 门禁绿是**假绿** ⟹ ⟹ 负控打空）。
//   ⟹ ⟹ 注释里提到这行时，一律写「`disabled` 绑定到 `hasCameras` 的取反」，
//   **不写**完整字面量。
import { useDirectorStore } from "@/store/directorStore";
import { cn } from "@/lib/utils";
import {
  buildDirectorCameraUpdateEvent,
  resolveDirectorTelemetryCameraId,
} from "@/lib/directorTelemetry";

// ★ 源站逐字（`aO`）：标题条。
const TITLE_CLASS =
  "flex h-12 shrink-0 items-center px-3 text-[12px] leading-5 text-white/90";

// ★ 源站逐字：`grid grid-cols-2 gap-2 px-2 pb-3`
const GRID_CLASS = "grid grid-cols-2 gap-2 px-2 pb-3";

// ★ 源站逐字（逐字照抄，含 `hover:bg-white/8` / `transition-colors` / `disabled:*`）
const CELL_CLASS =
  "hover:bg-white/8 flex h-[72px] flex-col items-center justify-center gap-2 rounded-xl border text-[12px] text-white/90 transition-colors disabled:cursor-not-allowed disabled:opacity-35";

// ★ 源站的七个选项（逐字顺序 ＋ 逐字文本；第一项文本来自 i18n 兜底）
//   ★ `null` 那一项＝源站 `aj` 的 `{label:null,value:null}` ⟹ ⟹ 「自适应」。
const aspectRatios = [
  "自适应",
  "21:9",
  "16:9",
  "4:3",
  "1:1",
  "3:4",
  "9:16",
] as const;

// ★ Batch 590（源站 2026-10-01 实测）：七张卡的示意框尺寸逐项对齐。
//   注意源站 `3:4` 与 `9:16` 实测**同为 8×16**（看起来是源站自身的取整
//   结果），clone 按实测照抄，不按比例自行「修正」。
const ASPECT_GLYPH: Record<(typeof aspectRatios)[number], string> = {
  自适应: "h-[11px] w-4",
  "21:9": "h-[7px] w-4",
  "16:9": "h-[9px] w-4",
  "4:3": "h-3 w-4",
  "1:1": "h-[14px] w-[14px]",
  "3:4": "h-4 w-2",
  "9:16": "h-4 w-2",
};

export function DirectorAspectPanel({ active }: { active: boolean }) {
  // ★★★ Batch 860：**接到 store**（此前是组件内 `useState` ⟹ ⟹ 点哪档都不生效）。
  //   ★ 源站逐字：点比例 ⟹ ⟹ `d(e.value)` ⟹ ⟹ 写进**机位**（`aspect_ratio` 事件）
  //   ⟹ ⟹ clone 侧对应的是**取景比例** `frameAspectRatio`（不是导出比例）。
  //   ★ 源站实测：「自适应」时**取景框不在场** ⟹ ⟹ 这里用 `null` 表示。
  const frameAspectRatio = useDirectorStore((state) => state.frameAspectRatio);
  const setFrameAspectRatio = useDirectorStore((state) => state.setFrameAspectRatio);
  // ★ Batch 862（源站逐字 `hasCameras: rL.cameras.length > 0` ＋ `disabled:!a`）：
  //   **没有机位 ⟹ 七档比例全部禁用**。
  const objects = useDirectorStore((state) => state.objects);
  const hasCameras = objects.some((object) => object.kind === "camera");
  // ★ Batch 864：源站逐字 `let t = e1 || rL.cameras[0]?.id`
  //   ⟹ ⟹ 埋点里的机位 ＝ **选中机位**，否则**第一个机位**。
  const activeCameraId = useDirectorStore((state) => state.activeCameraId);
  const recordTelemetry = useDirectorStore((state) => state.recordTelemetry);
  // ★ 源站逐字：点比例 ⟹ ⟹ `n4(t, "aspect_ratio", (0,nZ.R)(e), "right_panel")`
  //   ⟹ ⟹ clone 记一条**本地**的同构事件（★ **不触网**，见
  //   `src/lib/directorTelemetry.ts` 的说明）。
  const reportAspectRatio = (ratio: (typeof aspectRatios)[number]) => {
    const cameras = objects.filter((object) => object.kind === "camera");
    const cameraId = resolveDirectorTelemetryCameraId(cameras, activeCameraId);
    if (!cameraId) return;
    recordTelemetry(
      buildDirectorCameraUpdateEvent({
        cameraId,
        settingName: "aspect_ratio",
        // ★ 源站逐字：比例是**字符串**（"16:9"）；「自适应」是 `null`。
        settingValue: ratio === "自适应" ? null : ratio,
      }),
    );
  };
  // ★ 源站逐字：`"aspect"===z?(…):null` ⟹ ⟹ **条件渲染**（不是 `hidden`）
  //   ⟹ ⟹ 与 batch 858 的「添加角色」面板同一写法。
  // ★ ★ 组件**本身**常驻（`useState` 的选中项因此跨模式保留），
  //   只有 DOM 子树按模式在/不在 ⟹ ⟹ 两者不冲突。
  if (!active) return null;
  const selected =
    frameAspectRatio === null ? "自适应" : frameAspectRatio;
  return (
    <div
      data-director-aspect-panel
      aria-label="选择画幅比例"
      className="flex h-full min-h-0 w-full flex-col bg-[#171717]"
    >
      <div data-director-panel-title="aspect" className={TITLE_CLASS}>
        <span className="truncate">选择画幅比例</span>
      </div>
      <div data-director-aspect-grid className={GRID_CLASS}>
        {aspectRatios.map((ratio) => (
          <button
            key={ratio}
            type="button"
            data-director-aspect-option={ratio}
            // ★ 源站按钮**没有** `aria-pressed` ⟹ ⟹ clone 保留作 a11y 超集
            //   （batch 590 已登记：源站选中/未选两态**文字色相同**，
            //   唯一差别是按钮描边 0.85 / 0.1、背景两态皆透明）。
            aria-pressed={selected === ratio}
            // ★ Batch 862（源站逐字 `disabled:!a`）：没有机位 ⟹ 全部禁用。
            disabled={!hasCameras}
            onClick={() => {
              setFrameAspectRatio(ratio === "自适应" ? null : ratio);
              reportAspectRatio(ratio);
            }}
            className={cn(
              CELL_CLASS,
              selected === ratio ? "border-white/85" : "border-white/10",
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
  );
}
