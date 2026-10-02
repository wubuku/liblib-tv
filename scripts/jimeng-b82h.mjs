// 批次 82 · H：验证 g 轮撞出的那个真 bug，并把它变成手册里的一条契约。
//
// 🔴 **g 轮的「连点 5 次都 selected:true / enteredEdit:true」是假的。**
//    `.ProseMirror[contenteditable="true"]` 在那里 **`357×84@890,554` 恒定存在**、
//    `isConnected:true`、坐标 890,554 恒定不变——它**根本不在我的节点上**
//    （我的节点在 579,229）。它在**右下角**。
//    ⇒ 前一轮按 `⌘/` **打开的 Agent 抽屉里就有一个 ProseMirror 输入框**，
//      一旦抽屉开着，它就**常驻**，于是
//      「文档里有 ProseMirror」这个判据**永远为真**。
//
//    连锁后果（把 f/g 两轮的错误一次说清）：
//      · f 轮 B 档前置 `ok = sel && !inEdit` 里 `inEdit` **恒为 true**
//        ⇒ `ok` **恒为 false** ⇒ G@B / V@B / F@B / ⇧1 **全是假失败**。
//        **结论没变，证据是坏的。**
//      · f 轮 `visCount` 在 844 / 862 / 906 之间乱跳，也不是画布在变，
//        是 **Agent 抽屉在开与关**。
//    ⇒ 批次 80 写下的「出现 `.ProseMirror[contenteditable=true]` ⇒ 进入编辑态」
//      **这条判据本身有缺陷**，需要在手册里订正。
//
// 本轮三件事：
//   ① 把 **Agent 抽屉是否开着**提升为**一等前置**并显式断言（此前四轮都没管过它）；
//   ② 判据改成**作用域内**查询：编辑态 = **该节点内部**有 ProseMirror；
//   ③ 在 Agent 抽屉**显式关闭**的状态下重测 G@B / V@B / F@B。
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
const zoomPct = async () => { const l = await zoomLabel(); return l ? Number((l.match(/(\d+)%/) || [])[1]) : null; };
const dockBtn = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-pointer-tool-toggle"]');
  return e ? { aria: e.getAttribute('aria-label'), pressed: e.getAttribute('aria-pressed') } : null; });
const toast = () => p.evaluate(() => { const c = Array.from(document.querySelectorAll('div,span'))
    .filter((x) => /此快捷键当前不可用/.test((x.innerText || '').trim()) && x.children.length <= 2);
  const e = c.sort((a, b2) => b2.getBoundingClientRect().width - a.getBoundingClientRect().width)[0];
  if (!e) return null; const r = e.getBoundingClientRect();
  return { box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`, text: (e.innerText || '').trim() }; });
const visCount = () => p.evaluate(() => { let n = 0;
  for (const e of document.querySelectorAll('*')) { const r = e.getBoundingClientRect(); if (r.width > 0 && r.height > 0) n++; } return n; });
const fsDialog = () => p.evaluate(() => { const e = document.querySelector('[text-editor-fullscreen-dialog]'); if (!e) return null;
  const r = e.getBoundingClientRect(); return `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`; });

/** 🔴 本轮新增的一等前置：Agent 抽屉的开关状态。 */
const agentState = () => p.evaluate(() => {
  const els = Array.from(document.querySelectorAll('[data-testid^="canvas-agent-"]'));
  const withArea = els.filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; });
  const pms = Array.from(document.querySelectorAll('.ProseMirror[contenteditable="true"]')).map((e) => {
    const r = e.getBoundingClientRect();
    return { box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
      ce: e.getAttribute('contenteditable'), connected: e.isConnected,
      inAgent: !!e.closest('[data-testid^="canvas-agent-"]'),
      inNode: !!e.closest('.react-flow__node'),
      ph: e.getAttribute('data-placeholder') || e.getAttribute('placeholder') || (e.innerText || '').trim().slice(0, 20) };
  });
  return { total: els.length, withArea: withArea.length, proseMirrors: pms };
});
/** 编辑态判据（作用域内）——**只看该节点内部**，不受 Agent 抽屉污染。 */
const nodeEditing = (id) => p.evaluate((v) => {
  const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!n) return null;
  const e = n.querySelector('.ProseMirror[contenteditable="true"]');
  if (!e) return { inNode: false };
  const r = e.getBoundingClientRect();
  return { inNode: true, w: Math.round(r.width), h: Math.round(r.height), active: e.contains(document.activeElement) };
}, id);

const setZoom = async (target) => {
  for (let i = 0; i < 3; i++) {
    const cur = await zoomPct();
    if (cur === target) return { ok: true, pct: cur, tries: i };
    await p.evaluate((t) => { const i = document.querySelector('input[data-testid="canvas-zoom-percent-input"]');
      if (!i) return; const s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
      s.call(i, String(t)); i.dispatchEvent(new Event('input', { bubbles: true })); i.dispatchEvent(new Event('change', { bubbles: true })); i.blur(); }, target);
    await p.waitForTimeout(1400);
    const a = await zoomPct(); await p.waitForTimeout(900); const c = await zoomPct();
    if (a === c && a === target) return { ok: true, pct: a, tries: i + 1 };
  }
  return { ok: false, pct: await zoomPct() };
};

const clickPane = async () => {
  const e = await p.evaluate(() => { const pane = document.querySelector('.react-flow__pane'); if (!pane) return null;
    for (let y = 110; y < 660; y += 20) for (let x = 210; x < 1240; x += 28) {
      const h = document.elementFromPoint(x, y); if (h && pane.contains(h)) return { x, y }; }
    return null; });
  if (!e) return null; await p.mouse.click(e.x, e.y); await p.waitForTimeout(650); return e;
};
const titlePoint = (id) => p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!n) return null;
  const r = n.getBoundingClientRect();
  for (const f of [0.25, 0.5, 0.75]) { const x = Math.round(r.x + r.width * f), y = Math.round(r.y - 30);
    const h = document.elementFromPoint(x, y);
    if (h && n.contains(h) && (h.innerText || h.getAttribute('aria-label'))) return { x, y, txt: (h.innerText || '').trim().slice(0, 12) }; }
  return null; }, id);

try {
  // ══════ ① 归位缩放 + 读 Agent 抽屉真身 ══════
  out.zoomRestore = await setZoom(60);
  log('缩放归位', JSON.stringify(out.zoomRestore));
  out.agentInitial = await agentState();
  log('初始 Agent 状态', JSON.stringify(out.agentInitial, null, 1));

  // ══════ ② 用 ⌘/ 开关一次，把 ProseMirror 的归属钉死 ══════
  await clickPane();
  out.toggle = [];
  for (let i = 0; i < 2; i++) {
    const g = await keyGuard(p);
    if (!g.safe) { out.toggle.push({ i, refused: true }); break; }
    await p.keyboard.press('Meta+Slash'); await p.waitForTimeout(1500);
    out.toggle.push({ i, focus: g.where, ...(await agentState()), vis: await visCount() });
    log(`  ⌘/ 第${i + 1}次 →`, JSON.stringify(out.toggle[i]));
  }
  // 回到「抽屉关闭」基准
  out.agentFinal = await agentState();
  log('两按后 Agent 状态', JSON.stringify(out.agentFinal, null, 1));

  // ══════ ③ 抽屉关闭基准下重测三格 ══════
  if (out.agentFinal.withArea > 0) { await p.keyboard.press('Meta+Slash'); await p.waitForTimeout(1400);
    out.agentClosedAgain = await agentState(); log('再按一次关', JSON.stringify(out.agentClosedAgain)); }

  const pre = await ids();
  const rail = await p.evaluate(() => { const el = Array.from(document.querySelectorAll('button,[role="button"]'))
    .find((x) => /^文本$/.test(((x.getAttribute('aria-label') || '') + (x.innerText || '')).trim()));
    const r = el.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  for (let k = 0; k < 3; k++) { await p.mouse.click(rail.x, rail.y); await p.waitForTimeout(3000); }
  const made = (await ids()).filter((x) => !pre.includes(x));
  log('新建', made.length, made.join(' '));
  if (made.length < 3) throw new Error('新建不足：' + made.length);
  mine.push(...made);
  out.zoomAfterCreate = await zoomPct();
  log('新建后缩放', out.zoomAfterCreate + '%');

  out.keys = {};
  const stageB = async (id) => { await clickPane(); const pt = await titlePoint(id);
    if (!pt) return { ok: false, why: '无标题行落点' };
    await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(800);
    const s = await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); return /(^|\s)selected(\s|$)/.test(n.className); }, id);
    return { ok: s, pt, selected: s, nodeEditing: await nodeEditing(id), selCount: await selCount(), agent: (await agentState()).withArea }; };
  const runKey = async (name, id, key) => {
    const rec = {};
    try {
      const s = await stageB(id); rec.pre = s;
      if (!s.ok) rec.void = '前置不成立';
      else {
        const g = await keyGuard(p); rec.guardSafe = g.safe;
        rec.before = { sel: await selCount(), vis: await visCount(), zoom: await zoomLabel(), dock: await dockBtn(), fs: await fsDialog(), agent: (await agentState()).withArea };
        await pressLetter(p, key.letter);
        for (const d of (key.waits || [])) { await p.waitForTimeout(d); const t = await toast(); if (t) { rec.toast = t; rec.toastAfterMs = d; break; } }
        if (key.waits) { if (!rec.toast) rec.toast = null; rec.sampledToMs = key.waits.reduce((a, x) => a + x, 0); }
        rec.after = { sel: await selCount(), vis: await visCount(), zoom: await zoomLabel(), dock: await dockBtn(), fs: await fsDialog(), agent: (await agentState()).withArea, nodeEditing: await nodeEditing(id) };
        rec.changed = Object.fromEntries(Object.keys(rec.before)
          .map((k) => [k, JSON.stringify(rec.before[k]) === JSON.stringify(rec.after[k]) ? '同' : `${JSON.stringify(rec.before[k])}→${JSON.stringify(rec.after[k])}`])
          .filter(([, v]) => v !== '同'));
      }
    } catch (e) { rec.error = e.message; }
    out.keys[name] = rec; log(`${name} →`, JSON.stringify(rec));
  };
  await runKey('G@B', made[0], { letter: 'g', waits: [300, 700, 1500] });
  await runKey('V@B', made[1], { letter: 'v' });
  await runKey('F@B', made[2], { letter: 'f', waits: [400, 900] });
  await p.keyboard.press('Escape'); await p.waitForTimeout(1000);
  out.fsAfterEsc = { fs: await fsDialog(), nodeEditing: await nodeEditing(made[2]) };
  log('F 后 Esc', JSON.stringify(out.fsAfterEsc));
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
  out.zoomFinal = await setZoom(60);
  out.end = { status: await status(), zoomLabel: await zoomLabel(), zoomRestore: out.zoomFinal, leftover: left, agent: await agentState() };
  log('终态', JSON.stringify(out.end));
  try { const led = JSON.parse(readFileSync(LEDGER, 'utf8'));
    const add = mine.filter((x) => !led.ids.includes(x));
    if (add.length) { led.ids = [...new Set([...led.ids, ...add])].sort();
      led.per_batch = { ...(led.per_batch || {}), 82: [...new Set([...(led.per_batch?.['82'] || []), ...mine])] };
      writeFileSync(LEDGER, JSON.stringify(led, null, 1)); } } catch {}
  writeFileSync(new URL('./_tmp-b82h.json', import.meta.url), JSON.stringify(out, null, 1));
  await b.close();
}
