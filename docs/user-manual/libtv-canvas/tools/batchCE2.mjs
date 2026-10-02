// Batch CE-2：拍一张**看得见结果**的图 —— 上一张里提示词框在视口外，什么也没证明。
// 这一步：选节点 → 中键平移把框挪进画面 → 写英文 → `el.click()` 翻译 → 等结果 → 拍框 → 清空。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const MY_NODE = 't-2AK3Ukyxj3';
const TEXT = 'a cat sitting on a warm windowsill at sunrise';
const SEL = '.text-fg-default[contenteditable="true"]';
const PRE = 'M15.52 7.2c.16 0 .31.1.37.26l3.8 10';

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

const rectOf = () => page.evaluate((sel) => {
  const b = document.querySelector(sel);
  if (!b) return null;
  const r = b.getBoundingClientRect();
  return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)];
}, SEL);
const promptVal = () => page.evaluate((sel) => (document.querySelector(sel)?.innerText || '').trim(), SEL);
const clickTranslate = () => page.evaluate((pre) => {
  const n = document.querySelector('.react-flow__node.selected') || document.querySelector('.react-flow__node');
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  for (const b of [...n.querySelectorAll('button,[role="button"]')].filter(vis)) {
    const svg = b.querySelector('svg');
    const p = svg ? [...svg.querySelectorAll('path')].map((x) => x.getAttribute('d')).join(' ') : '';
    if (p.includes(pre)) { b.click(); return true; }
  }
  return false;
}, PRE);

await page.evaluate((nid) => document.querySelector(`.react-flow__node[data-id="${nid}"]`)?.click(), MY_NODE);
await page.waitForTimeout(1800);

// ⭐ 平移：把「框 + 它下面的参数条」一起挪进画面
let rect = await rectOf();
out.rect0 = rect;
for (let i = 0; i < 6; i += 1) {
  if (!rect) break;
  const bottom = rect[1] + rect[3] + 70;     // 还要给下面的参数条留 70px
  if (rect[0] >= 0 && rect[1] >= 40 && rect[0] + rect[2] <= 1440 && bottom <= 810) break;
  const nx = rect[0] < 0 ? -rect[0] + 40 : (rect[0] + rect[2] > 1440 ? 1440 - rect[0] - rect[2] - 40 : 0);
  const ny = rect[1] < 40 ? 40 - rect[1] : (bottom > 810 ? 810 - bottom : 0);
  await page.mouse.move(700, 300);
  await page.mouse.down({ button: 'middle' });
  await page.mouse.move(700 + nx, 300 + ny, { steps: 18 });
  await page.mouse.up({ button: 'middle' });
  await page.waitForTimeout(1300);
  rect = await rectOf();
}
out.rect = rect;
out.inView = rect ? (rect[0] >= 0 && rect[1] >= 0 && rect[0] + rect[2] <= 1440 && rect[1] + rect[3] <= 810) : false;

// 写英文
await page.mouse.move(rect[0] + 60, rect[1] + 16, { steps: 6 });
await page.waitForTimeout(300);
await page.mouse.click(rect[0] + 60, rect[1] + 16);
await page.waitForTimeout(500);
await page.keyboard.type(TEXT, { delay: 18 });
await page.waitForTimeout(1500);
out.before = await promptVal();
await shot(page, 'M-305-翻译提示词-点之前是英文.png', { clip: { x: 0, y: Math.max(0, rect[1] - 210), width: 900, height: 420 } });

// 点翻译
out.clicked = await clickTranslate();
for (let i = 0; i < 24; i += 1) {
  await page.waitForTimeout(300);
  const v = await promptVal();
  if (v && v !== out.before) { out.after = v; break; }
}
out.after = out.after || (await promptVal());
const r2 = await rectOf();
await shot(page, 'M-306-翻译提示词-点之后变成中文.png', { clip: { x: 0, y: Math.max(0, (r2?.[1] ?? rect[1]) - 210), width: 900, height: 420 } });

// 清空
await page.mouse.move(r2[0] + 60, r2[1] + 16, { steps: 6 });
await page.waitForTimeout(300);
await page.mouse.click(r2[0] + 60, r2[1] + 16);
await page.waitForTimeout(500);
await page.keyboard.press('Meta+a');
await page.waitForTimeout(400);
await page.keyboard.press('Backspace');
await page.waitForTimeout(1400);
out.afterClear = await promptVal();
out.changed = out.after !== out.before;
out.turnedChinese = /[一-鿿]/.test(out.after || '');
await writeFile(resolve(HERE, '.evidence/ce2-shot.json'), JSON.stringify(out, null, 2));
console.log(JSON.stringify({ rect0: out.rect0, rect: out.rect, inView: out.inView, before: out.before, clicked: out.clicked, after: out.after, changed: out.changed, turnedChinese: out.turnedChinese, afterClear: out.afterClear }, null, 2));
await browser.close();
