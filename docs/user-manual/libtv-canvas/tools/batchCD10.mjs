// Batch CD-10：点「翻译提示词」。
// 按钮已定位：文本节点参数条同一行上的**中间那枚** `[562,778,32,32]`（aria 为空、可用）；
// 右边 `[642,778,32,32]` 是生成按钮（提示词为空时 `disabled: true`）。
// ⭐ 采样三样东西：**提示词内容 / 新出现的浮层 / 积分余额**（余额必须前后各读一次）。
// 收尾：把测试文本清空（CD-6 已验证「清空会落盘」，不清就是给用户留垃圾）。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const MY_NODE = 't-2AK3Ukyxj3';
const TEXT = 'a cat sitting on a warm windowsill at sunrise';
const SEL = '.text-fg-default[contenteditable="true"]';

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
  const top = [...document.querySelectorAll('header *,nav *')].filter(vis)
    .map((e) => (e.innerText || '').trim()).filter((t) => /^\d{1,4}$/.test(t));
  return top.length ? Number(top[top.length - 1]) : null;
});
const state = (tag) => page.evaluate(({ t, nid, sel }) => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const box = document.querySelector(sel);
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  const newPanels = [...document.querySelectorAll('.mantine-Modal-content,[role="dialog"],.mantine-Popover-dropdown,.mantine-Menu-dropdown')]
    .filter(vis).map((e) => (e.innerText || '').replace(/\s+/g, ' ').slice(0, 70)).filter(Boolean);
  const toasts = [...document.querySelectorAll('[class*="toast"],[class*="Toast"],[role="alert"],[class*="notification"]')]
    .filter(vis).map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 70)).filter(Boolean);
  const barBtns = n ? [...n.querySelectorAll('button,[role="button"]')].filter((b) => {
    const r = b.getBoundingClientRect(); return r.width > 0 && r.y > 700;
  }).map((b) => { const r = b.getBoundingClientRect(); return { t: (b.innerText || '').trim().slice(0, 8), disabled: b.disabled === true, box: [Math.round(r.x), Math.round(r.y)] }; }) : [];
  return { t, val: box ? (box.innerText || '').trim() : null, newPanels, toasts, barBtns };
}, { t: tag, nid: MY_NODE, sel: SEL });

const focusNode = async () => {
  await page.evaluate(() => document.body.focus());
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2200);
  await page.evaluate((nid) => document.querySelector(`.react-flow__node[data-id="${nid}"]`)?.click(), MY_NODE);
  await page.waitForTimeout(1800);
  let r = await page.evaluate((sel) => { const b = document.querySelector(sel); const q = b.getBoundingClientRect(); return [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)]; }, SEL);
  if (r[0] < 0 || r[1] < 0 || r[0] + r[2] > 1440 || r[1] + r[3] > 810) {
    const nx = r[0] < 0 ? -r[0] + 40 : (r[0] + r[2] > 1440 ? 1440 - r[0] - r[2] - 40 : 0);
    const ny = r[1] < 0 ? -r[1] + 40 : (r[1] + r[3] > 810 ? 810 - r[1] - r[3] - 40 : 0);
    await page.mouse.move(700, 400);
    await page.mouse.down({ button: 'middle' });
    await page.mouse.move(700 + nx, 400 + ny, { steps: 18 });
    await page.mouse.up({ button: 'middle' });
    await page.waitForTimeout(1500);
    r = await page.evaluate((sel) => { const b = document.querySelector(sel); const q = b.getBoundingClientRect(); return [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)]; }, SEL);
  }
  return r;
};

await focusNode();
out.rect = await page.evaluate((sel) => { const b = document.querySelector(sel); const r = b.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; }, SEL);
out.bal0 = await balance();
out.t0 = await state('t0 空提示词');

// 写内容
await page.mouse.move(out.rect[0] + 60, out.rect[1] + 16, { steps: 6 });
await page.waitForTimeout(300);
await page.mouse.click(out.rect[0] + 60, out.rect[1] + 16);
await page.waitForTimeout(500);
await page.keyboard.type(TEXT, { delay: 20 });
await page.waitForTimeout(1500);
out.t1 = await state('t1 写完内容');
out.bal1 = await balance();

// 找「翻译提示词」= 参数条上**从左数第二枚**（第一枚是模型下拉，最后一枚是生成按钮）
const bar = out.t1.barBtns;
out.bar = bar;
let target = bar.length >= 3 ? bar[bar.length - 2] : (bar.length === 2 ? bar[0] : null);
if (!target) {
  // 退回按坐标：生成按钮左边 80px
  const gen = bar[bar.length - 1];
  target = { box: [gen.box[0] - 80, gen.box[1]], t: '(按坐标推定)' };
}
out.target = target;

await page.mouse.move(target.box[0] + 16, target.box[1] + 16, { steps: 8 });
await page.waitForTimeout(700);
await page.mouse.click(target.box[0] + 16, target.box[1] + 16);
for (const ms of [400, 600, 800, 1000, 1500, 2000, 3000]) {
  await page.waitForTimeout(ms);
  out.timeline.push(await state(`点后累计`));
}
out.bal2 = await balance();
await shot(page, 'M-303-文本节点-点翻译提示词之后.png', { clip: { x: 0, y: 0, width: 1440, height: 810 } });

// 收尾：清空
await page.evaluate(() => document.activeElement?.blur?.());
await page.waitForTimeout(500);
const r2 = await page.evaluate((sel) => { const b = document.querySelector(sel); const q = b.getBoundingClientRect(); return [Math.round(q.x), Math.round(q.y)]; }, SEL);
await page.mouse.move(r2[0] + 60, r2[1] + 16, { steps: 6 });
await page.waitForTimeout(300);
await page.mouse.click(r2[0] + 60, r2[1] + 16);
await page.waitForTimeout(500);
await page.keyboard.press('Meta+a');
await page.waitForTimeout(400);
await page.keyboard.press('Backspace');
await page.waitForTimeout(1400);
out.afterClear = await page.evaluate((sel) => (document.querySelector(sel)?.innerText || '').trim(), SEL);

await writeFile(resolve(HERE, '.evidence/cd10-translate.json'), JSON.stringify(out, null, 2));
console.log(JSON.stringify({ bal0: out.bal0, bal1: out.bal1, bal2: out.bal2, t0: out.t0, t1: out.t1, bar: out.bar, target: out.target, timeline: out.timeline, afterClear: out.afterClear }, null, 2).slice(0, 3500));
await browser.close();
