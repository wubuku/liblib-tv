// Batch CD-5：CD-4 一个都没查到，因为**提示词框只在节点被选中时才渲染**
//   （CD-4 直接读，当然读到 0 个 —— 又是一次「判据挡住了」的读数）。
// 这一步：⌘0 收全画布 → 逐个文本节点**点开** → 读它的提示词 → 有我那段就清空。
// ⭐ 清空后**刷新再读一遍**，确认是落盘清掉的、不是只在内存里看着干净。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const MY_MARK = 'windowsill';
const SEL = '.text-fg-default[contenteditable="true"]';

const { browser, page } = await launch();
const out = { steps: [] };

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

const readAll = () => page.evaluate((sel) => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  return [...document.querySelectorAll('.react-flow__node')].filter(vis).map((n) => {
    const label = (n.innerText || '').trim();
    const boxes = [...n.querySelectorAll(sel)].map((el) => {
      const r = el.getBoundingClientRect();
      return { box: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        inViewport: r.x >= 0 && r.y >= 0 && r.right <= 1440 && r.bottom <= 810,
        val: (el.innerText || '').trim().slice(0, 140) };
    });
    return { id: n.getAttribute('data-id'), isText: label.includes('文本节点'), selected: n.className.includes('selected'), boxes };
  }).filter((x) => x.isText);
}, SEL);

out.textNodes = await readAll();
const KNOWN = ['t-2AK3Ukyxj3', 't-UtVx3lZmrV'];

for (const id of KNOWN) {
  const step = { id };
  const present = out.textNodes.some((t) => t.id === id);
  step.inViewportNow = present;
  if (!present) { step.note = '不在视口（⌘0 之后仍不可见）'; out.steps.push(step); continue; }

  await page.evaluate((nid) => document.querySelector(`.react-flow__node[data-id="${nid}"]`)?.click(), id);
  await page.waitForTimeout(1800);
  const after = (await readAll()).find((t) => t.id === id);
  step.boxes = after?.boxes;
  const b = (after?.boxes || [])[0];
  step.val = b?.val ?? null;
  step.dirty = !!(b?.val || '').includes(MY_MARK);
  if (!step.dirty) { step.note = '本来是空的'; out.steps.push(step); continue; }

  if (b && !b.inViewport) {
    const needX = b.box[0] < 0 ? -b.box[0] + 40 : (b.box[0] + b.box[2] > 1440 ? 1440 - (b.box[0] + b.box[2]) - 40 : 0);
    const needY = b.box[1] < 0 ? -b.box[1] + 40 : (b.box[1] + b.box[3] > 810 ? 810 - (b.box[1] + b.box[3]) - 40 : 0);
    await page.mouse.move(700, 400);
    await page.mouse.down({ button: 'middle' });
    await page.mouse.move(700 + needX, 400 + needY, { steps: 18 });
    await page.mouse.up({ button: 'middle' });
    await page.waitForTimeout(1400);
  }
  const b2 = (await readAll()).find((t) => t.id === id)?.boxes?.[0];
  step.box2 = b2?.box;
  if (b2) {
    await page.mouse.move(b2.box[0] + 60, b2.box[1] + 16, { steps: 8 });
    await page.waitForTimeout(400);
    await page.mouse.click(b2.box[0] + 60, b2.box[1] + 16);
    await page.waitForTimeout(700);
    step.focusOk = await page.evaluate((sel) => document.activeElement === document.querySelector(sel), SEL);
    if (step.focusOk) {
      await page.keyboard.press('Meta+a');
      await page.waitForTimeout(500);
      await page.keyboard.press('Backspace');
      await page.waitForTimeout(1400);
      step.valAfterClear = (await readAll()).find((t) => t.id === id)?.boxes?.[0]?.val ?? null;
    }
  }
  out.steps.push(step);
}

// ⭐ 刷新复核
await open(page, URL_);
await closePromos(page);
await page.evaluate(() => document.body.focus());
await page.keyboard.press('Meta+0');
await page.waitForTimeout(2200);
out.afterReload = await readAll();
for (const id of KNOWN) {
  await page.evaluate((nid) => document.querySelector(`.react-flow__node[data-id="${nid}"]`)?.click(), id);
  await page.waitForTimeout(1600);
  const t = (await readAll()).find((x) => x.id === id);
  out[`recheck_${id}`] = t?.boxes?.[0]?.val ?? null;
}
out.allClean = Object.values(out).filter((v) => typeof v === 'string').every((v) => !v.includes(MY_MARK));
await shot(page, 'M-301-文本节点-提示词已清空.png', { clip: { x: 0, y: 0, width: 1440, height: 810 } });
await writeFile(resolve(HERE, '.evidence/cd5-restore.json'), JSON.stringify(out, null, 2));
console.log(JSON.stringify({ textNodes: out.textNodes, steps: out.steps, recheck_t2: out.recheck_t_2AK3Ukyxj3, recheck_tU: out.recheck_t_UtVx3lZmrV, allClean: out.allClean }, null, 2).slice(0, 3000));
await browser.close();
