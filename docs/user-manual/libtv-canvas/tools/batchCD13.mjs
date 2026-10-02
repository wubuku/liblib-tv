// Batch CD-13：最后一步 —— 缩到 **100%**，并用 `elementFromPoint` **自证点击落点**。
//
// 前两版（CD-11 / CD-12）阳性对照都失败。CD-12 已经把「基线不干净」这个假阳性排掉了，
// 剩下的解释只有一个：**那组坐标没点到按钮上**（47% 缩放下按钮只有十几个像素）。
// ⭐ 所以这一次**不信任坐标**，先问 `document.elementFromPoint` 站在哪儿，
//    确认它是（或包含）目标按钮，才点。
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

// 缩到 100% + 平移到视口内
await page.evaluate(() => document.body.focus());
await page.keyboard.press('Meta+0');
await page.waitForTimeout(2200);
await page.evaluate((nid) => document.querySelector(`.react-flow__node[data-id="${nid}"]`)?.click(), MY_NODE);
await page.waitForTimeout(1800);
out.zoom = await page.evaluate(() => (document.querySelector('.react-flow__viewport')?.style.transform || '').match(/scale\(([\d.]+)\)/)?.[1] || null);
await page.keyboard.press('Meta+0');
await page.waitForTimeout(400);
await page.evaluate((nid) => document.querySelector(`.react-flow__node[data-id="${nid}"]`)?.click(), MY_NODE);
await page.waitForTimeout(1600);
// 用「缩放至100%」
await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  [...document.querySelectorAll('[aria-label="缩放选项"],button')].filter(vis)
    .find((b) => (b.getAttribute('aria-label') || '').includes('缩放'))?.click();
});
await page.waitForTimeout(800);
await page.evaluate(() => {
  const it = [...document.querySelectorAll('.mantine-Menu-item,[role="menuitem"]')].find((el) => (el.innerText || '').trim() === '缩放至100%');
  it?.click();
});
await page.waitForTimeout(1800);
await page.evaluate((nid) => document.querySelector(`.react-flow__node[data-id="${nid}"]`)?.click(), MY_NODE);
await page.waitForTimeout(1800);
out.zoom100 = await page.evaluate(() => (document.querySelector('.react-flow__viewport')?.style.transform || '').match(/scale\(([\d.]+)\)/)?.[1] || null);

// 平移：把提示词框连同下面的参数条一起挪进视口
const rectOf = () => page.evaluate((sel) => { const q = document.querySelector(sel).getBoundingClientRect(); return [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)]; }, SEL);
let rect = await rectOf();
out.rect0 = rect;
for (let i = 0; i < 5; i += 1) {
  const bottom = rect[1] + rect[3] + 90;      // 还要给下面的参数条留 90px
  if (rect[0] >= 0 && rect[1] >= 60 && rect[0] + rect[2] <= 1440 && bottom <= 810) break;
  const nx = rect[0] < 0 ? -rect[0] + 40 : (rect[0] + rect[2] > 1440 ? 1440 - rect[0] - rect[2] - 40 : 0);
  const ny = rect[1] < 60 ? 60 - rect[1] : (bottom > 810 ? 810 - bottom : 0);
  await page.mouse.move(700, 300);
  await page.mouse.down({ button: 'middle' });
  await page.mouse.move(700 + nx, 300 + ny, { steps: 18 });
  await page.mouse.up({ button: 'middle' });
  await page.waitForTimeout(1400);
  rect = await rectOf();
}
out.rect = rect;

// 参数条按钮 + ⭐ elementFromPoint 自证
out.bar = await page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!n) return [];
  return [...n.querySelectorAll('button,[role="button"]')].filter((b) => { const r = b.getBoundingClientRect(); return r.width > 0; })
    .map((b) => { const r = b.getBoundingClientRect(); return { t: (b.innerText || '').trim().slice(0, 8), disabled: b.disabled === true, box: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; });
}, MY_NODE);
out.btn = out.bar.find((b) => !b.disabled && !b.t) || out.bar[out.bar.length - 2] || out.bar[0];

out.hitTest = await page.evaluate((b) => {
  const cx = b[0] + b[2] / 2;
  const cy = b[1] + b[3] / 2;
  const el = document.elementFromPoint(cx, cy);
  if (!el) return { ok: false, why: 'elementFromPoint 返回 null（点不在视口内）' };
  const btn = el.closest('button,[role="button"]');
  const r = el.getBoundingClientRect();
  return { ok: !!btn, tag: el.tagName, isBtn: !!btn, btnBox: btn ? [Math.round(btn.getBoundingClientRect().x), Math.round(btn.getBoundingClientRect().y), Math.round(btn.getBoundingClientRect().width), Math.round(btn.getBoundingClientRect().height)] : null,
    matches: btn ? (Math.abs(btn.getBoundingClientRect().x - b[0]) < 2 && Math.abs(btn.getBoundingClientRect().y - b[1]) < 2) : false,
    elBox: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
}, out.btn.box);

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
    hits.push({ text: t.slice(0, 60), tag: el.tagName, cls: (el.className?.toString?.() || '').slice(0, 50), box: [Math.round(r.x), Math.round(r.y)] });
  }
  return hits;
}, NEEDLE);

// ——— A：空提示词 ———
out.baseA = await scan();
await page.mouse.click(out.btn.box[0] + out.btn.box[2] / 2, out.btn.box[1] + out.btn.box[3] / 2);
let aHit = [];
for (let i = 0; i < 16; i += 1) { await page.waitForTimeout(160); const h = await scan(); if (h.length) { aHit = h; break; } }
out.aHit = aHit;
await shot(page, 'M-303-翻译提示词-空提示词时会弹提示.png', { clip: { x: 0, y: 0, width: 1440, height: 810 } });

// ——— B：有内容 ———
await page.waitForTimeout(2500);
await page.mouse.move(rect[0] + 60, rect[1] + 16, { steps: 6 });
await page.waitForTimeout(300);
await page.mouse.click(rect[0] + 60, rect[1] + 16);
await page.waitForTimeout(500);
await page.keyboard.type(TEXT, { delay: 18 });
await page.waitForTimeout(1600);
out.promptB = await page.evaluate((sel) => (document.querySelector(sel)?.innerText || '').trim(), SEL);
out.baseB = await scan();
await page.mouse.click(out.btn.box[0] + out.btn.box[2] / 2, out.btn.box[1] + out.btn.box[3] / 2);
let bHit = [];
for (let i = 0; i < 24; i += 1) { await page.waitForTimeout(200); const h = await scan(); if (h.length) { bHit = h; break; } }
out.bHit = bHit;
out.valAfter = await page.evaluate((sel) => (document.querySelector(sel)?.innerText || '').trim(), SEL);
out.barAfter = await page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  return n ? [...n.querySelectorAll('button,[role="button"]')].filter((b) => { const r = b.getBoundingClientRect(); return r.width > 0; }).map((b) => ({ t: (b.innerText || '').trim().slice(0, 8), disabled: b.disabled === true })) : [];
}, MY_NODE);
await shot(page, 'M-304-翻译提示词-有内容时的结果.png', { clip: { x: 0, y: 0, width: 1440, height: 810 } });

// 收尾
await page.evaluate(() => document.activeElement?.blur?.());
await page.waitForTimeout(400);
const r2 = await rectOf();
await page.mouse.move(r2[0] + 60, r2[1] + 16, { steps: 6 });
await page.waitForTimeout(300);
await page.mouse.click(r2[0] + 60, r2[1] + 16);
await page.waitForTimeout(500);
await page.keyboard.press('Meta+a');
await page.waitForTimeout(400);
await page.keyboard.press('Backspace');
await page.waitForTimeout(1400);
out.afterClear = await page.evaluate((sel) => (document.querySelector(sel)?.innerText || '').trim(), SEL);

out.controlPassed = out.baseA.length === 0 && out.aHit.length > 0;
out.verdict = !out.hitTest.matches
  ? '⛔ 落点自证没通过（elementFromPoint 指到的不是我以为的那枚按钮）—— 读数不成立'
  : !out.controlPassed
    ? '⛔ 阳性对照仍未通过 —— 读数不成立，不能下结论'
    : (out.bHit.length ? `✅ 有内容时出现了：${JSON.stringify(out.bHit).slice(0, 200)}`
      : '✅ 对照通过 + 有内容时**没有任何反应** —— 结论成立');
await writeFile(resolve(HERE, '.evidence/cd13-hittest.json'), JSON.stringify(out, null, 2));
console.log(JSON.stringify({ zoom: out.zoom, zoom100: out.zoom100, rect: out.rect, bar: out.bar, btn: out.btn, hitTest: out.hitTest, baseA: out.baseA, aHit: out.aHit, promptB: out.promptB, baseB: out.baseB, bHit: out.bHit, valAfter: out.valAfter, barAfter: out.barAfter, afterClear: out.afterClear, verdict: out.verdict }, null, 2).slice(0, 3200));
await browser.close();
