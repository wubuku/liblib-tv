// Batch CC-0：把「广场卡片」这个东西本身搞清楚。
// CA③ 上轮记成「脚本没找到卡片」—— ⭐ 先证明卡片**在不在**，再谈点它会发生什么。
// 这一步：进特效广场 → dump 卡片的真实 DOM 结构与坐标 → 读卡面上的每一个数字。
//
// ⛔ 本步只读：dump + 悬停，**不点卡片**。
//    点卡片可能触发「加入画布 / 下载 / 跳详情」等副作用，先看清它是什么再决定。
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

await page.evaluate(async () => {
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  for (let i = 0; i < 6; i += 1) {
    const hit = [...document.querySelectorAll('button, [role="button"]')].find((b) => (b.innerText || '').trim() === '知道了');
    if (hit) { hit.click(); await sleep(500); }
    if (!(document.body.innerText || '').includes('已升级为 TV Director')) return;
  }
});
await page.waitForTimeout(800);

// 进广场：素材库 → 特效库
out.enter = await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const b = [...document.querySelectorAll('[aria-label="素材库"]')].filter(vis)[0];
  if (!b) return { ok: false, why: '没有素材库按钮' };
  const r = b.getBoundingClientRect();
  b.click();
  return { ok: true, box: [Math.round(r.x), Math.round(r.y)] };
});
await page.waitForTimeout(1600);
out.afterOpen = await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const t = [...document.querySelectorAll('*')].filter((e) => vis(e) && (e.innerText || '').trim() === '特效库');
  return { hasSpecial: t.length, texts: (document.body.innerText || '').replace(/\s+/g, ' ').slice(0, 200) };
});
await page.evaluate(() => {
  const t = [...document.querySelectorAll('*')].find((e) => (e.innerText || '').trim() === '特效库' && e.children.length === 0);
  if (t) t.click();
});
await page.waitForTimeout(2600);
out.page = await page.evaluate(() => {
  const t = (document.body.innerText || '').replace(/\s+/g, ' ');
  return { head: t.slice(0, 400) };
});
await shot(page, 'M-296-特效广场-全景.png', { clip: { x: 0, y: 0, width: 1440, height: 810 } });

// —— dump 卡片：找「成组的重复结构」而不是猜 class ——
out.cards = await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 120 && r.height > 120 && r.width < 500 && r.height < 600; };
  const nodes = [...document.querySelectorAll('div')].filter(vis);
  // 卡片是「里面没有别的同尺寸 div」的叶子块
  const leaves = nodes.filter((n) => !nodes.some((m) => m !== n && n.contains(m)));
  return leaves.map((n) => {
    const r = n.getBoundingClientRect();
    return {
      x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height),
      cls: (n.className?.toString?.() || '').slice(0, 70),
      text: (n.innerText || '').replace(/\s+/g, ' ').slice(0, 120),
      imgs: n.querySelectorAll('img').length,
      svgs: n.querySelectorAll('svg').length,
      btns: n.querySelectorAll('button,[role="button"]').length,
    };
  }).slice(0, 24);
});

await writeFile(resolve(HERE, '.evidence/cc0-cards.json'), JSON.stringify(out, null, 2));
console.log(JSON.stringify({ enter: out.enter, afterOpen: out.afterOpen, page: out.page, cards: out.cards?.slice(0, 10) }, null, 2));
await browser.close();
