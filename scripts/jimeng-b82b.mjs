// 批次 82 · B：修两处**前置条件不完整**后重跑。
// ① 上一版点「快捷键」之后又按了一次 Esc —— 抽屉已经被那次点击打开了，
//    Esc 正好把它关掉，于是 `drawer.found:false`。
//    修法：点完之后先判断**菜单是否还开着**，开着才按 Esc。
// ② 更要紧：上一版按 G / ⇧2 / ⌘A / V 时，`keyGuard` 报 `where: BUTTON aria="文本"`
//    —— **焦点还停在左栏那个按钮上，不在画布上**。
//    「节点被选中」≠「焦点在画布上」（批次 77 的老坑），页面自己的表里也写了
//    「⌘ + 滚轮：焦点在画布上才生效」。
//    ⇒ 上一轮那四个键的读数**全部作废(VOID)**。本轮先把焦点挪到画布再按，
//      并把 `keyGuard` 报的 `where` 一起记进证据。
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
const toast = () => p.evaluate(() => { const cands = Array.from(document.querySelectorAll('div,span'))
    .filter((x) => /此快捷键当前不可用/.test((x.innerText || '').trim()) && x.children.length <= 2);
  const e = cands.sort((a, c) => c.getBoundingClientRect().width - a.getBoundingClientRect().width)[0];
  if (!e) return null; const r = e.getBoundingClientRect();
  return { box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`, text: (e.innerText || '').trim() }; });
/** 把焦点从左栏挪回画布：点**自建节点的标题行**（批次 77：点标题行最安全）。 */
const focusToCanvas = async (v) => {
  const t = await p.evaluate((id) => { const n = document.querySelector(`.react-flow__node[data-id="${id}"]`); const r = n.getBoundingClientRect();
    return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y - 15) }; }, v);
  await p.mouse.click(t.x, t.y); await p.waitForTimeout(900);
  const g = await keyGuard(p);
  const sel = await p.evaluate((id) => { const n = document.querySelector(`.react-flow__node[data-id="${id}"]`); return /(^|\s)selected(\s|$)/.test(n.className); }, v);
  return { where: g.where, safe: g.safe, selected: sel, guardReason: g.reason || null };
};
try {
  // —————————————— ① 用户菜单 + 快捷键抽屉（不再多余按 Esc） ——————————————
  const um = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-user-menu-trigger"]'); if (!e) return null;
    const r = e.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  await p.mouse.click(um.x, um.y); await p.waitForTimeout(1300);
  out.userMenu = await p.evaluate(() => {
    const m = Array.from(document.querySelectorAll('[role="menu"],[data-testid*="menu"]')).filter((e) => e.getBoundingClientRect().width > 1)
      .sort((a, c) => c.getBoundingClientRect().height - a.getBoundingClientRect().height)[0];
    if (!m) return { found: false };
    const r = m.getBoundingClientRect();
    // 账号信息区：菜单**顶部**、第一个 menuitem 之前的兄弟节点
    const firstItem = m.querySelector('[role="menuitem"],[role="menuitemradio"]');
    let account = null;
    for (let e = m; e && e !== document.body; e = e.parentElement) {
      const cand = Array.from(e.children).filter((c) => c !== firstItem && /昵称|会员|账号|创作|积分/.test(c.innerText || ''));
      if (cand.length) { const q = cand[0].getBoundingClientRect();
        account = { text: (cand[0].innerText || '').trim().split('\n').slice(0, 3).join(' / ').slice(0, 60),
          box: `${Math.round(q.width)}x${Math.round(q.height)}@${Math.round(q.x)},${Math.round(q.y)}` }; break; }
    }
    return { found: true, box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
      count: m.querySelectorAll('[role="menuitem"],[role="menuitemradio"]').length,
      items: Array.from(m.querySelectorAll('[role="menuitem"],[role="menuitemradio"]')).map((e) => (e.innerText || '').split('\n').filter(Boolean).slice(-1)[0] || ''),
      account };
  });
  log('用户菜单', JSON.stringify(out.userMenu, null, 1));
  const sk = await p.evaluate(() => { const it = Array.from(document.querySelectorAll('[role="menuitem"],[role="menuitemradio"]'))
    .find((e) => /快捷键/.test(e.innerText || '')); if (!it) return null;
    const r = it.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  await p.mouse.click(sk.x, sk.y); await p.waitForTimeout(1800);
  // ⚠️ 只有**菜单还开着**才按 Esc 关它；抽屉此刻应该已经打开了
  const menuStillOpen = await p.evaluate(() => Array.from(document.querySelectorAll('[role="menu"]')).some((e) => e.getBoundingClientRect().width > 1));
  out.menuStillOpenAfterClick = menuStillOpen;
  if (menuStillOpen) { await p.keyboard.press('Escape'); await p.waitForTimeout(900); }
  log('点「快捷键」后菜单仍开着 =', menuStillOpen);
  const drawerFound = await p.evaluate(() => Array.from(document.querySelectorAll('div,aside,section'))
    .some((e) => /快捷键/.test(e.innerText || '') && e.getBoundingClientRect().width > 100 && e.getBoundingClientRect().height > 100));
  out.drawerFound = drawerFound; log('抽屉出现 =', drawerFound);
  if (!drawerFound) throw new Error('抽屉仍没出现 ⇒ 后续作废(VOID)');
  // 逐屏滚动读全四组
  out.panelRows = []; const seen = new Set();
  for (let step = 0; step < 10; step++) {
    const rows = await p.evaluate(() => {
      const d = Array.from(document.querySelectorAll('div,aside,section')).filter((e) => {
        const b = e.getBoundingClientRect(); return /快捷键/.test(e.innerText || '') && b.width > 100 && b.height > 100; })
        .sort((a, c) => (c.innerText || '').length - (a.innerText || '').length)[0];
      if (!d) return [];
      const res = [];
      for (const e of d.querySelectorAll('div')) {
        if (e.children.length > 3) continue;
        const lines = (e.innerText || '').trim().split('\n').map((x) => x.trim()).filter(Boolean);
        if (lines.length < 2) continue;
        res.push({ fn: lines[0].slice(0, 22), key: lines.slice(1).join(' ').slice(0, 22) });
      }
      return res;
    });
    for (const r of rows) { const k = r.fn + '|' + r.key; if (!seen.has(k)) { seen.add(k); out.panelRows.push(r); } }
    const mv = await p.evaluate(() => {
      const d = Array.from(document.querySelectorAll('div,aside,section')).filter((e) => {
        const b = e.getBoundingClientRect(); return /快捷键/.test(e.innerText || '') && b.width > 100 && b.height > 100; })
        .sort((a, c) => (c.innerText || '').length - (a.innerText || '').length)[0];
      for (const e of [d, ...d.querySelectorAll('*')]) if (e.scrollHeight > e.clientHeight + 8 && e.clientHeight > 100) {
        const before = e.scrollTop; e.scrollTop = before + Math.max(120, e.clientHeight - 60);
        return { before, after: e.scrollTop, max: e.scrollHeight - e.clientHeight }; }
      return null; });
    if (!mv || mv.after === mv.before) break;
  }
  out.drawerBox = await p.evaluate(() => { const d = Array.from(document.querySelectorAll('div,aside,section'))
      .filter((e) => { const b = e.getBoundingClientRect(); return /快捷键/.test(e.innerText || '') && b.width > 100 && b.height > 100; })
      .sort((a, c) => (c.innerText || '').length - (a.innerText || '').length)[0];
    const b = d.getBoundingClientRect();
    let sc = null; for (const e of [d, ...d.querySelectorAll('*')]) if (e.scrollHeight > e.clientHeight + 8 && e.clientHeight > 100) { sc = e; break; }
    return { box: `${Math.round(b.width)}x${Math.round(b.height)}@${Math.round(b.x)},${Math.round(b.y)}`,
      scroller: sc ? { scrollHeight: sc.scrollHeight, clientHeight: sc.clientHeight, testid: sc.getAttribute('data-testid') || '' } : null,
      hasCloseBtn: !!d.querySelector('[aria-label*="lose" i]') }; });
  log('抽屉', JSON.stringify(out.drawerBox, null, 1));
  log('读到的面板行（' + out.panelRows.length + '）：');
  for (const r of out.panelRows) log('   ', r.fn.padEnd(14), r.key);
  await p.keyboard.press('Escape'); await p.waitForTimeout(1000);
  out.drawerClosed = await p.evaluate(() => !Array.from(document.querySelectorAll('div,aside,section'))
    .some((e) => /快捷键/.test(e.innerText || '') && e.getBoundingClientRect().width > 100 && e.getBoundingClientRect().height > 100));
  log('抽屉已关闭 =', out.drawerClosed);

  // —————————————— ② 四个键：**先把焦点挪到画布**再按 ——————————————
  const pre = await ids();
  const rail = await p.evaluate(() => { const el = Array.from(document.querySelectorAll('button,[role="button"]'))
    .find((x) => /^文本$/.test(((x.getAttribute('aria-label') || '') + (x.innerText || '')).trim()));
    const r = el.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  await p.mouse.click(rail.x, rail.y); await p.waitForTimeout(3000);
  const made = (await ids()).filter((x) => !pre.includes(x));
  if (made.length !== 1) throw new Error('新建异常');
  mine = made[0];
  const foc = await focusToCanvas(mine);
  out.focus = foc; log('焦点归位', JSON.stringify(foc), '|', await status());
  if (!foc.selected) throw new Error('节点未选中 ⇒ VOID');
  if (!/body|react-flow|DIV\.react/i.test(foc.where) && !foc.safe) throw new Error('焦点仍不安全 ⇒ VOID');

  // ②a G（页面记：选中后弹「此快捷键当前不可用」）
  out.gKey = { focusWhere: foc.where, before: { sel: await selCount() } };
  const gG = await keyGuard(p); if (!gG.safe) throw new Error('keyGuard 拒绝：' + gG.reason);
  await pressLetter(p, 'g');
  for (const d of [250, 800, 1600]) { await p.waitForTimeout(d); const t = await toast(); if (t) { out.gKey.toast = t; out.gKey.toastAtMs = d; break; } }
  if (!out.gKey.toast) out.gKey.toast = null;
  log('G →', JSON.stringify(out.gKey));

  // ②b V
  out.vKey = { dockBefore: await dockBtn() };
  const gv = await keyGuard(p); if (!gv.safe) throw new Error('keyGuard 拒绝');
  await pressLetter(p, 'v'); await p.waitForTimeout(1100);
  out.vKey.dockAfter = await dockBtn();
  log('V →', JSON.stringify(out.vKey));

  // ②c ⌘A
  out.cmdA = { before: await selCount() };
  await p.keyboard.press('Meta+A'); await p.waitForTimeout(1000);
  out.cmdA.after = await selCount();
  log('⌘A →', JSON.stringify(out.cmdA));
  await p.keyboard.press('Escape'); await p.waitForTimeout(600);

  // ②d ⇧2
  const f2 = await focusToCanvas(mine);
  out.shift2 = { focus: f2.where, selected: f2.selected, zoomBefore: await zoomLabel() };
  const g2 = await keyGuard(p); if (!g2.safe) throw new Error('keyGuard 拒绝');
  await p.keyboard.press('Shift+Digit2'); await p.waitForTimeout(1300);
  out.shift2.zoomAfter = await zoomLabel();
  log('⇧2 →', JSON.stringify(out.shift2));
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
  writeFileSync(new URL('./_tmp-b82b.json', import.meta.url), JSON.stringify(out, null, 1));
  await b.close();
}
