// 批次 92 · E：给 P1 补上**焦点前置**再测一次 ⌘Z。
//
// d 轮的结果是「⌘Z 没恢复被删的副本」，但**那一轮没有断言焦点在画布上** ——
// 按完「删除」菜单项之后，焦点可能不在画布容器里。
// 本页第 178 行自己就写过同一个坑：「从『搜索』面板选中的节点，按 ⌫ 删不掉」，
// 原因是**焦点没落到画布上**，React Flow 收不到按键。
// ⇒ **在断言「⌘Z 失效」之前，必须先断言 `document.activeElement` 在画布里。**
//     否则就是把「我没测到前置」打成「功能不存在」（批次 88 的第三次复发）。
//
// ⇒ 本轮把 P1 拆成两格，**焦点是唯一变量**：
//   格 1：删除后**不碰焦点**，直接 ⌘Z
//   格 2：删除后**先点空白画布把焦点交回画布**，再 ⌘Z
//   ⇒ 若格 1 不恢复、格 2 恢复 ⇒ 结论是「⌘Z 依赖画布焦点」，不是「⌘Z 不能用」。
import { chromium } from 'playwright';
import { writeFileSync, readFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const LEDGER = new URL('./jimeng-ephemeral-ledger.json', import.meta.url);
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };
const mine = [];

const ids = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const selN = async () => p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]);
const credits = async () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-commerce-entry"]'); return e ? e.getAttribute('aria-label') : null; });
const zoomPct = async () => p.evaluate(() => { const e = document.querySelector('button[aria-label^="Zoom options"]'); return e ? Number((e.getAttribute('aria-label').match(/(\d+)%/) || [])[1]) : null; });
const info = (id) => p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return null;
  const m = (n.getAttribute('style') || '').match(/translate\(\s*([-\d.]+)px,\s*([-\d.]+)px/);
  return { aria: n.getAttribute('aria-label'), x: m ? Number(m[1]) : null, y: m ? Number(m[2]) : null }; }, id);
/** 🔑 本轮的关键读数：焦点到底在不在画布里 */
const focusRead = () => p.evaluate(() => { const a = document.activeElement; if (!a) return { tag: null, inCanvas: false };
  const inCanvas = !!(a.closest && (a.closest('.react-flow') || a.closest('[data-testid="canvas-main-region"]')));
  return { tag: a.tagName, tid: a.getAttribute('data-testid'), aria: a.getAttribute('aria-label'),
    cls: String(a.className || '').slice(0, 40), inCanvas }; });
const setZoom = async (t0) => { for (let t = 1; t <= 3; t++) { if (await zoomPct() === t0) return true;
  await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(800);
  const has = await p.evaluate(() => !!document.querySelector('input[data-testid="canvas-zoom-percent-input"]'));
  if (!has) { await p.keyboard.press('Escape'); await p.waitForTimeout(500); continue; }
  await p.evaluate((v) => { const i = document.querySelector('input[data-testid="canvas-zoom-percent-input"]');
    Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(i, String(v));
    i.dispatchEvent(new Event('input', { bubbles: true })); i.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
    i.dispatchEvent(new Event('change', { bubbles: true })); i.blur(); }, t0);
  await p.waitForTimeout(1400); await p.keyboard.press('Escape'); await p.waitForTimeout(700); return true; } return false; };
const scan = (id) => p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return null;
  const r = n.getBoundingClientRect();
  for (let fx = 0.04; fx <= 0.96; fx += 0.04) for (let fy = 0.04; fy <= 0.96; fy += 0.04) {
    const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
    if (x < 0 || y < 0 || x > 1280 || y > 720) continue;
    const el = document.elementFromPoint(x, y);
    if (el && el.closest('.react-flow__node') === n) return { x, y }; }
  return { fail: true }; }, id);
const selectNode = async (id) => { for (const z of [await zoomPct(), 100, 200, 400, 800]) { if (!await setZoom(z)) continue;
  const pt = await scan(id); if (!pt || pt.fail) continue;
  await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1000);
  const got = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
  if (got[0] === id) return { ok: true, zoom: z, pt };
  await p.keyboard.press('Escape'); await p.waitForTimeout(500); } return { ok: false }; };
const openMenu = async (x, y) => { await p.mouse.move(x, y); await p.waitForTimeout(150);
  await p.mouse.down({ button: 'right' }); await p.waitForTimeout(220); await p.mouse.up({ button: 'right' }); await p.waitForTimeout(1100);
  return p.evaluate(() => { const m = document.querySelector('[data-testid="canvas-context-menu"]'); if (!m) return null;
    return Array.from(m.querySelectorAll('[role="menuitem"]')).map((x) => ({ t: x.innerText.replace(/\s+/g, ' ').trim(), dis: x.getAttribute('aria-disabled') })); }); };
const clickItem = async (src) => { const ok = await p.evaluate((s) => { const m = document.querySelector('[data-testid="canvas-context-menu"]'); if (!m) return false;
  const it = Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => new RegExp(s).test(x.innerText.replace(/\s+/g, ' ').trim())); if (it) { it.click(); return true; } return false; }, src);
  await p.waitForTimeout(1700); return ok; };
/** 找一个真正空白、且点它之后焦点会落进画布的点 */
const blankPoint = () => p.evaluate(() => { const r = document.querySelector('.react-flow__pane'); if (!r) return null;
  const q = r.getBoundingClientRect();
  for (let fx = 0.1; fx <= 0.9; fx += 0.05) for (let fy = 0.1; fy <= 0.9; fy += 0.05) {
    const x = Math.round(q.x + q.width * fx), y = Math.round(q.y + q.height * fy);
    const el = document.elementFromPoint(x, y);
    if (el && !el.closest('.react-flow__node') && !el.closest('button') && !el.closest('input')) return { x, y }; }
  return null; });

try {
  if (await selN() !== '0') { await p.keyboard.press('Escape'); await p.waitForTimeout(600); }
  await setZoom(60);
  out.start = { nodes: (await ids()).length, sel: await selN(), credits: await credits(), zoom: await zoomPct(), focus: await focusRead() };
  log('起点：', JSON.stringify(out.start));

  const mkCopy = async (label) => {
    const pre0 = await ids();
    const rail = await p.evaluate(() => { const el = Array.from(document.querySelectorAll('button,[role="button"]'))
      .find((x) => /^文本$/.test(((x.getAttribute('aria-label') || '') + (x.innerText || '')).trim()));
      if (!el) return null; const r = el.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
    await p.mouse.click(rail.x, rail.y); await p.waitForTimeout(3800);
    const A = (await ids()).filter((x) => !pre0.includes(x))[0]; if (!A) throw new Error('新建失败');
    mine.push(A); await p.keyboard.press('Escape'); await p.waitForTimeout(800);
    const s = await selectNode(A); if (!s.ok) throw new Error('A 选不中');
    const r = await openMenu(s.pt.x, s.pt.y); if (!r) throw new Error('菜单没开');
    const pre1 = await ids(); await clickItem('^复制副本');
    const B = (await ids()).filter((x) => !pre1.includes(x))[0]; if (B) mine.push(B);
    log(`  ${label}：A=${A}（${(await info(A)).aria}） 副本 B=${B}（${B ? (await info(B)).aria : '无'}）`);
    return { A, B, s };
  };

  // ═══ 格 1：删除后**不碰焦点**，直接 ⌘Z ═══
  const g1 = await mkCopy('格1 造节点');
  if (g1.B) {
    const s = await selectNode(g1.B);
    const r = await openMenu(s.pt.x, s.pt.y);
    const focusBeforeMenu = await focusRead();
    await clickItem('^删除');
    out.g1 = { deleteOk: !(await ids()).includes(g1.B), focusBeforeMenu, focusAfterDelete: await focusRead(), nodesAfter: (await ids()).length };
    log('格1 删除后焦点：', JSON.stringify(out.g1.focusAfterDelete));
    await p.keyboard.press('Meta+z'); await p.waitForTimeout(2200);
    const back = await ids();
    out.g1_undo = { bBack: back.includes(g1.B), nodes: back.length, focus: await focusRead() };
    log('格1 ⌘Z（焦点未交回）：', JSON.stringify(out.g1_undo));
  }

  // ═══ 格 2：删除后**先点空白画布**，再 ⌘Z ═══
  const g2 = await mkCopy('格2 造节点');
  if (g2.B) {
    const s = await selectNode(g2.B);
    await openMenu(s.pt.x, s.pt.y); await clickItem('^删除');
    out.g2 = { deleteOk: !(await ids()).includes(g2.B), nodesAfter: (await ids()).length };
    const bp = await blankPoint();
    if (bp) { await p.mouse.click(bp.x, bp.y); await p.waitForTimeout(900); }
    out.g2.focus = await focusRead();
    out.g2.blankPoint = bp;
    log('格2 点空白后焦点：', JSON.stringify(out.g2.focus));
    await p.keyboard.press('Meta+z'); await p.waitForTimeout(2200);
    const back = await ids();
    out.g2_undo = { bBack: back.includes(g2.B), bInfo: back.includes(g2.B) ? await info(g2.B) : null, nodes: back.length };
    log('格2 ⌘Z（焦点已交回画布）：', JSON.stringify(out.g2_undo));
  }
  out.verdict = { g1_restores: out.g1_undo?.bBack, g2_restores: out.g2_undo?.bBack,
    sameIdInG2: out.g2_undo?.bBack ? (out.g2_undo.bInfo?.aria || '') : null,
    conclusion: out.g1_undo?.bBack === out.g2_undo?.bBack ? '焦点不是变量' : '⌘Z 依赖画布焦点' };
  log('判定：', JSON.stringify(out.verdict));
} catch (e) { out.error = String(e); log('🔴', String(e)); }
finally {
  log('── 收尾');
  await setZoom(60);
  for (const id of mine) { if (!(await ids()).includes(id)) continue;
    const s = await selectNode(id); if (!s.ok) { log('  ⚠️ 选不中', id); continue; }
    const r = await openMenu(s.pt.x, s.pt.y); if (r) await clickItem('^删除');
    log('  删', id, '→', (await ids()).includes(id) ? '🔴 还在' : '✅'); }
  if (await selN() !== '0') { await p.keyboard.press('Escape'); await p.waitForTimeout(600); }
  await setZoom(60);
  const left = (await ids()).filter((x) => mine.includes(x));
  out.cleanup = { mine, leftover: left, nodes: (await ids()).length };
  log('清理', mine.length, '→ 剩', left.length, left.length ? '🔴 ' + left.join(' ') : '✅', '｜画布', out.cleanup.nodes);
  if (!left.length && mine.length) { try { const led = JSON.parse(readFileSync(LEDGER, 'utf8'));
    const add = mine.filter((x) => !led.ids.includes(x));
    if (add.length) { led.ids = [...new Set([...led.ids, ...add])].sort();
      led.per_batch = { ...(led.per_batch || {}), 92: [...new Set([...(led.per_batch?.['92'] || []), ...mine])] };
      led.updated_at = new Date().toISOString().slice(0, 10); writeFileSync(LEDGER, JSON.stringify(led, null, 1)); log('已登记台账'); } } catch (e) { log('台账失败', String(e)); } }
  out.end = { credits: await credits(), zoom: await zoomPct() };
  writeFileSync(new URL('./_tmp-b92e.json', import.meta.url), JSON.stringify(out, null, 1));
  await b.close();
}
