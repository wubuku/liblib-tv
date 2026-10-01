// 批次 71 · 第六轮：补一张**同源不同向**的配图。
//
// 已有两张图分属两个源：主体源=after ⊕（添加节点）、时间线源=before ⊕（添加上下文）。
// 但「方向才是变量」这句话需要**同一个源**的两张菜单来证明，
// 否则读者仍可能理解成「时间线这种源天生是另一种菜单」（正是批次 59 的错）。
//
// 本轮：建一个主体源 → **先点 before ⊕** 读+拍照 → 再点 after ⊕ 读（同一实例，不拍照，
// 因为 after 那张 71-subject-source-menu.png 已经有了，避免零增量重复截图）。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';
const BASE = JSON.parse(readFileSync(new URL('./jimeng-baseline-nodes.json', import.meta.url), 'utf8'));
const SHOTS = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url);
const OUT = new URL('./_tmp-b71f.json', import.meta.url);

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0]);
const zoomOf = () => p.evaluate(() => (document.querySelector('button[aria-label^="Zoom options"]') || {}).getAttribute?.('aria-label'));
const credit = () => p.evaluate(() => { const m = document.body.innerText.match(/(\d[\d,]*)\s*基础会员/); return m ? parseInt(m[1].replace(/,/g, ''), 10) : null; });
const ids = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const selCount = () => p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
const esc = async (n = 1) => { for (let i = 0; i < n; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(380); } };
async function deselectReal() {
  await esc(2);
  const pt = await p.evaluate(() => { for (let y = 120; y < 640; y += 20) for (let x = 100; x < 1200; x += 20) { if (x > 1120 && y > 540) continue;
      const el = document.elementFromPoint(x, y); if (!el || el.closest('.react-flow__node')) continue;
      if (el.closest('button,[role="button"],input,textarea,[role="menu"],[role="listbox"],[role="dialog"],[data-testid="node-toolbar"],[data-testid="workspace-bottom-dock-frame"],[data-testid="canvas-fixed-toolbar-left-rail"],[data-testid="canvas-top-bar-actions"],[data-testid="canvas-panel-launcher"],[data-testid="canvas-feature-sidecar"]')) continue;
      return { x, y }; } return null; });
  if (pt) { await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(900); }
}
const scanPlus = (id) => p.evaluate((vid) => Array.from(document.querySelectorAll('[aria-label^="Create connected node"]')).map((e) => {
  const q = e.getBoundingClientRect(); if (q.width <= 1) return null;
  return { testid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'), box: `${Math.round(q.width)}x${Math.round(q.height)}`,
    cx: Math.round(q.x + q.width / 2), cy: Math.round(q.y + q.height / 2), inTarget: !!e.closest(`.react-flow__node[data-id="${vid}"]`) }; }).filter(Boolean), id);
async function selectNode(id) {
  for (const [fx, fy] of [[0.5, 0.2], [0.5, 0.12], [0.15, 0.2], [0.85, 0.2], [0.3, 0.3], [0.5, 0.5], [0.7, 0.18], [0.25, 0.45]]) {
    const pt = await p.evaluate(([vid, ax, ay]) => { const n = document.querySelector(`.react-flow__node[data-id="${vid}"]`); if (!n) return null;
      const r = n.getBoundingClientRect(); const x = Math.round(r.x + r.width * ax), y = Math.round(r.y + r.height * ay);
      if (x < 4 || y < 4 || x > innerWidth - 4 || y > innerHeight - 4) return null;
      return { x, y, inNode: !!(document.elementFromPoint(x, y) || {}).closest?.(`.react-flow__node[data-id="${vid}"]`) }; }, [id, fx, fy]);
    if (!pt || !pt.inNode) continue;
    await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(900);
    if (await p.evaluate((v) => !!document.querySelector(`.react-flow__node[data-id="${v}"].selected`), id)) return true;
  } return false;
}
const readMenu = () => p.evaluate(() => { const ms = Array.from(document.querySelectorAll('[role="menu"],[data-testid="canvas-context-menu"]')).filter((e) => e.getBoundingClientRect().width > 1);
  const el = ms[ms.length - 1]; if (!el) return { none: true }; const r = el.getBoundingClientRect();
  return { aria: el.getAttribute('aria-label'), box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
    items: Array.from(el.querySelectorAll('[role="menuitem"]')).map((x) => ({ name: (x.innerText || '').trim().split('\n')[0].trim(),
      reason: (x.textContent || '').replace((x.innerText || '').split('\n')[0], '').replace(/\s+/g, ' ').trim() || null,
      dis: x.getAttribute('aria-disabled'), cursor: getComputedStyle(x).cursor })) }; });
async function ctxDelete(id) {
  const box = await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!n) return null;
    const r = n.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + 14) }; }, id);
  if (!box) return true;
  await p.mouse.click(box.x, box.y, { button: 'right' }); await p.waitForTimeout(900);
  await p.evaluate(() => { const m = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"],[role="menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop();
    const it = m && Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => /删除/.test(x.innerText || '')); if (it) it.click(); });
  await p.waitForTimeout(1500);
  return !(await ids()).includes(id);
}
const out = { startedAt: new Date().toISOString() };
const log = (...a) => console.log(a.join(' '));
let mine = null;
try {
  log('开跑前:', await status(), '| 缩放', await zoomOf(), '| 积分', await credit());
  const pre = await ids();
  const rail = await p.evaluate(() => { const el = Array.from(document.querySelectorAll('button,[role="button"]'))
    .find((x) => /^主体$/.test(((x.getAttribute('aria-label') || '') + (x.innerText || '')).trim()));
    if (!el) return null; const r = el.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  await p.mouse.click(rail.x, rail.y); await p.waitForTimeout(2300);
  const created = (await ids()).filter((x) => !pre.includes(x));
  if (created.length !== 1) throw new Error('新建数异常 ' + JSON.stringify(created));
  mine = created[0];
  await deselectReal();
  if (!(await selectNode(mine)) || (await selCount()) !== 1) throw new Error('前置不成立：主体节点没选中');
  const plus = await scanPlus(mine);
  log('⊕', plus.length, JSON.stringify(plus.map((x) => x.testid)));
  const before = plus.find((x) => /target/.test(x.testid));
  if (!before) throw new Error('没有 before ⊕');
  await p.mouse.click(before.cx, before.cy); await p.waitForTimeout(1800);
  const m1 = await readMenu();
  log('before ⊕ →', m1.aria, m1.box, '\n  可用', m1.items.filter((i) => i.dis !== 'true' && i.cursor !== 'not-allowed').map((i) => i.name).join('/'),
      '\n  禁用', m1.items.filter((i) => i.dis === 'true').map((i) => `${i.name}:${i.reason}`).join(' | '));
  // 配图：节点 ∪ 菜单，并**断言七项中心全部落在 clip 内**（批次 64 的教训：按单边算会裁掉项）
  const clip = await p.evaluate(() => { const n = document.querySelector('.react-flow__node.selected'); if (!n) return null;
    const ms = Array.from(document.querySelectorAll('[role="menu"],[data-testid="canvas-context-menu"]')).filter((e) => e.getBoundingClientRect().width > 1);
    const rects = [n.getBoundingClientRect(), ...ms.map((e) => e.getBoundingClientRect())];
    const L = Math.max(0, Math.round(Math.min(...rects.map((r) => r.x)) - 26)), T = Math.max(0, Math.round(Math.min(...rects.map((r) => r.y)) - 26));
    const R = Math.min(1280, Math.round(Math.max(...rects.map((r) => r.right)) + 26)), B = Math.min(720, Math.round(Math.max(...rects.map((r) => r.bottom)) + 26));
    const keys = []; for (const m of ms) for (const it of m.querySelectorAll('[role="menuitem"]')) { const q = it.getBoundingClientRect(); if (q.width <= 1) continue;
      keys.push({ what: (it.innerText || '').trim().split('\n')[0], cx: Math.round(q.x + q.width / 2), cy: Math.round(q.y + q.height / 2) }); }
    return { x: L, y: T, width: R - L, height: B - T, keys: keys.map((k) => ({ ...k, ok: k.cx >= L && k.cx <= R && k.cy >= T && k.cy <= B })) }; });
  const bad = clip.keys.filter((k) => !k.ok);
  log('clip', JSON.stringify({ x: clip.x, y: clip.y, width: clip.width, height: clip.height }), '| 项', clip.keys.length, '被裁', bad.length);
  if (!bad.length) { await p.screenshot({ path: new URL('71-subject-before-menu.png', SHOTS).pathname, clip: { x: clip.x, y: clip.y, width: clip.width, height: clip.height } }); log('📷 71-subject-before-menu.png'); }
  // 同一实例再读 after ⊕（不拍照，只留读数作对照）
  await esc(1);
  if ((await selCount()) !== 1) { await selectNode(mine); log('↺ 重新选中 selected=', await selCount()); }
  const after = plus.find((x) => /source/.test(x.testid));
  await p.mouse.click(after.cx, after.cy); await p.waitForTimeout(1800);
  const m2 = await readMenu();
  log('after ⊕ →', m2.aria, m2.box, '\n  可用', m2.items.filter((i) => i.dis !== 'true' && i.cursor !== 'not-allowed').map((i) => i.name).join('/'));
  out.reads = { before: m1, after: m2 };
  await esc(2);
} catch (e) { console.error('ABORT:', e.message); out.abort = e.message; }
finally {
  await esc(3);
  if (mine && (await ids()).includes(mine)) log('清理', mine, (await ctxDelete(mine)) ? '✅ deleted' : '🔴 仍在');
  await esc(3);
  for (let t = 0; t < 3; t++) { const z = await zoomOf(); if (z && z.includes('60%')) break;
    await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(700);
    const sl = 'input[data-testid=canvas-zoom-percent-input]';
    if (await p.$(sl)) { await p.fill(sl, '60'); await p.keyboard.press('Enter'); await p.waitForTimeout(1100); } else { await p.keyboard.press('Escape'); await p.waitForTimeout(400); } }
  const cp = await p.evaluate(() => Object.fromEntries(Array.from(document.querySelectorAll('.react-flow__node')).map((e) => {
    const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(e.style.transform || '');
    return [e.getAttribute('data-id'), m ? [Math.round(parseFloat(m[1]) * 100) / 100, Math.round(parseFloat(m[2]) * 100) / 100] : null]; })));
  const dev = []; for (const [id, b2] of Object.entries(BASE.nodes)) { const c = cp[id]; const d = c && b2.canvas ? [Math.round((c[0] - b2.canvas[0]) * 100) / 100, Math.round((c[1] - b2.canvas[1]) * 100) / 100] : 'MISSING';
    if (d === 'MISSING' || (Array.isArray(d) && (Math.abs(d[0]) > 0.01 || Math.abs(d[1]) > 0.01))) dev.push([id, d]); }
  const extra = Object.keys(cp).filter((x) => !BASE.nodes[x]);
  out.end = { status: await status(), zoom: await zoomOf(), credit: await credit(), nodes: Object.keys(cp).length, dev, extra };
  log('终态', JSON.stringify(out.end));
  writeFileSync(OUT, JSON.stringify(out, null, 1)); await b.close();
}
