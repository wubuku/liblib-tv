// 批次 74：菜单项尺寸 **144×22（批次 28）vs 192×36（批次 69/71/73）** —— 量到的是动画中途吗？
//
// 台账里同一个菜单的同一批菜单项，出现两个差 34% 的尺寸：
//   批次 28（§3.45 / AUDIT.md）记「七项各 **144×22**」
//   批次 69/71/72/73 四轮独立跑都读到 **192×36**
// 这与批次 72 的手柄事件同族：**先问是不是量到了不同时刻/状态**。
// 批次 68 写过「浮层要等 1.6s 再数（动画中途会少项）」—— 但那是**项数**，不是**尺寸**。
//
// 方法：把采样器**装在页面里**再点 ⊕（CDP 往返有几十毫秒，事后轮询会漏掉开头），
// 每 60ms 采一次「菜单本体尺寸 + 首末项尺寸 + 项数」，持续 2.5s。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';
const BASE = JSON.parse(readFileSync(new URL('./jimeng-baseline-nodes.json', import.meta.url), 'utf8'));
const LEDGER = new URL('./jimeng-ephemeral-ledger.json', import.meta.url);
const OUT = new URL('./_tmp-b74.json', import.meta.url);

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0]);
const zoomOf = () => p.evaluate(() => (document.querySelector('button[aria-label^="Zoom options"]') || {}).getAttribute?.('aria-label'));
const credit = () => p.evaluate(() => { const m = document.body.innerText.match(/(\d[\d,]*)\s*基础会员/); return m ? parseInt(m[1].replace(/,/g, ''), 10) : null; });
const ids = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const selCount = () => p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
const esc = async (n = 1) => { for (let i = 0; i < n; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(400); } };
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
async function ctxDelete(id) {
  const box = await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!n) return null;
    const r = n.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + 14) }; }, id);
  if (!box) return true;
  await p.mouse.click(box.x, box.y, { button: 'right' }); await p.waitForTimeout(1000);
  await p.evaluate(() => { const m = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"],[role="menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop();
    const it = m && Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => /删除/.test(x.innerText || '')); if (it) it.click(); });
  await p.waitForTimeout(1600);
  return !(await ids()).includes(id);
}

const out = { startedAt: new Date().toISOString(), created: [], runs: [] };
const log = (...a) => console.log(a.join(' '));
let mine = null;
try {
  log('开跑前:', await status(), '| 缩放', await zoomOf(), '| 积分', await credit());
  const pre = await ids();
  const rail = await p.evaluate(() => { const el = Array.from(document.querySelectorAll('button,[role="button"]'))
    .find((x) => /^图片$/.test(((x.getAttribute('aria-label') || '') + (x.innerText || '')).trim()));
    if (!el) return null; const r = el.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  await p.mouse.click(rail.x, rail.y); await p.waitForTimeout(2500);
  const created = (await ids()).filter((x) => !pre.includes(x));
  if (created.length !== 1) throw new Error('新建数异常 ' + JSON.stringify(created));
  mine = created[0]; out.created.push(mine);
  await esc(1);
  if (!(await selectNode(mine)) || (await selCount()) !== 1) throw new Error('前置不成立：没选中 ⇒ 读数作废');
  const plus = await p.evaluate(() => Array.from(document.querySelectorAll('[aria-label^="Create connected node"]')).map((e) => {
    const q = e.getBoundingClientRect(); if (q.width <= 1) return null;
    return { testid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'), cx: Math.round(q.x + q.width / 2), cy: Math.round(q.y + q.height / 2) }; }).filter(Boolean));
  log('⊕', plus.length, JSON.stringify(plus.map((x) => x.testid)));

  // 跑三轮（每轮都重新开菜单），看**逐帧**尺寸曲线是否可复现
  for (let round = 1; round <= 3; round++) {
    if ((await selCount()) !== 1) { await selectNode(mine); log(`  ↺ 重新选中 selected=${await selCount()}`); }
    if ((await selCount()) !== 1) { log('⛔ 选中不成立，本轮作废'); break; }
    const btn = plus[round % plus.length];
    // 采样器**先装上**再点：CDP 往返几十毫秒，事后轮询会漏掉开头几帧
    const sampler = p.evaluate(() => new Promise((resolve) => {
      const s = []; const t0 = performance.now();
      const tick = () => {
        const ms = Array.from(document.querySelectorAll('[role="menu"]')).filter((e) => e.getBoundingClientRect().width > 0.5);
        const el = ms[ms.length - 1];
        const t = Math.round(performance.now() - t0);
        if (el) { const r = el.getBoundingClientRect();
          const items = Array.from(el.querySelectorAll('[role="menuitem"]')).map((x) => { const q = x.getBoundingClientRect(); return [Math.round(q.width), Math.round(q.height)]; });
          const cs = getComputedStyle(el);
          s.push({ t, menu: [Math.round(r.width), Math.round(r.height)], n: items.length, items, opacity: cs.opacity, transform: cs.transform.slice(0, 40) });
        } else s.push({ t, menu: null, n: 0, items: [] });
        if (t < 2600) setTimeout(tick, 60); else resolve(s);
      };
      tick();
    }));
    await p.waitForTimeout(150);
    await p.mouse.click(btn.cx, btn.cy);
    const samples = await sampler;
    const withMenu = samples.filter((s) => s.menu);
    const uniq = [];
    for (const s of withMenu) { const key = `${s.menu.join('x')}|${s.items[0] ? s.items[0].join('x') : ''}|${s.items.length}|${s.opacity}|${s.transform}`;
      if (!uniq.length || uniq[uniq.length - 1].key !== key) uniq.push({ key, at: s.t, menu: s.menu, n: s.items.length, first: s.items[0], last: s.items[s.items.length - 1], opacity: s.opacity, transform: s.transform }); }
    out.runs.push({ round, btn: btn.testid, uniq, total: samples.length, firstWithMenuAt: withMenu.length ? withMenu[0].t : null, lastAt: withMenu.length ? withMenu[withMenu.length - 1].t : null });
    log(`\n── 第 ${round} 轮（${btn.testid.replace(/flow-node-|-connection-menu-button/g, '')}）尺寸变化点：`);
    for (const u of uniq) log(`   t=+${String(u.at).padStart(4)}ms  菜单 ${u.menu.join('×')}｜项数 ${u.n}｜首项 ${u.first ? u.first.join('×') : '—'}｜opacity ${u.opacity}｜transform ${u.transform}`);
    await esc(1);
  }
  await esc(2);
  log('\n积分（全程）:', await credit());
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
  writeFileSync(OUT, JSON.stringify(out, null, 1));
  try { const led = JSON.parse(readFileSync(LEDGER, 'utf8')); led.ids = [...new Set([...(led.ids || []), ...out.created])].sort();
    led.per_batch = { ...(led.per_batch || {}), 74: out.created }; led.updated_at = new Date().toISOString().slice(0, 10);
    writeFileSync(LEDGER, JSON.stringify(led, null, 1)); log('ledger 追加', JSON.stringify(out.created)); } catch (e) { log('ledger 更新失败', e.message); }
  await b.close();
}
