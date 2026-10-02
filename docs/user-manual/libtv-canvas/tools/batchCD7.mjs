// Batch CD-7：正题 —— **有内容时点「翻译提示词」会发生什么**（CA④ 挂了两批的 📖）。
//
// 这一步会**真的发一次翻译请求**。为什么可以做：
//   · 内容是本手册自己编的一句无害英文，不是用户的任何数据；
//   · 它是节点参数条上的**辅助按钮**，不在「需用户授权」清单里
//     （真实生成 / TV Director 派发 / 发布分享 / 签署承诺书 / 充值）；
//   · ⭐ **积分余额前后各读一次** —— 万一它要扣分，如实报告，不瞒。
//
// 收尾：翻译结果会写进提示词框，**用完清空**（CD-6 已验证「清空会落盘」）。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const MY_NODE = 't-2AK3Ukyxj3';           // CA 那轮补建的节点，**本手册自己造的**
const TEXT = 'a cat sitting on a warm windowsill at sunrise';
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

const balance = () => page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const cand = [...document.querySelectorAll('*')].filter((e) => {
    if (!vis(e) || e.children.length) return false;
    return /^\s*\d+\s*$/.test((e.innerText || '').trim());
  });
  // 找紧挨着闪电/积分图标的数字
  for (const e of cand) {
    const p = e.parentElement;
    if (p && /积分|credit|balance/i.test(p.getAttribute('aria-label') || p.className?.toString?.() || '')) {
      return { n: Number((e.innerText || '').trim()), where: 'near-credit-icon' };
    }
  }
  const top = [...document.querySelectorAll('header *,nav *')].filter(vis)
    .map((e) => (e.innerText || '').trim()).filter((t) => /^\d{1,4}$/.test(t));
  return { n: top.length ? Number(top[top.length - 1]) : null, where: 'header-scan', top };
});

const readPrompt = (id) => page.evaluate(({ nid, sel }) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!n) return { found: false };
  const b = [...n.querySelectorAll(sel)][0];
  if (!b) return { found: true, box: false };
  const r = b.getBoundingClientRect();
  return { found: true, box: true, val: (b.innerText || '').trim(),
    rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    inViewport: r.x >= 0 && r.y >= 0 && r.right <= 1440 && r.bottom <= 810 };
}, { nid: MY_NODE, sel: SEL });

const selectNode = async () => {
  await page.evaluate((nid) => document.querySelector(`.react-flow__node[data-id="${nid}"]`)?.click(), MY_NODE);
  await page.waitForTimeout(1600);
};

const panIntoView = async () => {
  const p = await readPrompt(MY_NODE);
  if (!p.rect || p.inViewport) return p;
  const [x, y, w, h] = p.rect;
  const needX = x < 0 ? -x + 40 : (x + w > 1440 ? 1440 - (x + w) - 40 : 0);
  const needY = y < 0 ? -y + 40 : (y + h > 810 ? 810 - (y + h) - 40 : 0);
  await page.mouse.move(700, 400);
  await page.mouse.down({ button: 'middle' });
  await page.mouse.move(700 + needX, 400 + needY, { steps: 18 });
  await page.mouse.up({ button: 'middle' });
  await page.waitForTimeout(1500);
  return readPrompt(MY_NODE);
};

// —— 0. 找不到「翻译提示词」时，用**悬停读 Tooltip** 实名（本手册的老规矩） ——
await selectNode();
out.bar0 = await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  return [...document.querySelectorAll('button,[role="button"]')].filter(vis).map((b) => {
    const r = b.getBoundingClientRect();
    return { aria: b.getAttribute('aria-label'), t: (b.innerText || '').trim().slice(0, 10), disabled: b.disabled === true,
      hasSvg: !!b.querySelector('svg'), box: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
  }).filter((b) => b.box[1] > 500 && b.box[1] < 810 && b.box[0] > -50 && b.box[0] < 800);
});

out.p0 = await panIntoView();
out.balance0 = await balance();

// —— 1. 写字 ——
if (out.p0.rect) {
  const [x, y] = out.p0.rect;
  await page.mouse.move(x + 60, y + 16, { steps: 8 });
  await page.waitForTimeout(400);
  await page.mouse.click(x + 60, y + 16);
  await page.waitForTimeout(600);
  out.focusOk = await page.evaluate((sel) => document.activeElement === document.querySelector(sel), SEL);
  await page.keyboard.type(TEXT, { delay: 20 });
  await page.waitForTimeout(1500);
}
out.p1_afterType = await readPrompt(MY_NODE);

// —— 2. 悬停参数条上那枚无名按钮，认它是不是「翻译提示词」 ——
out.hoverNames = [];
for (const b of out.bar0.filter((x) => x.hasSvg)) {
  if (b.box[1] < 0) continue;
  await page.mouse.move(b.box[0] + b.box[2] / 2, b.box[1] + b.box[3] / 2, { steps: 8 });
  await page.waitForTimeout(1100);
  const tip = await page.evaluate(() => {
    const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
    const t = [...document.querySelectorAll('[role="tooltip"],.mantine-Tooltip-tooltip')].filter(vis)
      .map((e) => (e.innerText || '').trim()).filter(Boolean);
    return t;
  });
  out.hoverNames.push({ aria: b.aria, box: b.box, tip });
}

await shot(page, 'M-302-文本节点-翻译提示词按钮.png', { clip: { x: 0, y: 500, width: 900, height: 310 } });
await writeFile(resolve(HERE, '.evidence/cd7-before.json'), JSON.stringify(out, null, 2));
console.log(JSON.stringify({ bar0: out.bar0, p0: out.p0, balance0: out.balance0, focusOk: out.focusOk, p1: out.p1_afterType, hoverNames: out.hoverNames }, null, 2).slice(0, 3200));
await browser.close();
