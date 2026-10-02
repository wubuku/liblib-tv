// 批次 82 · E：前四轮（a/b/c/d）留下的三个洞，这一轮各打一个。
//
// 洞 1 —— **面板全表根本没抓到**。d 轮的行提取器（取 `div` 的 innerText 前两行）
//   拿到的是「通用操作」这个**组头**（组头和第一行同处一个 div），
//   于是 `lines[1]` 恒等于功能名、`lines[2]` 才是键，最终只导出 1 行。
//   正确做法：**不猜 DOM 结构**，直接把滚动区 `innerText` 按 scrollTop 分段抓全，
//   再按行序去重 —— 面板是文本流，不是结构化表格。
//
// 洞 2 —— **`selectSafely` 选不中节点**。d 轮点 `r.y - 15`，结果 `selected:false`。
//   但 `focusWhere` 已经是 `DIV[rf__wrapper] aria="Canvas"` ⇒ 焦点确实在画布上，
//   失败的是**选中**这一步。所以问题不在焦点，在落点。
//   批次 78 钉过：标题行在节点矩形**上方 31–33 canvas px**；
//   60% 缩放下 = 屏上 19–20px ⇒ **`r.y - 15` 恰好落在缝隙里**。这轮把落点
//   逐个候选点全 dump 出来（坐标 + elementFromPoint 描述），当场选对的那个。
//
// 洞 3 —— **G / V / ⌘/ 的前置只有一种被真正验过**。
//   页面写「未选中节点时 G 完全静默」「V 不切换工具」「⌘/ 可开关 Agent」，
//   但 c 轮那次的焦点在 `BUTTON aria="文本"`（左栏按钮）上 —— 那**不是画布焦点**，
//   「静默」有可能只是焦点根本不在画布。d 轮虽然焦点对了，却被 `ok` 判据一起作废。
//   这轮把**前置拆成两档**分别测：① 画布焦点 + 0 选中；② 画布焦点 + 1 选中。
//   任何一档单独失败都不连坐。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport, keyGuard, pressLetter } from './jimeng-safe-keys.mjs';
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
  const e = c.sort((a, b2) => b2.getBoundingClientRect().width - a.getBoundingClientRect().width)[0];
  if (!e) return null; const r = e.getBoundingClientRect();
  return { box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`, text: (e.innerText || '').trim() }; });
const agentCount = () => p.evaluate(() => document.querySelectorAll('[data-testid^="canvas-agent-"]').length);
const visCount = () => p.evaluate(() => { const n = 0;
  for (const e of document.querySelectorAll('*')) { const r = e.getBoundingClientRect(); if (r.width > 0 && r.height > 0) n++; } return n; });

/** 面板定位：锚=关闭钮，向上找第一个「100<w<400 且含通用操作」的祖先。 */
const findPanel = () => p.evaluate(() => {
  const closes = Array.from(document.querySelectorAll('button,[role="button"]'))
    .filter((e) => { const a = e.getAttribute('aria-label') || ''; return /关闭|Close/i.test(a) && e.getBoundingClientRect().width > 1; })
    .sort((a, b2) => b2.getBoundingClientRect().width - a.getBoundingClientRect().width);
  if (!closes.length) return null;
  for (let e = closes[0]; e && e !== document.body; e = e.parentElement) {
    const bb = e.getBoundingClientRect();
    if (bb.width > 100 && bb.width < 400 && /通用操作/.test(e.innerText || '')) return e;
  } return null;
});

/** 前置档 A：画布焦点 + 0 选中（点空白，落点必须是 `.react-flow__pane`）。 */
const focusCanvasZeroSel = async () => {
  const empty = await p.evaluate(() => { const pane = document.querySelector('.react-flow__pane'); if (!pane) return null;
    for (let y = 120; y < 660; y += 24) for (let x = 200; x < 1240; x += 32) {
      const h = document.elementFromPoint(x, y);
      if (h && pane.contains(h)) return { x, y, hit: h.className || h.tagName }; }
    return null; });
  if (!empty) return { ok: false, why: '找不到可确认的空白落点' };
  await p.mouse.click(empty.x, empty.y); await p.waitForTimeout(700);
  const g = await keyGuard(p);
  return { ok: /Canvas|react-flow/i.test(g.where), emptyAt: `${empty.x},${empty.y}`, hit: String(empty.hit).slice(0, 40),
    sel: await selCount(), focusWhere: g.where, guardSafe: g.safe, stage: 'A(画布焦点/0选中)' };
};

/** 前置档 B：画布焦点 + 恰好 1 选中。落点候选逐个 dump，当场选对的那个。 */
const focusCanvasOneSel = async (id) => {
  await focusCanvasZeroSel();
  // 把节点上方一带的落点候选全打出来，用「命中元素描述」判断哪个是标题行
  const cands = await p.evaluate((v) => {
    const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!n) return null;
    const r = n.getBoundingClientRect();
    const list = [];
    for (let dy = -45; dy <= 5; dy += 5) for (let f of [0.5, 0.25, 0.75]) {
      const x = Math.round(r.x + r.width * f), y = Math.round(r.y + dy);
      if (x < 0 || y < 0 || y > 718) continue;
      const h = document.elementFromPoint(x, y);
      if (!h) { list.push({ dx: dy, f, x, y, hit: null }); continue; }
      const inNode = n.contains(h);
      list.push({ dx: dy, f, x, y, inNode,
        hit: `${h.tagName}.${String(h.className || '').split(' ').slice(0, 2).join('.')}`.slice(0, 64),
        txt: (h.innerText || h.getAttribute('aria-label') || '').trim().slice(0, 18) });
    } return { nodeBox: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`, list };
  }, id);
  // 优先挑「命中元素在节点内、且带文字或 aria」的候选（标题行特征）
  const pick = (cands?.list || []).filter((c) => c.inNode && (c.txt || '').length)[0]
    || (cands?.list || []).filter((c) => c.inNode).pop()
    || (cands?.list || [])[0];
  if (!pick) return { ok: false, why: '没有可用落点', cands };
  await p.mouse.click(pick.x, pick.y); await p.waitForTimeout(800);
  const g = await keyGuard(p);
  const sel = await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); return /(^|\s)selected(\s|$)/.test(n.className); }, id);
  const inEdit = await p.evaluate(() => !!document.querySelector('.ProseMirror[contenteditable="true"]'));
  return { ok: sel && !inEdit, nodeBox: cands?.nodeBox, picked: pick, candsSample: (cands?.list || []).slice(0, 8),
    sel: await selCount(), selected: sel, enteredEdit: inEdit, focusWhere: g.where, guardSafe: g.safe, stage: 'B(画布焦点/1选中)' };
};

try {
  // ══════════════ 洞 1：面板全表逐字 ══════════════
  const um = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-user-menu-trigger"]'); if (!e) return null;
    const r = e.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  await p.mouse.click(um.x, um.y); await p.waitForTimeout(1300);
  const sk = await p.evaluate(() => { const it = Array.from(document.querySelectorAll('[role="menuitem"],[role="menuitemradio"]'))
    .find((e) => /快捷键/.test(e.innerText || '')); if (!it) return null;
    const r = it.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  await p.mouse.click(sk.x, sk.y); await p.waitForTimeout(1900);
  out.drawer = await p.evaluate(() => {
    const closes = Array.from(document.querySelectorAll('button,[role="button"]'))
      .filter((e) => { const a = e.getAttribute('aria-label') || ''; return /关闭|Close/i.test(a) && e.getBoundingClientRect().width > 1; })
      .sort((a, b2) => b2.getBoundingClientRect().width - a.getBoundingClientRect().width);
    if (!closes.length) return { found: false };
    const r = closes[0].getBoundingClientRect();
    return { found: true, closeAria: closes[0].getAttribute('aria-label'),
      closeBox: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}` };
  });
  // 滚动区 innerText 分段全抓
  out.panelText = []; const seenLines = new Set();
  for (let step = 0; step < 16; step++) {
    const seg = await p.evaluate(() => {
      const closes = Array.from(document.querySelectorAll('button,[role="button"]'))
        .filter((e) => { const a = e.getAttribute('aria-label') || ''; return /关闭|Close/i.test(a) && e.getBoundingClientRect().width > 1; })
        .sort((a, b2) => b2.getBoundingClientRect().width - a.getBoundingClientRect().width);
      let panel = null;
      for (let e = closes[0]; e && e !== document.body; e = e.parentElement) {
        const bb = e.getBoundingClientRect();
        if (bb.width > 100 && bb.width < 400 && /通用操作/.test(e.innerText || '')) { panel = e; break; } }
      if (!panel) return null;
      let sc = null;
      for (const e of [panel, ...panel.querySelectorAll('*')]) if (e.scrollHeight > e.clientHeight + 8 && e.clientHeight > 100) { sc = e; break; }
      if (!sc) return { text: panel.innerText, done: true, testid: null };
      const pr = panel.getBoundingClientRect();
      return { text: sc.innerText, scrollTop: sc.scrollTop, sh: sc.scrollHeight, ch: sc.clientHeight, done: false,
        testid: sc.getAttribute('data-testid') || '',
        panelBox: `${Math.round(pr.width)}x${Math.round(pr.height)}@${Math.round(pr.x)},${Math.round(pr.y)}` };
    });
    if (!seg) break;
    if (step === 0) { out.scroller = { testid: seg.testid, scrollHeight: seg.sh, clientHeight: seg.ch, panelBox: seg.panelBox }; log('滚动区', JSON.stringify(out.scroller)); }
    for (const L of (seg.text || '').split('\n').map((x) => x.trim())) if (L && !seenLines.has(L)) { seenLines.add(L); out.panelText.push(L); }
    if (seg.done) break;
    const mv = await p.evaluate(() => {
      const closes = Array.from(document.querySelectorAll('button,[role="button"]'))
        .filter((e) => { const a = e.getAttribute('aria-label') || ''; return /关闭|Close/i.test(a) && e.getBoundingClientRect().width > 1; })
        .sort((a, b2) => b2.getBoundingClientRect().width - a.getBoundingClientRect().width);
      let panel = null;
      for (let e = closes[0]; e && e !== document.body; e = e.parentElement) {
        const bb = e.getBoundingClientRect();
        if (bb.width > 100 && bb.width < 400 && /通用操作/.test(e.innerText || '')) { panel = e; break; } }
      if (!panel) return null;
      for (const e of [panel, ...panel.querySelectorAll('*')]) if (e.scrollHeight > e.clientHeight + 8 && e.clientHeight > 100) {
        const before = e.scrollTop; e.scrollTop = before + 300; return { before, after: e.scrollTop }; }
      return null;
    });
    if (!mv || mv.after === mv.before) break;
  }
  log(`面板逐字行（${out.panelText.length}）：`);
  out.panelText.forEach((L, i) => log(`  ${String(i).padStart(2)} ${L}`));

  // Esc 关抽屉（页面原子步骤第 3 步声称 Esc 可关）
  const beforeEsc = await p.evaluate(() => !!document.querySelector('[data-testid="shortcut-help-scroll-region"]'));
  await p.keyboard.press('Escape'); await p.waitForTimeout(1200);
  out.escCloses = { before: beforeEsc, after: await p.evaluate(() => !!document.querySelector('[data-testid="shortcut-help-scroll-region"]')) };
  log('Esc 关抽屉', JSON.stringify(out.escCloses));

  // ══════════════ 建一个自建节点 ══════════════
  const pre = await ids();
  const rail = await p.evaluate(() => { const el = Array.from(document.querySelectorAll('button,[role="button"]'))
    .find((x) => /^文本$/.test(((x.getAttribute('aria-label') || '') + (x.innerText || '')).trim()));
    const r = el.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  await p.mouse.click(rail.x, rail.y); await p.waitForTimeout(3200);
  const made = (await ids()).filter((x) => !pre.includes(x));
  if (made.length !== 1) throw new Error('新建异常 ' + made.length);
  mine = made[0]; log('自建节点', mine);

  // ══════════════ 洞 2 + 洞 3：两档前置 × 四个键 ══════════════
  out.keys = {};
  const runKey = async (name, preStage, key) => {
    try {
      const s = preStage === 'A' ? await focusCanvasZeroSel() : await focusCanvasOneSel(mine);
      log(`  前置[${preStage}]`, JSON.stringify(s));
      const rec = { pre: s };
      if (!s.ok) rec.void = '前置不成立';
      else {
        const g = await keyGuard(p);
        if (!g.safe) rec.void = 'keyGuard 拒绝';
        else {
          if (key.meta) await p.keyboard.press(key.meta);
          else if (key.shiftDigit) await p.keyboard.press(key.shiftDigit);
          else await pressLetter(p, key.letter);
          if (key.probe) rec.observed = await key.probe();
          for (const d of (key.waits || [400, 800, 1600])) { await p.waitForTimeout(d); const t = await toast(); if (t) { rec.toast = t; rec.toastAfterMs = d; break; } }
          if (!rec.toast) rec.toast = null;
          if (key.after) rec.after = await key.after();
        }
      }
      out.keys[`${name}@${preStage}`] = rec;
      log(`${name}@${preStage} →`, JSON.stringify(rec));
    } catch (e) { out.keys[`${name}@${preStage}`] = { error: e.message }; log(`${name}@${preStage} !! ${e.message}`); }
  };

  // G：宫格视图。页面声称「选中才有提示，未选中完全静默」
  await runKey('G', 'A', { letter: 'g', waits: [300, 700, 1500], after: async () => ({ sel: await selCount(), vis: await visCount() }) });
  await runKey('G', 'B', { letter: 'g', waits: [300, 700, 1500], after: async () => ({ sel: await selCount(), vis: await visCount() }) });
  // V：移动工具。页面声称「不切换工具」
  await runKey('V', 'A', { letter: 'v', after: async () => ({ dock: await dockBtn() }) });
  await runKey('V', 'B', { letter: 'v', after: async () => ({ dock: await dockBtn() }) });
  // ⌘/：开关 Agent 抽屉。页面声称「可用」
  await runKey('cmdSlash', 'A', { meta: 'Meta+Slash', after: async () => ({ agent: await agentCount(), vis: await visCount() }) });
  await runKey('cmdSlash', 'B', { meta: 'Meta+Slash', after: async () => ({ agent: await agentCount(), vis: await visCount() }) });
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
  writeFileSync(new URL('./_tmp-b82e.json', import.meta.url), JSON.stringify(out, null, 1));
  await b.close();
}
