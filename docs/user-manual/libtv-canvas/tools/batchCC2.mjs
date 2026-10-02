// Batch CC-2：特效广场的卡片本体。
//   A. dump 一张卡片的**每一层**：有哪些图标、哪些文字、数字旁边有没有 title/aria
//   B. **点一张卡片本身**（不是 ⤢ 详情、不是 •••）看会发生什么 —— CA③ 的正题
// ⛔ 收尾守则：点之前先记下画布节点数与**全部 data-id**；
//    点完如果多出节点，**只按本轮记下的新 id 删**，绝不按位置/顺序（CA 教训）。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;

const { browser, page } = await launch();
await open(page, URL_);
await closePromos(page);
const out = {};

// 画布基线
out.canvasBefore = await page.evaluate(() => ({
  ids: [...document.querySelectorAll('.react-flow__node')].map((n) => n.getAttribute('data-id')),
  edges: document.querySelectorAll('.react-flow__edge').length,
}));

await page.evaluate(async () => {
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  for (let i = 0; i < 6; i += 1) {
    const hit = [...document.querySelectorAll('button, [role="button"]')].find((b) => (b.innerText || '').trim() === '知道了');
    if (hit) { hit.click(); await sleep(500); }
    if (!(document.body.innerText || '').includes('已升级为 TV Director')) return;
  }
});
await page.waitForTimeout(800);
await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  [...document.querySelectorAll('[aria-label="素材库"]')].filter(vis)[0]?.click();
});
await page.waitForTimeout(1800);
await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const hit = [...document.querySelectorAll('*')].filter((e) => vis(e) && (e.innerText || '').trim() === '特效库');
  let el = hit[hit.length - 1];
  let btn = null;
  for (let i = 0; i < 5 && el && !btn; i += 1) {
    if (el.tagName === 'BUTTON' || el.getAttribute('role') === 'button') btn = el;
    el = el.parentElement;
  }
  (btn || hit[hit.length - 1].parentElement)?.click();
});
await page.waitForTimeout(3000);

// —— A. 卡片结构 ——
out.cardStruct = await page.evaluate(() => {
  const m = [...document.querySelectorAll('.mantine-Modal-content')]
    .find((el) => (el.innerText || '').includes('特效广场'));
  if (!m) return { err: '没有特效广场' };
  // 卡片 = `rounded-xl flex flex-col gap-2 p-2` 那类
  const cards = [...m.querySelectorAll('div')].filter((el) => {
    const c = el.className?.toString?.() || '';
    return /rounded-xl/.test(c) && /flex-col/.test(c) && /p-2/.test(c);
  });
  const card = cards[0];
  if (!card) return { err: '没找到卡片', cardClasses: [...new Set([...m.querySelectorAll('div')].map((e) => (e.className?.toString?.() || '').slice(0, 40)))].slice(0, 20) };
  const r = card.getBoundingClientRect();
  const walk = (el, depth) => {
    const rr = el.getBoundingClientRect();
    const own = [...el.childNodes].filter((n) => n.nodeType === 3).map((n) => n.textContent.trim()).filter(Boolean).join(' ');
    const node = {
      d: depth, tag: el.tagName, own: own.slice(0, 30),
      aria: el.getAttribute('aria-label'), title: el.getAttribute('title'),
      role: el.getAttribute('role'),
      cls: (el.className?.toString?.() || '').slice(0, 55),
      box: [Math.round(rr.x), Math.round(rr.y), Math.round(rr.width), Math.round(rr.height)],
    };
    if (el.tagName === 'svg' || el.tagName === 'IMG') {
      node.path = (el.getAttribute('d') || el.getAttribute('src') || '').slice(0, 60);
      node.viewBox = el.getAttribute('viewBox');
    }
    node.kids = depth < 5 ? [...el.children].map((c) => walk(c, depth + 1)) : [];
    return node;
  };
  return { n: cards.length, cardBox: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], tree: walk(card, 0) };
});
await shot(page, 'M-296-特效广场-卡片全景.png', { clip: { x: 100, y: 79, width: 1240, height: 400 } });

// —— B. 点一张卡片本身 ——
out.cardBox = out.cardStruct?.cardBox;
if (out.cardBox) {
  const cx = out.cardBox[0] + out.cardBox[2] / 2;
  const cy = out.cardBox[1] + out.cardBox[3] / 2;
  out.beforeClick = await page.evaluate(() => ({
    modals: [...document.querySelectorAll('.mantine-Modal-content')].map((m) => (m.innerText || '').replace(/\s+/g, ' ').slice(0, 60)),
    nodes: [...document.querySelectorAll('.react-flow__node')].map((n) => n.getAttribute('data-id')),
    toasts: [...document.querySelectorAll('[class*="toast"],[class*="Toast"],[role="alert"]')].map((t) => (t.innerText || '').trim()).filter(Boolean),
  }));
  await page.mouse.move(cx, cy, { steps: 10 });
  await page.waitForTimeout(800);
  await shot(page, 'M-297-特效卡片-悬停.png', { clip: { x: 100, y: 79, width: 900, height: 400 } });
  await page.mouse.click(cx, cy);
  await page.waitForTimeout(2500);
  out.afterClick = await page.evaluate(() => ({
    modals: [...document.querySelectorAll('.mantine-Modal-content')].map((m) => (m.innerText || '').replace(/\s+/g, ' ').slice(0, 90)),
    nodes: [...document.querySelectorAll('.react-flow__node')].map((n) => n.getAttribute('data-id')),
    toasts: [...document.querySelectorAll('[class*="toast"],[class*="Toast"],[role="alert"]')].map((t) => (t.innerText || '').trim()).filter(Boolean),
    bodyHead: (document.body.innerText || '').replace(/\s+/g, ' ').slice(0, 200),
  }));
  await shot(page, 'M-298-特效卡片-点开之后.png', { clip: { x: 0, y: 0, width: 1440, height: 810 } });
}

await writeFile(resolve(HERE, '.evidence/cc2-card.json'), JSON.stringify(out, null, 2));
console.log(JSON.stringify({ canvasBefore: out.canvasBefore, cardBox: out.cardBox, beforeClick: out.beforeClick, afterClick: out.afterClick }, null, 2));
await browser.close();
