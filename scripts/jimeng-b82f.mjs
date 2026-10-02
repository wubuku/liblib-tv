// 批次 82 · F：e 轮修三个 bug，并补上被 bug 吃掉的四个格。
//
// 🔴 **e 轮最大的收获其实是它自己的失败**：面板逐字 60 行里，
//    「缩放时间线」后面**没有跟键行**——不是面板没写，是**我的去重器吃掉了**。
//    因为视图组「缩放画布」的键**也是 `⌘ scroll`**，
//    按字符串 `Set` 去重时第二次出现被丢弃。
//    ⇒ 面板上**两个不同功能的键字符串逐字相同**，这恰恰是页面反复强调的
//    「同一个键在不同上下文」现象，**在面板上就长得一模一样，肉眼分不出来**。
//    这轮**不按字符串去重**，按分段的完整行序保留，让重复行原样留下。
//
// 修 bug：
//   ① `visCount` 里 `const n = 0` 却 `n++` ⇒ G / ⌘/ 的 after 抛
//      「Assignment to constant variable」，被外层 catch 覆盖成 `{error}`，
//      **前面已经采到的 toast 证据全丢**。改 `let`，并让 catch **追加** `rec.error`
//      而不是整条替换（e 轮的错误二：catch 吞掉已完成的工作）。
//   ② B 档前置点标题行会**进编辑态** —— 因为同一节点被 G/V/⌘/ 连续点过多次。
//      修正：点完若 `enteredEdit` 则 Esc 一次，再断言 selected。
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
const visCount = () => p.evaluate(() => { let n = 0;   // ← e 轮写成了 const
  for (const e of document.querySelectorAll('*')) { const r = e.getBoundingClientRect(); if (r.width > 0 && r.height > 0) n++; } return n; });
const fsDialog = () => p.evaluate(() => { const e = document.querySelector('[text-editor-fullscreen-dialog]'); if (!e) return null;
  const r = e.getBoundingClientRect(); return `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`; });

const panelAnchor = () => p.evaluate(() => {
  const closes = Array.from(document.querySelectorAll('button,[role="button"]'))
    .filter((e) => { const a = e.getAttribute('aria-label') || ''; return /关闭|Close/i.test(a) && e.getBoundingClientRect().width > 1; })
    .sort((a, b2) => b2.getBoundingClientRect().width - a.getBoundingClientRect().width);
  if (!closes.length) return null;
  for (let e = closes[0]; e && e !== document.body; e = e.parentElement) {
    const bb = e.getBoundingClientRect();
    if (bb.width > 100 && bb.width < 400 && /通用操作/.test(e.innerText || '')) return e;
  } return null;
});

const focusCanvasZeroSel = async () => {
  const empty = await p.evaluate(() => { const pane = document.querySelector('.react-flow__pane'); if (!pane) return null;
    for (let y = 120; y < 660; y += 24) for (let x = 200; x < 1240; x += 32) {
      const h = document.elementFromPoint(x, y); if (h && pane.contains(h)) return { x, y, hit: h.className || h.tagName }; }
    return null; });
  if (!empty) return { ok: false, why: '找不到空白落点' };
  await p.mouse.click(empty.x, empty.y); await p.waitForTimeout(700);
  const g = await keyGuard(p);
  return { ok: /Canvas|react-flow/i.test(g.where), emptyAt: `${empty.x},${empty.y}`, sel: await selCount(),
    focusWhere: g.where, guardSafe: g.safe, stage: 'A(画布焦点/0选中)' };
};

/** B 档：落点固定用 e 轮验出的 `dx = -30`（标题行），进编辑态则 Esc 一次。 */
const focusCanvasOneSel = async (id) => {
  await focusCanvasZeroSel();
  const pick = await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!n) return null;
    const r = n.getBoundingClientRect();
    for (const f of [0.25, 0.5, 0.75]) { const x = Math.round(r.x + r.width * f), y = Math.round(r.y - 30);
      const h = document.elementFromPoint(x, y);
      if (h && n.contains(h) && (h.innerText || h.getAttribute('aria-label'))) return { x, y, txt: (h.innerText || '').trim().slice(0, 12) }; }
    return null; }, id);
  if (!pick) return { ok: false, why: '找不到标题行落点' };
  await p.mouse.click(pick.x, pick.y); await p.waitForTimeout(800);
  let inEdit = await p.evaluate(() => !!document.querySelector('.ProseMirror[contenteditable="true"]'));
  let escUsed = false;
  if (inEdit) { await p.keyboard.press('Escape'); await p.waitForTimeout(600); escUsed = true;     // ← e 轮缺这一步
    inEdit = await p.evaluate(() => !!document.querySelector('.ProseMirror[contenteditable="true"]')); }
  const sel = await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); return /(^|\s)selected(\s|$)/.test(n.className); }, id);
  return { ok: sel && !inEdit, picked: pick, escUsed, sel: await selCount(), selected: sel, enteredEdit: inEdit,
    stage: 'B(画布焦点/1选中)' };
};

try {
  // ══════ ① 面板全表：**保留重复行**，不再按字符串去重 ══════
  const um = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-user-menu-trigger"]'); if (!e) return null;
    const r = e.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  await p.mouse.click(um.x, um.y); await p.waitForTimeout(1300);
  const sk = await p.evaluate(() => { const it = Array.from(document.querySelectorAll('[role="menuitem"],[role="menuitemradio"]'))
    .find((e) => /快捷键/.test(e.innerText || '')); if (!it) return null;
    const r = it.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  await p.mouse.click(sk.x, sk.y); await p.waitForTimeout(1900);
  out.segs = [];
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
      const src = sc || panel;
      return { top: sc ? sc.scrollTop : 0, sh: sc ? sc.scrollHeight : 0, ch: sc ? sc.clientHeight : 0,
        lines: src.innerText.split('\n').map((x) => x.trim()).filter(Boolean) };
    });
    if (!seg) break;
    out.segs.push({ scrollTop: seg.top, lines: seg.lines });
    if (step === 0) out.scroller = { scrollHeight: seg.sh, clientHeight: seg.ch };
    if (seg.lines.length && seg.top === 0 && step === 0) { /* 首屏 */ }
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
  log('分段（scrollTop / 行数）：');
  out.segs.forEach((s) => log(`  top=${s.scrollTop}  ${s.lines.length} 行`));
  // 取最长的那一段（视口内完整行），它就是全表
  const full = out.segs.reduce((a, s) => (s.lines.length > (a?.lines.length ?? -1) ? s : a), null);
  out.panelFull = full?.lines || [];
  log(`最长分段 top=${full?.scrollTop}，${out.panelFull.length} 行逐字：`);
  out.panelFull.forEach((L, i) => log(`  ${String(i).padStart(2)} ${L}`));
  // ⌘ scroll 到底出现几次
  out.scrollCount = out.panelFull.filter((L) => L === '⌘ scroll').length;
  log('`⌘ scroll` 在同一屏出现次数 =', out.scrollCount);
  await p.keyboard.press('Escape'); await p.waitForTimeout(1200);

  // ══════ ② 建节点，四格逐个测 ══════
  const pre = await ids();
  const rail = await p.evaluate(() => { const el = Array.from(document.querySelectorAll('button,[role="button"]'))
    .find((x) => /^文本$/.test(((x.getAttribute('aria-label') || '') + (x.innerText || '')).trim()));
    const r = el.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  await p.mouse.click(rail.x, rail.y); await p.waitForTimeout(3200);
  const made = (await ids()).filter((x) => !pre.includes(x));
  if (made.length !== 1) throw new Error('新建异常 ' + made.length);
  mine = made[0]; log('自建节点', mine);

  out.keys = {};
  const runKey = async (name, stage, key) => {
    const rec = { stage };
    try {
      const s = stage === 'A' ? await focusCanvasZeroSel() : await focusCanvasOneSel(mine);
      rec.pre = s;
      if (!s.ok) rec.void = '前置不成立';
      else {
        const g = await keyGuard(p);
        if (!g.safe) rec.void = 'keyGuard 拒绝';
        else {
          rec.before = { sel: await selCount(), vis: await visCount(), zoom: await zoomLabel(), dock: await dockBtn(), agent: await agentCount(), fs: await fsDialog() };
          if (key.meta) await p.keyboard.press(key.meta); else await pressLetter(p, key.letter);
          for (const d of (key.waits || [300, 700, 1500])) { await p.waitForTimeout(d); const t = await toast(); if (t) { rec.toast = t; rec.toastAfterMs = d; break; } }
          if (key.waits) { if (!rec.toast) rec.toast = null; rec.sampledToMs = key.waits.reduce((a, x) => a + x, 0); }
          rec.after = { sel: await selCount(), vis: await visCount(), zoom: await zoomLabel(), dock: await dockBtn(), agent: await agentCount(), fs: await fsDialog() };
          rec.diff = Object.fromEntries(Object.keys(rec.before).map((k) => [k, rec.before[k] === rec.after[k] ? '同' : `${JSON.stringify(rec.before[k])}→${JSON.stringify(rec.after[k])}`]));
        }
      }
    } catch (e) { rec.error = e.message; }     // ← 追加，不覆盖
    out.keys[`${name}@${stage}`] = rec;
    log(`${name}@${stage} →`, JSON.stringify(rec));
  };

  await runKey('G', 'A', { letter: 'g', waits: [300, 700, 1500] });
  await runKey('G', 'B', { letter: 'g', waits: [300, 700, 1500] });
  await runKey('cmdSlash', 'A', { meta: 'Meta+Slash' });
  await runKey('cmdSlash', 'B', { meta: 'Meta+Slash' });
  await runKey('V', 'B', { letter: 'v' });
  // F：文本节点选中后按 F 应开全屏编辑器
  await runKey('F', 'B', { letter: 'f', waits: [400, 900] });
  await p.keyboard.press('Escape'); await p.waitForTimeout(900);
  out.fsAfterEsc = await fsDialog();
  log('Esc 后全屏编辑器', JSON.stringify(out.fsAfterEsc));
  // ⇧ 1：面板写「适配画布 ⇧ 1 或 ⌘ 0」，页面只举了 ⌘0 的实测，⇧1 从未单独按过
  {
    const rec = { stage: 'B' };
    try {
      const s = await focusCanvasOneSel(mine); rec.pre = s;
      const g = await keyGuard(p); rec.guardSafe = g.safe;
      const z0 = await zoomLabel();
      await p.keyboard.press('Shift+Digit1'); await p.waitForTimeout(1600);
      const z1 = await zoomLabel();
      rec.shift1 = { before: z0, after: z1, changed: z0 !== z1 };
    } catch (e) { rec.error = e.message; }
    out.keys['shift1@B'] = rec; log('⇧1@B →', JSON.stringify(rec));
  }
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
  writeFileSync(new URL('./_tmp-b82f.json', import.meta.url), JSON.stringify(out, null, 1));
  await b.close();
}
