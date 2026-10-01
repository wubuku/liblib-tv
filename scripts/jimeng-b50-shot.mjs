// 批次 50 配图：在**受控条件**下（组内只有 3 个文本节点，无任何媒体节点）
// 拍一张组工具条截图，作为「组工具条有四项（含下载）」的直接图像证据。
// 拍完立刻解除编组、按 id 删掉自建节点、缩放归位。
import { chromium } from 'playwright';
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
import { keyGuard, canvasBaseline, diffNodePositions, pinViewport } from './jimeng-safe-keys.mjs';

const BASELINE = JSON.parse(readFileSync(new URL('./jimeng-baseline-nodes.json', import.meta.url), 'utf8'));
const OTHERS = Object.keys(BASELINE.nodes);
const OUT = new URL('../docs/user-manual/jimeng-canvas/screenshots/98-group-toolbar-four-items.png', import.meta.url).pathname;

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
if (!p) { console.error('canvas page not found'); process.exit(1); }
await pinViewport(p);
const reset = async () => { for (let i = 0; i < 3; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(320); } };
const real = (l) => l.filter((x) => !String(x).startsWith('__group-resize-chrome__'));
const ids = async () => real(await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id'))));
const selIds = async () => real(await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((e) => e.getAttribute('data-id'))));
const groupIds = async () => real(await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node-group')).map((e) => e.getAttribute('data-id'))));
const vp = () => p.evaluate(() => { const v = document.querySelector('.react-flow__viewport'); const m = v && /translate\(([-\d.]+)px,\s*([-\d.]+)px\)\s*scale\(([-\d.]+)\)/.exec(v.style.transform); return m ? { tx: +m[1], ty: +m[2], scale: +m[3] } : null; });
const isEmpty = (x, y) => p.evaluate(([x, y]) => { const el = document.elementFromPoint(x, y); if (!el) return true;
  if (el.closest('.react-flow__node')) return false;
  if (el.closest('button,[role="button"],input,textarea,[role="menu"],[role="listbox"],[data-testid="node-toolbar"],[data-testid="workspace-bottom-dock-frame"],[data-testid="canvas-fixed-toolbar-left-rail"],[data-testid="canvas-top-bar-actions"],[data-testid="canvas-panel-launcher"]')) return false;
  return true; }, [x, y]);
const findEmpty = async () => { for (let y = 110; y <= 630; y += 20) for (let x = 80; x <= 1250; x += 20) { if (x > 1150 && y > 600) continue; if (await isEmpty(x, y)) return { x, y }; } return null; };
const setTool = async (want) => { const cur = await p.evaluate(() => (document.querySelector('[data-testid="canvas-pointer-tool-toggle"]') || {}).getAttribute?.('aria-label'));
  if (cur !== want) { await p.evaluate(() => document.querySelector('[data-testid="canvas-pointer-tool-toggle"]').click()); await p.waitForTimeout(600); } };
const drag = async (from, tdx, tdy) => { const steps = Math.max(1, Math.ceil(Math.max(Math.abs(tdx), Math.abs(tdy)) / 130));
  await p.mouse.move(from.x, from.y); await p.mouse.down(); await p.waitForTimeout(120);
  for (let i = 1; i <= steps; i++) { await p.mouse.move(from.x + (tdx * i) / steps, from.y + (tdy * i) / steps); await p.waitForTimeout(45); }
  await p.mouse.up(); await p.waitForTimeout(650); };
const panTo = async (CX, CY) => { for (let r = 0; r < 20; r++) { const v = await vp(); if (!v) return false;
  const tx = 640 - CX * v.scale, ty = 480 - CY * v.scale, dx = tx - v.tx, dy = ty - v.ty;
  if (Math.abs(dx) < 4 && Math.abs(dy) < 4) return true;
  const s = await findEmpty(); if (!s) return false;
  await drag(s, Math.max(-130, Math.min(130, dx)), Math.max(-90, Math.min(90, dy))); } return false; };
const centerMine = async (myIds) => { for (let r = 0; r < 8; r++) {
  const u = await p.evaluate((I) => { const rs = I.map((id) => { const e = document.querySelector(`.react-flow__node[data-id="${id}"]`); return e ? e.getBoundingClientRect() : null; }).filter(Boolean);
    if (rs.length !== I.length) return null; const x0 = Math.min(...rs.map((r) => r.x)), x1 = Math.max(...rs.map((r) => r.right)), y0 = Math.min(...rs.map((r) => r.y)), y1 = Math.max(...rs.map((r) => r.bottom));
    return { cx: (x0 + x1) / 2, cy: (y0 + y1) / 2, rect: [Math.round(x0), Math.round(y0), Math.round(x1), Math.round(y1)] }; }, myIds);
  if (!u) return false; const dx = 640 - u.cx, dy = 480 - u.cy;
  if (Math.abs(dx) < 6 && Math.abs(dy) < 6) { console.log('  并集屏幕框', JSON.stringify(u.rect), '已居中'); return true; }
  const s = await findEmpty(); if (!s) return false; await drag(s, Math.max(-130, Math.min(130, dx)), Math.max(-130, Math.min(130, dy))); } return false; };
const toolbarItems = () => p.evaluate(() => Array.from(document.querySelectorAll('[data-testid="node-toolbar"]')).filter((e) => e.getBoundingClientRect().width > 1)
  .map((bar) => { const r = bar.getBoundingClientRect(); return { bar: `${Math.round(r.width)}x${Math.round(r.height)}`,
    items: Array.from(bar.querySelectorAll('button,[role="button"]')).map((e) => { const rr = e.getBoundingClientRect();
      return { name: e.getAttribute('aria-label') || (e.innerText || '').trim().slice(0, 8), w: Math.round(rr.width), h: Math.round(rr.height), cx: Math.round(rr.x + rr.width / 2), cy: Math.round(rr.y + rr.height / 2) }; }) }; }));
const deleteById = async (id) => { if (!(await ids()).includes(id)) return 'absent';
  const pt = await p.evaluate((v) => { const e = document.querySelector(`.react-flow__node[data-id="${v}"]`); const r = e.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + 16) }; }, id);
  await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(650);
  if (await p.evaluate((v) => { const s = document.querySelector('.react-flow__node.selected'); return !s || s.getAttribute('data-id') !== v; }, id)) {
    await p.evaluate((v) => { const e = document.querySelector(`.react-flow__node[data-id="${v}"]`); const r = e.getBoundingClientRect();
      for (const t of ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click']) e.dispatchEvent(new MouseEvent(t, { bubbles: true, cancelable: true, clientX: Math.round(r.x + r.width / 2), clientY: Math.round(r.y + 16) })); }, id);
    await p.waitForTimeout(650); }
  if (await p.evaluate((v) => { const s = document.querySelector('.react-flow__node.selected'); return !s || s.getAttribute('data-id') !== v; }, id)) return 'notselected';
  await p.evaluate((v) => { const e = document.querySelector(`.react-flow__node[data-id="${v}"]`); const r = e.getBoundingClientRect(); e.dispatchEvent(new MouseEvent('contextmenu', { bubbles: true, cancelable: true, clientX: Math.round(r.x + r.width / 2), clientY: Math.round(r.y + 12) })); }, id);
  await p.waitForTimeout(650);
  const ok = await p.evaluate(() => { const m = Array.from(document.querySelectorAll('[role="menu"],[data-testid="canvas-context-menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop(); if (!m) return false;
    const it = Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => /删除/.test(x.innerText || '')); if (!it) return false; it.click(); return true; });
  await p.waitForTimeout(1200); return ok ? 'deleted' : 'noclick'; };

// ---- 起点 ----
await reset();
const bad0 = await diffNodePositions(p, BASELINE.nodes, 1.5);
if (bad0.length || (await ids()).length !== 6) { console.error('ABORT: 起点与基线不一致', JSON.stringify(bad0)); await b.close(); process.exit(2); }
console.log('起点与基线一致 ✅');

await setTool('抓手工具');
if (!await panTo(1700, 400)) { console.error('ABORT: 平移失败'); await b.close(); process.exit(3); }
await setTool('选择工具');
const myIds = [];
for (let i = 0; i < 3; i++) {
  const before = await ids();
  await p.evaluate(() => { const t = Array.from(document.querySelectorAll('button,[role="button"]')).find((e) => e.getAttribute('aria-label') === '文本'); if (t) t.click(); });
  await p.waitForTimeout(1700);
  const fresh = (await ids()).filter((x) => !before.includes(x));
  if (fresh.length !== 1) { console.error('ABORT: 建节点异常', fresh); await b.close(); process.exit(4); }
  myIds.push(fresh[0]);
}
console.log('自建 3 个文本节点:', JSON.stringify(myIds), '缩放', JSON.stringify(await vp()));
await reset();
await setTool('抓手工具');
if (!await centerMine(myIds)) { console.error('ABORT: 居中失败'); await b.close(); process.exit(5); }
await setTool('选择工具');

// 框选（三重断言）
const mine = await p.evaluate((I) => I.map((id) => { const e = document.querySelector(`.react-flow__node[data-id="${id}"]`); const r = e.getBoundingClientRect(); return { id, x: r.x, y: r.y, w: r.width, h: r.height }; }), myIds);
const others = await p.evaluate((I) => I.map((id) => { const e = document.querySelector(`.react-flow__node[data-id="${id}"]`); if (!e) return null; const r = e.getBoundingClientRect(); return { id, x: r.x, y: r.y, w: r.width, h: r.height }; }).filter(Boolean), OTHERS);
const sx = Math.round(Math.min(...mine.map((m) => m.x)) - 28), sy = Math.round(Math.min(...mine.map((m) => m.y)) - 28);
const ex = Math.round(Math.max(...mine.map((m) => m.x + m.w)) + 24), ey = Math.round(Math.max(...mine.map((m) => m.y + m.h)) + 24);
const hit = others.filter((o) => o.x < ex && o.x + o.w > sx && o.y < ey && o.y + o.h > sy);
console.log(`  框选矩形 (${sx},${sy})-(${ex},${ey})，与他人节点相交 ${hit.length} 个`);
if (hit.length || (await selIds()).length) { console.error('ABORT: 框选不安全'); await b.close(); process.exit(6); }
await p.mouse.move(sx, sy); await p.mouse.down();
for (let i = 1; i <= 10; i++) { await p.mouse.move(sx + ((ex - sx) * i) / 10, sy + ((ey - sy) * i) / 10); await p.waitForTimeout(55); }
await p.mouse.up(); await p.waitForTimeout(750);
const post = (await selIds()).sort(), want = [...myIds].sort();
const ok = post.length === want.length && post.every((v, i) => v === want[i]);
console.log('  框选结果:', post.join(','), ok ? '✅ 与目标完全一致' : '❌ 不一致');
if (!ok) { console.error('ABORT: 选中集合不符'); await b.close(); process.exit(7); }

// 编组
const gb = (await toolbarItems()).flatMap((t) => t.items).find((i) => i.name === '编组');
if (!gb) { console.error('ABORT: 没有编组项'); await b.close(); process.exit(8); }
await p.mouse.click(gb.cx, gb.cy); await p.waitForTimeout(1100);
const gid = (await groupIds())[0];
console.log('  编组后真组数', (await groupIds()).length, gid);
if (!gid) { console.error('ABORT: 编组失败'); await b.close(); process.exit(9); }
await reset();
const gpt = await p.evaluate((v) => { const g = document.querySelector(`.react-flow__node-group[data-id="${v}"]`); const r = g.getBoundingClientRect(); const cx = Math.round(r.x + r.width / 2);
  for (let y = Math.round(r.y + 2); y <= Math.round(r.y + 40); y += 2) { const el = document.elementFromPoint(cx, y); if (el && el.closest(`.react-flow__node-group[data-id="${v}"]`)) return { x: cx, y }; } return null; }, gid);
await p.mouse.click(gpt.x, gpt.y); await p.waitForTimeout(900);
const tb = await toolbarItems();
console.log('  🔑 组工具条:', JSON.stringify(tb.map((t) => ({ bar: t.bar, items: t.items.map((i) => `${i.name} ${i.w}×${i.h}`) }))));
if (!(await selIds()).includes(gid)) { console.error('ABORT: 组没被选中'); await b.close(); process.exit(10); }
const othersVisible = others.filter((o) => o.x < 1280 && o.x + o.w > 0 && o.y < 720 && o.y + o.h > 0);
console.log('  画面内他人节点:', othersVisible.length, '个', othersVisible.map((o) => o.id).join(',') || '（无）');

// 截图
const buf = await p.screenshot({ type: 'png' });
writeFileSync(OUT, buf);
const sha = createHash('sha256').update(buf).digest('hex');
console.log('  截图已存:', OUT, '\n  sha256:', sha, '\n  字节:', buf.length);

// 收尾
const un = tb.flatMap((t) => t.items).find((i) => i.name === '解除编组');
if (un) { await p.mouse.click(un.cx, un.cy); await p.waitForTimeout(1100); }
console.log('  解除编组后真组数', (await groupIds()).length);
await reset();
for (const id of myIds) console.log('  删', id, '→', await deleteById(id));
await reset();
await setTool('选择工具');
await p.mouse.click(700, 150); await p.waitForTimeout(500);
await p.keyboard.press('Escape'); await p.waitForTimeout(400);
await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(600);
const z = 'input[data-testid="canvas-zoom-percent-input"]';
if (await p.$(z)) { await p.fill(z, '60'); await p.keyboard.press('Enter'); await p.waitForTimeout(900); }
await p.keyboard.press('Escape'); await p.waitForTimeout(400);
await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(600);
await p.evaluate(() => { const m = document.querySelector('[data-testid="canvas-zoom-menu"]'); const it = m && Array.from(m.querySelectorAll('button,[role="menuitem"]')).find((e) => /适配画布/.test(e.innerText || '')); if (it) it.click(); });
await p.waitForTimeout(1300);
await p.keyboard.press('Escape'); await p.waitForTimeout(400);
await p.mouse.click(700, 150); await p.waitForTimeout(700);
const fin = await canvasBaseline(p);
const bad = await diffNodePositions(p, BASELINE.nodes, 1.5);
const g = await keyGuard(p);
console.log('\n=== 收尾核对 ===');
console.log(' 焦点守卫:', g.safe ? '✅' : g.where, '| 节点数', fin.nodes.length, '| 真组数', (await groupIds()).length);
console.log(' 状态行:', fin.status, '| 积分', fin.credit, '| 缩放', fin.zoom);
console.log(' 位置偏离:', bad.length, bad.length ? bad.join(',') : '✅ 0');
await b.close();
