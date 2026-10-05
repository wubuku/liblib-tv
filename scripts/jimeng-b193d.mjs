// 批次 193 d 轮：导演台的两个连接手柄 `opacity` 在**悬停节点时仍然是 0**（c 轮实测），
// 而画面上确实看不到它们 ⇒ 显影条件既不是「悬停节点」也不是「悬停自己」。
// 本轮只问一件事：**选中**是不是显影条件（把 静息 / 选中 两态的 opacity 与尺寸一次读全）。
import fs from 'node:fs';
import { openCanvas, readers, setZoom, settle } from './jimeng-b135-lib.mjs';

const NID = 'node_pxvkay973v';
const 读 = (p) => p.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`); if (!n) return null;
  const 一 = (sel) => { const e = n.querySelector(sel); if (!e) return null; const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    return { 屏上: [Math.round(r.width), Math.round(r.height)], opacity: cs.opacity, visibility: cs.visibility, display: cs.display,
      background: cs.backgroundColor, border: cs.border }; };
  return { 选中: n.classList.contains('selected'),
    target: 一('[data-testid="flow-node-target-handle"]'), source: 一('[data-testid="flow-node-source-handle"]'),
    节点内全部带handle后缀的testid: Array.from(new Set(Array.from(n.querySelectorAll('[data-testid*="handle"]')).map((e) => e.getAttribute('data-testid')))),
    节点内全部带button后缀的testid: Array.from(new Set(Array.from(n.querySelectorAll('[data-testid*="button"]')).map((e) => e.getAttribute('data-testid')))) };
}, NID);

const { b, p } = await openCanvas();
const R = readers(p);
await settle(p, R);
await setZoom(p, 26); await p.waitForTimeout(600);
{
  const btn = await p.evaluate(() => { const a = Array.from(document.querySelectorAll('BUTTON[data-testid="canvas-panel-launcher"]'))
    .find((x) => (x.getAttribute('aria-label') || '') === '搜索'); const r = a.getBoundingClientRect();
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
  await p.mouse.click(btn[0], btn[1]); await p.waitForTimeout(1100);
  const 点 = await p.evaluate(() => { const i = document.querySelector('input[aria-label="搜索"]'); const r = i.getBoundingClientRect();
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
  await p.mouse.click(点[0], 点[1]); await p.waitForTimeout(300);
  await p.keyboard.press('Meta+a'); await p.keyboard.type('导演台'); await p.waitForTimeout(1500);
  const 行 = await p.evaluate(() => { const r = document.querySelector('[data-testid="canvas-search-result-node_pxvkay973v"]');
    if (!r) return null; const q = r.getBoundingClientRect(); return [Math.round(q.x + q.width / 2), Math.round(q.y + q.height / 2)]; });
  if (行) { await p.mouse.click(行[0], 行[1]); await p.waitForTimeout(2400); }
}
await p.keyboard.press('Escape'); await p.waitForTimeout(700);
const 空 = await p.evaluate(() => { const nodes = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getBoundingClientRect());
  for (let y = 100; y < innerHeight - 100; y += 15) for (let x = 330; x < innerWidth - 350; x += 15) {
    const h = document.elementFromPoint(x, y);
    if (h && h.classList && h.classList.contains('react-flow__pane') && !nodes.some((r) => x >= r.x && x <= r.right && y >= r.y && y <= r.bottom)) return [x, y]; }
  return null; });
if (空) { await p.mouse.click(空[0], 空[1]); await p.waitForTimeout(1000); }
const 静息 = { 选中数: await R.selCount(), 读数: await 读(p) };
console.log('静息 =', JSON.stringify(静息, null, 1));
if (静息.选中数 !== 0) { console.log('前置不成立，停'); await b.close(); process.exit(1); }
const 落点 = await p.evaluate((nid) => { const t = document.querySelector(`.react-flow__node[data-id="${nid}"] [data-testid="flow-node-title"]`);
  const r = t.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, NID);
await p.mouse.click(落点[0], 落点[1]); await p.waitForTimeout(1300);
const 选中 = { 选中数: await R.selCount(), 读数: await 读(p) };
console.log('选中 =', JSON.stringify(选中, null, 1));
fs.writeFileSync('/tmp/b193d.json', JSON.stringify({ 静息, 选中 }, null, 1));
const 空2 = await p.evaluate(() => { const nodes = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getBoundingClientRect());
  for (let y = 100; y < innerHeight - 100; y += 15) for (let x = 330; x < innerWidth - 350; x += 15) {
    const h = document.elementFromPoint(x, y);
    if (h && h.classList && h.classList.contains('react-flow__pane') && !nodes.some((r) => x >= r.x && x <= r.right && y >= r.y && y <= r.bottom)) return [x, y]; }
  return null; });
if (空2) { await p.mouse.click(空2[0], 空2[1]); await p.waitForTimeout(900); }
await setZoom(p, 26); await p.waitForTimeout(500);
console.log('收尾 =', JSON.stringify({ 状态行: await R.status(), 选中: await R.selCount(), zoom: await R.zoom() }));
await b.close();
