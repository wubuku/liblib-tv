// Batch CD-3：框在 `[-14, 803, 634, 80]` —— 左边出界 14px、下边出界 73px。
// 缩放菜单里也**没有 35% 这一档**（只有 缩放至50% / 100% / 800%），
// 所以 BI3 当年说的「缩到 35%」不是从菜单里选的。
// 这一步改用本手册验过 **1:1 严格**的**中键拖拽**把画布往下平移，把它挪进视口。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const TEXT = 'a cat sitting on a warm windowsill at sunrise';
const SEL = '.text-fg-default[contenteditable="true"]';

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

const boxInfo = () => page.evaluate((sel) => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  return [...document.querySelectorAll(sel)].filter(vis).map((el) => {
    const r = el.getBoundingClientRect();
    return { box: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      inViewport: r.x >= 0 && r.y >= 0 && r.right <= 1440 && r.bottom <= 810,
      val: (el.innerText || '').trim().slice(0, 80) };
  });
}, SEL);

await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  [...document.querySelectorAll('.react-flow__node')].filter(vis).find((e) => (e.innerText || '').includes('文本节点'))?.click();
});
await page.waitForTimeout(1800);
out.t1 = await boxInfo();

// ⭐ 中键拖拽平移（AJ 验过 1:1 严格）：往下 +100、往右 +140
out.pan = await page.evaluate(() => {
  const vp = document.querySelector('.react-flow__viewport');
  return vp ? { t: vp.style.transform } : { err: 'no viewport' };
});
await page.mouse.move(900, 400);
await page.mouse.down({ button: 'middle' });
await page.mouse.move(900 + 140, 400 + 110, { steps: 20 });
await page.mouse.up({ button: 'middle' });
await page.waitForTimeout(1500);
out.t2_afterPan = await boxInfo();
out.panAfter = await page.evaluate(() => document.querySelector('.react-flow__viewport')?.style.transform || null);

// 还出界就再拖一次（方向由读数决定，不预设）
for (let i = 0; i < 3; i += 1) {
  const b = (out.t2_afterPan || [])[0];
  if (b?.inViewport) break;
  const needX = b ? (b.box[0] < 0 ? -b.box[0] + 40 : (b.box[0] + b.box[2] > 1440 ? 1440 - (b.box[0] + b.box[2]) - 40 : 0)) : 0;
  const needY = b ? (b.box[1] < 0 ? -b.box[1] + 40 : (b.box[1] + b.box[3] > 810 ? 810 - (b.box[1] + b.box[3]) - 40 : 0)) : 0;
  out[`panStep${i}`] = { needX, needY };
  await page.mouse.move(900, 400);
  await page.mouse.down({ button: 'middle' });
  await page.mouse.move(900 + needX, 400 + needY, { steps: 18 });
  await page.mouse.up({ button: 'middle' });
  await page.waitForTimeout(1400);
  out.t2_afterPan = await boxInfo();
}
out.finalBox = (out.t2_afterPan || [])[0];
out.inView = !!out.finalBox?.inViewport;

if (out.inView) {
  const cx = out.finalBox.box[0] + 50;
  const cy = out.finalBox.box[1] + 16;
  await page.mouse.move(cx, cy, { steps: 8 });
  await page.waitForTimeout(400);
  await page.mouse.click(cx, cy);
  await page.waitForTimeout(700);
  out.focus = await page.evaluate((sel) => {
    const a = document.activeElement;
    return { isIt: a === document.querySelector(sel), tag: a?.tagName, cls: (a?.className?.toString?.() || '').slice(0, 60) };
  }, SEL);
  // ⭐ 阳性对照：先打一个字符当场回读
  await page.keyboard.type('A', { delay: 60 });
  await page.waitForTimeout(500);
  out.probe1 = (await boxInfo())[0];
  out.probeOk = (out.probe1?.val || '').includes('A');
  if (out.probeOk) {
    await page.keyboard.press('Backspace');
    await page.waitForTimeout(300);
    await page.keyboard.type(TEXT, { delay: 20 });
    await page.waitForTimeout(1300);
  }
}
out.final = await boxInfo();
out.typedOk = (out.final[0]?.val || '').includes(TEXT);

// 参数条上那几枚按钮此刻的状态
out.bar = await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  return [...document.querySelectorAll('button,[role="button"]')].filter(vis).map((x) => {
    const r = x.getBoundingClientRect();
    return { aria: x.getAttribute('aria-label'), t: (x.innerText || '').trim().slice(0, 12), disabled: x.disabled === true,
      box: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
  }).filter((x) => x.box[0] > -60 && x.box[0] < 700 && x.box[1] > 600);
});

await shot(page, 'M-300-文本节点-提示词框写进内容之后.png', { clip: { x: 0, y: 0, width: 1440, height: 810 } });
await writeFile(resolve(HERE, '.evidence/cd3-type.json'), JSON.stringify(out, null, 2));
console.log(JSON.stringify({ t1: out.t1, panAfter: out.panAfter, panStep0: out.panStep0, panStep1: out.panStep1, finalBox: out.finalBox, inView: out.inView, focus: out.focus, probe1: out.probe1, probeOk: out.probeOk, final: out.final, typedOk: out.typedOk, bar: out.bar }, null, 2).slice(0, 3200));
await browser.close();
