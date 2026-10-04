// ⭐ 画布基线 —— 唯一权威来源。
//
// ⚠️ 2026-10-04 更新（Batch ED）：基线里的 `a-CUfJfmKzUJ`（音频节点 6）
//    在 ED-1c 被误删，**产品内不可恢复**（画布无回收站、`⌘Z` 撤不回，
//    见 90-troubleshooting.md「误删了节点或连线」一节）。
//    经用户同意，已用底部工具条 `+ → 音频` 重建 `a-GgqvrVz0pw` 顶替。
//    ⇒ **节点总数仍是 11，但 id 换了一个**。
//
// ⭐ 后续脚本一律 import 这个 BASE，**不要再各写一份** ——
//    本次事故的直接原因之一就是「基线散落在几十个脚本里，没人知道它变过」。
//
// ⛔ 画布基线是**别人也在用的测试画布**：只读它、别删它。
//    需要建节点做实验时，只删**本轮自己刚建、id 不在这个列表里、且是 `m-` 前缀**的对象。

/** 当前 11 个节点的 data-id（已排序）。 */
export const BASE = [
  'a-GgqvrVz0pw',  // 音频节点 7（Batch ED 重建，顶替被删的 a-CUfJfmKzUJ）
  'a-THmbuJXQj4',  // 音频节点 1
  'b-mfkcQNULC3',  // 逐帧拉片
  'i-9nlG6HdjK2',  // 图片节点 2
  'i-sODTbgLUm1',  // 图片节点 2
  'n-56F19pXVB4',  // 导演台 5
  't-2AK3Ukyxj3',  // 文本节点 1
  't-UtVx3lZmrV',  // 文本节点 1
  'v-eMpqKtiLlx',  // 视频节点 3
  'v-oZNpH99MtM',  // 智能剪辑 4
  'v-v2hlWY4Br3',  // 视频节点 3
];

/** ⛔ 已从画布上消失的 id（别再指望它们还在）。 */
export const 已删除 = ['a-CUfJfmKzUJ'];

/** 画布 id 在不在基线里。用于「只删本轮自己建的对象」这条自证。 */
export const 是基线节点 = (id) => BASE.includes(id);

/** ⭐ 通用安全断言：只允许删「本轮新建 + m- 前缀 + 不在基线」的对象。 */
export const 允许删除 = (id, 本轮新建的 = []) =>
  本轮新建的.includes(id) && id.startsWith('m-') && !是基线节点(id);
