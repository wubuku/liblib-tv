// 批次 170 s 轮：把子菜单切换阈值从 (640,700] 夹到具体值。
import { openCanvas, readers } from './jimeng-b135-lib.mjs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const { b, p: shared } = await openCanvas();
const p = shared;
const R = readers(p);

const tab = await b.contexts()[0].newPage();
await tab.goto(shared.url(), { waitUntil: 'domcontentloaded' });
await tab.waitForSelector('.react-flow__node', { timeout: 60000 });
await tab.waitForTimeout(3500);

const step = async (w) => {
  await tab.context().newCDPSession(tab).then(async (s) => {
    await s.send('Emulation.setDeviceMetricsOverride', { width: w, height: 720, deviceScaleFactor: 2, mobile: false });
  });
  await tab.waitForTimeout(1200);
  await tab.keyboard.press('Escape'); await tab.waitForTimeout(250);
  const pt = await tab.evaluate(() => {
    for (let y = 20; y < innerHeight - 10; y += 10)
      for (let x = 20; x < innerWidth - 10; x += 10) {
        const e = document.elementFromPoint(x, y);
        if (e && e.closest('.react-flow__pane') && !e.closest('.react-flow__node')) return [x, y];
      }
    return null;
  });
  if (!pt) return { w, 跳过: true };
  await tab.mouse.click(pt[0], pt[1], { button: 'right' });
  await tab.waitForTimeout(950);
  const d = await tab.evaluate(() => {
    const e = document.querySelector('[data-testid="canvas-context-menu"]');
    if (!e) return null;
    const trig = e.firstElementChild.firstElementChild;
    for (const c of trig.querySelectorAll('div')) {
      if (c.querySelectorAll('[role=menuitem]').length >= 5) return getComputedStyle(c).position;
    }
    return null;
  });
  return { w, pos: d };
};

const rows = [];
for (const w of [700, 680, 672, 668, 664, 660, 656, 652, 648, 644, 641, 640]) {
  const r = await step(w);
  rows.push(r);
  console.log(`  ${String(w).padStart(4)} → ${r.pos === 'absolute' ? '飞出' : r.pos === 'static' ? '流内' : '?'}`);
}
const fly = rows.filter((r) => r.pos === 'absolute').map((r) => r.w);
const inl = rows.filter((r) => r.pos === 'static').map((r) => r.w);
console.log(`\n流出侧: ${Math.max(...fly)} 仍飞出；流内侧: ${Math.min(...inl)} 已流内`);
console.log(`⇒ 阈值 ∈ (${Math.min(...inl)}, ${Math.max(...fly)}]`);
await tab.keyboard.press('Escape'); await tab.waitForTimeout(300);
await tab.close();
console.log('\n共享页签复位:', JSON.stringify(await pinViewport(shared)), JSON.stringify({ sel: await R.selCount(), credits: await R.credits() }));
const fs = await import('node:fs');
fs.writeFileSync(new URL('./_tmp-b170s.json', import.meta.url), JSON.stringify(rows, null, 1));
await b.close();
