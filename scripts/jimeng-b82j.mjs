// 批次 82 · J：把 i 轮诊断出来的两个机理修掉，再把 G@B / V@B / F@B 补上。
//
// 🔴 **h 轮 `setZoom(60)` 三次全失败的机理查明了**：
//    `input[data-testid="canvas-zoom-percent-input]` **不在 DOM 里**。
//    历来的脚本（b63/b73/b74/b80e）都是**先点 `Zoom options` 按钮把菜单打开**
//    再找这个 input —— 也就是说**这个 input 只在缩放菜单打开期间挂载**，
//    不是常驻元素。我 h 轮直接 querySelector，必然为 null，写值等于没写。
//    ⇒ 这是一条 testid 契约：**不是「缩放输入框」，是「缩放菜单里的输入框」**。
//
// 🔴 **h/g 两轮「无标题行落点」的机理也查明了**：
//    我用**固定屏上像素 `dy = -30`** 去够标题行。而 30 屏上 px 在不同缩放下
//    对应的 canvas 距离差 5 倍：60% 时 = 50 canvas（命中），
//    13% 时 = 230 canvas（落到画布空白，`.react-flow__pane`）。
//    这是批次 78 那条教训的**第四次复发**：**除数必须当场读，绝不写死**。
//    本轮 `titlePoint` 改为：**先从 viewport inline transform 读 scale**，
//    再用 `-32 * scale` 换算屏上偏移，并在该邻域内扫候选点，
//    取第一个「命中元素在节点内、且带文字或 aria」的点。
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
/** Agent 抽屉状态 —— 本轮的一等前置（h 轮证明它会带进一个 ProseMirror）。 */
const agentState = () => p.evaluate(() => {
  const els = Array.from(document.querySelectorAll('[data-testid^="canvas-agent-"]'));
  const area = els.filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; });
  return { total: els.length, withArea: area.length,
    pmInAgent: document.querySelectorAll('[data-testid^="canvas-agent-"] .ProseMirror[contenteditable="true"]').length,
    pmInNode: document.querySelectorAll('.react-flow__node .ProseMirror[contenteditable="true"]').length,
    pmAnywhere: document.querySelectorAll('.ProseMirror[contenteditable="true"]').length };
});

/** 🔑 当场读 scale，连读两次相同才算静止。 */
const readScale = async () => {
  const rd = () => p.evaluate(() => { const vp = document.querySelector('.react-flow__viewport');
    const t = vp ? (vp.style.transform || '') : ''; const m = t.match(/scale\(([-\d.]+)\)/); return m ? Number(m[1]) : null; });
  const a = await rd(); await p.waitForTimeout(500); const c = await rd();
  return { scale: a, stable: a !== null && a === c, again: c };
};

/** 归位：先开缩放菜单，输入框才在 DOM 里。 */
const setZoom = async (target) => {
  for (let t = 1; t <= 3; t++) {
    const cur = await zoomPct(); if (cur === target) return { ok: true, pct: cur, tries: t - 1, how: 'already' };
    await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(800);
    const seen = await p.evaluate(() => { const i = document.querySelector('input[data-testid="canvas-zoom-percent-input"]'); return i ? i.value : null; });
    if (seen === null) { log(`  第${t}次：菜单开了但 input 仍不在`); await p.keyboard.press('Escape'); await p.waitForTimeout(500); continue; }
    await p.evaluate((v) => { const i = document.querySelector('input[data-testid="canvas-zoom-percent-input"]');
      const s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
      s.call(i, String(v)); i.dispatchEvent(new Event('input', { bubbles: true })); i.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
      i.dispatchEvent(new Event('change', { bubbles: true })); i.blur(); }, target);
    await p.waitForTimeout(1300);
    await p.keyboard.press('Escape'); await p.waitForTimeout(600);
    const a = await zoomPct(); await p.waitForTimeout(900); const c = await zoomPct();
    log(`  第${t}次：input 读到 ${seen}，写 ${target} → ${a}/${c}`);
    if (a === c && a === target) return { ok: true, pct: a, tries: t, how: 'input' };
  }
  return { ok: false, pct: await zoomPct() };
};

/** 🔑 标题行落点：按**当场读的 scale** 换算成屏上偏移，再在邻域里扫，
 *  取第一个「命中元素在节点内、且带文字或 aria」的点。绝不写死屏上像素。 */
/** 同上，但返回可直接点的屏幕坐标（把 nodeBox 的 x/width 一起带出来）。 */
const titlePointXY = async (id) => {
  const sc = await readScale();
  if (!sc.scale) return null;
  return await p.evaluate((arg) => {
    const n = document.querySelector(`.react-flow__node[data-id="${arg.v}"]`); if (!n) return null;
    const rr = n.getBoundingClientRect();
    const tries = [];
    for (let k = -70; k <= 4; k += 3) for (const f of [0.25, 0.5, 0.75]) {
      const x = Math.round(rr.x + rr.width * f), y = Math.round(rr.y + Math.round(k * arg.scale));
      if (x < 0 || y < 0 || y > 716) continue;
      const h = document.elementFromPoint(x, y); if (!h || !n.contains(h)) continue;
      const txt = (h.innerText || h.getAttribute('aria-label') || '').trim();
      tries.push({ k, f, x, y, txt: txt.slice(0, 14), hit: `${h.tagName}.${String(h.className || '').split(' ')[0]}`.slice(0, 44) });
    }
    const withTxt = tries.filter((t) => t.txt);
    const pick = withTxt[0] || tries[0] || null;
    return { scale: arg.scale, nodeBox: `${Math.round(rr.width)}x${Math.round(rr.height)}@${Math.round(rr.x)},${Math.round(rr.y)}`,
      pick, nTries: tries.length, sample: tries.slice(0, 5) };
  }, { v: id, scale: sc.scale });
};

const clickPane = async () => {
  const e = await p.evaluate(() => { const pane = document.querySelector('.react-flow__pane'); if (!pane) return null;
    for (let y = 110; y < 660; y += 20) for (let x = 210; x < 1240; x += 28) {
      const h = document.elementFromPoint(x, y); if (h && pane.contains(h)) return { x, y }; }
    return null; });
  if (!e) return null; await p.mouse.click(e.x, e.y); await p.waitForTimeout(650); return e;
};

try {
  out.zoom = await setZoom(60);
  log('缩放归位', JSON.stringify(out.zoom));
  out.scaleRead = await readScale();
  log('scale', JSON.stringify(out.scaleRead));
  out.agentBefore = await agentState();
  log('Agent 前置', JSON.stringify(out.agentBefore));
  if (out.agentBefore.withArea > 0) { await p.keyboard.press('Meta+Slash'); await p.waitForTimeout(1400);
    out.agentForced = await agentState(); log('强制关抽屉', JSON.stringify(out.agentForced)); }

  const pre = await ids();
  const rail = await p.evaluate(() => { const el = Array.from(document.querySelectorAll('button,[role="button"]'))
    .find((x) => /^文本$/.test(((x.getAttribute('aria-label') || '') + (x.innerText || '')).trim()));
    const r = el.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  for (let k = 0; k < 3; k++) { await p.mouse.click(rail.x, rail.y); await p.waitForTimeout(3000); }
  const made = (await ids()).filter((x) => !pre.includes(x));
  log('新建', made.length, made.join(' '), '缩放=', await zoomPct());
  if (made.length < 3) throw new Error('新建不足：' + made.length);
  mine.push(...made);

  out.keys = {};
  const stageB = async (id) => { await clickPane(); const t = await titlePointXY(id);
    if (!t || !t.pick) return { ok: false, why: '无标题行落点', t };
    await p.mouse.click(t.pick.x, t.pick.y); await p.waitForTimeout(800);
    const s = await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); return /(^|\s)selected(\s|$)/.test(n.className); }, id);
    const ag = await agentState();
    return { ok: s, scale: t.scale, nodeBox: t.nodeBox, pick: t.pick, selected: s,
      selCount: await selCount(), agent: ag, focusWhere: (await keyGuard(p)).where }; };
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
        rec.after = { sel: await selCount(), vis: await visCount(), zoom: await zoomLabel(), dock: await dockBtn(), fs: await fsDialog(), agent: (await agentState()).withArea };
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
  out.fsAfterEsc = { fs: await fsDialog(), agent: await agentState() };
  log('F 后 Esc', JSON.stringify(out.fsAfterEsc));
} catch (e) { out.error = e.message; console.error('ABORT:', e.message); }
finally {
  for (let i = 0; i < 2; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(400); }
  for (const v of mine) {
    for (let a = 1; a <= 3 && (await ids()).includes(v); a++) {
      const sc = await readScale();
      const q = await p.evaluate((arg) => { const n = document.querySelector(`.react-flow__node[data-id="${arg.v}"]`); if (!n) return null;
        const r = n.getBoundingClientRect();
        for (const f of [[0.5, 0.5], [0.5, 0.2], [0.25, 0.5], [0.75, 0.5], [0.5, 0.8]]) { const x = Math.round(r.x + r.width * f[0]), y = Math.round(r.y + r.height * f[1]);
          const h = document.elementFromPoint(x, y); if (h && n.contains(h) && !h.closest('[role="menu"]')) return { x, y }; } return null; }, { v });
      if (!q) { log('  删不掉，落点全空，scale=', sc.scale); break; }
      await p.mouse.click(q.x, q.y, { button: 'right' }); await p.waitForTimeout(950);
      await p.evaluate(() => { const m = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"],[role="menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop();
        const it = m && Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => /删除/.test(x.innerText || '')); if (it) it.click(); });
      await p.waitForTimeout(1400);
    }
  }
  const left = (await ids()).filter((x) => mine.includes(x));
  log('清理', mine.length, '个 → 剩', left.length, left.length ? '🔴 ' + left.join(' ') : '✅');
  out.zoomFinal = await setZoom(60);
  out.end = { status: await status(), zoomLabel: await zoomLabel(), zoomRestore: out.zoomFinal, leftover: left, scale: await readScale() };
  log('终态', JSON.stringify(out.end));
  try { const led = JSON.parse(readFileSync(LEDGER, 'utf8'));
    const add = mine.filter((x) => !led.ids.includes(x));
    if (add.length) { led.ids = [...new Set([...led.ids, ...add])].sort();
      led.per_batch = { ...(led.per_batch || {}), 82: [...new Set([...(led.per_batch?.['82'] || []), ...mine])] };
      writeFileSync(LEDGER, JSON.stringify(led, null, 1)); } } catch {}
  writeFileSync(new URL('./_tmp-b82j.json', import.meta.url), JSON.stringify(out, null, 1));
  await b.close();
}
