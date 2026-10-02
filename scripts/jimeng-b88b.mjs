// 批次 88 · B：补 a 轮两个没测到的格，并验一条刚露头的线索。
//
// 🔴 **a 轮最大的失误：「静息态」根本没静息。**
//    三档的 `sel` 全是 **1** —— 新建的导演台节点**默认就自动选中**
//    （摘要早就记过这条：「新节点本来就自动选中」，我在 a 轮按的 Esc 对它无效）。
//    ⇒ **「静息态 vs 选中态」这一组完全没测到**，`diff60 新增 0` 正是因为
//    前后是**同一个状态**。这与批次 87 那条教训同源：
//    **判据没成立却当成「测了」，比没测更危险。**
//    正确做法：**断言 `sel === 0`** 才算静息态，不成立就记 VOID。
//
// 🔑 **a 轮漏出的一条线索（可能是真发现）**：标题 `flow-node-title` 的顶边
//    相对节点顶边的偏移，**两档屏上都是 32**：
//      60%（scale 0.6）：title y=232、节点 y=264 → **屏上差 32**（canvas 差 53.3）
//      100%（scale 1）  ：title y=168、节点 y=200 → **屏上差 32**（canvas 差 32）
//    ⇒ 若第三档（40%）**屏上差仍是 32**，那就说明**标题行也不随画布缩放**
//    （portal 挂载），而**批次 78 钉的「标题行在节点上方 31–33 canvas px」是错的量纲**。
//    ⇒ 这正是批次 85/87/88 反复出现的同一族结论。**必须加第三档。**
//
// ⚠️ 另一件没查成的：`Rename 导演台` 两档都是 `null`。
//    a 轮的选择器是「在节点 DOM 内找 innerText/aria 含 `Rename 导演台` 的元素」。
//    页面说它是「盖在标题上的透明命中区，`39×32@564,232`，与 `flow-node-title`
//    `59×32@544,232` **同一 y**」⇒ **它可能不在节点 DOM 内**（同 `node-toolbar` 一样挂在
//    `.react-flow__renderer` 下）。本轮改成**按位置找**：取 title 矩形，
//    在**整个文档**里找与它同 y、x 落在 title 范围内的元素。
//
// ⛔ 仍不点：进入导演台 / Rename 导演台 / 两个连接手柄 / F 键。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';
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
const zoomPct = async () => { const l = await p.evaluate(() => { const e = document.querySelector('button[aria-label^="Zoom options"]');
    return e ? e.getAttribute('aria-label') : null; }); return l ? Number((l.match(/(\d+)%/) || [])[1]) : null; };
const readScale = async () => { const rd = () => p.evaluate(() => { const vp = document.querySelector('.react-flow__viewport');
    const m = (vp ? (vp.style.transform || '') : '').match(/scale\(([-\d.]+)\)/); return m ? Number(m[1]) : null; });
  const a = await rd(); await p.waitForTimeout(500); const c = await rd(); return { scale: a, stable: a !== null && a === c }; };
const setZoom = async (t0) => { for (let t = 1; t <= 3; t++) { if (await zoomPct() === t0) return { ok: true, how: 'already' };
    await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(800);
    if (!await p.evaluate(() => !!document.querySelector('input[data-testid="canvas-zoom-percent-input"]'))) { await p.keyboard.press('Escape'); await p.waitForTimeout(500); continue; }
    await p.evaluate((v) => { const i = document.querySelector('input[data-testid="canvas-zoom-percent-input"]');
      Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(i, String(v));
      i.dispatchEvent(new Event('input', { bubbles: true })); i.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
      i.dispatchEvent(new Event('change', { bubbles: true })); i.blur(); }, t0);
    await p.waitForTimeout(1300); await p.keyboard.press('Escape'); await p.waitForTimeout(600);
    const a = await zoomPct(); await p.waitForTimeout(900); const c = await zoomPct();
    if (a === c && a === t0) return { ok: true, how: 'input', pct: a }; }
  return { ok: false, pct: await zoomPct() }; };
const clickPane = async () => { const e = await p.evaluate(() => { const pane = document.querySelector('.react-flow__pane'); if (!pane) return null;
    for (let y = 110; y < 660; y += 20) for (let x = 210; x < 1240; x += 28) { const h = document.elementFromPoint(x, y); if (h && pane.contains(h)) return { x, y }; }
    return null; });
  if (!e) return null; await p.mouse.click(e.x, e.y); await p.waitForTimeout(900); return e; };
const titlePointXY = async (id) => { const sc = await readScale();
  return await p.evaluate((arg) => { const n = document.querySelector(`.react-flow__node[data-id="${arg.v}"]`); if (!n) return null;
    const r = n.getBoundingClientRect();
    // 只认命中**标题**（testid=flow-node-title 或文字逐字为「导演台」）的落点
    for (let k = -70; k <= 4; k += 2) for (const f of [0.1, 0.25, 0.5, 0.75, 0.9]) {
      const x = Math.round(r.x + r.width * f), y = Math.round(r.y + Math.round(k * arg.scale));
      if (x < 0 || y < 0 || y > 716) continue;
      const h = document.elementFromPoint(x, y); if (!h || !n.contains(h)) continue;
      const tt = h.getAttribute('data-testid') || '';
      if (/flow-node-title/.test(tt) || /^(导演台|Rename)/.test((h.innerText || '').trim())) return { x, y, k, hit: tt || h.tagName, txt: (h.innerText || '').trim().slice(0, 14) }; }
    return null; }, { v: id, scale: sc.scale }); };

/** 🔑 按**位置**找：与 title 同一 y、x 落在 title 范围内的所有元素（全文档）。 */
const probeTitleRow = (id) => p.evaluate((v) => {
  const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!n) return null;
  const t = n.querySelector('[data-testid="flow-node-title"]'); if (!t) return null;
  const nr = n.getBoundingClientRect(), tr = t.getBoundingClientRect();
  const vp = document.querySelector('.react-flow__viewport');
  const m = (vp ? (vp.style.transform || '') : '').match(/scale\(([-\d.]+)\)/); const scale = m ? Number(m[1]) : null;
  const hits = [];
  for (const e of document.querySelectorAll('*')) { const r = e.getBoundingClientRect();
    if (!(r.width > 0 && r.height > 0)) continue;
    if (Math.abs(r.y - tr.y) > 2) continue;                       // 同一 y
    if (r.x < tr.x - 6 || r.x + r.width > tr.x + tr.width + 6) continue;  // x 落在 title 范围附近
    hits.push({ tag: e.tagName, cls: String(e.className || '').split(' ').slice(0, 2).join('.'),
      box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
      canvas: scale ? `${Math.round(r.width / scale)}x${Math.round(r.height / scale)}` : null,
      testid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'),
      t: (e.innerText || '').trim().slice(0, 18), inNode: n.contains(e),
      op: getComputedStyle(e).opacity, pe: getComputedStyle(e).pointerEvents, cur: getComputedStyle(e).cursor }); }
  return { title: `${Math.round(tr.width)}x${Math.round(tr.height)}@${Math.round(tr.x)},${Math.round(tr.y)}`,
    nodeBox: `${Math.round(nr.width)}x${Math.round(nr.height)}@${Math.round(nr.x)},${Math.round(nr.y)}`,
    titleOffsetScreen: { dy: Math.round(tr.y - nr.y), dx: Math.round(tr.x - nr.x) },
    titleOffsetCanvas: scale ? { dy: Math.round((tr.y - nr.y) / scale), dx: Math.round((tr.x - nr.x) / scale) } : null,
    scale, hits };
}, id);

try {
  out.zoom0 = await setZoom(60);
  const pre = await ids();
  const rail = await p.evaluate(() => { const el = Array.from(document.querySelectorAll('button,[role="button"]'))
    .find((x) => /^导演台$/.test(((x.getAttribute('aria-label') || '') + (x.innerText || '')).trim()));
    const r = el.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  await p.mouse.click(rail.x, rail.y); await p.waitForTimeout(3400);
  const made = (await ids()).filter((x) => !pre.includes(x));
  if (made.length !== 1) throw new Error('新建异常 ' + made.length);
  mine.push(made[0]); const id = made[0];
  log('自建节点', id, '初始 sel =', await selCount(), '（注意：新节点默认自动选中）');

  out.grids = [];
  // ══════ ① 真·静息态：先点空白把选中消掉，并**断言 sel===0** ══════
  await clickPane();
  const selIdle = await selCount();
  out.grids.push({ tag: '静息', sel: selIdle, asserted: selIdle === '0', ...(await probeTitleRow(id)) });
  log(`静息态 sel=${selIdle} 断言=${selIdle === '0'}`);
  if (selIdle === '0') {
    log('  title', out.grids[0].title, '偏移屏上', JSON.stringify(out.grids[0].titleOffsetScreen), 'canvas', JSON.stringify(out.grids[0].titleOffsetCanvas));
    log(`  同 y 命中 ${out.grids[0].hits.length} 个：`);
    out.grids[0].hits.forEach((h) => log('    ·', JSON.stringify(h)));
  } else out.grids[0].void = '断言未过：sel 不为 0，不算静息态';

  // ══════ ② 选中态：点标题行 ══════
  const t = await titlePointXY(id);
  log('标题落点', JSON.stringify(t));
  if (t) { await p.mouse.click(t.x, t.y); await p.waitForTimeout(2000); }
  const selSel = await selCount();
  const g2 = { tag: '选中', sel: selSel, asserted: selSel !== '0', titlePoint: t, ...(await probeTitleRow(id)) };
  out.grids.push(g2);
  log(`选中态 sel=${selSel}`);
  if (g2.hits) {
    log('  title', g2.title, '偏移屏上', JSON.stringify(g2.titleOffsetScreen), 'canvas', JSON.stringify(g2.titleOffsetCanvas));
    log(`  同 y 命中 ${g2.hits.length} 个：`);
    g2.hits.forEach((h) => log('    ·', JSON.stringify(h)));
  }
  // 两态差集（限定在 title 那一行）
  if (out.grids[0].hits && g2.hits) {
    const k0 = new Set(out.grids[0].hits.map((h) => `${h.tag}|${h.box}|${h.aria}|${h.testid}`));
    out.rowDiff = g2.hits.filter((h) => !k0.has(`${h.tag}|${h.box}|${h.aria}|${h.testid}`));
    log(`🔑 静息→选中，title 那一行新增 ${out.rowDiff.length} 个：`);
    out.rowDiff.forEach((h) => log('    +', JSON.stringify(h)));
  }
  await p.keyboard.press('Escape'); await p.waitForTimeout(800);

  // ══════ ③ 第三档缩放：验「32」是屏上恒定还是 canvas 恒定 ══════
  for (const z of [40, 100]) {
    const zz = await setZoom(z);
    await p.waitForTimeout(900);
    await clickPane();
    const s = await selCount();
    const g = { tag: `静息@${z}%`, zoom: await zoomPct(), setZoom: zz, sel: s, asserted: s === '0', ...(await probeTitleRow(id)) };
    out.grids.push(g);
    log(`── ${z}% ── sel=${s}`, g.titleOffsetScreen ? `title 偏移 屏上 dy=${g.titleOffsetScreen.dy} dx=${g.titleOffsetScreen.dx} | canvas dy=${g.titleOffsetCanvas.dy} dx=${g.titleOffsetCanvas.dx} | node ${g.nodeBox}` : '(未取到)');
    if (g.hits) g.hits.forEach((h) => log('    ·', JSON.stringify(h)));
  }
  out.offsetTable = out.grids.filter((g) => g.titleOffsetScreen).map((g) => ({
    tag: g.tag, zoom: await0(g), scale: g.scale,
    screenDy: g.titleOffsetScreen.dy, screenDx: g.titleOffsetScreen.dx,
    canvasDy: g.titleOffsetCanvas ? g.titleOffsetCanvas.dy : null, canvasDx: g.titleOffsetCanvas ? g.titleOffsetCanvas.dx : null,
    nodeBox: g.nodeBox, titleBox: g.title }));
  log('偏移汇总：');
  out.offsetTable.forEach((r) => log('   ', JSON.stringify(r)));
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
  log('清理', mine.length, '→ 剩', left.length, left.length ? '🔴 ' + left.join(' ') : '✅');
  out.zoomFinal = await setZoom(60);
  out.end = { status: await status(), leftover: left };
  log('终态', JSON.stringify(out.end));
  try { const led = JSON.parse(readFileSync(LEDGER, 'utf8'));
    const add = mine.filter((x) => !led.ids.includes(x));
    if (add.length) { led.ids = [...new Set([...led.ids, ...add])].sort();
      led.per_batch = { ...(led.per_batch || {}), 88: [...new Set([...(led.per_batch?.['88'] || []), ...mine])] };
      writeFileSync(LEDGER, JSON.stringify(led, null, 1)); } } catch {}
  writeFileSync(new URL('./_tmp-b88b.json', import.meta.url), JSON.stringify(out, null, 1));
  await b.close();
}
function await0() { return null; }
