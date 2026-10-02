// Batch CD-12：阳性对照重做 —— 这次**不挑 class**，直接扫全页文本。
//
// CD-11 的对照没通过，于是脚本正确地拒绝下结论（好）。但有两种可能：
//   ① 点击真的没落到那枚按钮上；② 点击落了，**只是我没找对 toast 的位置**。
// 用**全页 innerText 差分**来分辨：toast 出现在哪不重要，页面上多出那句话才重要。
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
const out = { hits: [] };

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
    const t = (n.textContent || '').trim();
    const el0 = n.parentElement;
    // ⛔ 必须排除 SCRIPT/STYLE —— Next.js 的 RSC 数据块里含整份页面文本，
    //    不排除的话「点击前基线」就天然非 0，对照直接作废（CD-12 踩过）。
    if (!el0 || /^(SCRIPT|STYLE|NOSCRIPT|TEMPLATE)$/.test(el0.tagName)) continue;
    const r0 = el0.getBoundingClientRect();
    if (r0.width <= 0 && r0.height <= 0) continue;
    if (t && t.includes(needle)) {
      const el = el0;
      const r = r;
      hits.push({ text: t.slice(0, 80), tag: el.tagName, cls: (el.className?.toString?.() || '').slice(0, 60),
        box: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        chain: (() => { const c = []; let e = el; for (let i = 0; i < 5 && e; i += 1) { c.push(`${e.tagName}.${(e.className?.toString?.() || '').split(' ').slice(0,2).join('.')}`); e = e.parentElement; } return c; })() });
    }
  }
  return hits;
}, NEEDLE);

const setup = async () => {
  await page.evaluate(() => document.body.focus());
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2200);
  await page.evaluate((nid) => document.querySelector(`.react-flow__node[data-id="${nid}"]`)?.click(), MY_NODE);
  await page.waitForTimeout(1800);
  let r = await page.evaluate((sel) => { const q = document.querySelector(sel).getBoundingClientRect(); return [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)]; }, SEL);
  if (r[0] < 0 || r[1] < 0 || r[0] + r[2] > 1440 || r[1] + r[3] > 810) {
    const nx = r[0] < 0 ? -r[0] + 40 : (r[0] + r[2] > 1440 ? 1440 - r[0] - r[2] - 40 : 0);
    const ny = r[1] < 0 ? -r[1] + 40 : (r[1] + r[3] > 810 ? 810 - r[1] - r[3] - 40 : 0);
    await page.mouse.move(700, 400);
    await page.mouse.down({ button: 'middle' });
    await page.mouse.move(700 + nx, 400 + ny, { steps: 18 });
    await page.mouse.up({ button: 'middle' });
    await page.waitForTimeout(1500);
    r = await page.evaluate((sel) => { const q = document.querySelector(sel).getBoundingClientRect(); return [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)]; }, SEL);
  }
  return r;
};

const barBtns = () => page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!n) return [];
  return [...n.querySelectorAll('button,[role="button"]')].filter((b) => { const r = b.getBoundingClientRect(); return r.width > 0 && r.y > 700; })
    .map((b) => { const r = b.getBoundingClientRect(); return { t: (b.innerText || '').trim().slice(0, 8), disabled: b.disabled === true, box: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; });
}, MY_NODE);

out.rect = await setup();
out.bar = await barBtns();
out.btn = out.bar[out.bar.length - 2];
out.base = await scan();

// —— A：空提示词，点同一坐标 ——
const [bx, by, bw, bh] = out.btn.box;
await page.mouse.move(bx + bw / 2, by + bh / 2, { steps: 8 });
await page.waitForTimeout(500);
await page.mouse.down();
await page.waitForTimeout(80);
await page.mouse.up();
for (let i = 0; i < 14; i += 1) {
  await page.waitForTimeout(160);
  const h = await scan();
  if (h.length) { out.hits.push({ phase: 'A 空提示词', i, h }); break; }
}
if (!out.hits.length) out.hits.push({ phase: 'A 空提示词', i: -1, h: [] });
out.aPassed = out.base.length === 0 && out.hits.some((x) => x.phase.startsWith('A') && x.h.length);
await shot(page, 'M-303-翻译提示词-空提示词时会弹提示.png', { clip: { x: 0, y: 0, width: 1440, height: 810 } });

// —— B：有内容，点同一坐标 ——
await page.waitForTimeout(2500);
const r = out.rect;
await page.mouse.move(r[0] + 60, r[1] + 16, { steps: 6 });
await page.waitForTimeout(300);
await page.mouse.click(r[0] + 60, r[1] + 16);
await page.waitForTimeout(500);
await page.keyboard.type(TEXT, { delay: 18 });
await page.waitForTimeout(1500);
out.promptB = await page.evaluate((sel) => (document.querySelector(sel)?.innerText || '').trim(), SEL);
out.baseB = await scan();
out.bBaselineClean = out.baseB.length === 0;
await page.mouse.move(bx + bw / 2, by + bh / 2, { steps: 8 });
await page.waitForTimeout(400);
await page.mouse.click(bx + bw / 2, by + bh / 2);
let bHit = [];
for (let i = 0; i < 22; i += 1) {
  await page.waitForTimeout(200);
  const h = await scan();
  if (h.length) { bHit = h; break; }
}
out.bHit = bHit;
out.valAfter = await page.evaluate((sel) => (document.querySelector(sel)?.innerText || '').trim(), SEL);
await shot(page, 'M-304-翻译提示词-有内容时的结果.png', { clip: { x: 0, y: 0, width: 1440, height: 810 } });

// 收尾清空
await page.evaluate(() => document.activeElement?.blur?.());
await page.waitForTimeout(400);
const r2 = await page.evaluate((sel) => { const q = document.querySelector(sel).getBoundingClientRect(); return [Math.round(q.x), Math.round(q.y)]; }, SEL);
await page.mouse.move(r2[0] + 60, r2[1] + 16, { steps: 6 });
await page.waitForTimeout(300);
await page.mouse.click(r2[0] + 60, r2[1] + 16);
await page.waitForTimeout(500);
await page.keyboard.press('Meta+a');
await page.waitForTimeout(400);
await page.keyboard.press('Backspace');
await page.waitForTimeout(1400);
out.afterClear = await page.evaluate((sel) => (document.querySelector(sel)?.innerText || '').trim(), SEL);

out.verdict = out.base.length !== 0
  ? '⛔ 基线不为 0（点击前页面上就有那句话）—— 对照作废'
  : !out.aPassed
  ? '⛔ 阳性对照仍未通过（空提示词时也没找到「提示词为空」六个字）—— 读数不成立，不能下结论'
  : (out.bHit.length
    ? `✅ 有内容时也出现了：${JSON.stringify(out.bHit).slice(0, 200)}`
    : '✅ 阳性对照通过（同一坐标、空提示词时能看到「提示词为空」），有内容时**什么都没有** —— 结论成立');
await writeFile(resolve(HERE, '.evidence/cd12-control2.json'), JSON.stringify(out, null, 2));
console.log(JSON.stringify({ bar: out.bar, btn: out.btn, base: out.base, aPassed: out.aPassed, hits: out.hits, promptB: out.promptB, baseB: out.baseB, bHit: out.bHit, valAfter: out.valAfter, afterClear: out.afterClear, verdict: out.verdict }, null, 2).slice(0, 3000));
await browser.close();
