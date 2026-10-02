// Batch CD-8：从**提示词框往上找参数条容器**，只认它里面的按钮 ——
//   CD-7 的悬停扫的是全页按钮，扫到的是底栏和画布上的建议词，**参数条那几枚根本没进筛子**。
// ⭐ 「我扫了一堆按钮都没找到」和「那枚按钮不存在」不是一回事 —— 先把范围圈对。
//
// 找到之后：实名 → 点它 → 采样「提示词内容 / 弹层 / 积分余额」的前后变化。
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
const out = {};

await open(page, URL_);
await closePromos(page);
await page.evaluate(async () => {
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  for (let i = 0; i < 6; i += 1) {
    const hit = [...document.querySelectorAll('button,[role="button"]')].find((b) => (b.innerText || '').trim() === '知道了');
    if (hit) { hit.click(); await sleep(500); }
    if (!(document.body.innerText || '').includes('已升级为 TV Director')) return;
  }
});
await page.waitForTimeout(800);
await page.evaluate(() => document.body.focus());
await page.keyboard.press('Meta+0');
await page.waitForTimeout(2200);
await page.evaluate((nid) => document.querySelector(`.react-flow__node[data-id="${nid}"]`)?.click(), MY_NODE);
await page.waitForTimeout(1700);

// 平移到视口内
let rect = await page.evaluate((sel) => {
  const b = document.querySelector(sel);
  if (!b) return null;
  const r = b.getBoundingClientRect();
  return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)];
}, SEL);
if (rect && (rect[0] < 0 || rect[1] < 0 || rect[0] + rect[2] > 1440 || rect[1] + rect[3] > 810)) {
  const needX = rect[0] < 0 ? -rect[0] + 40 : (rect[0] + rect[2] > 1440 ? 1440 - rect[0] - rect[2] - 40 : 0);
  const needY = rect[1] < 0 ? -rect[1] + 40 : (rect[1] + rect[3] > 810 ? 810 - rect[1] - rect[3] - 40 : 0);
  await page.mouse.move(700, 400);
  await page.mouse.down({ button: 'middle' });
  await page.mouse.move(700 + needX, 400 + needY, { steps: 18 });
  await page.mouse.up({ button: 'middle' });
  await page.waitForTimeout(1500);
  rect = await page.evaluate((sel) => {
    const b = document.querySelector(sel);
    const r = b.getBoundingClientRect();
    return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)];
  }, SEL);
}
out.rect = rect;

// 写字
await page.mouse.move(rect[0] + 60, rect[1] + 16, { steps: 8 });
await page.waitForTimeout(300);
await page.mouse.click(rect[0] + 60, rect[1] + 16);
await page.waitForTimeout(600);
await page.keyboard.type(TEXT, { delay: 20 });
await page.waitForTimeout(1500);
out.typed = await page.evaluate((sel) => (document.querySelector(sel)?.innerText || '').trim(), SEL);

// ⭐ 参数条容器 = 提示词框的祖先里，**横向包住整条参数条**的那一层
out.bar = await page.evaluate((sel) => {
  const box = document.querySelector(sel);
  if (!box) return { err: 'no box' };
  let bar = box;
  for (let i = 0; i < 8 && bar.parentElement; i += 1) {
    const cand = bar.parentElement;
    const btns = cand.querySelectorAll('button,[role="button"]').length;
    if (btns >= 2) { bar = cand; break; }
    bar = cand;
  }
  const r = bar.getBoundingClientRect();
  return {
    barBox: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    cls: (bar.className?.toString?.() || '').slice(0, 80),
    buttons: [...bar.querySelectorAll('button,[role="button"]')].map((b) => {
      const br = b.getBoundingClientRect();
      return { aria: b.getAttribute('aria-label'), t: (b.innerText || '').trim().slice(0, 14),
        disabled: b.disabled === true, hasSvg: !!b.querySelector('svg'),
        box: [Math.round(br.x), Math.round(br.y), Math.round(br.width), Math.round(br.height)] };
    }),
  };
}, SEL);

// 悬停逐枚实名
out.names = [];
for (const b of (out.bar?.buttons || [])) {
  await page.mouse.move(b.box[0] + b.box[2] / 2, b.box[1] + b.box[3] / 2, { steps: 8 });
  await page.waitForTimeout(1000);
  const tip = await page.evaluate(() => {
    const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
    return [...document.querySelectorAll('[role="tooltip"],.mantine-Tooltip-tooltip')].filter(vis)
      .map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim()).filter(Boolean);
  });
  out.names.push({ aria: b.aria, t: b.t, box: b.box, tip });
}
await shot(page, 'M-302-文本节点-参数条逐枚实名.png', { clip: { x: 0, y: Math.max(0, (out.rect?.[1] ?? 600) - 190), width: 1000, height: 400 } });
await writeFile(resolve(HERE, '.evidence/cd8-bar.json'), JSON.stringify(out, null, 2));
console.log(JSON.stringify({ rect: out.rect, typed: out.typed, barBox: out.bar?.barBox, names: out.names }, null, 2).slice(0, 3000));
await browser.close();
