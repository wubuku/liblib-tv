// ⭐⭐⭐⭐⭐ Batch FR-2：把 FR-1 命中的两个 chunk 抓下来，逐词定位
//
// FR-1 的关键读数（已定案的一半）：
//   ① `0xi3d93gswcjd.js` 里有 `"planCreateVideoContinuation"` —— 一个 **store action 名**，
//      同段的守卫是 `if(!e.sourceNodeId.trim() || !e.sourceToTargetEdgeId.trim() || !a(e.range)) throw …`
//      ⇒ **必须先有：源节点 id、源到目标的连线 id、一段 range**。
//   ② ⭐⭐⭐ `1bzx2qa4_zu4z.js` 里有
//      `ej = eL([ a && {key:"segmentRemake", featureId:"video.segmentRemake", label: ei("canvas:segmentRemakeEntry") …},
//                 E && {key:"continuation…`
//      ⇒ **智能续写是某个下拉/菜单里的第二项，第一项是「片段重剪」**。
//      同一个文件里还有 `onSeparateAvClick` / `onVocalSplitClick` / `onExpandClick`
//      / `separateAvDisabledReason` / `vocalSplitDisabledReason`
//      ⇒ ⭐ **这一排菜单项各自带「禁用原因」**（和预设面板的灰态一个套路）。
//      还有 `em({source, sessionPhase, width, duration, startSec, endSec, handleWidth:16, variant:"clip"})`
//      ⇒ ⭐ **一条带左右手柄的视频裁剪条** —— 正是「请截取续写前置视频」那个控件。
//
// 本轮要定位的：
//   ① `ej` 这个菜单**挂在哪个组件**上（class 名 / 父容器）
//   ② `continuation…` 那一项的**完整 key / 文案 key / 禁用条件**
//   ③ `videoContinuationSelectionDisabled`（当前模型或模式不支持）在代码里由什么决定
//   ④ 顺带：节点标题上那个数字的渲染代码
//
// ⛔ 全程只读：只做 GET。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = resolve(HERE, '.evidence');
const R = { 步骤: [], 读数: {} };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFR2.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };

const 浏览器 = await launch();
const page = 浏览器.page;

/** 把命中词周围的原文抓下来，落到文件里慢慢读。 */
async function 挖(文件, 词, 前后 = 700, 每词最多 = 3) {
  return page.evaluate(async ({ u, w, pad, cap }) => {
    const r = await fetch(u);
    const txt = await r.text();
    const out = [];
    let i = txt.indexOf(w);
    let n = 0;
    while (i !== -1 && n < cap) {
      out.push({ 位置: i, 原文: txt.slice(Math.max(0, i - pad), i + pad) });
      i = txt.indexOf(w, i + 1);
      n += 1;
    }
    return { 文件: u.split('/').pop(), 字节: txt.length, 词: w, 次数: out.length, 段: out };
  }, { u: 文件, w: 词, pad: 前后, cap: 每词最多 });
}

try {
  mkdirSync(EVID, { recursive: true });
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(13000);
  await closePromos(page);

  const 脚本 = await page.evaluate(() => [...document.querySelectorAll('script[src]')].map((s) => s.src));
  const 找 = (名) => 脚本.find((u) => u.includes(名));

  const 目标 = ['1bzx2qa4_zu4z.js', '0xi3d93gswcjd.js']
    .map(找)
    .filter(Boolean);
  R.读数.目标 = 目标.map((u) => u.split('/').pop());
  记('目标 chunk：' + JSON.stringify(R.读数.目标));

  // ① 智能续写那一项的完整定义
  记('=== ① 「continuation」菜单项的完整定义 ===');
  const A = await 挖(目标[0], 'key:"continuation');
  记(`   ${A.文件}：${A.次数} 处`);
  A.段.forEach((s, i) => 记(`   [${i} @${s.位置}] ${s.原文.replace(/\s+/g, ' ')}`));

  // ② 整个菜单项数组 eL([...]) 的完整内容
  记('=== ② 菜单项数组的完整内容 ===');
  const B = await 挖(目标[0], 'segmentRemake', 1400, 1);
  B.段.forEach((s, i) => 记(`   [${i} @${s.位置}] ${s.原文.replace(/\s+/g, ' ')}`));

  // ③ videoContinuation 文案 key 的调用点
  记('=== ③ videoContinuation 文案 key 的调用点 ===');
  const C = await 挖(目标[0], 'videoContinuation', 420, 12);
  记(`   ${C.文件}：命中 ${C.次数} 处`);
  C.段.forEach((s, i) => 记(`   [${i} @${s.位置}] ${s.原文.replace(/\s+/g, ' ')}`));

  // ④ 裁剪条组件 em(
  记('=== ④ 带手柄的裁剪条组件 ===');
  const D = await 挖(目标[0], 'variant:"clip"', 900, 2);
  D.段.forEach((s, i) => 记(`   [${i} @${s.位置}] ${s.原文.replace(/\s+/g, ' ')}`));

  // ⑤ planCreateVideoContinuation 的守卫
  记('=== ⑤ planCreateVideoContinuation 的守卫条件 ===');
  const E = await 挖(目标[1], 'planCreateVideoContinuation', 900, 2);
  E.段.forEach((s, i) => 记(`   [${i} @${s.位置}] ${s.原文.replace(/\s+/g, ' ')}`));

  // ⑥ 节点标题的数字
  记('=== ⑥ 节点标题上的数字 ===');
  for (const w of ['nodeIndex', 'nodeTypeLabel', '节点', 'audioNode', 'videoNode']) {
    const F = await 挖(目标[0] || 脚本.find((u) => u.includes('1bzx2qa4')), w, 260, 1);
    if (F.次数) 记(`   「${w}」${F.次数} 处：[${F.段[0].位置}] ${F.段[0].原文.replace(/\s+/g, ' ').slice(0, 420)}`);
  }
} catch (e) {
  记('❌ 异常：' + e.message);
  R.读数.错误 = e.message;
} finally {
  writeFileSync(HERE + 'batchFR2.json', JSON.stringify(R, null, 2));
  await 浏览器.browser.close().catch(() => {});
  console.log('\n完成。');
}
