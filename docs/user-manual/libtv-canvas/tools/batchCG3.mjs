// Batch CG-3：点那枚 `⤢`（节点浮层右上角、28×28、四类节点都有、**悬停无任何名字**）。
//
// 手册 `10-tasks/create-nodes.md` 早就记下了这枚图标，但只写了
// 「在图片节点上是 `cursor: not-allowed`（视频节点上同一枚是可点的）」——
// **它自己从来没被点过**，所以「点下去会发生什么」是空白。
//
// ⭐ 为什么现在敢点（上一轮想点又不敢的那些顾虑，逐条核过）：
//   ① 它**不在参数条上**（`absolute right-2 top-2`，`size-7`），
//      而参数条上有独立的生成按钮（`M8.3.3…`）和**明码标价的 `135`**；
//   ② 它的 class 里**没有**任何和生成/提交相关的字样；
//   ③ 它在**卡片右上角**这个典型「展开详情」位上；
//   ④ 即使判断错了，也**可逆**（再点一次或刷新即复原）。
// 仍然保留的纪律：⛔ 前后各读一次余额；⛔ 刷新两轮复核复原。
//
// ⭐ 方法：CC 的教训是**单点采样不足以定性**，所以点完做 **8 次 × 400ms 的时间序列采样**，
// 看它是「立刻变」还是「慢慢变」还是「没变」。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { fingerprint } from './scenario.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const EXPAND = 'M1.4 8.9c.22 0 .4.18.4.4v5.54l5.26-5.26a.4.4 0 0 1 .57 0l.7.71';
const VID = 'v-eMpqKtiLlx';

const { browser, page } = await launch();
const out = { timeline: [] };

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

const balance = () => page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const t = [...document.querySelectorAll('header *,nav *')].filter(vis).map((e) => (e.innerText || '').trim()).filter((x) => /^\d{1,4}$/.test(x));
  return t.length ? Number(t[t.length - 1]) : null;
});

// 真值读数：节点数走**抽屉的「共 N 节点」**（`.react-flow__node` 只渲染视口内）
const truth = () => page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0 && getComputedStyle(el).visibility !== 'hidden'; };
  let 共N节点 = null;
  for (const el of document.querySelectorAll('div,span,p')) {
    if (!vis(el)) continue;
    const t = (el.innerText || '').trim();
    const m = t.match(/^共\s*(\d+)\s*节点$/);
    if (m && el.children.length === 0) { 共N节点 = Number(m[1]); break; }
  }
  const f = document.querySelector('.react-flow__node.float-ui, .node-floating-ui');
  const fr = f ? f.getBoundingClientRect() : null;
  return {
    url: location.href,
    共N节点,
    视口内节点数: document.querySelectorAll('.react-flow__node').length,
    浮层卡片: fr ? { x: Math.round(fr.x), y: Math.round(fr.y), w: Math.round(fr.width), h: Math.round(fr.height) } : null,
    节点壳: (() => { const s = document.querySelector('.node-shell'); if (!s) return null; const r = s.getBoundingClientRect(); return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }; })(),
    对话框数: document.querySelectorAll('[role="dialog"]').length,
    展开元素数: document.querySelectorAll('[aria-expanded="true"]').length,
    缩放: (() => { for (const el of document.querySelectorAll('div,span')) { if (!vis(el)) continue; const t = (el.innerText || '').trim(); if (/^\d{1,3}%$/.test(t) && el.children.length === 0) return t; } return null; })(),
  };
});

const clickExpand = () => page.evaluate(({ n, pre }) => {
  const node = document.querySelector(`.react-flow__node[data-id="${n}"]`);
  if (!node) return { ok: false, why: 'node not in DOM' };
  for (const b of node.querySelectorAll('button,[role="button"]')) {
    const svg = b.querySelector('svg');
    const d = svg ? [...svg.querySelectorAll('path')].map((x) => x.getAttribute('d')).join(' ') : '';
    if (d.includes(pre)) {
      const r = b.getBoundingClientRect();
      const st = { disabled: b.disabled === true, cursor: getComputedStyle(b).cursor, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
      b.click();
      return { ok: true, ...st };
    }
  }
  return { ok: false, why: '没找到该路径的按钮' };
}, { n: VID, pre: EXPAND });

// 硬前置：收全 → 选中 → 断言
await page.evaluate(() => document.body.focus());
await page.keyboard.press('Meta+0');
await page.waitForTimeout(2200);
await page.evaluate((n) => document.querySelector(`.react-flow__node[data-id="${n}"]`)?.click(), VID);
await page.waitForTimeout(2000);
const sel = await page.evaluate((n) => {
  const el = document.querySelector(`.react-flow__node[data-id="${n}"]`);
  return { inDom: !!el, selected: !!el && el.className.includes('selected') };
}, VID);
if (!sel.inDom || !sel.selected) { console.log('!! 没选中，读数作废'); await browser.close(); process.exit(1); }

// 基线
out.balance0 = await balance();
out.baseline = await truth();
out.fp0 = await fingerprint(page);
out.节点提示词_基线 = await page.evaluate((n) => {
  const node = document.querySelector(`.react-flow__node[data-id="${n}"]`);
  const b = node ? node.querySelector('.text-fg-default[contenteditable="true"]') : null;
  return b ? (b.innerText || '').trim() : null;
}, VID);

// 点
out.click = await clickExpand();
// 时间序列采样：单点采样不足以定性（CC 的教训）
for (let i = 0; i < 8; i += 1) {
  await page.waitForTimeout(400);
  out.timeline.push({ i, ...(await truth()) });
}
out.after = out.timeline[out.timeline.length - 1];
out.balance1 = await balance();

// ⭐ 差异判定：拿基线里的浮层卡片尺寸做对照
const sizeOf = (o) => (o && o.浮层卡片) ? `${o.浮层卡片.w}x${o.浮层卡片.h}@${o.浮层卡片.x},${o.浮层卡片.y}` : '无浮层卡片';
out.判定 = {
  浮层卡片: `基线 ${sizeOf(out.baseline)} → 点后 ${sizeOf(out.after)}`,
  变了: sizeOf(out.baseline) !== sizeOf(out.after),
  节点数: `${out.baseline.共N节点} → ${out.after.共N节点}`,
  对话框: `${out.baseline.对话框数} → ${out.after.对话框数}`,
  url变了: out.baseline.url !== out.after.url,
};

await shot(page, 'M-309-点了右上角展开之后.png');

// 复原：再点一次
out.复原_再点一次 = await clickExpand();
await page.waitForTimeout(1500);
out.afterRestore = await truth();
out.balance2 = await balance();
out.判定.复原 = `再点后 浮层卡片 ${sizeOf(out.afterRestore)}；节点数 ${out.afterRestore.共N节点}`;

// 再刷新复核（两轮独立刷新）
await page.reload({ waitUntil: 'domcontentloaded' });
await page.waitForTimeout(4500);
await closePromos(page);
await page.waitForTimeout(800);
out.复原_刷新1 = await truth();
await page.reload({ waitUntil: 'domcontentloaded' });
await page.waitForTimeout(4500);
await closePromos(page);
await page.waitForTimeout(800);
out.复原_刷新2 = await truth();
out.判定.刷新后 = `刷新1 浮层卡片 ${sizeOf(out.复原_刷新1)}；刷新2 ${sizeOf(out.复原_刷新2)}`;

await writeFile(resolve(HERE, '.evidence/cg3-expand-click.json'), JSON.stringify(out, null, 2));
console.log('click =', JSON.stringify(out.click));
console.log('判定 =', JSON.stringify(out.判定, null, 2));
console.log('baseline =', JSON.stringify(out.baseline));
console.log('时间序列 =');
for (const t of out.timeline) console.log('  ', t.i, JSON.stringify(t));
console.log('提示词基线 =', JSON.stringify(out.节点提示词_基线));
console.log('balance 0/1/2 =', out.balance0, out.balance1, out.balance2);
await browser.close();
