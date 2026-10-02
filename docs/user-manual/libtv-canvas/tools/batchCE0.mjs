// Batch CE-0：⭐ **换一种点法** —— 前三轮全部栽在「坐标点不中按钮」上。
// 这一步不再用坐标，而是：**先在 DOM 里认出那枚按钮，再对它 `el.click()`**。
// 认出它的办法不是坐标，是**图标形状**：`文A` 那一枚的 SVG 路径是固定的。
//
// 仍然是老规矩：**阳性对照必须先通过**，才准谈「有内容时会发生什么」。
//   对照组：空提示词 + 同一枚按钮 + 同一个 el.click() ⇒ 应弹「提示词为空，请输入内容后点击」
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const MY_NODE = 't-2AK3Ukyxj3';
const TEXT = 'a cat sitting on a warm windowsill at sunrise';
const SEL = '.text-fg-default[contenteditable="true"]';
const NEEDLE = '提示词为空';

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

const scan = () => page.evaluate((needle) => {
  const hits = [];
  const walk = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let n;
  while ((n = walk.nextNode())) {
    const el = n.parentElement;
    if (!el || /^(SCRIPT|STYLE|NOSCRIPT|TEMPLATE)$/.test(el.tagName)) continue;
    const t = (n.textContent || '').trim();
    if (!t.includes(needle)) continue;
    const r = el.getBoundingClientRect();
    if (r.width <= 0 && r.height <= 0) continue;
    hits.push({ text: t.slice(0, 70), tag: el.tagName, cls: (el.className?.toString?.() || '').slice(0, 50), box: [Math.round(r.x), Math.round(r.y)] });
  }
  return hits;
}, NEEDLE);

// ⭐ 认出那枚按钮：参数条里 **aria 为空、可用、不是模型下拉也不是生成按钮** 的那一枚，
//    并把它的 SVG 路径取出来当**身份证**（坐标会随缩放变，路径不会）
out.identify = await page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!n) return { err: 'node not in DOM' };
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const btns = [...n.querySelectorAll('button,[role="button"]')].filter(vis);
  return btns.map((b, i) => {
    const r = b.getBoundingClientRect();
    const svg = b.querySelector('svg');
    return {
      i, aria: b.getAttribute('aria-label'), t: (b.innerText || '').trim().slice(0, 12),
      disabled: b.disabled === true,
      box: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      path: svg ? [...svg.querySelectorAll('path')].map((p) => p.getAttribute('d')).join(' ').slice(0, 90) : null,
    };
  });
}, MY_NODE);
console.log('参数条按钮：', JSON.stringify(out.identify, null, 2));

// 选节点 + 往视口里挪（不做也得做：按钮得先渲染出来）
await page.evaluate(() => document.body.focus());
await page.keyboard.press('Meta+0');
await page.waitForTimeout(2200);
await page.evaluate((nid) => document.querySelector(`.react-flow__node[data-id="${nid}"]`)?.click(), MY_NODE);
await page.waitForTimeout(1800);
out.identify2 = await page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!n) return { err: 'node not in DOM' };
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  return [...n.querySelectorAll('button,[role="button"]')].filter(vis).map((b, i) => {
    const r = b.getBoundingClientRect();
    const svg = b.querySelector('svg');
    return { i, aria: b.getAttribute('aria-label'), t: (b.innerText || '').trim().slice(0, 12), disabled: b.disabled === true,
      box: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      path: svg ? [...svg.querySelectorAll('path')].map((p) => p.getAttribute('d')).join(' ').slice(0, 90) : null };
  });
}, MY_NODE);
console.log('选中后：', JSON.stringify(out.identify2, null, 2));

await writeFile(resolve(HERE, '.evidence/ce0-identify.json'), JSON.stringify(out, null, 2));
await browser.close();
