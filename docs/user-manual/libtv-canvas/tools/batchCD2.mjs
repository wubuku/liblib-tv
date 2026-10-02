// Batch CD-2：CD-1 的「打不进字」又是**探针问题**——框在 `x=-683`，**根本没点中**
//   （`document.activeElement` 全程是 `BODY`）。**「没反应」不等于「不能」，先证明自己点中了。**
// 这一步：用站点自带的「适合屏幕」(`⌘0`) 把整张画布收进视口，
//   然后**先自证框的四条边都在视口内**，再点进去打字。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { fitView } from './canvas-ops.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const TEXT = 'a cat sitting on a warm windowsill at sunrise';
const SEL = '.text-fg-default[contenteditable="true"]';
const VP = { w: 1440, h: 810 };

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

const boxInfo = () => page.evaluate(({ sel, vw, vh }) => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  return [...document.querySelectorAll(sel)].filter(vis).map((el) => {
    const r = el.getBoundingClientRect();
    return { box: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      inViewport: r.x >= 0 && r.y >= 0 && r.right <= vw && r.bottom <= vh,
      val: (el.innerText || '').trim().slice(0, 60) };
  });
}, { sel: SEL, vw: VP.w, vh: VP.h });

// 1. 选中文本节点
await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  [...document.querySelectorAll('.react-flow__node')].filter(vis).find((e) => (e.innerText || '').includes('文本节点'))?.click();
});
await page.waitForTimeout(1800);
out.t1_afterSelect = await boxInfo();

// 2. ⌘0 适合屏幕
await page.evaluate(() => document.body.focus());
await page.keyboard.press('Meta+0');
await page.waitForTimeout(2200);
out.t2_afterFit = await boxInfo();

// 3. 还不在视口就再缩一档（站点自己的缩放菜单，35%）
if (!out.t2_afterFit.some((b) => b.inViewport)) {
  out.zoomMenu = await page.evaluate(() => {
    const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
    const b = [...document.querySelectorAll('button,[role="button"]')].filter(vis)
      .find((x) => /缩放|zoom/i.test((x.getAttribute('aria-label') || '') + (x.innerText || '')));
    if (!b) return { ok: false };
    b.click();
    return { ok: true };
  });
  await page.waitForTimeout(900);
  out.zoomOptions = await page.evaluate(() => [...document.querySelectorAll('.mantine-Menu-item,[role="menuitem"]')]
    .filter((el) => { const r = el.getBoundingClientRect(); return r.width > 0; })
    .map((el) => (el.innerText || '').trim()).filter(Boolean));
  const hit35 = await page.evaluate(() => {
    const it = [...document.querySelectorAll('.mantine-Menu-item,[role="menuitem"]')]
      .find((el) => (el.innerText || '').trim() === '35%');
    if (!it) return false;
    it.click();
    return true;
  });
  out.clicked35 = hit35;
  await page.waitForTimeout(2000);
  out.t3_after35 = await boxInfo();
}
const target = [...(out.t3_after35 || out.t2_afterFit || [])].find((b) => b.inViewport);
out.target = target;

if (target) {
  const cx = target.box[0] + 40;
  const cy = target.box[1] + 16;
  await page.mouse.move(cx, cy, { steps: 8 });
  await page.waitForTimeout(400);
  await page.mouse.click(cx, cy);
  await page.waitForTimeout(700);
  out.focus = await page.evaluate((sel) => {
    const a = document.activeElement;
    return { isIt: a === document.querySelector(sel), tag: a?.tagName, cls: (a?.className?.toString?.() || '').slice(0, 60) };
  }, SEL);
  // ⭐ 阳性对照：先打一个字符，**当场回读**，确认键盘真的进了框
  await page.keyboard.type('A', { delay: 60 });
  await page.waitForTimeout(600);
  out.probe1 = (await boxInfo())[0];
  await page.keyboard.type(TEXT, { delay: 25 });
  await page.waitForTimeout(1200);
}
out.final = await boxInfo();
out.typedOk = (out.final[0]?.val || '').includes(TEXT);
await shot(page, 'M-300-文本节点-提示词框写进内容之后.png', { clip: { x: 0, y: 0, width: 1440, height: 810 } });
await writeFile(resolve(HERE, '.evidence/cd2-type.json'), JSON.stringify(out, null, 2));
console.log(JSON.stringify({ t1: out.t1_afterSelect, t2: out.t2_afterFit, zoomOptions: out.zoomOptions, t3: out.t3_after35, target: out.target, focus: out.focus, probe1: out.probe1, final: out.final, typedOk: out.typedOk }, null, 2).slice(0, 3000));
await browser.close();
