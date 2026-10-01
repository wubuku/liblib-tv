// 批次 59 配图：时间线源的菜单标题是「**添加上下文**」，不是「添加节点」
//
// 7×7 矩阵实测里，**六种源**打开的菜单标题逐字都是「添加节点」，
// 唯独**从时间线节点出发**是「添加上下文」—— 手册此前完全没记这个差异。
// 顺带把「时间线源只有 before ⊕、没有 after ⊕」一起拍进去。
import { chromium } from 'playwright';
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const BASELINE = JSON.parse(readFileSync(new URL('./jimeng-baseline-nodes.json', import.meta.url), 'utf8'));
const DIR = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url);
const OUT = new URL('_tmp-b59-shots.json', import.meta.url);
const MINE = [];

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
if (!p) { console.error('ABORT: 找不到画布页面'); process.exit(1); }
await pinViewport(p);
const reset = async () => { for (let i = 0; i < 3; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(320); } };
const selIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((e) => e.getAttribute('data-id')));
const zoomOf = () => p.evaluate(() => (document.querySelector('button[aria-label^="Zoom options"]') || {}).getAttribute?.('aria-label'));
const isEmpty = (x, y) => p.evaluate(([x, y]) => { const el = document.elementFromPoint(x, y); if (!el) return true;
  if (el.closest('.react-flow__node')) return false;
  if (el.closest('button,[role="button"],input,textarea,[role="menu"],[role="listbox"],[data-testid="node-toolbar"],[data-testid="workspace-bottom-dock-frame"],[data-testid="canvas-fixed-toolbar-left-rail"],[data-testid="canvas-top-bar-actions"],[data-testid="canvas-panel-launcher"]')) return false;
  return true; }, [x, y]);
const findEmpty = async () => { for (let y = 110; y <= 630; y += 20) for (let x = 80; x <= 1250; x += 20) { if (x > 1150 && y > 600) continue; if (await isEmpty(x, y)) return { x, y }; } return null; };
const deselect = async () => { await reset(); const e = await findEmpty();
  if (e) { await p.mouse.click(e.x, e.y); await p.waitForTimeout(600); }
  for (let i = 0; i < 3 && (await selIds()).length; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(400); }
  return (await selIds()).length === 0; };
const selectByScan = async (id) => {
  const pts = await p.evaluate((vid) => { const n = document.querySelector(`.react-flow__node[data-id="${vid}"]`); if (!n) return [];
    const r = n.getBoundingClientRect(); const out = [];
    for (let fy = 0.10; fy <= 0.92; fy += 0.06) for (let fx = 0.10; fx <= 0.92; fx += 0.06) {
      const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
      if (x < 2 || y < 2 || x > innerWidth - 2 || y > innerHeight - 2) continue;
      const el = document.elementFromPoint(x, y);
      if (!el || !el.closest(`.react-flow__node[data-id="${vid}"]`)) continue;
      if (el.closest('button,a,[role="button"],input,textarea,select,[role="menu"],[contenteditable="true"]')) continue;
      out.push({ x, y }); } return out; }, id);
  for (const pt of pts) { await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(550);
    const s = await selIds(); if (s.length === 1 && s[0] === id) return true; }
  return false;
};
const deleteById = async (id) => {
  if (!(await p.evaluate((v) => !!document.querySelector(`.react-flow__node[data-id="${v}"]`), id))) return 'absent';
  await deselect(); if (!(await selectByScan(id))) return 'notselected';
  await p.evaluate((v) => { const e = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!e) return;
    const r = e.getBoundingClientRect();
    e.dispatchEvent(new MouseEvent('contextmenu', { bubbles: true, cancelable: true, clientX: Math.round(r.x + r.width / 2), clientY: Math.round(r.y + 14) })); }, id);
  await p.waitForTimeout(800);
  const ok = await p.evaluate(() => { const m = Array.from(document.querySelectorAll('[role="menu"],[data-testid="canvas-context-menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop(); if (!m) return false;
    const it = Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => /删除/.test(x.innerText || '')); if (!it) return false; it.click(); return true; });
  await p.waitForTimeout(1300); await reset(); return ok ? 'deleted' : 'noclick';
};

console.log('=== 批次 59 配图 ===\n');
const shots = [];
await deselect();
const rb = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('aside[data-testid="canvas-fixed-toolbar-left-rail"] button')).find((x) => (x.getAttribute('aria-label') || '').startsWith('时间线'));
  if (!e) return null; const r = e.getBoundingClientRect(); return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; });
const pre = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
await p.mouse.click(rb.cx, rb.cy); await p.waitForTimeout(3000);
const made = (await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')))).filter((x) => !pre.includes(x));
if (made.length !== 1) { console.error('ABORT: 时间线节点未建成', made); await b.close(); process.exit(2); }
MINE.push(made[0]);
console.log('时间线节点', made[0], '选中:', await selectByScan(made[0]));

const plus = await p.evaluate((vid) => { const n = document.querySelector(`.react-flow__node[data-id="${vid}"]`); if (!n) return null;
  const g = (t) => { const e = n.querySelector(`[data-testid="${t}"]`); if (!e) return null; const r = e.getBoundingClientRect();
    return r.width > 1 ? { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) } : null; };
  return { before: g('flow-node-target-connection-menu-button'), after: g('flow-node-source-connection-menu-button') }; }, made[0]);
console.log('⊕ before:', plus.before ? JSON.stringify(plus.before) : '无', '| after:', plus.after ? JSON.stringify(plus.after) : '无');
if (!plus.before) { console.error('ABORT: 时间线节点没有 before ⊕'); await b.close(); process.exit(3); }
await p.mouse.click(plus.before.x, plus.before.y); await p.waitForTimeout(1200);

const info = await p.evaluate(() => {
  const m = Array.from(document.querySelectorAll('[role="menu"],[data-testid="canvas-context-menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop();
  if (!m) return null;
  const r = m.getBoundingClientRect();
  // 菜单标题 = 第一个非 menuitem 的可见文本行
  const head = Array.from(m.children).find((c) => c.getAttribute('role') !== 'menuitem' && (c.innerText || '').trim());
  const hr = head ? head.getBoundingClientRect() : null;
  const host = document.createElement('div');
  host.id = '__b59_markup__';
  host.style.cssText = 'position:fixed;inset:0;pointer-events:none;z-index:2147483647';
  if (hr) { const bx = document.createElement('div');
    bx.style.cssText = `position:absolute;left:${hr.x - 3}px;top:${hr.y - 3}px;width:${hr.width + 6}px;height:${hr.height + 6}px;border:2px solid rgb(255,162,30);border-radius:3px`;
    host.appendChild(bx); }
  document.body.appendChild(host);
  return { title: (m.innerText || '').split('\n')[0].trim(), box: `${Math.round(r.width)}x${Math.round(r.height)}`,
    n: m.querySelectorAll('[role="menuitem"]').length,
    clip: { x: Math.max(0, Math.round(r.x - 120)), y: Math.max(0, Math.round(r.y - 60)),
            width: Math.round(r.width + 240), height: Math.round(r.height + 120) } };
});
if (!info) { console.error('ABORT: 菜单没打开'); await b.close(); process.exit(4); }
console.log(`菜单 ${info.box}  标题逐字「${info.title}」  ${info.n} 项`);
const buf = await p.screenshot({ type: 'png', clip: info.clip });
writeFileSync(new URL('101-timeline-source-menu-title.png', DIR), buf);
const sha = createHash('sha256').update(buf).digest('hex');
console.log(`截图 101-timeline-source-menu-title.png  ${buf.length} 字节  sha256=${sha}`);
shots.push({ file: '101-timeline-source-menu-title.png', ...info, sha, bytes: buf.length });
await p.evaluate(() => { const e = document.getElementById('__b59_markup__'); if (e) e.remove(); });
await reset();
console.log('删除时间线节点:', await deleteById(made[0]));

await reset();
for (let t = 0; t < 3; t++) { const z = await zoomOf();
  if (z && z.includes('60%')) { console.log('缩放归位 ok:', z); break; }
  await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(700);
  const s = 'input[data-testid="canvas-zoom-percent-input"]';
  if (await p.$(s)) { await p.fill(s, '60'); await p.keyboard.press('Enter'); await p.waitForTimeout(1100); }
  else { await p.keyboard.press('Escape'); await p.waitForTimeout(400); }
  if (t === 2) console.log('缩放归位 FAILED:', await zoomOf()); }
await reset();
const fin = await p.evaluate(() => Object.fromEntries(Array.from(document.querySelectorAll('.react-flow__node')).map((e) => {
  const mm = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(e.style.transform || '');
  return [e.getAttribute('data-id'), mm ? [Math.round(parseFloat(mm[1]) * 100) / 100, Math.round(parseFloat(mm[2]) * 100) / 100] : null]; })));
console.log('终态缩放:', await zoomOf(), '| 节点数:', Object.keys(fin).length, '| 选中:', (await selIds()).length);
for (const [id, c] of Object.entries(fin)) { const bs = BASELINE.nodes[id];
  console.log(`  ${id} Δ=${JSON.stringify(bs ? [+(c[0] - bs.canvas[0]).toFixed(2), +(c[1] - bs.canvas[1]).toFixed(2)] : '?')}`); }
writeFileSync(OUT, JSON.stringify({ shots, end: fin }, null, 1));
await b.close();
