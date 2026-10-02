// 批次 82 · G：解决 B 档前置反复失败，测掉最后四个空格。
//
// 🔴 f 轮 B 档在 4 个键里有 3 个失败，而 e 轮同一条代码是成功的。
//    两次唯一的差别是**点标题行的次数**：e 轮那台节点是第 1 次被点，
//    f 轮它已经是第 2/3/4/5 次。⇒ 不是代码问题，是**状态漂移**。
//    本轮用**可证伪的判据**验这件事：同一个节点连续点标题行 N 次，
//    每次都记录 `selected` 与 `enteredEdit`。
//
// 🔴 顺带钉一条判据陷阱：f 轮里 `Esc` 之后 `.ProseMirror[contenteditable="true"]`
//    **仍然存在**。批次 80 说过「编辑态按 Esc 是提交」，而提交之后 ProseMirror
//    还留在 DOM 里 ⇒ **「有 ProseMirror」不能当「处于编辑态」用**。
//    本轮把 ProseMirror 的可见性/面积一起记下来，看它到底是残留还是还在编辑。
//
// 空格清单（全部在 1 选中 + 画布焦点下，且**每格一个全新节点**）：
//   V @B、F @B、G @B、⇧1 @A（适配画布不需要选中，放 A 档更干净）
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
const mine = [];
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
const visCount = () => p.evaluate(() => { let n = 0;
  for (const e of document.querySelectorAll('*')) { const r = e.getBoundingClientRect(); if (r.width > 0 && r.height > 0) n++; } return n; });
/** ProseMirror 三件套：存在 / 有面积 / contenteditable —— 分开记，不合并成一个布尔。 */
const pm = () => p.evaluate(() => { const e = document.querySelector('.ProseMirror[contenteditable="true"]');
  if (!e) return { exists: false };
  const r = e.getBoundingClientRect();
  return { exists: true, w: Math.round(r.width), h: Math.round(r.height),
    box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
    ce: e.getAttribute('contenteditable'), connected: e.isConnected,
    active: e.contains(document.activeElement) }; });
const fsDialog = () => p.evaluate(() => { const e = document.querySelector('[text-editor-fullscreen-dialog]'); if (!e) return null;
  const r = e.getBoundingClientRect(); return `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`; });

const clickPane = async () => {
  const empty = await p.evaluate(() => { const pane = document.querySelector('.react-flow__pane'); if (!pane) return null;
    for (let y = 120; y < 660; y += 24) for (let x = 200; x < 1240; x += 32) {
      const h = document.elementFromPoint(x, y); if (h && pane.contains(h)) return { x, y }; }
    return null; });
  if (!empty) return null; await p.mouse.click(empty.x, empty.y); await p.waitForTimeout(650); return empty;
};
/** 标题行落点：e 轮验出 `dy = -30` 命中 `SPAN`（带文字）。 */
const titlePoint = (id) => p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!n) return null;
  const r = n.getBoundingClientRect();
  for (const f of [0.25, 0.5, 0.75]) { const x = Math.round(r.x + r.width * f), y = Math.round(r.y - 30);
    const h = document.elementFromPoint(x, y);
    if (h && n.contains(h) && (h.innerText || h.getAttribute('aria-label'))) return { x, y, txt: (h.innerText || '').trim().slice(0, 12) }; }
  return null; }, id);
const probe = (id) => p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!n) return { sel: null };
  return { sel: /(^|\s)selected(\s|$)/.test(n.className) }; }, id);

try {
  // ══════ ① 建 5 个自建文本节点 ══════
  const pre = await ids();
  const rail = await p.evaluate(() => { const el = Array.from(document.querySelectorAll('button,[role="button"]'))
    .find((x) => /^文本$/.test(((x.getAttribute('aria-label') || '') + (x.innerText || '')).trim()));
    const r = el.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  for (let k = 0; k < 5; k++) { await p.mouse.click(rail.x, rail.y); await p.waitForTimeout(3000); }
  const made = (await ids()).filter((x) => !pre.includes(x));
  log('新建', made.length, made.join(' '));
  if (made.length < 5) throw new Error('新建不足 5：' + made.length);
  mine.push(...made);
  out.nodeBox = await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); const r = n.getBoundingClientRect();
    return { id: v, box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}` }; }, made[0]);

  // ══════ ② 连点同一节点 5 次：selected / enteredEdit / ProseMirror 逐次记录 ══════
  out.repeatClick = [];
  const t0 = made[0];
  for (let i = 0; i < 5; i++) {
    await clickPane();
    const pt = await titlePoint(t0);
    if (!pt) { out.repeatClick.push({ i, err: '无落点' }); continue; }
    await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(800);
    const s = await probe(t0);
    out.repeatClick.push({ i, pt, ...s, pm: await pm(), selCount: await selCount() });
    log(`  连点#${i}`, JSON.stringify(out.repeatClick[i]));
  }
  await p.keyboard.press('Escape'); await p.waitForTimeout(800);
  out.afterEsc = { pm: await pm(), sel: await selCount() };
  log('Esc 一次后', JSON.stringify(out.afterEsc));
  await p.keyboard.press('Escape'); await p.waitForTimeout(800);
  out.afterEsc2 = { pm: await pm(), sel: await selCount() };
  log('Esc 两次后', JSON.stringify(out.afterEsc2));

  // ══════ ③ 空格：每格一个全新节点 ══════
  out.keys = {};
  const stageA = async () => { await clickPane(); const g = await keyGuard(p);
    return { ok: /Canvas|react-flow/i.test(g.where), sel: await selCount(), focusWhere: g.where, stage: 'A(画布焦点/0选中)' }; };
  const stageB = async (id) => { await clickPane(); const pt = await titlePoint(id);
    if (!pt) return { ok: false, why: '无标题行落点', stage: 'B' };
    await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(800);
    const s = await probe(id);
    return { ok: s.sel, pt, ...s, pm: await pm(), selCount: await selCount(), focusWhere: (await keyGuard(p)).where, stage: 'B(1选中)' }; };

  const runKey = async (name, id, stage, key) => {
    const rec = {};
    try {
      const s = stage === 'A' ? await stageA() : await stageB(id); rec.pre = s;
      if (!s.ok) rec.void = '前置不成立';
      else {
        const g = await keyGuard(p); rec.guardSafe = g.safe;
        if (!g.safe) rec.void = 'keyGuard 拒绝';
        else {
          rec.before = { sel: await selCount(), vis: await visCount(), zoom: await zoomLabel(), dock: await dockBtn(), fs: await fsDialog(), pm: await pm() };
          if (key.meta) await p.keyboard.press(key.meta); else await pressLetter(p, key.letter);
          for (const d of (key.waits || [])) { await p.waitForTimeout(d); const t = await toast(); if (t) { rec.toast = t; rec.toastAfterMs = d; break; } }
          if (key.waits) { if (!rec.toast) rec.toast = null; rec.sampledToMs = key.waits.reduce((a, x) => a + x, 0); }
          rec.after = { sel: await selCount(), vis: await visCount(), zoom: await zoomLabel(), dock: await dockBtn(), fs: await fsDialog(), pm: await pm() };
          rec.changed = Object.fromEntries(Object.keys(rec.before)
            .map((k) => [k, JSON.stringify(rec.before[k]) === JSON.stringify(rec.after[k]) ? '同' : `${JSON.stringify(rec.before[k])}→${JSON.stringify(rec.after[k])}`])
            .filter(([, v]) => v !== '同'));
        }
      }
    } catch (e) { rec.error = e.message; }
    out.keys[`${name}@${stage}`] = rec;
    log(`${name}@${stage} →`, JSON.stringify(rec));
  };

  await runKey('G', made[1], 'B', { letter: 'g', waits: [300, 700, 1500] });
  await runKey('V', made[2], 'B', { letter: 'v' });
  await runKey('F', made[3], 'B', { letter: 'f', waits: [400, 900] });
  await p.keyboard.press('Escape'); await p.waitForTimeout(1000);
  out.fsAfterEsc = { fs: await fsDialog(), pm: await pm() };
  log('F 后 Esc', JSON.stringify(out.fsAfterEsc));
  await runKey('shift1', null, 'A', { meta: 'Shift+Digit1' });
} catch (e) { out.error = e.message; console.error('ABORT:', e.message); }
finally {
  for (let i = 0; i < 2; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(400); }
  for (const v of mine) {
    for (let a = 1; a <= 3 && (await ids()).includes(v); a++) {
      const q = await p.evaluate((x) => { const n = document.querySelector(`.react-flow__node[data-id="${x}"]`); if (!n) return null;
        const r = n.getBoundingClientRect();
        for (const f of [[0.5, 0.5], [0.5, 0.2], [0.25, 0.5], [0.75, 0.5], [0.5, 0.8]]) { const X = Math.round(r.x + r.width * f[0]), Y = Math.round(r.y + r.height * f[1]);
          const h = document.elementFromPoint(X, Y); if (h && n.contains(h) && !h.closest('[role="menu"]')) return { x: X, y: Y }; } return null; }, v);
      if (!q) break;
      await p.mouse.click(q.x, q.y, { button: 'right' }); await p.waitForTimeout(950);
      await p.evaluate(() => { const m = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"],[role="menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop();
        const it = m && Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => /删除/.test(x.innerText || '')); if (it) it.click(); });
      await p.waitForTimeout(1400);
    }
  }
  const left = (await ids()).filter((x) => mine.includes(x));
  log('清理', mine.length, '个 → 剩', left.length, left.length ? '🔴 ' + left.join(' ') : '✅');
  out.end = { status: await status(), zoomLabel: await zoomLabel(), leftover: left };
  log('终态', JSON.stringify(out.end));
  try { const led = JSON.parse(readFileSync(LEDGER, 'utf8'));
    const add = mine.filter((x) => !led.ids.includes(x));
    if (add.length) { led.ids = [...new Set([...led.ids, ...add])].sort();
      led.per_batch = { ...(led.per_batch || {}), 82: [...new Set([...(led.per_batch?.['82'] || []), ...mine])] };
      writeFileSync(LEDGER, JSON.stringify(led, null, 1)); } } catch {}
  writeFileSync(new URL('./_tmp-b82g.json', import.meta.url), JSON.stringify(out, null, 1));
  await b.close();
}
