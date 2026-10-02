// Batch CG-11：只拍两张图，用**新文件名**（前面的 M-313/M-314 反复对不上读数，
// 有 Read 缓存的嫌疑），构图改成**视口上部整幅**（不裁剪，避免一切 clip 计算问题）。
//
// ⭐ 本批真正的证据是**元素差集**（点前 33 项 → 点后 2 项，消失 31 项、新增 0 项，
//    逐项列名），那比任何截图都硬。配图只负责让读者**一眼看出卡片不见了**，
//    所以构图优先「看得全」而不是「切得准」。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const EXPAND = 'M1.4 8.9c.22 0 .4.18.4.4v5.54l5.26-5.26a.4.4 0 0 1 .57 0l.7.71';
const VID = 'v-eMpqKtiLlx';
const FULL = { x: 0, y: 0, width: 1440, height: 700 };

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
await page.reload({ waitUntil: 'domcontentloaded' });
await page.waitForTimeout(5000);
await closePromos(page);
await page.waitForTimeout(1200);

const brief = () => page.evaluate((n) => {
  const node = document.querySelector(`.react-flow__node[data-id="${n}"]`);
  if (!node) return { err: 'not in DOM' };
  const fus = [...node.querySelectorAll('.node-floating-ui')].map((el) => {
    const r = el.getBoundingClientRect();
    return `${Math.round(r.width)}x${Math.round(r.height)}`;
  }).filter((s) => !s.endsWith('x0'));
  return { 浮层: fus.sort(), 文字: (node.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 80), 元素数: node.querySelectorAll('*').length };
}, VID);

const findBlank = () => page.evaluate(() => {
  for (const [x, y] of [[720, 90], [1300, 170], [720, 690], [200, 370], [1240, 630], [80, 190], [1360, 390]]) {
    const el = document.elementFromPoint(x, y);
    if (el && !el.closest('.react-flow__node') && !el.closest('button,[role="button"]') && !el.closest('input,[contenteditable="true"]')) return { x, y };
  }
  return null;
});
const blank = await findBlank();
await page.mouse.click(blank.x, blank.y);
await page.waitForTimeout(800);
await page.evaluate(() => document.body.focus());
await page.keyboard.press('Meta+0');
await page.waitForTimeout(2400);
const c = await page.evaluate((n) => {
  const el = document.querySelector(`.react-flow__node[data-id="${n}"]`);
  if (!el) return null;
  const b = el.getBoundingClientRect();
  return { cx: Math.round(b.x + b.width / 2), cy: Math.round(b.y + b.height / 2) };
}, VID);
const hitId = await page.evaluate(({ x, y, n }) => {
  const el = document.elementFromPoint(x, y);
  const nd = el ? el.closest('.react-flow__node') : null;
  return nd ? nd.getAttribute('data-id') : null;
}, { x: c.cx, y: c.cy, n: VID });
if (hitId !== VID) { console.log('!! 点不中', hitId); await browser.close(); process.exit(1); }
await page.mouse.move(c.cx, c.cy);
await page.waitForTimeout(400);
await page.mouse.click(c.cx, c.cy);
await page.waitForTimeout(2200);

out.展开态 = await brief(VID);
await shot(page, 'M-315-参数卡片-展开时-全屏.png', { clip: FULL });

const ex = await page.evaluate(({ n, p }) => {
  const node = document.querySelector(`.react-flow__node[data-id="${n}"]`);
  for (const b of node.querySelectorAll('button,[role="button"]')) {
    const svg = b.querySelector('svg');
    const d = svg ? [...svg.querySelectorAll('path')].map((x) => x.getAttribute('d')).join(' ') : '';
    if (d.includes(p)) { const r = b.getBoundingClientRect(); return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; }
  }
  return null;
}, { n: VID, p: EXPAND });
if (!ex) { console.log('!! 找不到 ⤢'); await browser.close(); process.exit(1); }
await page.mouse.move(ex.cx, ex.cy);
await page.waitForTimeout(600);
await page.mouse.click(ex.cx, ex.cy);
await page.waitForTimeout(1800);

out.折叠态 = await brief(VID);
await shot(page, 'M-316-参数卡片-折叠后-全屏.png', { clip: FULL });

out.balance = await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const t = [...document.querySelectorAll('header *,nav *')].filter(vis).map((e) => (e.innerText || '').trim()).filter((x) => /^\d{1,4}$/.test(x));
  return t.length ? Number(t[t.length - 1]) : null;
});
console.log('展开态 =', JSON.stringify(out.展开态));
console.log('折叠态 =', JSON.stringify(out.折叠态));
console.log('余额 =', out.balance);

await writeFile(resolve(HERE, '.evidence/cg11-shots.json'), JSON.stringify(out, null, 2));
await browser.close();
