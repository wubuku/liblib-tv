// 批次 108 · i 轮：一趟做完 —— 选中组 → 读工具条 → 点「背景色」→ 截图 + 圆点扫描。
//   （h 轮进场时组已不是选中态 —— 共享画布上状态会被别处改动，脚本必须**每次自证**。）
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString() };
out.groupId = 'node_0ctj8mcr3m';
const G = out.groupId;
const save = () => writeFileSync(new URL('./_tmp-b108i.json', import.meta.url), JSON.stringify(out, null, 1));

const status = () => p.evaluate(() => { const t = document.body.innerText;
  return { nodes: (t.match(/(\d+) nodes?/) || [])[1], sel: (t.match(/(\d+) selected/) || [])[1] }; });
const groupInfo = () => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return { __err: 'gone' };
  const r = n.getBoundingClientRect();
  const t = n.querySelector('[data-testid="group-title-chrome"]');
  const tr = t ? t.getBoundingClientRect() : null;
  return { sel: n.classList.contains('selected'), members: (n.innerText.match(/(\d+) members/) || [])[1] || null,
    text: n.innerText.replace(/\s+/g, ' ').trim().slice(0, 110),
    rect: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`,
    title: tr ? { w: Math.round(tr.width), h: Math.round(tr.height), cx: Math.round(tr.x + tr.width / 2), cy: Math.round(tr.y + tr.height / 2) } : null };
}, G);
const roundDots = () => p.evaluate(() => {
  const o = [];
  for (const e of document.querySelectorAll('body *')) {
    const r = e.getBoundingClientRect();
    if (r.width < 8 || r.width > 60 || Math.abs(r.width - r.height) > 1.5) continue;
    const cs = getComputedStyle(e);
    if (cs.visibility === 'hidden' || cs.display === 'none') continue;
    if (cs.backgroundColor === 'rgba(0, 0, 0, 0)') continue;
    if ((parseFloat(cs.borderRadius) || 0) < r.width / 2 - 1) continue;
    o.push({ tag: e.tagName, tid: e.getAttribute('data-testid'), a: e.getAttribute('aria-label'),
      t: (e.innerText || '').trim().slice(0, 8), w: Math.round(r.width),
      x: Math.round(r.x), y: Math.round(r.y), bg: cs.backgroundColor, bdr: cs.borderColor,
      inVp: r.x >= 0 && r.y >= 0 && r.x + r.width <= innerWidth && r.y + r.height <= innerHeight });
  }
  return { count: o.length, items: o.slice(0, 24) };
});

log('起点状态行：', JSON.stringify(await status()));
let g = await groupInfo();
log('组：', JSON.stringify(g));
if (!g.sel) {
  if (!g.title) { log('🔴 没有标题区'); save(); await b.close(); process.exit(1); }
  log('>>> 点标题区', JSON.stringify(g.title));
  await p.mouse.move(g.title.cx, g.title.cy); await p.waitForTimeout(600);
  await p.mouse.click(g.title.cx, g.title.cy); await p.waitForTimeout(1800);
  g = await groupInfo();
  log('点标题后：', JSON.stringify(g));
  if (!g.sel) { log('🔴 点标题没选中'); save(); await b.close(); process.exit(1); }
}
out.g = g;
out.statusSelected = await status();
log('状态行：', JSON.stringify(out.statusSelected));

// 工具条四项逐字
out.bar = await p.evaluate(() => {
  const bar = Array.from(document.querySelectorAll('[data-testid="node-toolbar"]'))
    .find((e) => { const r = e.getBoundingClientRect(); return r.width > 100 && r.y > 0 && r.y < 400 && getComputedStyle(e).visibility !== 'hidden'; });
  if (!bar) return null;
  const r = bar.getBoundingClientRect();
  return { tid: bar.getAttribute('data-testid'), w: Math.round(r.width), h: Math.round(r.height), x: Math.round(r.x), y: Math.round(r.y),
    items: Array.from(bar.querySelectorAll('button,[role=button]')).map((e) => { const q = e.getBoundingClientRect();
      return { t: (e.innerText || '').trim(), a: e.getAttribute('aria-label'), w: Math.round(q.width), h: Math.round(q.height),
        cx: Math.round(q.x + q.width / 2), cy: Math.round(q.y + q.height / 2) }; }) };
});
log('\n组工具条：', JSON.stringify(out.bar));
save();

await p.screenshot({ path: '/tmp/b108-i-0-选中组.png', clip: { x: 430, y: 150, width: 560, height: 400 } });

const bg = out.bar && out.bar.items.find((i) => /背景色/.test(i.t));
if (!bg) { log('🔴 工具条里没有「背景色」'); save(); await b.close(); process.exit(1); }
log('\n>>> 点「背景色」', JSON.stringify(bg));
out.dotsBefore = await roundDots();
log('点前圆点数：', out.dotsBefore.count);
await p.mouse.move(bg.cx, bg.cy); await p.waitForTimeout(650);
await p.mouse.click(bg.cx, bg.cy); await p.waitForTimeout(2200);
await p.screenshot({ path: '/tmp/b108-i-1-点背景色后.png', clip: { x: 430, y: 150, width: 560, height: 400 } });
out.dotsAfter = await roundDots();
log('点后圆点数：', out.dotsAfter.count);
log('圆点明细：', JSON.stringify(out.dotsAfter.items, null, 1));
out.statusAfter = await status();
log('状态行：', JSON.stringify(out.statusAfter));
save();
log('\n已落盘');
await b.close();
