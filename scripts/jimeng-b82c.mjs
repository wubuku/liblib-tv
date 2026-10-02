// 批次 82 · C：再修两处判据。
// ① 抽屉定位错了：我按「含『快捷键』文字最多的元素」找，抓到的是**全屏遮罩**（1280×720），
//    于是 scrollHeight 2302 / clientHeight 720、逐行读到的全是画布上别的节点的文字。
//    页面记的是抽屉面板 **240×604**、可滚动 1300 > 可见 548 —— 那才是要量的东西。
//    修法：改成「**宽度 < 400** 且含『通用操作』的那个元素」。
// ② `focusToCanvas` 点的是**标题行**，而节点本来已选中 ⇒ 那是 **toggle** ⇒ 反而取消了选中
//    （`selected:false`）。修法：点**节点主体**（0.5,0.5），已选中时点击不会取消它，
//    只把焦点挪到画布；点完**两个前置都要断言**：selected===true 且 keyGuard.where 是画布。
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
/** 点**节点主体**，让焦点落到画布；已选中时点击**不会**取消选中（那是 toggle，只对标题行成立）。 */
const focusToCanvas = async (v) => {
  const t = await p.evaluate((id) => { const n = document.querySelector(`.react-flow__node[data-id="${id}"]`); const r = n.getBoundingClientRect();
    return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height * 0.6) }; }, v);
  await p.mouse.click(t.x, t.y); await p.waitForTimeout(900);
  const g = await keyGuard(p);
  const sel = await p.evaluate((id) => { const n = document.querySelector(`.react-flow__node[data-id="${id}"]`); return /(^|\s)selected(\s|$)/.test(n.className); }, v);
  const inEdit = await p.evaluate(() => !!document.querySelector('.ProseMirror[contenteditable="true"]'));
  return { where: g.where, safe: g.safe, selected: sel, enteredEdit: inEdit };
};
try {
  // —————————————— ① 抽屉：按「窄 + 含通用操作」定位 ——————————————
  const um = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-user-menu-trigger"]'); if (!e) return null;
    const r = e.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  await p.mouse.click(um.x, um.y); await p.waitForTimeout(1300);
  const sk = await p.evaluate(() => { const it = Array.from(document.querySelectorAll('[role="menuitem"],[role="menuitemradio"]'))
    .find((e) => /快捷键/.test(e.innerText || '')); if (!it) return null;
    const r = it.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  await p.mouse.click(sk.x, sk.y); await p.waitForTimeout(1800);
  out.drawerFound = await p.evaluate(() => Array.from(document.querySelectorAll('div,aside,section'))
    .some((e) => /通用操作/.test(e.innerText || '') && e.getBoundingClientRect().width > 100));
  log('抽屉出现 =', out.drawerFound);
  if (!out.drawerFound) throw new Error('抽屉没出现 ⇒ VOID');
  /** 窄 + 含「通用操作」的那个面板。 */
  const PICK = `(() => { const c = Array.from(document.querySelectorAll('div,aside,section'))
      .filter((e) => { const b = e.getBoundingClientRect();
        return /通用操作/.test(e.innerText || '') && b.width > 100 && b.width < 400 && b.height > 200; });
    return c.sort((a, b) => a.querySelectorAll('*').length - b.querySelectorAll('*').length)[0] || null; })()`;
  const panel = await p.evaluate((pick) => {
    const d = eval(pick); if (!d) return { found: false };
    const b = d.getBoundingClientRect();
    let sc = null; for (const e of [d, ...d.querySelectorAll('*')]) if (e.scrollHeight > e.clientHeight + 8 && e.clientHeight > 100) { sc = e; break; }
    return { found: true, box: `${Math.round(b.width)}x${Math.round(b.height)}@${Math.round(b.x)},${Math.round(b.y)}`,
      testid: d.getAttribute('data-testid') || '', cls: (d.getAttribute('class') || '').slice(0, 46),
      scroller: sc ? { scrollHeight: sc.scrollHeight, clientHeight: sc.clientHeight, testid: sc.getAttribute('data-testid') || '' } : null,
      hasCloseBtn: !!d.querySelector('[aria-label*="lose" i]') };
  }, PICK);
  out.drawer = panel; log('抽屉面板', JSON.stringify(panel, null, 1));
  // 逐屏读行
  out.panelRows = []; const seen = new Set();
  for (let step = 0; step < 12; step++) {
    const rows = await p.evaluate((pick) => {
      const d = eval(pick); if (!d) return [];
      const res = [];
      for (const e of d.querySelectorAll('div')) {
        if (e.children.length > 3) continue;
        const lines = (e.innerText || '').trim().split('\n').map((x) => x.trim()).filter(Boolean);
        if (lines.length < 2 || lines[1].length > 16) continue;
        res.push({ fn: lines[0].slice(0, 24), key: lines[1] });
      }
      return res;
    }, PICK);
    for (const r of rows) { const k = r.fn + '|' + r.key; if (!seen.has(k)) { seen.add(k); out.panelRows.push(r); } }
    const mv = await p.evaluate((pick) => { const d = eval(pick); if (!d) return null;
      for (const e of [d, ...d.querySelectorAll('*')]) if (e.scrollHeight > e.clientHeight + 8 && e.clientHeight > 100) {
        const before = e.scrollTop; e.scrollTop = before + Math.max(100, e.clientHeight - 50);
        return { before, after: e.scrollTop, max: e.scrollHeight - e.clientHeight }; }
      return null; }, PICK);
    if (!mv || mv.after === mv.before) break;
  }
  log('读到的面板行（' + out.panelRows.length + '）：');
  for (const r of out.panelRows) log('   ', r.fn.padEnd(16), r.key);
  await p.keyboard.press('Escape'); await p.waitForTimeout(1100);
  out.drawerClosed = await p.evaluate(() => !Array.from(document.querySelectorAll('div,aside,section'))
    .some((e) => /通用操作/.test(e.innerText || '') && e.getBoundingClientRect().width > 100 && e.getBoundingClientRect().width < 400));
  log('抽屉已关闭 =', out.drawerClosed);

  // —————————————— ② 四个键：焦点在画布 + 节点选中，两个前置都断言 ——————————————
  const pre = await ids();
  const rail = await p.evaluate(() => { const el = Array.from(document.querySelectorAll('button,[role="button"]'))
    .find((x) => /^文本$/.test(((x.getAttribute('aria-label') || '') + (x.innerText || '')).trim()));
    const r = el.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  await p.mouse.click(rail.x, rail.y); await p.waitForTimeout(3000);
  const made = (await ids()).filter((x) => !pre.includes(x));
  if (made.length !== 1) throw new Error('新建异常');
  mine = made[0];
  let foc = await focusToCanvas(mine);
  log('焦点归位', JSON.stringify(foc), '|', await status());
  if (!foc.selected) { log('⚠️ 点主体后仍未选中，再点一次'); await p.mouse.click(foc.where ? 0 : 0, 0).catch(() => {}); }
  if (!foc.selected) throw new Error('节点未选中 ⇒ VOID');
  if (foc.enteredEdit) throw new Error('误入编辑态 ⇒ VOID');
  if (!/Canvas|react-flow|body/i.test(foc.where)) throw new Error('焦点不在画布 ⇒ VOID（keyGuard: ' + foc.where + '）');

  out.gKey = { focusWhere: foc.where, selBefore: await selCount() };
  const gG = await keyGuard(p); if (!gG.safe) throw new Error('keyGuard 拒绝：' + gG.reason);
  await pressLetter(p, 'g');
  for (const d of [250, 700, 1500, 2500]) { await p.waitForTimeout(d); const t = await toast(); if (t) { out.gKey.toast = t; out.gKey.toastAtMs = d; break; } }
  if (!out.gKey.toast) out.gKey.toast = null;
  log('G →', JSON.stringify(out.gKey));

  out.vKey = { dockBefore: await dockBtn() };
  const gv = await keyGuard(p); if (!gv.safe) throw new Error('keyGuard 拒绝');
  await pressLetter(p, 'v'); await p.waitForTimeout(1100);
  out.vKey.dockAfter = await dockBtn();
  log('V →', JSON.stringify(out.vKey));

  out.cmdA = { before: await selCount(), sel: foc.selected };
  await p.keyboard.press('Meta+A'); await p.waitForTimeout(1000);
  out.cmdA.after = await selCount();
  log('⌘A →', JSON.stringify(out.cmdA));
  await p.keyboard.press('Escape'); await p.waitForTimeout(700);

  foc = await focusToCanvas(mine);
  out.shift2 = { focus: foc.where, selected: foc.selected, zoomBefore: await zoomLabel() };
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
  writeFileSync(new URL('./_tmp-b82c.json', import.meta.url), JSON.stringify(out, null, 1));
  await b.close();
}
