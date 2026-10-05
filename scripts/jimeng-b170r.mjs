// 批次 170 r 轮：夹出「子菜单从飞出片段切成流内菜单」的**宽度阈值**。
//
// 已知两个包夹点（q 轮）：
//   1280 宽 → 子菜单 pos=absolute（`z-50 absolute invisible`，212×404，left:100%/top:−4px）
//    400 宽 → 子菜单 pos=static （完整 `octo-context-menu--compact-surface`，width:200px，404 高）
// ⇒ 阈值在 (400, 1280]。本轮二分夹到具体值。
// ⚠️ 顺带复核宽度夹取：400→240（未夹，400−16=384>240）、250→234、210→194。
import { openCanvas, readers } from './jimeng-b135-lib.mjs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const { b, p: shared } = await openCanvas();
const p = shared;
const R = readers(p);

const tab = await b.contexts()[0].newPage();
await tab.goto(shared.url(), { waitUntil: 'domcontentloaded' });
await tab.waitForSelector('.react-flow__node', { timeout: 60000 });
await tab.waitForTimeout(3500);

const step = async (w, h = 720) => {
  await tab.context().newCDPSession(tab).then(async (s) => {
    await s.send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: 2, mobile: false });
  });
  await tab.waitForTimeout(1300);
  await tab.keyboard.press('Escape'); await tab.waitForTimeout(250);
  const pt = await tab.evaluate(() => {
    for (let y = 20; y < innerHeight - 10; y += 10)
      for (let x = 20; x < innerWidth - 10; x += 10) {
        const e = document.elementFromPoint(x, y);
        if (e && e.closest('.react-flow__pane') && !e.closest('.react-flow__node')) return [x, y];
      }
    return null;
  });
  if (!pt) return { 视口: w, 跳过: '无空白点' };
  await tab.mouse.click(pt[0], pt[1], { button: 'right' });
  await tab.waitForTimeout(1000);
  const d = await tab.evaluate(() => {
    const e = document.querySelector('[data-testid="canvas-context-menu"]');
    if (!e) return null;
    const mr = e.getBoundingClientRect();
    const trig = e.firstElementChild.firstElementChild;
    let sub = null;
    for (const c of trig.querySelectorAll('div')) {
      if (c.querySelectorAll('[role=menuitem]').length >= 5) {
        const cs = getComputedStyle(c), r = c.getBoundingClientRect();
        sub = { pos: cs.position, w: Math.round(r.width), h: Math.round(r.height) };
        break;
      }
    }
    return {
      菜单: [Math.round(mr.x), Math.round(mr.y), Math.round(mr.width), Math.round(mr.height)],
      触发器高: Math.round(trig.getBoundingClientRect().height),
      子菜单: sub,
    };
  });
  return { 视口: w, ...d };
};

const rows = [];
for (const w of [1280, 1024, 896, 800, 768, 700, 640, 600, 560, 520, 480, 440, 400]) {
  const r = await step(w);
  rows.push(r);
  const 态 = r.子菜单 ? (r.子菜单.pos === 'absolute' ? '飞出(absolute)' : '流内(static)') : '?';
  console.log(`  ${String(w).padStart(4)} → 菜单 ${r.菜单 ? r.菜单[2] + '×' + r.菜单[3] : '?'}  触发器高 ${r.触发器高}  子菜单 ${态} ${r.子菜单 ? r.子菜单.w + '×' + r.子菜单.h : ''}`);
}

const lastFlyout = [...rows].reverse().find((r) => r.子菜单 && r.子菜单.pos === 'absolute');
const firstInline = rows.find((r) => r.子菜单 && r.子菜单.pos !== 'absolute');
console.log(`\n阈值包夹: 最宽的「流出」=${lastFlyout && lastFlyout.视口}，最窄的「流内」=${firstInline && firstInline.视口}`);
console.log('⇒ 子菜单切换宽度阈值 ∈ (' + (firstInline && firstInline.视口) + ', ' + (lastFlyout && lastFlyout.视口) + ']');

await tab.keyboard.press('Escape'); await tab.waitForTimeout(300);
await tab.close();
console.log('\n共享页签复位:', JSON.stringify(await pinViewport(shared)), JSON.stringify({ sel: await R.selCount(), credits: await R.credits() }));
const fs = await import('node:fs');
fs.writeFileSync(new URL('./_tmp-b170r.json', import.meta.url), JSON.stringify(rows, null, 1));
await b.close();
