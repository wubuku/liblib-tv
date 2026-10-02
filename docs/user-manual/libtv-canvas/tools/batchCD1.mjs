// Batch CD-1：把「文本」节点的提示词框**挪进视口**、**写进内容**、**回读自证**。
//
// ⭐ 两个前置坑，都是本手册已经踩过的：
//   ① 提示词框**不是 `textarea`**，是 `contenteditable="true"` 的 `div` ——
//      按 `textarea` 找必然 0 命中（CA④ 记的「提示词框没找到」就是这个原因）。
//   ② 选中节点后那个框在 `y=842`，**视口高只有 810** —— 视口外的东西不能记成「没有」
//      （BI3 的教训）。所以先缩放/平移把它挪进来，再操作。
//
// 这一步**只往框里写字并回读**，⛔ 不点「翻译提示词」（它会外发一次翻译请求）。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const TEXT = 'a cat sitting on a warm windowsill at sunrise';

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

const PROMPT_SEL = '.text-fg-default[contenteditable="true"]';
const promptBox = () => page.evaluate((sel) => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const all = [...document.querySelectorAll(sel)];
  return all.map((el) => {
    const r = el.getBoundingClientRect();
    return { box: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], vis: vis(el), val: (el.innerText || '').trim() };
  });
}, PROMPT_SEL);

// —— 1. 选中文本节点 ——
await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  [...document.querySelectorAll('.react-flow__node')].filter(vis)
    .find((e) => (e.innerText || '').includes('文本节点'))?.click();
});
await page.waitForTimeout(2000);
out.afterSelect = await promptBox();

// —— 2. 缩到 35%，把参数条挪进视口（BI3 用的办法） ——
out.zoomed = await page.evaluate(() => {
  const el = document.querySelector('.react-flow__viewport');
  if (!el) return { ok: false };
  const before = el.style.transform;
  el.style.transform = 'translate(0px, 0px) scale(0.35)';
  return { ok: true, before };
});
await page.waitForTimeout(1400);
out.at35 = await promptBox();

// —— 3. 真点进去 + 真键盘打字（比设 value 更接近真人） ——
const box = out.at35.find((b) => b.vis);
out.pick = box;
if (box) {
  const cx = box.box[0] + Math.min(60, box.box[2] / 2);
  const cy = box.box[1] + box.box[2] * 0 + 14;
  await page.mouse.move(cx, cy, { steps: 8 });
  await page.mouse.click(cx, cy);
  await page.waitForTimeout(600);
  out.focused = await page.evaluate((sel) => {
    const el = document.querySelector(sel);
    return { active: document.activeElement === el, tag: document.activeElement?.tagName, cls: (document.activeElement?.className?.toString?.() || '').slice(0, 50) };
  }, PROMPT_SEL);
  await page.keyboard.type(TEXT, { delay: 30 });
  await page.waitForTimeout(1200);
}
out.afterType = await promptBox();
// ⭐ 阳性对照：打字到底进没进框
out.typedOk = (out.afterType.find((b) => b.vis)?.val || '').includes(TEXT);

// —— 4. 参数条上「翻译提示词」那枚按钮现在什么状态 ——
out.translateBtn = await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const all = [...document.querySelectorAll('button,[role="button"]')].filter(vis);
  const hit = all.filter((b) => b.querySelector('svg'));
  return all.map((b) => {
    const r = b.getBoundingClientRect();
    return { aria: b.getAttribute('aria-label'), t: (b.innerText || '').trim().slice(0, 12),
      disabled: b.disabled === true, box: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
  }).filter((b) => b.box[1] < 400);
});

await shot(page, 'M-300-文本节点-提示词框写进内容之后.png', { clip: { x: 0, y: 0, width: 1440, height: 810 } });
await writeFile(resolve(HERE, '.evidence/cd1-type.json'), JSON.stringify(out, null, 2));
console.log(JSON.stringify({ afterSelect: out.afterSelect, at35: out.at35, focused: out.focused, afterType: out.afterType, typedOk: out.typedOk, translateBtn: out.translateBtn?.slice(0, 14) }, null, 2).slice(0, 3500));
await browser.close();
