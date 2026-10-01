/**
 * 节点卡片与标题行的共享几何 (Batch 812)。
 *
 * 这些值原先散落在 8 个节点类型里各写一份，改一处就要改八处 ——
 * 事实是它们**只有一套**，所以收成常量。
 *
 * SOURCE_FACT batch 812 (2026-10-03 @1512×950 源站登录态，100% 缩放，
 * 逐元素量卡片上方区域 + 枚举全部 boxShadow)：
 *
 * ## 1. 描边环 —— 源站是 **inset**，不是 outset
 *
 * 源站在卡片外侧另有一层 `pointer-events-none absolute` 的交互/描边层
 * (577×328 @ 卡片 -4,-4)，它才是画环的地方：
 *   - 未选中 `rgba(255,255,255,0.2) 0 0 0 1px inset`
 *   -   选中 `rgba(255,255,255,0.6) 0 0 0 1px inset,
 *           color(srgb 1 1 1 / 0.192) 0 2px 8px -2px`
 * 复刻此前是 `0 0 0 1.5px rgba(255,255,255,0.92)`（outset、1.5px、92%），
 * 选中时明显更亮更粗，且会把环画到卡片**外面**，与源站相反。
 *
 * 另有一层恒存在的 `rgba(255,255,255,0.04) 0 0 0 1px inset` 画在**媒体层**
 * (567×318 @ 卡片 +1,+1) 上 —— 那是媒体区自己的内描边，与选中态无关。
 *
 * ## 2. 标题行 —— 内容顶对齐在 -31，不是"在 32px 行里居中"
 *
 * 源站标题行盒 56×32 @ (0,-31)，但盒内并没有居中：
 *   图标 svg  16×16 @ (0,-27)   ← 比行顶低 4
 *   文字 span 36×24 @ (20,-31)  ← 顶着行顶，高 24（13px/20 行高 + 上下各 1px padding）
 * 两者互为中心对齐（中心都在 -19），整体偏上。
 * 复刻此前用 `bottom-full h-8` + items-center 把 22px 高的文字放在 -27，
 * 整体低了 4px，且 `gap-1.5`(6px) 让文字起点落到 x=22（源站 20）。
 */

/** 节点描边环：selected=true 时加白色投影。inset 1px，见文件头 SOURCE_FACT。 */
export function nodeRingShadow(selected: boolean): string {
  return selected
    ? "inset 0 0 0 1px rgba(255,255,255,0.6), 0 2px 8px -2px rgba(255,255,255,0.192)"
    : "inset 0 0 0 1px rgba(255,255,255,0.2)";
}

/** 媒体区恒存在的内描边（与选中态无关）。 */
export const MEDIA_INSET_RING = "inset 0 0 0 1px rgba(255,255,255,0.04)";

/**
 * 标题行容器：`bottom-full h-8` → `top-[-31px] h-8`。
 * 保持 32px 命中区（源站行盒就是 32 高、且下缘探入卡片 1px），
 * 但把内容从"垂直居中"改成"顶对齐"。
 */
export const TITLE_ROW_CLASS =
  "absolute inset-x-0 top-[-31px] z-10 flex h-8 items-start text-left";

/** 标题行左簇：24px 高的内容盒，与文字顶对齐。 */
export const TITLE_LEFT_CLASS =
  "flex h-6 min-w-0 items-center gap-1 text-white/70";

/** 标题文字：13px/20 行高 + 上下各 1px padding = 24 高（源站实测 36×24）。 */
export const TITLE_TEXT_CLASS =
  "max-w-full cursor-text truncate whitespace-nowrap py-px text-[13px] leading-[20px]";

/**
 * 右侧标签钮：源站 `Add tags`，24×24、rounded-lg(8px)、padding 0 4px，
 * 外面再套一层 `-inset-1`(32×32) 的悬停命中区。
 * 右缘落在卡片右缘内侧 1px（源站 24 宽 @x=544，卡片宽 569 → 右缘 568）。
 */
export const TITLE_TAG_BTN_CLASS =
  "nodrag flex size-6 items-center justify-center rounded-lg px-1";
