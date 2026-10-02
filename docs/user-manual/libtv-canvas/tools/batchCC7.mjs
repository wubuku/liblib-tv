// Batch CC-7：CC-2 与 CC-4 对「点完卡片之后广场还开不开」读数打架
//   （CC-2 说还开着，CC-4 说关上了）。**读数打架不能靠挑一个信，要靠采样定死。**
// 这一步：点一次，然后每 400ms 采一次「广场开没开 / 适配模型面板在不在 / 抽屉里的节点数」，
//   一直采 4.5 秒。
// ⭐ 节点数用**抽屉的「共 N 节点」**当基准 —— `.react-flow__node` 只渲染视口内的节点，
//   落点在视口外的新节点根本不在那个列表里（CC-2 就是被它骗的）。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;

const { browser, page } = await launch();
await open(page, URL_);
await closePromos(page);
const out = { timeline: [] };

const probe = (tag) => page.evaluate((t) => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const m = [...document.querySelectorAll('.mantine-Modal-content')].filter(vis)
    .find((el) => (el.innerText || '').includes('特效广场'));
  const drawer = [...document.querySelectorAll('.mantine-Drawer-content')].filter(vis)
    .find((el) => [...el.querySelectorAll('button')].some((b) => ['画布', '资产'].includes((b.innerText || '').trim())));
  const dtxt = drawer ? (drawer.innerText || '').replace(/\s+/g, ' ') : '';
  const c = dtxt.match(/共 (\d+) 节点/);
  const toasts = [...document.querySelectorAll('[class*="toast"],[class*="Toast"],[role="alert"],[class*="notification"]')]
    .filter(vis).map((t) => (t.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 60)).filter(Boolean);
  return {
    t,
    plazaOpen: !!m,
    modelPanel: m ? (m.innerText || '').includes('全部适配模型') : null,
    modelText: m && (m.innerText || '').includes('全部适配模型')
      ? (m.innerText || '').replace(/\s+/g, ' ').slice((m.innerText || '').indexOf('全部适配模型'), (m.innerText || '').indexOf('全部适配模型') + 46) : null,
    cardCount: m ? [...m.querySelectorAll('div')].filter((el) => { const cc = el.className?.toString?.() || ''; return /rounded-xl/.test(cc) && /flex-col/.test(cc) && /p-2/.test(cc); }).length : null,
    drawerCount: c ? Number(c[1]) : null,
    newNodeNames: [...new Set((dtxt.match(/素材-特效-[^\s共]+/g) || []))],
    toasts,
  };
}, tag);

await page.evaluate(async () => {
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  for (let i = 0; i < 6; i += 1) {
    const hit = [...document.querySelectorAll('button, [role="button"]')].find((b) => (b.innerText || '').trim() === '知道了');
    if (hit) { hit.click(); await sleep(500); }
    if (!(document.body.innerText || '').includes('已升级为 TV Director')) return;
  }
});
await page.waitForTimeout(700);
await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  [...document.querySelectorAll('[aria-label="素材库"]')].filter(vis)[0]?.click();
});
await page.waitForTimeout(1700);
await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const hit = [...document.querySelectorAll('*')].filter((e) => vis(e) && (e.innerText || '').trim() === '特效库');
  let el = hit[hit.length - 1];
  let btn = null;
  for (let i = 0; i < 5 && el && !btn; i += 1) { if (el.tagName === 'BUTTON' || el.getAttribute('role') === 'button') btn = el; el = el.parentElement; }
  (btn || hit[hit.length - 1]?.parentElement)?.click();
});
await page.waitForTimeout(3000);

const cb = await page.evaluate(() => {
  const m = [...document.querySelectorAll('.mantine-Modal-content')].find((el) => (el.innerText || '').includes('特效广场'));
  const cards = [...m.querySelectorAll('div')].filter((el) => { const c = el.className?.toString?.() || ''; return /rounded-xl/.test(c) && /flex-col/.test(c) && /p-2/.test(c); });
  const r = cards[0].getBoundingClientRect();
  return { box: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], name: (cards[0].innerText || '').replace(/\s+/g, ' ').slice(0, 30) };
});
out.card = cb;
out.timeline.push(await probe('t=-0 悬停前'));

const cx = cb.box[0] + cb.box[2] / 2;
const cy = cb.box[1] + 90;   // 预览图正中
await page.mouse.move(cx, cy, { steps: 10 });
await page.waitForTimeout(900);
out.timeline.push(await probe('t=0.9s 只悬停，未点'));
await shot(page, 'M-297-特效卡片-只悬停.png', { clip: { x: 100, y: 79, width: 800, height: 430 } });

await page.mouse.click(cx, cy);
for (const ms of [300, 400, 500, 600, 800, 1000, 1200]) {
  await page.waitForTimeout(ms);
  out.timeline.push(await probe(`点后累计`));
}
await page.waitForTimeout(1500);
out.timeline.push(await probe('点后 +4.5s'));
await shot(page, 'M-298-特效卡片-点开之后.png', { clip: { x: 0, y: 0, width: 1440, height: 810 } });

await writeFile(resolve(HERE, '.evidence/cc7-timeline.json'), JSON.stringify(out, null, 2));
console.log(JSON.stringify({ card: out.card, timeline: out.timeline }, null, 2));
await browser.close();
