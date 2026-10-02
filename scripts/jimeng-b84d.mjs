// 批次 84 · D：把 c 轮那个**设计有缺陷的阳性对照**补正。
//
// c 轮：点画布空白 ⇒ 焦点 `DIV[rf__wrapper] aria="Canvas"` ⇒ 按 G ⇒ **无提示**。
// 我当时把它当成「对照失败」，其实它**不是失败，是复现了批次 82 的 A 档**：
//   批次 82 `G@A`（0 选中 + 焦点在画布）→ 无提示；
//   批次 82 `G@B'`（多选中 + 焦点在画布）→ **300ms 弹提示**。
// ⇒ **G 需要「有节点选中」＋「焦点在画布」两样**，c 轮只给了后一样。
//
// 🔑 由此定出本轮真正要验的**完整四格**——把「选中」和「焦点」两个因子交叉，
//    每一格都断言两个因子各自的值，而不是只看「按了有没有反应」：
//
//   | 格 | 选中 | 焦点 | 期望 |
//   |---|---|---|---|
//   │ A │ ✅ 1  │ 画布   │ ✅ 出提示（阳性对照，必须成立，否则后面三格不可信）│
//   │ B │ ✅ 1  │ 输入框 │ 字母进输入框，无提示                              │
//   │ C │ ✅ 1  │ ASIDE   │ 键完全消失，无提示                                │
//   │ D │ ✅ 1  │ 画布（收起后重新框选）│ ✅ 恢复出提示                       │
//
// B/C 与 A 的**唯一差别就是焦点**，这才是「焦点决定快捷键生不生效」的直接证据。
// D 与 A 的唯一差别是**中间开过又关过抽屉**，用来排除「开一次就把快捷键弄坏了」。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport, keyGuard, pressLetter } from './jimeng-safe-keys.mjs';
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0]);
const selCount = () => p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]);
const zoomLabel = () => p.evaluate(() => (document.querySelector('button[aria-label^="Zoom options"]') || {}).getAttribute?.('aria-label'));
const zoomPct = async () => { const l = await zoomLabel(); return l ? Number((l.match(/(\d+)%/) || [])[1]) : null; };
const toast = () => p.evaluate(() => { const c = Array.from(document.querySelectorAll('div,span'))
    .filter((x) => /此快捷键当前不可用/.test((x.innerText || '').trim()) && x.children.length <= 2);
  const e = c.sort((a, b2) => b2.getBoundingClientRect().width - a.getBoundingClientRect().width)[0];
  if (!e) return null; const r = e.getBoundingClientRect();
  return { box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`, text: (e.innerText || '').trim() }; });
const pmText = () => p.evaluate(() => { const e = document.querySelector('[data-testid="prompt-composer"] .ProseMirror');
  return e ? (e.innerText || '').replace(/\n/g, '|').slice(0, 20) : null; });
const drawerOpen = () => p.evaluate(() => { const s = document.querySelector('[data-testid="canvas-feature-sidecar"]'); if (!s) return null;
  const r = s.getBoundingClientRect(); return `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`; });
const setZoom = async (t0) => { for (let t = 1; t <= 3; t++) { if (await zoomPct() === t0) return { ok: true, how: 'already' };
    await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(800);
    if (!await p.evaluate(() => !!document.querySelector('input[data-testid="canvas-zoom-percent-input"]'))) { await p.keyboard.press('Escape'); await p.waitForTimeout(500); continue; }
    await p.evaluate((v) => { const i = document.querySelector('input[data-testid="canvas-zoom-percent-input"]');
      Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(i, String(v));
      i.dispatchEvent(new Event('input', { bubbles: true })); i.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
      i.dispatchEvent(new Event('change', { bubbles: true })); i.blur(); }, t0);
    await p.waitForTimeout(1300); await p.keyboard.press('Escape'); await p.waitForTimeout(600);
    const a = await zoomPct(); await p.waitForTimeout(900); const c = await zoomPct();
    if (a === c && a === t0) return { ok: true, how: 'input', pct: a }; }
  return { ok: false, pct: await zoomPct() }; };
const waitToast = async () => { for (const d of [300, 700, 1500]) { await p.waitForTimeout(d); const t = await toast(); if (t) return { toast: t, afterMs: d }; } return { toast: null, afterMs: 2500 }; };

/** 框选一片 ⇒ 「有节点选中」＋「焦点在画布」两个因子同时成立（批次 83 验过这条路）。 */
const marquee = async () => {
  const geo = await p.evaluate(() => { const ns = Array.from(document.querySelectorAll('.react-flow__node'))
    .map((n) => { const r = n.getBoundingClientRect(); return { x: r.x, y: r.y, w: r.width, h: r.height }; })
    .filter((r) => r.w > 20 && r.y > 60 && r.y + r.h < 700 && r.x > 200);
  if (!ns.length) return null; const r = ns[0]; return r; });
  if (!geo) return null;
  const pad = 30, x0 = Math.round(geo.x - pad), y0 = Math.round(geo.y - pad), x1 = Math.round(geo.x + geo.w + pad), y1 = Math.round(geo.y + geo.h + pad);
  if (x0 < 0 || y0 < 0 || y1 > 716) return null;
  const ok = await p.evaluate(([x, y]) => { const pane = document.querySelector('.react-flow__pane'); const h = document.elementFromPoint(x, y); return !!(pane && h && pane.contains(h)); }, [x0, y0]);
  if (!ok) return null;
  await p.mouse.move(x0, y0); await p.mouse.down();
  for (let k = 1; k <= 6; k++) { await p.mouse.move(Math.round(x0 + (x1 - x0) * k / 6), Math.round(y0 + (y1 - y0) * k / 6)); await p.waitForTimeout(70); }
  await p.mouse.up(); await p.waitForTimeout(900);
  return { from: `${x0},${y0}`, to: `${x1},${y1}` };
};
/** 记录两个因子的当前值。 */
const factors = async () => { const g = await keyGuard(p);
  return { sel: await selCount(), focusWhere: g.where, focusTag: g.tag, focusTestid: g.testid,
    onCanvasPane: /Canvas|react-flow/i.test(g.where), guardSafe: g.safe, pm: await pmText(), drawer: await drawerOpen() }; };
/** 🔑 绕过守卫按 G，同时读「输入框拿到了什么」+「画布有没有提示」。 */
const pressG = async () => { const before = await factors();
  await p.keyboard.press('g');
  const w = await waitToast();
  const after = await factors();
  return { before, toast: w.toast, toastAfterMs: w.afterMs, sampledToMs: 2500, after,
    verdict: w.toast ? '画布收到 G，弹出提示' : (after.pm && after.pm.replace(/\|/g, '').trim() ? '字母被输入框吃掉' : '键完全消失') }; };

try {
  out.zoom = await setZoom(60);
  // 起手：确保抽屉是折叠态
  let st = await drawerOpen(); log('进场抽屉', st);
  if (st && st.startsWith('400x')) { await p.keyboard.press('Meta+Slash'); await p.waitForTimeout(1700); log('⌘/ 收起', await drawerOpen()); }

  out.grids = {};
  // ── 格 A：1 选中 + 焦点在画布（阳性对照） ──
  const mA = await marquee();
  out.grids.A = { marquee: mA, ...(await pressG()) };
  log('格A', JSON.stringify(out.grids.A.verdict), '| sel', out.grids.A.after.sel, '| 焦点', out.grids.A.after.focusWhere);
  if (!out.grids.A.toast) out.verdict = '阳性对照不成立，后续三格不可信';

  // ── 格 B：1 选中 + 焦点在输入框 ──
  await p.keyboard.press('Meta+Slash'); await p.waitForTimeout(1900);
  const pt = await p.evaluate(() => { const e = document.querySelector('[data-testid="prompt-composer"] .ProseMirror'); if (!e) return null;
    const r = e.getBoundingClientRect(); return { x: Math.round(r.x + 20), y: Math.round(r.y + 20) }; });
  if (pt) { await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(900); }
  out.grids.B = { clicked: pt, ...(await pressG()) };
  log('格B', JSON.stringify(out.grids.B.verdict), '| sel', out.grids.B.after.sel, '| 焦点', out.grids.B.after.focusWhere, '| 输入框', JSON.stringify(out.grids.B.after.pm));

  // ── 格 C：1 选中 + 焦点在 ASIDE 侧栏（点一个非输入框的地方） ──
  const head = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('[data-testid="canvas-feature-sidecar"] h1,[data-testid="canvas-feature-sidecar"] h2,[data-testid="canvas-feature-sidecar"] h3'))
      .find((x) => (x.innerText || '').trim().length > 0);
    if (!e) return null; const r = e.getBoundingClientRect(); return { x: Math.round(r.x + 5), y: Math.round(r.y + r.height / 2), t: (e.innerText || '').trim().slice(0, 12) }; });
  if (head) { await p.mouse.click(head.x, head.y); await p.waitForTimeout(900); }
  out.grids.C = { clicked: head, ...(await pressG()) };
  log('格C', JSON.stringify(out.grids.C.verdict), '| sel', out.grids.C.after.sel, '| 焦点', out.grids.C.after.focusWhere);

  // ── 收尾：清脏 + 收起 + 格 D ──
  const pmPt2 = await p.evaluate(() => { const e = document.querySelector('[data-testid="prompt-composer"] .ProseMirror'); if (!e) return null;
    const r = e.getBoundingClientRect(); return { x: Math.round(r.x + 20), y: Math.round(r.y + 20) }; });
  if (pmPt2) { await p.mouse.click(pmPt2.x, pmPt2.y); await p.waitForTimeout(700);
    for (let k = 0; k < 6; k++) { const t = await pmText(); if (!t || !t.replace(/\|/g, '').trim()) break; await p.keyboard.press('Backspace'); await p.waitForTimeout(450); } }
  out.cleaned = await pmText();
  log('清脏后输入框', JSON.stringify(out.cleaned));

  await p.keyboard.press('Meta+Slash'); await p.waitForTimeout(1800);
  const cb = await p.evaluate(() => { const s = document.querySelector('[data-testid="canvas-feature-sidecar"]'); if (!s) return null;
    const x = Array.from(s.querySelectorAll('button,[role="button"]')).find((e) => /收起|折叠|collapse/i.test((e.getAttribute('aria-label') || '') + (e.innerText || '')));
    if (!x) return null; const r = x.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  if (cb) { await p.mouse.click(cb.x, cb.y); await p.waitForTimeout(1700); }
  out.afterCollapse = { drawer: await drawerOpen(), focus: (await keyGuard(p)).where };
  log('收起后', JSON.stringify(out.afterCollapse));

  // ── 格 D：1 选中 + 焦点在画布（重新框选） ──
  const mD = await marquee();
  out.grids.D = { marquee: mD, ...(await pressG()) };
  log('格D', JSON.stringify(out.grids.D.verdict), '| sel', out.grids.D.after.sel, '| 焦点', out.grids.D.after.focusWhere);

  out.zoomFinal = await setZoom(60);
  out.end = { status: await status(), zoom: await zoomLabel(), drawer: await drawerOpen(), pm: await pmText(), sel: await selCount() };
  log('终态', JSON.stringify(out.end));
} catch (e) { out.error = e.message; console.error('ABORT:', e.message); }
writeFileSync(new URL('./_tmp-b84d.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
