/**
 * ★ Batch 853：导演台的**打组／解组快捷键**（⌘G／⌘⇧G／⌘⇧D）。
 *
 * ★ 逐字依据（源站 chunk `0fmehki05gkzw.js.js`，机器提取见
 *   `docs/research/liblib-canvas-batch853-2026-10-01/raw/source-853-contract.json`）：
 *
 * ```js
 * // keydown 的白名单与修饰键条件
 * hY=new Set(["escape","enter","v","r","f","h","x","t","y","c","d","g","delete","backspace","z"])
 * …
 * &&("g"!==n||e.ctrlKey||e.metaKey)&&("d"!==n||e.shiftKey&&(e.ctrlKey||e.metaKey))
 *
 * // 分支
 * else if("g"===n||"d"===n)if(e.shiftKey){
 *   let e=nf.current.selectedGroupId;e&&rY(e)      // ⇧ ⟹ 解组
 * }else"g"===n&&rW();                              // 无 ⇧ 且是 g ⟹ 打组
 * ```
 *
 * ★ ⇒ **行为矩阵**（由上面两段逐字推出）：
 *
 * | 按键 | 结果 |
 * | --- | --- |
 * | `⌘G` | **打组**（`createCharacterGroup()`，无参 ⟹ 用当前选择） |
 * | `⌘⇧G` | **解组**（⇧ 分支，优先级高于字母） |
 * | `⌘⇧D` | **解组** |
 * | `⌘D` | **无**（`d` 要求 `⇧` ＋ ⌘） |
 * | 裸 `G`／裸 `D`／裸 `⇧D` | **无**（`g`／`d` 都要求 ⌘） |
 *
 * ★ 本模块只回答「这个按键组合该做什么」，**不做任何状态判断**：
 * ★ 「够不够两个成员」「有没有选中组」是**运行时**的判据，由 store 那两个
 * action 自己把关（源站的 `r.length<2` 与 `e&&rY(e)` 同理）。
 */

/** 打组／解组快捷键的动作 */
export type DirectorGroupShortcutAction = "group" | "ungroup";

export interface DirectorGroupShortcutInput {
  /** 按键字母（小写） */
  key: string;
  /** 是否按下了 ⌘（macOS）或 Ctrl（Windows） */
  modifier: boolean;
  /** 是否按下了 Shift */
  shift: boolean;
}

/**
 * 源站 `hY` 块里 `g`／`d` 两段的修饰键条件 ＋ 分支体 ⟹ 合成一张动作表。
 *
 * ★ 逐字对应：
 * - `"g"!==n||e.ctrlKey||e.metaKey` ⟹ `g` **必须**带 ⌘；
 * - `"d"!==n||e.shiftKey&&(e.ctrlKey||e.metaKey)` ⟹ `d` **必须**带 ⇧ ＋ ⌘；
 * - `if(e.shiftKey){…解组…}else"g"===n&&rW()` ⟹ **带 ⇧ 一律解组**，
 *   **不带 ⇧ 时只有 `g` 才打组**。
 */
export function resolveDirectorGroupShortcutAction(
  input: DirectorGroupShortcutInput,
): DirectorGroupShortcutAction | null {
  const { key, modifier, shift } = input;
  if (!modifier) return null;
  if (key === "g") return shift ? "ungroup" : "group";
  if (key === "d") return shift ? "ungroup" : null;
  return null;
}
