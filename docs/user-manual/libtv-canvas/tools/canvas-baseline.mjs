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

// ---------------------------------------------------------------------------
// ⭐ 节点坐标（画布坐标系，来自每个节点 DOM 的 style.transform）
//
// 2026-10-04 新增。起因：Batch EI 为了构造「纯 2 个图片节点」的选区，
// 反复挪动节点，其中一次拖拽抓错了节点、另一次把节点拖偏了 2000+ 画布 px。
// 有了这张表，任何一轮都能**读 transform 核对**，而不是靠肉眼看截图。
//
// ⚠️ 挪动节点复原时，用画布坐标驱动（Δscreen = Δcanvas × zoom），
//    不要用屏幕坐标 —— 过程中视口会平移，屏幕坐标复原会让画布坐标留在错位上
//    （EI-12 就栽在这：屏幕上回去了，transform 差了 891px）。
//
// ⭐ 低缩放下两个节点在屏幕上会叠在一起，落点很容易抓到隔壁节点。
//    拖之前**必须**用 document.elementFromPoint(x, y).closest('.react-flow__node')
//    确认那个像素属于目标节点（EI-22 靠这一招一次就修对了两个节点）。
// ---------------------------------------------------------------------------
export const 坐标 = {
  'a-GgqvrVz0pw': [719.388, 1509.13],
  'a-THmbuJXQj4': [-1356, 600],
  'b-mfkcQNULC3': [636, 300],
  'i-9nlG6HdjK2': [-1764, 900],
  'i-sODTbgLUm1': [-168, 900],
  'n-56F19pXVB4': [-1225.03, 370.975],
  't-2AK3Ukyxj3': [-1476, 1524],
  't-UtVx3lZmrV': [600, 900],
  'v-eMpqKtiLlx': [-1787, 900],
  'v-oZNpH99MtM': [132, 300],
  'v-v2hlWY4Br3': [-696, 300],
};

/** 坐标是否已偏离基线（容差 1.5 画布 px）。用于每轮收尾的自检。 */
export const 坐标有偏差 = (id, 现, 容差 = 1.5) => {
  const 标 = 坐标[id];
  if (!标 || !现) return true;
  return Math.abs(现[0] - 标[0]) > 容差 || Math.abs(现[1] - 标[1]) > 容差;
};

/** 从页面读回全部节点坐标，格式 { id: [x, y] }。 */
export const 读全部坐标 = (page) => page.evaluate(() => {
  const o = {};
  for (const n of document.querySelectorAll('.react-flow__node')) {
    const m = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform || '');
    o[n.getAttribute('data-id')] = m ? [parseFloat(m[1]), parseFloat(m[2])] : null;
  }
  return o;
});

/** 读回坐标并列出所有偏离基线的节点。收尾自检用。 */
export const 核对坐标 = async (page, 容差 = 1.5) => {
  const 现 = await 读全部坐标(page);
  return Object.keys(坐标)
    .filter((id) => 坐标有偏差(id, 现[id], 容差))
    .map((id) => ({ id, 标准: 坐标[id], 现: 现[id] }));
};
