// Batch CG-1：那枚 28×28 的无名按钮到底在哪、是什么。
//
// CG-0 的读数推翻了它自己的分类：
//   - 尺寸 **28×28**，而参数条上所有按钮都是 **32×32**；
//   - y 比生成按钮**高 200px**（视频：它 y=512，生成 y=712）；
//   - x 却和生成按钮**几乎重合**（生成 x=905，它 x=909）。
// ⇒ 它**不在参数条上**，在节点卡片的**右上角**。
// ⛔ 而 CF-0 那张「按钮身份证表」用的是 `node.querySelectorAll('button')` ——
//    扫的是**整个节点**，却把结果当「参数条」列了出来。**本步先把这个判据错误坐实。**
//
// 悬停读不出名字，而**阳性对照通过**（同一套手法 hover `M15.52` 读出「翻译提示词」）
// ⇒ 「没气泡」是真的，不是手法失效。所以改用另外三条路：
//   ① 读**祖先链与兄弟**（它在什么容器里、旁边有什么字）；
//   ② 读**未选中**时它在不在（区分「常驻」与「选中才出现」）；
//   ③ **拍特写**（形状是最硬的证据）。
//
// ⛔ 只读、只拍。**不点。**
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const MYSTERY = 'M1.4 8.9c.22 0 .4.18.4.4v5.54l5.26-5.26a.4.4 0';
const GEN = 'M8.3.3a1 1 0 0 1 1.4 0l8 8';
const VID = 'v-eMpqKtiLlx';

const { browser, page } = await launch();
const out = {};

await open(page, URL_);
await closePromos(page);
await page.evaluate(async () => {
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  for (let i = 0; i < 6; i += 1) {
    const hit = [...document.querySelectorAll('button, [role="button"]')].find((b) => (b.innerText || '').trim() === '知道了');
    if (hit) { hit.click(); await sleep(500); }
    if (!(document.body.innerText || '').includes('已升级为 TV Director')) return;
  }
});
await page.waitForTimeout(800);

// 祖先链 + 兄弟 + 容器文字
const inspect = (nid) => page.evaluate(({ n, pre, gen }) => {
  const node = document.querySelector(`.react-flow__node[data-id="${n}"]`);
  if (!node) return { err: 'node not in DOM' };
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const all = [...node.querySelectorAll('button,[role="button"]')].filter(vis);
  let me = null; let genEl = null;
  for (const b of all) {
    const svg = b.querySelector('svg');
    const d = svg ? [...svg.querySelectorAll('path')].map((x) => x.getAttribute('d')).join(' ') : '';
    if (d.includes(pre)) me = b;
    if (d.includes(gen)) genEl = b;
  }
  if (!me) return { err: '没找到那枚按钮' };
  const box = (el) => { const r = el.getBoundingClientRect(); return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }; };
  const chain = [];
  for (let el = me; el && el !== document.body; el = el.parentElement) {
    const r = el.getBoundingClientRect();
    chain.push({ tag: el.tagName.toLowerCase(), cls: (el.className || '').toString().slice(0, 70), 尺寸: `${Math.round(r.width)}x${Math.round(r.height)}` });
    if (chain.length >= 5) break;
  }
  return {
    它: box(me),
    祖先链: chain,
    兄弟按钮: me.parentElement
      ? [...me.parentElement.children].map((c) => {
        const r = c.getBoundingClientRect();
        return { tag: c.tagName.toLowerCase(), cls: (c.className || '').toString().slice(0, 46), 文字: (c.innerText || '').trim().slice(0, 24), 尺寸: `${Math.round(r.width)}x${Math.round(r.height)}` };
      })
      : null,
    它所在容器文字: me.parentElement ? (me.parentElement.innerText || '').trim().slice(0, 160) : null,
    它上面一层的文字: me.parentElement?.parentElement ? (me.parentElement.parentElement.innerText || '').trim().slice(0, 200) : null,
    生成按钮: genEl ? box(genEl) : null,
    与生成按钮纵向差: genEl ? Math.round(genEl.getBoundingClientRect().y - me.getBoundingClientRect().y) : null,
  };
}, { n: nid, pre: MYSTERY, gen: GEN });

// ① 未选中时在不在
await page.evaluate(() => document.body.focus());
await page.keyboard.press('Meta+0');
await page.waitForTimeout(2200);
out.未选中时 = await page.evaluate(({ n, pre }) => {
  const node = document.querySelector(`.react-flow__node[data-id="${n}"]`);
  if (!node) return { err: 'node not in DOM' };
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  let n0 = 0;
  for (const b of [...node.querySelectorAll('button,[role="button"]')].filter(vis)) {
    const svg = b.querySelector('svg');
    const d = svg ? [...svg.querySelectorAll('path')].map((x) => x.getAttribute('d')).join(' ') : '';
    if (d.includes(pre)) n0 += 1;
  }
  return { 该节点可见按钮总数: [...node.querySelectorAll('button,[role="button"]')].filter(vis).length, 其中这枚: n0, 节点是否selected: node.className.includes('selected') };
}, { n: VID, pre: MYSTERY });

// ② 选中后详细结构
await page.evaluate((n) => document.querySelector(`.react-flow__node[data-id="${n}"]`)?.click(), VID);
await page.waitForTimeout(2000);
out.sel = await page.evaluate((n) => {
  const el = document.querySelector(`.react-flow__node[data-id="${n}"]`);
  return { inDom: !!el, selected: !!el && el.className.includes('selected') };
}, VID);
if (!out.sel.inDom || !out.sel.selected) { console.log('!! 没选中，读数作废'); await browser.close(); process.exit(1); }
out.结构 = await inspect(VID);

// ③ 拍特写：把视口挪到能同时看见它和生成按钮的位置
await page.mouse.move(5, 5);
await page.waitForTimeout(500);
const clip = await page.evaluate(({ n, pre }) => {
  const node = document.querySelector(`.react-flow__node[data-id="${n}"]`);
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  for (const b of [...node.querySelectorAll('button,[role="button"]')].filter(vis)) {
    const svg = b.querySelector('svg');
    const d = svg ? [...svg.querySelectorAll('path')].map((x) => x.getAttribute('d')).join(' ') : '';
    if (d.includes(pre)) {
      const r = b.getBoundingClientRect();
      const nr = node.getBoundingClientRect();
      return { x: Math.max(0, Math.round(nr.x - 10)), y: Math.max(0, Math.round(r.y - 60)), width: Math.min(1440, Math.round(nr.width + 20)), height: Math.min(810, Math.round(r.height + 120)) };
    }
  }
  return null;
}, { n: VID, pre: MYSTERY });
if (clip) {
  await shot(page, 'M-308-节点右上角那枚无名按钮特写.png', { clip });
  out.特写clip = clip;
}

await writeFile(resolve(HERE, '.evidence/cg1-mystery-closeup.json'), JSON.stringify(out, null, 2));
console.log(JSON.stringify(out, null, 2).slice(0, 4500));
await browser.close();
