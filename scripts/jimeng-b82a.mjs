// 批次 82 · A：快捷键面板与用户菜单的**逐字复核**，外加三个高价值键的复测。
// 为什么打这一页：它是普查的下一名（批次 60）。更关键的是**页面第 272 行声称
// 「本手册的快捷键表已无未确认项」**，而那张全表是 **2026-10-01** 抓的 ——
// 而批次 81 刚证明**构建已经变了**（顶栏多出「分享」「更多」）。面板很可能也变了。
//
// 三件事：
// ① 用户菜单六项 + 快捷键抽屉（四组全表）**逐字**复核当前构建；
// ② 三个「声明 ≠ 可用」的键复测：**⌘A**（页面记「无效」）、**⇧2**（页面记「直接按键无效」）、
//    **V**（页面记「不切换工具」）、**G**（页面记「选中后才弹不可用提示」）；
// ③ 全程按字母/数字键都过 `keyGuard`（焦点不在输入面才允许）。
//
// 🔒 只读 / 本地：开面板、点「快捷键」、按这几个键、Escape。**不点任何生成/发送/下载，
//    不按 F（导演台那一行仍未授权）。**
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
const toast = () => p.evaluate(() => { const e = Array.from(document.querySelectorAll('div'))
    .find((x) => (x.innerText || '').trim() === '此快捷键当前不可用' && x.getBoundingClientRect().width > 1);
  if (!e) return null; const r = e.getBoundingClientRect();
  return { box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`, text: (e.innerText || '').trim() }; });
try {
  // —————————————— ① 用户菜单 ——————————————
  const um = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-user-menu-trigger"]'); if (!e) return null;
    const r = e.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  if (!um) throw new Error('用户菜单按钮没找到');
  await p.mouse.click(um.x, um.y); await p.waitForTimeout(1300);
  out.userMenu = await p.evaluate(() => {
    const cands = Array.from(document.querySelectorAll('[role="menu"],[data-testid*="menu"]')).filter((e) => e.getBoundingClientRect().width > 1);
    const m = cands.sort((a, c) => c.getBoundingClientRect().height - a.getBoundingClientRect().height)[0];
    if (!m) return { found: false };
    const r = m.getBoundingClientRect();
    const items = Array.from(m.querySelectorAll('[role="menuitem"],[role="menuitemradio"]')).map((e) => ({ text: (e.innerText || '').split('\n').filter(Boolean).slice(-1)[0] || '',
      box: (() => { const q = e.getBoundingClientRect(); return `${Math.round(q.width)}x${Math.round(q.height)}`; })() }));
    return { found: true, box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
      count: items.length, items, hasAccountBlock: /昵称|会员|账号/.test(m.innerText || '') };
  });
  log('用户菜单', JSON.stringify(out.userMenu, null, 1));

  // —————————————— ①2 快捷键抽屉：逐字读全四组（边滚边读） ——————————————
  const sk = await p.evaluate(() => { const it = Array.from(document.querySelectorAll('[role="menuitem"],[role="menuitemradio"]'))
    .find((e) => /快捷键/.test(e.innerText || '')); if (!it) return null;
    const r = it.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  if (!sk) throw new Error('菜单里没有「快捷键」项');
  await p.mouse.click(sk.x, sk.y); await p.waitForTimeout(1600);
  await p.keyboard.press('Escape'); await p.waitForTimeout(900);   // 菜单可能仍开着，关一次
  const drawer = await p.evaluate(() => {
    const cands = Array.from(document.querySelectorAll('div,aside,section')).filter((e) => {
      const t = (e.innerText || ''); if (!/快捷键/.test(t)) return false;
      const b = e.getBoundingClientRect(); return b.width > 100 && b.height > 100; });
    if (!cands.length) return { found: false };
    // 取**含文本最多**的那个（最外层抽屉容器）
    const d = cands.sort((a, c) => (c.innerText || '').length - (a.innerText || '').length)[0];
    const b = d.getBoundingClientRect();
    // 找到真正可滚动的子容器
    let sc = null;
    for (const e of [d, ...d.querySelectorAll('*')]) {
      if (e.scrollHeight > e.clientHeight + 8 && e.clientHeight > 100) { sc = e; break; }
    }
    return { found: true, box: `${Math.round(b.width)}x${Math.round(b.height)}@${Math.round(b.x)},${Math.round(b.y)}`,
      hasClose: !!d.querySelector('[aria-label*="lose" i],[aria-label*="关闭"]'),
      scroller: sc ? { testid: sc.getAttribute('data-testid') || '', cls: (sc.getAttribute('class') || '').slice(0, 40),
        scrollHeight: sc.scrollHeight, clientHeight: sc.clientHeight } : null };
  });
  out.drawer = drawer; log('快捷键抽屉', JSON.stringify(drawer, null, 1));
  if (drawer.found && drawer.scroller) {
    // 逐屏滚动，累积所有行
    out.panelRows = [];
    const seen = new Set();
    for (let step = 0; step < 8; step++) {
      const rows = await p.evaluate(() => {
        // 从抽屉容器里取所有「左功能名 + 右快捷键」的行
        const cands = Array.from(document.querySelectorAll('div,aside,section')).filter((e) => {
          const t = (e.innerText || ''); if (!/快捷键/.test(t)) return false;
          const b = e.getBoundingClientRect(); return b.width > 100 && b.height > 100; });
        if (!cands.length) return [];
        const d = cands.sort((a, c) => (c.innerText || '').length - (a.innerText || '').length)[0];
        const out2 = [];
        for (const e of d.querySelectorAll('*')) {
          const t = (e.innerText || '').trim();
          if (!t || t.includes('\\n') === false) { /* 继续 */ }
          const lines = t.split('\\n').map((x) => x.trim()).filter(Boolean);
          if (lines.length !== 2) continue;
          if (lines[1].length > 14) continue;
          if (e.children.length > 6) continue;
          out2.push({ fn: lines[0].slice(0, 20), key: lines[1] });
        }
        return out2;
      });
      for (const r of rows) { const k = r.fn + '|' + r.key; if (!seen.has(k)) { seen.add(k); out.panelRows.push(r); } }
      const moved = await p.evaluate(() => {
        const cands = Array.from(document.querySelectorAll('div,aside,section')).filter((e) => {
          const t = (e.innerText || ''); if (!/快捷键/.test(t)) return false;
          const b = e.getBoundingClientRect(); return b.width > 100 && b.height > 100; });
        const d = cands.sort((a, c) => (c.innerText || '').length - (a.innerText || '').length)[0];
        for (const e of [d, ...d.querySelectorAll('*')]) if (e.scrollHeight > e.clientHeight + 8 && e.clientHeight > 100) {
          const before = e.scrollTop; e.scrollTop = before + Math.max(120, e.clientHeight - 60);
          return { before, after: e.scrollTop, max: e.scrollHeight - e.clientHeight }; }
        return null;
      });
      if (!moved || moved.after === moved.before) break;
    }
    log('面板读到的行（' + out.panelRows.length + ' 行）：');
    for (const r of out.panelRows) log('   ', r.fn.padEnd(12), r.key);
  }
  // 关闭抽屉
  await p.keyboard.press('Escape'); await p.waitForTimeout(1000);
  out.drawerClosed = await p.evaluate(() => !Array.from(document.querySelectorAll('div,aside,section'))
    .some((e) => /快捷键/.test(e.innerText || '') && e.getBoundingClientRect().width > 100 && e.getBoundingClientRect().height > 100));
  log('抽屉已关闭 =', out.drawerClosed);

  // —————————————— ② 三个键的复测 ——————————————
  const pre = await ids();
  const rail = await p.evaluate(() => { const el = Array.from(document.querySelectorAll('button,[role="button"]'))
    .find((x) => /^文本$/.test(((x.getAttribute('aria-label') || '') + (x.innerText || '')).trim()));
    const r = el.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  await p.mouse.click(rail.x, rail.y); await p.waitForTimeout(3000);
  const made = (await ids()).filter((x) => !pre.includes(x));
  if (made.length !== 1) throw new Error('新建异常');
  mine = made[0];
  const sel0 = await p.evaluate((v) => /(^|\s)selected(\s|$)/.test(document.querySelector(`.react-flow__node[data-id="${v}"]`).className), mine);
  log('新建', mine, '自动选中 =', sel0, '|', await status());
  if (!sel0) throw new Error('未选中 ⇒ 复测作废(VOID)');

  // ②a ⌘A
  out.cmdA = { beforeSelected: await selCount(), precondition: '自建节点已选中（≥1）' };
  const gA = await keyGuard(p); out.cmdA.guard = { safe: gA.safe, where: gA.where };
  if (gA.safe) { await p.keyboard.press('Meta+A'); await p.waitForTimeout(900); }
  out.cmdA.afterSelected = await selCount();
  out.cmdA.effective = out.cmdA.afterSelected !== out.cmdA.beforeSelected;
  log('⌘A', JSON.stringify(out.cmdA));
  await p.keyboard.press('Escape'); await p.waitForTimeout(600);
  log('  Esc 后 selected =', await selCount());

  // ②b ⇧2（页面记「直接按键无效」）
  const isSel = await p.evaluate((v) => /(^|\s)selected(\s|$)/.test(document.querySelector(`.react-flow__node[data-id="${v}"]`).className), mine);
  out.shift2 = { nodeSelected: isSel, zoomBefore: await zoomLabel() };
  const g2 = await keyGuard(p); out.shift2.guard = { safe: g2.safe, where: g2.where };
  if (g2.safe) { await p.keyboard.press('Shift+Digit2'); await p.waitForTimeout(1200); }
  out.shift2.zoomAfter = await zoomLabel();
  out.shift2.effective = out.shift2.zoomAfter !== out.shift2.zoomBefore;
  log('⇧2', JSON.stringify(out.shift2));

  // ②c V（页面记「不切换工具」）
  out.vKey = { dockBefore: await dockBtn() };
  const gv = await keyGuard(p); out.vKey.guard = { safe: gv.safe, where: gv.where };
  if (gv.safe) await pressLetter(p, 'v');
  await p.waitForTimeout(1000);
  out.vKey.dockAfter = await dockBtn();
  out.vKey.effective = out.vKey.dockBefore && out.vKey.dockAfter && out.vKey.dockBefore.aria !== out.vKey.dockAfter.aria;
  log('V', JSON.stringify(out.vKey));

  // ②d G（页面记「选中后弹此快捷键当前不可用」）
  const gG = await keyGuard(p); out.gKey = { guard: { safe: gG.safe, where: gG.where } };
  if (gG.safe) await pressLetter(p, 'g');
  await p.waitForTimeout(300); const t1 = await toast(); await p.waitForTimeout(1200); const t2 = await toast();
  out.gKey.toastEarly = t1; out.gKey.toastLate = t2;
  log('G', JSON.stringify(out.gKey));
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
  writeFileSync(new URL('./_tmp-b82.json', import.meta.url), JSON.stringify(out, null, 1));
  await b.close();
}
