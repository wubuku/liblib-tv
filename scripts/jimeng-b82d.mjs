// 批次 82 · D：第三轮修判据，并让**每个键独立失败不连坐**。
// ① 抽屉：前两版分别抓到「全屏遮罩 1280×720」与「内层 232×356」。
//    这次**以关闭钮为锚**：先找 aria-label 含「关闭/Close」的元素，再向上走到
//    第一个宽度 < 400 的祖先 —— 那才是既带 ✕ 又带滚动列表的抽屉面板。
// ② 焦点：**点文本节点主体会直接进编辑态**（焦点落 `DIV aria="Text"`、
//    出现 `.ProseMirror`）—— 批次 77 早就记过这个坑，我连踩两次。
//    正解流程（批次 77 原话）：**点空白 → 再点标题行**。
//    「点空白」也要验：落点 `elementFromPoint` 必须是 `.react-flow__pane`，
//    否则就是点在别人的节点上，不能算空白。
// ③ 每个键的前置不成立时**只把这一个键记 VOID**，继续测下一个 —— 不再让一个坑带走整批。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport, keyGuard, pressLetter } from './jimeng-safe-keys.mjs';
const BASE = JSON.parse(readFileSync(new URL('./jimeng-baseline-nodes.json', import.meta.url), 'utf8'));
const LEDGER = new URL('./jimeng-ephemeral-ledger.json', import.meta.url);
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const ids = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };
let mine = null;
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0]);
const selCount = () => p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]);
const zoomLabel = () => p.evaluate(() => (document.querySelector('button[aria-label^="Zoom options"]') || {}).getAttribute?.('aria-label'));
const dockBtn = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-pointer-tool-toggle"]');
  return e ? { aria: e.getAttribute('aria-label'), pressed: e.getAttribute('aria-pressed') } : null; });
const toast = () => p.evaluate(() => { const c = Array.from(document.querySelectorAll('div,span'))
    .filter((x) => /此快捷键当前不可用/.test((x.innerText || '').trim()) && x.children.length <= 2);
  const e = c.sort((a, b) => b.getBoundingClientRect().width - a.getBoundingClientRect().width)[0];
  if (!e) return null; const r = e.getBoundingClientRect();
  return { box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`, text: (e.innerText || '').trim() }; });
/** 批次 77 正解：点**空白**（落点必须是 `.react-flow__pane`）→ 再点**标题行**。 */
const selectSafely = async (v) => {
  const empty = await p.evaluate(() => { const pane = document.querySelector('.react-flow__pane'); if (!pane) return null;
    for (let y = 120; y < 660; y += 30) for (let x = 200; x < 1240; x += 40) {
      const h = document.elementFromPoint(x, y);
      if (h && (h === pane || pane.contains(h))) return { x, y }; }
    return null; });
  if (!empty) return { ok: false, why: '找不到可确认的空白落点' };
  await p.mouse.click(empty.x, empty.y); await p.waitForTimeout(700);
  const t = await p.evaluate((id) => { const n = document.querySelector(`.react-flow__node[data-id="${id}"]`); const r = n.getBoundingClientRect();
    return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y - 15) }; }, v);
  await p.mouse.click(t.x, t.y); await p.waitForTimeout(900);
  const g = await keyGuard(p);
  const sel = await p.evaluate((id) => { const n = document.querySelector(`.react-flow__node[data-id="${id}"]`); return /(^|\s)selected(\s|$)/.test(n.className); }, v);
  const inEdit = await p.evaluate(() => !!document.querySelector('.ProseMirror[contenteditable="true"]'));
  return { ok: sel && !inEdit && /Canvas|react-flow|body/i.test(g.where), emptyAt: `${empty.x},${empty.y}`,
    selected: sel, enteredEdit: inEdit, focusWhere: g.where, guardSafe: g.safe };
};
try {
  // —————————————— ① 抽屉：以关闭钮为锚 ——————————————
  const um = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-user-menu-trigger"]'); if (!e) return null;
    const r = e.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  await p.mouse.click(um.x, um.y); await p.waitForTimeout(1300);
  const sk = await p.evaluate(() => { const it = Array.from(document.querySelectorAll('[role="menuitem"],[role="menuitemradio"]'))
    .find((e) => /快捷键/.test(e.innerText || '')); if (!it) return null;
    const r = it.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  await p.mouse.click(sk.x, sk.y); await p.waitForTimeout(1800);
  out.drawer = await p.evaluate(() => {
    const cls = document.querySelector('div,aside,section');
    // 锚：可见的关闭钮
    const closes = Array.from(document.querySelectorAll('button,[role="button"]'))
      .filter((e) => { const a = e.getAttribute('aria-label') || ''; return /关闭|Close/i.test(a) && e.getBoundingClientRect().width > 1; });
    if (!closes.length) return { found: false, why: '找不到关闭钮' };
    const close = closes.sort((a, b) => b.getBoundingClientRect().width - a.getBoundingClientRect().width)[0];
    // 从关闭钮向上找第一个「窄 + 含通用操作」的祖先
    let panel = null;
    for (let e = close; e && e !== document.body; e = e.parentElement) {
      const b = e.getBoundingClientRect();
      if (b.width > 100 && b.width < 400 && /通用操作/.test(e.innerText || '')) { panel = e; break; }
    }
    if (!panel) { const b = close.closest('aside') || close.parentElement; panel = b; }
    const r = panel.getBoundingClientRect();
    let sc = null; for (const e of [panel, ...panel.querySelectorAll('*')]) if (e.scrollHeight > e.clientHeight + 8 && e.clientHeight > 100) { sc = e; break; }
    return { found: true, closeAria: close.getAttribute('aria-label'),
      box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
      title: (panel.querySelector('h1,h2,h3,[class*="itle"]') || {}).innerText || null,
      scroller: sc ? { scrollHeight: sc.scrollHeight, clientHeight: sc.clientHeight, testid: sc.getAttribute('data-testid') || '' } : null };
  });
  log('抽屉', JSON.stringify(out.drawer, null, 1));
  if (out.drawer.found) {
    out.panelRows = []; const seen = new Set();
    for (let step = 0; step < 14; step++) {
      const rows = await p.evaluate(() => {
        const closes = Array.from(document.querySelectorAll('button,[role="button"]'))
          .filter((e) => { const a = e.getAttribute('aria-label') || ''; return /关闭|Close/i.test(a) && e.getBoundingClientRect().width > 1; })
          .sort((a, b) => b.getBoundingClientRect().width - a.getBoundingClientRect().width);
        let panel = null;
        for (let e = closes[0]; e && e !== document.body; e = e.parentElement) {
          const b = e.getBoundingClientRect();
          if (b.width > 100 && b.width < 400 && /通用操作/.test(e.innerText || '')) { panel = e; break; } }
        if (!panel) return [];
        const res = [];
        for (const e of panel.querySelectorAll('div')) {
          if (e.children.length > 3) continue;
          const lines = (e.innerText || '').trim().split('\n').map((x) => x.trim()).filter(Boolean);
          if (lines.length < 2 || lines[1].length > 16) continue;
          res.push({ fn: lines[0].slice(0, 24), key: lines[1] });
        }
        return res;
      });
      for (const r of rows) { const k = r.fn + '|' + r.key; if (!seen.has(k)) { seen.add(k); out.panelRows.push(r); } }
      const mv = await p.evaluate(() => {
        const closes = Array.from(document.querySelectorAll('button,[role="button"]'))
          .filter((e) => { const a = e.getAttribute('aria-label') || ''; return /关闭|Close/i.test(a) && e.getBoundingClientRect().width > 1; })
          .sort((a, b) => b.getBoundingClientRect().width - a.getBoundingClientRect().width);
        let panel = null;
        for (let e = closes[0]; e && e !== document.body; e = e.parentElement) {
          const b = e.getBoundingClientRect();
          if (b.width > 100 && b.width < 400 && /通用操作/.test(e.innerText || '')) { panel = e; break; } }
        if (!panel) return null;
        for (const e of [panel, ...panel.querySelectorAll('*')]) if (e.scrollHeight > e.clientHeight + 8 && e.clientHeight > 100) {
          const before = e.scrollTop; e.scrollTop = before + Math.max(100, e.clientHeight - 50);
          return { before, after: e.scrollTop }; }
        return null; });
      if (!mv || mv.after === mv.before) break;
    }
    log('面板行（' + out.panelRows.length + '）：');
    for (const r of out.panelRows) log('   ', r.fn.padEnd(16), r.key);
  }
  await p.keyboard.press('Escape'); await p.waitForTimeout(1100);
  out.drawerClosed = await p.evaluate(() => !Array.from(document.querySelectorAll('button,[role="button"]'))
    .some((e) => { const a = e.getAttribute('aria-label') || ''; return /关闭|Close/i.test(a) && /通用操作/.test((e.closest('div,aside') || document.body).innerText || '') && e.getBoundingClientRect().width > 1; }));
  log('抽屉已关闭 =', out.drawerClosed);

  // —————————————— ② 四个键：逐个独立，互不连坐 ——————————————
  const pre = await ids();
  const rail = await p.evaluate(() => { const el = Array.from(document.querySelectorAll('button,[role="button"]'))
    .find((x) => /^文本$/.test(((x.getAttribute('aria-label') || '') + (x.innerText || '')).trim()));
    const r = el.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  await p.mouse.click(rail.x, rail.y); await p.waitForTimeout(3000);
  const made = (await ids()).filter((x) => !pre.includes(x));
  if (made.length !== 1) throw new Error('新建异常');
  mine = made[0];
  const prepare = async () => { const s = await selectSafely(mine); log('  前置', JSON.stringify(s)); return s; };
  out.keys = {};
  // G
  try {
    const s = await prepare();
    out.keys.G = { pre: s };
    if (!s.ok) out.keys.G.void = '前置不成立';
    else { const g = await keyGuard(p); if (!g.safe) out.keys.G.void = 'keyGuard 拒绝';
      else { await pressLetter(p, 'g');
        for (const d of [250, 700, 1500, 2500]) { await p.waitForTimeout(d); const t = await toast(); if (t) { out.keys.G.toast = t; out.keys.G.toastAtMs = d; break; } }
        if (!out.keys.G.toast) out.keys.G.toast = null; } }
  } catch (e) { out.keys.G = { error: e.message }; }
  log('G →', JSON.stringify(out.keys.G));
  // V
  try {
    const s = await prepare();
    out.keys.V = { pre: s, dockBefore: await dockBtn() };
    if (!s.ok) out.keys.V.void = '前置不成立';
    else { const g = await keyGuard(p); if (!g.safe) out.keys.V.void = 'keyGuard 拒绝';
      else { await pressLetter(p, 'v'); await p.waitForTimeout(1100); out.keys.V.dockAfter = await dockBtn(); } }
  } catch (e) { out.keys.V = { error: e.message }; }
  log('V →', JSON.stringify(out.keys.V));
  // ⌘A
  try {
    const s = await prepare();
    out.keys.cmdA = { pre: s, before: await selCount() };
    if (!s.ok) out.keys.cmdA.void = '前置不成立';
    else { await p.keyboard.press('Meta+A'); await p.waitForTimeout(1000); out.keys.cmdA.after = await selCount(); }
  } catch (e) { out.keys.cmdA = { error: e.message }; }
  log('⌘A →', JSON.stringify(out.keys.cmdA));
  await p.keyboard.press('Escape'); await p.waitForTimeout(700);
  // ⇧2
  try {
    const s = await prepare();
    out.keys.shift2 = { pre: s, zoomBefore: await zoomLabel() };
    if (!s.ok) out.keys.shift2.void = '前置不成立';
    else { const g = await keyGuard(p); if (!g.safe) out.keys.shift2.void = 'keyGuard 拒绝';
      else { await p.keyboard.press('Shift+Digit2'); await p.waitForTimeout(1300); out.keys.shift2.zoomAfter = await zoomLabel(); } }
  } catch (e) { out.keys.shift2 = { error: e.message }; }
  log('⇧2 →', JSON.stringify(out.keys.shift2));
} catch (e) { out.error = e.message; console.error('ABORT:', e.message); }
finally {
  for (let i = 0; i < 2; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(450); }
  if (mine) {
    for (let a = 1; a <= 3 && (await ids()).includes(mine); a++) {
      const q = await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!n) return null;
        const r = n.getBoundingClientRect();
        for (const f of [[0.5, 0.5], [0.5, 0.2], [0.25, 0.5], [0.75, 0.5], [0.5, 0.8]]) { const x = Math.round(r.x + r.width * f[0]), y = Math.round(r.y + r.height * f[1]);
          const h = document.elementFromPoint(x, y); if (h && n.contains(h) && !h.closest('[role="menu"]')) return { x, y }; } return null; }, mine);
      if (!q) break;
      await p.mouse.click(q.x, q.y, { button: 'right' }); await p.waitForTimeout(1000);
      await p.evaluate(() => { const m = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"],[role="menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop();
        const it = m && Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => /删除/.test(x.innerText || '')); if (it) it.click(); });
      await p.waitForTimeout(1500);
    }
    log('清理', mine, (await ids()).includes(mine) ? '🔴 仍在' : '✅');
  }
  out.end = { status: await status(), zoomLabel: await zoomLabel() };
  log('终态', JSON.stringify(out.end));
  try { const led = JSON.parse(readFileSync(LEDGER, 'utf8')); if (mine && !led.ids.includes(mine)) {
    led.ids = [...new Set([...led.ids, mine])].sort();
    led.per_batch = { ...(led.per_batch || {}), 82: [...new Set([...(led.per_batch?.['82'] || []), mine])] };
    writeFileSync(LEDGER, JSON.stringify(led, null, 1)); } } catch {}
  writeFileSync(new URL('./_tmp-b82d.json', import.meta.url), JSON.stringify(out, null, 1));
  await b.close();
}
