// 批次 71 · 第二轮：只重测**时间线源**，且**断言前置条件**
//
// 第一轮的时间线源读数是 `选中? false | ⊕ 数量 0` —— **前置条件没成立**，
// 这个读数**无效**（批次 69 的教训：「不存在」是最贵的结论，
// 而前置条件没满足时得到的 0 不算证据）。
// 手册本来就有时间线源的菜单配图 `101-timeline-source-menu-title.png`（标题「添加上下文」），
// 说明**时间线源是有菜单的** ⇒ 我的 0 是自造的。
//
// 修法：点击点改到**标题行**（时间线节点 720×124，按 0.75 高度点会落在轨道区），
// 并在读数前**硬断言 selected === true**，不满足就报失败而不是继续。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';
const BASE = JSON.parse(readFileSync(new URL('./jimeng-baseline-nodes.json', import.meta.url), 'utf8'));
const SHOTS = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url);
const OUT = new URL('./_tmp-b71b.json', import.meta.url);
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0]);
const zoomOf = () => p.evaluate(() => (document.querySelector('button[aria-label^="Zoom options"]') || {}).getAttribute?.('aria-label'));
const credit = () => p.evaluate(() => { const m = document.body.innerText.match(/(\d[\d,]*)\s*基础会员/); return m ? parseInt(m[1].replace(/,/g, ''), 10) : null; });
const ids = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const esc = async (n = 3) => { for (let i = 0; i < n; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(340); } };
const deselectReal = async () => { await esc(2);
  const pt = await p.evaluate(() => { for (let y = 120; y < 640; y += 20) for (let x = 100; x < 1200; x += 20) { if (x > 1120 && y > 540) continue;
    const el = document.elementFromPoint(x, y); if (!el || el.closest('.react-flow__node')) continue;
    if (el.closest('button,[role="button"],input,textarea,[role="menu"],[role="listbox"],[role="dialog"],[data-testid="node-toolbar"],[data-testid="workspace-bottom-dock-frame"],[data-testid="canvas-fixed-toolbar-left-rail"],[data-testid="canvas-top-bar-actions"],[data-testid="canvas-panel-launcher"],[data-testid="canvas-feature-sidecar"]')) continue;
    return { x, y }; } return null; });
  if (pt) { await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(900); } return p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length); };
const scanPlus = (id) => p.evaluate((vid) => Array.from(document.querySelectorAll('[aria-label^="Create connected node"]'))
  .map((e) => { const q = e.getBoundingClientRect(); if (q.width <= 1) return null;
    return { testid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'), box: `${Math.round(q.width)}x${Math.round(q.height)}`,
      cx: Math.round(q.x + q.width / 2), cy: Math.round(q.y + q.height / 2), inTarget: !!e.closest(`.react-flow__node[data-id="${vid}"]`) }; })
  .filter(Boolean), id);
/** 在节点内找一个「不是按钮/轨道」的落点，并逐个尝试直到选中 */
async function selectNode(id) {
  const tries = [];
  for (const [fx, fy] of [[0.5, 0.2], [0.15, 0.2], [0.85, 0.2], [0.5, 0.12], [0.3, 0.3], [0.5, 0.5], [0.7, 0.18]]) {
    const pt = await p.evaluate(([vid, ax, ay]) => { const n = document.querySelector(`.react-flow__node[data-id="${vid}"]`); if (!n) return null;
      const r = n.getBoundingClientRect(); const x = Math.round(r.x + r.width * ax), y = Math.round(r.y + r.height * ay);
      if (x < 4 || y < 4 || x > innerWidth - 4 || y > innerHeight - 4) return null;
      const el = document.elementFromPoint(x, y);
      return { x, y, inNode: !!(el && el.closest(`.react-flow__node[data-id="${vid}"]`)), tag: el ? el.tagName + '.' + String(el.className).slice(0, 40) : 'null' }; }, [id, fx, fy]);
    if (!pt || !pt.inNode) { tries.push({ fx, fy, skip: '落点不在节点内' }); continue; }
    await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(900);
    const ok = await p.evaluate((v) => !!document.querySelector(`.react-flow__node[data-id="${v}"].selected`), id);
    tries.push({ fx, fy, at: { x: pt.x, y: pt.y }, el: pt.tag, selected: ok });
    if (ok) return { ok, tries };
  }
  return { ok: false, tries };
}
async function ctxDelete(id) {
  await p.evaluate((vid) => { const s = document.querySelector(`.react-flow__node[data-id="${vid}"]`); if (!s) return;
    const r = s.getBoundingClientRect(); s.dispatchEvent(new MouseEvent('contextmenu', { bubbles: true, cancelable: true, clientX: Math.round(r.x + r.width / 2), clientY: Math.round(r.y + 14) })); }, id);
  await p.waitForTimeout(800);
  await p.evaluate(() => { const m = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"],[role="menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop();
    const it = m && Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => /删除/.test(x.innerText || '')); if (it) it.click(); });
  await p.waitForTimeout(1400);
  return !(await ids()).includes(id);
}
const out = { startedAt: new Date().toISOString(), steps: [] };
const log = (...a) => { const s = a.join(' '); console.log(s); out.steps.push(s); };
const MINE = [];
try {
  log('开跑前:', await status(), '| 缩放', await zoomOf(), '| 积分', await credit());
  const pre = await ids();
  const rail = await p.evaluate(() => { const b = Array.from(document.querySelectorAll('button,[role="button"]')).find((x) => /^时间线$/.test(((x.getAttribute('aria-label') || '') + (x.innerText || '')).trim()));
    if (!b) return null; const r = b.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  log('左栏时间线入口:', JSON.stringify(rail));
  await p.mouse.click(rail.x, rail.y); await p.waitForTimeout(2200);
  const created = (await ids()).filter((x) => !pre.includes(x));
  log('新建:', JSON.stringify(created), '|', await status());
  const id = created[0]; MINE.push(id);
  const box = await p.evaluate((v) => { const r = document.querySelector(`.react-flow__node[data-id="${v}"]`).getBoundingClientRect();
    return `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`; }, id);
  log('时间线节点尺寸:', box);

  await deselectReal();
  const sel = await selectNode(id);
  log('\n=== 选中尝试 ===', JSON.stringify(sel.tries, null, 1));
  log('选中成功 =', sel.ok, '| selected 计数 =', await p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length));
  if (!sel.ok) throw new Error('前置条件不成立：时间线节点没能选中，本轮读数一律作废');
  const plus = await scanPlus(id);
  log('★ 选中后 ⊕ 按钮:', JSON.stringify(plus, null, 1));
  if (!plus.length) { log('🔴 仍无 ⊕ —— 与手册 101- 配图矛盾，须记为未解释'); out.plus = []; }
  else {
    const btn = plus.find((x) => /after/.test(x.aria)) || plus[0];
    await p.mouse.click(btn.cx, btn.cy); await p.waitForTimeout(1700);
    const menu = await p.evaluate(() => { const ms = Array.from(document.querySelectorAll('[role="menu"],[data-testid*="connection-menu"]')).filter((e) => e.getBoundingClientRect().width > 1);
      const el = ms[ms.length - 1]; if (!el) return { none: true, all: ms.map((e) => e.getAttribute('role') + ':' + (e.getAttribute('aria-label') || '') + ':' + (e.getAttribute('data-testid') || '')) };
      const r = el.getBoundingClientRect();
      return { testid: el.getAttribute('data-testid'), role: el.getAttribute('role'), aria: el.getAttribute('aria-label'),
        box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
        items: Array.from(el.querySelectorAll('[role="menuitem"]')).map((x) => { const q = x.getBoundingClientRect();
          const lines = (x.innerText || '').trim().split('\n').map((s) => s.trim()).filter(Boolean);
          return { name: lines[0], reason: lines.slice(1).join(' / ') || null, dis: x.getAttribute('aria-disabled'), cursor: getComputedStyle(x).cursor, box: `${Math.round(q.width)}x${Math.round(q.height)}` }; }) }; });
    log('菜单:', JSON.stringify(menu, null, 1));
    out.plus = plus; out.menu = menu;
    if (menu.items) {
      const clip = await p.evaluate(() => { const n = document.querySelector('.react-flow__node.selected'); if (!n) return null;
        const ms = Array.from(document.querySelectorAll('[role="menu"],[data-testid*="connection-menu"]')).filter((e) => e.getBoundingClientRect().width > 1);
        const rects = [n.getBoundingClientRect(), ...ms.map((e) => e.getBoundingClientRect())];
        const L = Math.max(0, Math.round(Math.min(...rects.map((r) => r.x)) - 28));
        const T = Math.max(0, Math.round(Math.min(...rects.map((r) => r.y)) - 28));
        const R = Math.min(1280, Math.round(Math.max(...rects.map((r) => r.right)) + 28));
        const B = Math.min(720, Math.round(Math.max(...rects.map((r) => r.bottom)) + 28));
        const keys = [];
        for (const m of ms) for (const it of m.querySelectorAll('[role="menuitem"]')) { const q = it.getBoundingClientRect(); if (q.width <= 1) continue;
          keys.push({ what: (it.innerText || '').trim().split('\n')[0], cx: Math.round(q.x + q.width / 2), cy: Math.round(q.y + q.height / 2) }); }
        return { x: L, y: T, width: R - L, height: B - T, keys: keys.map((k) => ({ ...k, ok: k.cx >= L && k.cx <= R && k.cy >= T && k.cy <= B })) }; });
      if (clip) { const bad = clip.keys.filter((k) => !k.ok);
        log('配图 clip', JSON.stringify({ x: clip.x, y: clip.y, width: clip.width, height: clip.height }), '| 项', clip.keys.length, '被裁', bad.length, JSON.stringify(bad.map((k) => k.what)));
        if (!bad.length) { await p.screenshot({ path: new URL('71-timeline-source-menu.png', SHOTS).pathname, clip: { x: clip.x, y: clip.y, width: clip.width, height: clip.height } });
          log('📷 71-timeline-source-menu.png'); out.clip = clip; } }
    }
    await esc(2);
  }
  log('\n积分:', await credit()); out.creditAfter = await credit();
} catch (e) { console.error('ABORT:', e.message); out.abort = e.message; }
finally {
  await esc(3);
  for (const id of [...new Set(MINE)]) { if (!(await ids()).includes(id)) { log('清理', id, '不存在'); continue; }
    await ctxDelete(id); log('清理', id, '→', (await ids()).includes(id) ? '🔴 仍在' : '✅ deleted'); }
  await esc(3);
  for (let t = 0; t < 3; t++) { const z = await zoomOf(); if (z && z.includes('60%')) { log('缩放 60%'); break; }
    await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(700);
    const sl = 'input[data-testid=canvas-zoom-percent-input]';
    if (await p.$(sl)) { await p.fill(sl, '60'); await p.keyboard.press('Enter'); await p.waitForTimeout(1100); } else { await p.keyboard.press('Escape'); await p.waitForTimeout(400); } }
  await esc(3);
  const cp = await p.evaluate(() => Object.fromEntries(Array.from(document.querySelectorAll('.react-flow__node')).map((e) => { const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(e.style.transform || ''); return [e.getAttribute('data-id'), m ? [Math.round(parseFloat(m[1]) * 100) / 100, Math.round(parseFloat(m[2]) * 100) / 100] : null]; })));
  let dev = []; for (const [id, b2] of Object.entries(BASE.nodes)) { const c = cp[id]; const d2 = c && b2.canvas ? [Math.round((c[0] - b2.canvas[0]) * 100) / 100, Math.round((c[1] - b2.canvas[1]) * 100) / 100] : 'MISSING';
    if (d2 === 'MISSING' || (Array.isArray(d2) && (Math.abs(d2[0]) > 0.01 || Math.abs(d2[1]) > 0.01))) dev.push([id, d2]); }
  const extra = Object.keys(cp).filter((x) => !BASE.nodes[x]);
  log('终态', await status(), '| 缩放', await zoomOf(), '| 积分', await credit(), '| 节点', Object.keys(cp).length, '| 偏离', JSON.stringify(dev), '| 剩余自建', JSON.stringify(extra));
  out.end = { status: await status(), zoom: await zoomOf(), credit: await credit(), nodes: Object.keys(cp).length, dev, extra };
  writeFileSync(OUT, JSON.stringify(out, null, 1)); log('写入', OUT.pathname);
  await b.close();
}
