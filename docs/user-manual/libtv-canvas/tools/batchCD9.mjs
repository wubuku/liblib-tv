// Batch CD-9：参数条按钮不在「提示词框的祖先」里 —— CD-8 圈出来的容器 `buttons: []`。
// 换个基准：**文本节点的参数条上写着模型名 `GVLM 3.1`**，用它的 y 当横轴，
// 把**同一行**上的所有按钮捞出来逐枚悬停实名。
//
// ⚠️ 同时先把框里 CD-7 留下的字清掉（上一步读数已经显示「打字会落盘」，
//    留到收尾不清就是给用户留垃圾）。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const MY_NODE = 't-2AK3Ukyxj3';
const SEL = '.text-fg-default[contenteditable="true"]';

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
await page.evaluate(() => document.body.focus());
await page.keyboard.press('Meta+0');
await page.waitForTimeout(2200);
await page.evaluate((nid) => document.querySelector(`.react-flow__node[data-id="${nid}"]`)?.click(), MY_NODE);
await page.waitForTimeout(1800);

let rect = await page.evaluate((sel) => {
  const b = document.querySelector(sel); const r = b.getBoundingClientRect();
  return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)];
}, SEL);
if (rect[0] < 0 || rect[1] < 0 || rect[0] + rect[2] > 1440 || rect[1] + rect[3] > 810) {
  const needX = rect[0] < 0 ? -rect[0] + 40 : (rect[0] + rect[2] > 1440 ? 1440 - rect[0] - rect[2] - 40 : 0);
  const needY = rect[1] < 0 ? -rect[1] + 40 : (rect[1] + rect[3] > 810 ? 810 - rect[1] - rect[3] - 40 : 0);
  await page.mouse.move(700, 400);
  await page.mouse.down({ button: 'middle' });
  await page.mouse.move(700 + needX, 400 + needY, { steps: 18 });
  await page.mouse.up({ button: 'middle' });
  await page.waitForTimeout(1500);
  rect = await page.evaluate((sel) => {
    const b = document.querySelector(sel); const r = b.getBoundingClientRect();
    return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)];
  }, SEL);
}
out.rect = rect;
out.current = await page.evaluate((sel) => (document.querySelector(sel)?.innerText || '').trim(), SEL);

// —— 清理 CD-7 留下的字 ——
if (out.current) {
  await page.mouse.move(rect[0] + 60, rect[1] + 16, { steps: 6 });
  await page.waitForTimeout(300);
  await page.mouse.click(rect[0] + 60, rect[1] + 16);
  await page.waitForTimeout(500);
  await page.keyboard.press('Meta+a');
  await page.waitForTimeout(400);
  await page.keyboard.press('Backspace');
  await page.waitForTimeout(1200);
}
out.afterClear = await page.evaluate((sel) => (document.querySelector(sel)?.innerText || '').trim(), SEL);

// —— 以 `GVLM 3.1` 那行为基准捞同排按钮 ——
out.rowProbe = await page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!n) return { err: 'no node' };
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const model = [...n.querySelectorAll('*')].find((e) => (e.innerText || '').trim() === 'GVLM 3.1' && e.children.length === 0);
  if (!model) return { err: 'no model label', all: [...n.querySelectorAll('button,[role="button"]')].map((b) => { const r = b.getBoundingClientRect(); return { aria: b.getAttribute('aria-label'), t: (b.innerText || '').trim().slice(0, 12), box: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; }) };
  const mr = model.getBoundingClientRect();
  const my = mr.y + mr.height / 2;
  const row = [...n.querySelectorAll('button,[role="button"]')].filter((b) => {
    const r = b.getBoundingClientRect();
    return r.width > 0 && Math.abs((r.y + r.height / 2) - my) < 18;
  }).map((b) => {
    const r = b.getBoundingClientRect();
    return { aria: b.getAttribute('aria-label'), t: (b.innerText || '').trim().slice(0, 12),
      disabled: b.disabled === true, hasSvg: !!b.querySelector('svg'),
      box: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
  });
  return { modelY: Math.round(my), modelBox: [Math.round(mr.x), Math.round(mr.y), Math.round(mr.width), Math.round(mr.height)], row };
}, MY_NODE);

out.names = [];
for (const b of (out.rowProbe?.row || [])) {
  await page.mouse.move(b.box[0] + b.box[2] / 2, b.box[1] + b.box[3] / 2, { steps: 8 });
  await page.waitForTimeout(1000);
  const tip = await page.evaluate(() => {
    const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
    return [...document.querySelectorAll('[role="tooltip"],.mantine-Tooltip-tooltip')].filter(vis)
      .map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim()).filter(Boolean);
  });
  out.names.push({ ...b, tip });
}
await shot(page, 'M-302-文本节点-参数条逐枚实名.png', { clip: { x: 0, y: Math.max(0, rect[1] - 230), width: 1000, height: 400 } });
await writeFile(resolve(HERE, '.evidence/cd9-row.json'), JSON.stringify(out, null, 2));
console.log(JSON.stringify({ rect: out.rect, current: out.current, afterClear: out.afterClear, rowProbe: out.rowProbe, names: out.names }, null, 2).slice(0, 3000));
await browser.close();
