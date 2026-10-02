// Batch CD-11：⭐ 给「有内容时点『翻译提示词』没反应」配**阳性对照**。
//
// 问题：CD-10 读到「点了 8 次采样什么都没变」。但**「没反应」有两种**：
//   ① 真的没反应；② **根本没点中**（点偏了、被挡住、坐标算错）。
// 两者长得一模一样 —— 与 §58 同源。
//
// 阳性对照设计：⭐ **用完全相同的坐标**，只把「提示词有内容 / 没内容」这一个变量变。
//   · 有内容 → 已知读数：什么都没变（CD-10）
//   · 没内容 → 已知它**会**弹顶部提示「提示词为空，请输入内容后点击」（BI5 验过）
// 于是：**同一坐标能弹出那条提示** ⇒ 坐标没问题、点击确实落到了
//        ⇒ 「有内容时没反应」就是真的没反应。
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
    const hit = [...document.querySelectorAll('button, [role="button"]')].find((b) => (b.innerText || '').trim() === '知道了');
    if (hit) { hit.click(); await sleep(500); }
    if (!(document.body.innerText || '').includes('已升级为 TV Director')) return;
  }
});
await page.waitForTimeout(800);

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
const prompts = () => page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  return [...document.querySelectorAll('[role="alert"],[class*="toast"],[class*="Toast"],[class*="notification"],[class*="MantineNotification"]')]
    .filter(vis).map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim()).filter(Boolean);
});
const barBtns = () => page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!n) return [];
  return [...n.querySelectorAll('button,[role="button"]')].filter((b) => { const r = b.getBoundingClientRect(); return r.width > 0 && r.y > 700; })
    .map((b) => { const r = b.getBoundingClientRect(); return { t: (b.innerText || '').trim().slice(0, 8), disabled: b.disabled === true, box: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; });
}, MY_NODE);

// ——— 步骤 A：清空提示词 → 点同一坐标 ———
out.rect = await setup();
out.barA = await barBtns();
out.btn = out.barA.length >= 3 ? out.barA[out.barA.length - 2] : out.barA[0];
out.promptA_before = await page.evaluate((sel) => (document.querySelector(sel)?.innerText || '').trim(), SEL);

const clickBtn = async () => {
  const [x, y, w, h] = out.btn.box;
  await page.mouse.move(x + w / 2, y + h / 2, { steps: 8 });
  await page.waitForTimeout(600);
  await page.mouse.click(x + w / 2, y + h / 2);
};

await clickBtn();
out.promptsA = [];
for (const ms of [300, 500, 700, 1000, 1500]) { await page.waitForTimeout(ms); out.promptsA.push(await prompts()); }
out.peakA = out.promptsA.find((p) => p.length) || [];
await shot(page, 'M-303-翻译提示词-空提示词时会弹提示.png', { clip: { x: 0, y: 0, width: 1440, height: 810 } });

// ——— 步骤 B：写内容 → 点**同一坐标** ———
const r = out.rect;
await page.mouse.move(r[0] + 60, r[1] + 16, { steps: 6 });
await page.waitForTimeout(300);
await page.mouse.click(r[0] + 60, r[1] + 16);
await page.waitForTimeout(500);
await page.keyboard.type(TEXT, { delay: 20 });
await page.waitForTimeout(1500);
out.promptB_before = await page.evaluate((sel) => (document.querySelector(sel)?.innerText || '').trim(), SEL);
out.barB = await barBtns();
out.sameBtnBox = JSON.stringify(out.barB[out.barB.length - 2]?.box) === JSON.stringify(out.btn.box);

await clickBtn();
out.promptsB = [];
for (const ms of [300, 500, 700, 1000, 1500, 2000, 2500]) { await page.waitForTimeout(ms); out.promptsB.push(await prompts()); }
out.peakB = out.promptsB.find((p) => p.length) || [];
out.valAfter = await page.evaluate((sel) => (document.querySelector(sel)?.innerText || '').trim(), SEL);
await shot(page, 'M-304-翻译提示词-有内容时不弹提示.png', { clip: { x: 0, y: 0, width: 1440, height: 810 } });

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

out.controlPassed = out.peakA.length > 0;
out.verdict = !out.controlPassed
  ? '⛔ 阳性对照没通过 —— 「有内容时没反应」这个读数**不成立**，不能下结论'
  : (out.peakB.length === 0 ? '✅ 阳性对照通过 + 有内容时确实什么都没弹 —— 结论成立' : '✅ 有内容时也弹了东西：' + JSON.stringify(out.peakB));
await writeFile(resolve(HERE, '.evidence/cd11-control.json'), JSON.stringify(out, null, 2));
console.log(JSON.stringify({ rect: out.rect, btn: out.btn, sameBtnBox: out.sameBtnBox, promptA: out.promptA_before, peakA: out.peakA, promptB: out.promptB_before, peakB: out.peakB, valAfter: out.valAfter, afterClear: out.afterClear, controlPassed: out.controlPassed, verdict: out.verdict }, null, 2).slice(0, 2500));
await browser.close();
