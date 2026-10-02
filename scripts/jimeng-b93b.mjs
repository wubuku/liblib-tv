// 批次 93 · B：受控复测 a 轮那两个「说不清」的结果。
//
// a 轮拿到的四条：
//   ① class `.react-flow__node-toolbar` 命中 **3** 个，testid `[data-testid=node-toolbar]` 只命中 **2** 个
//      ⇒ 多出来那个是 `0×0@640,228` 的占位，**class 比 testid 宽**。
//   ② @60% 工具条 `192×40`（canvas `320×67`）复现；**@100% / @40% 变成 `0×0`、按钮 0 个**。
//   ③ 双击后**仍是 3 项**（背景色/全屏/下载），**没有变成八项**。
//   ④ 本页第 38 行的 **`185×40` 三档都没复现**。
//
// 🔴 ② 与 ③ 都不能直接下结论，因为 a 轮**没有断言前置**：
//   - ② 换缩放后节点可能被移出视口 ⇒ 工具条折叠。所以每档都要**断言节点在视口内**且
//     **`sel === 1`**，再读工具条。
//   - ③ 双击未必进了编辑态。所以每一步都读 **`contenteditable` / `.ProseMirror` 是否存在**
//     —— 那是「进没进编辑态」的机械判据，而不是靠看工具条变没变。
import { chromium } from 'playwright';
import { writeFileSync, readFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const LEDGER = new URL('./jimeng-ephemeral-ledger.json', import.meta.url);
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };
const mine = [];

const ids = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const selN = async () => p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]);
const credits = async () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-commerce-entry"]'); return e ? e.getAttribute('aria-label') : null; });
const zoomPct = async () => p.evaluate(() => { const e = document.querySelector('button[aria-label^="Zoom options"]'); return e ? Number((e.getAttribute('aria-label').match(/(\d+)%/) || [])[1]) : null; });
const setZoom = async (t0) => { for (let t = 1; t <= 3; t++) { if (await zoomPct() === t0) return true;
  await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(800);
  const has = await p.evaluate(() => !!document.querySelector('input[data-testid="canvas-zoom-percent-input"]'));
  if (!has) { await p.keyboard.press('Escape'); await p.waitForTimeout(500); continue; }
  await p.evaluate((v) => { const i = document.querySelector('input[data-testid="canvas-zoom-percent-input"]');
    Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(i, String(v));
    i.dispatchEvent(new Event('input', { bubbles: true })); i.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
    i.dispatchEvent(new Event('change', { bubbles: true })); i.blur(); }, t0);
  await p.waitForTimeout(1400); await p.keyboard.press('Escape'); await p.waitForTimeout(700);
  const a = await zoomPct(); await p.waitForTimeout(800); const c = await zoomPct();
  if (a === t0 && a === c) return true; } return false; };
const scan = (id) => p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return null;
  const r = n.getBoundingClientRect();
  const inVp = r.left >= 0 && r.top >= 0 && r.right <= 1280 && r.bottom <= 720;
  let pt = null;
  for (let fx = 0.04; fx <= 0.96 && !pt; fx += 0.04) for (let fy = 0.04; fy <= 0.96 && !pt; fy += 0.04) {
    const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
    if (x < 0 || y < 0 || x > 1280 || y > 720) continue;
    const el = document.elementFromPoint(x, y);
    if (el && el.closest('.react-flow__node') === n) pt = { x, y }; }
  return { pt, inVp, box: `${Math.round(r.width)}×${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}` }; }, id);
/** 选中并**回读确认**：返回前置是否全部成立 */
const selectStrict = async (id) => {
  for (const z of [await zoomPct(), 60, 100, 40, 200, 400, 800]) {
    if (!await setZoom(z)) continue;
    const s = await scan(id);
    if (!s || !s.pt) { log(`   @${z}% 找不到落点（${s?.box}）`); continue; }
    await p.mouse.click(s.pt.x, s.pt.y); await p.waitForTimeout(1100);
    const sel = await selN();
    const who = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
    if (sel === '1' && who[0] === id) return { ok: true, zoom: z, pt: s.pt, inViewport: s.inVp, sel, who };
    log(`   @${z}% 点上去 sel=${sel} who=${JSON.stringify(who)}`);
    await p.keyboard.press('Escape'); await p.waitForTimeout(500); }
  return { ok: false }; };
const rightClick = async (x, y) => { await p.mouse.move(x, y); await p.waitForTimeout(150);
  await p.mouse.down({ button: 'right' }); await p.waitForTimeout(220); await p.mouse.up({ button: 'right' }); await p.waitForTimeout(1100); };
const clickMenuItem = async (src) => { const ok = await p.evaluate((s) => { const m = document.querySelector('[data-testid="canvas-context-menu"]'); if (!m) return false;
  const it = Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => new RegExp(s).test(x.innerText.replace(/\s+/g, ' ').trim())); if (it) { it.click(); return true; } return false; }, src);
  await p.waitForTimeout(1600); return ok; };

const read = () => p.evaluate(() => {
  const byClass = Array.from(document.querySelectorAll('.react-flow__node-toolbar'));
  const byTid = Array.from(document.querySelectorAll('[data-testid="node-toolbar"]'));
  const desc = (e) => { const r = e.getBoundingClientRect();
    return { hasTid: e.getAttribute('data-testid'), box: `${Math.round(r.width)}×${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
      n: e.querySelectorAll('button,[role="button"]').length,
      labels: Array.from(e.querySelectorAll('button,[role="button"]')).map((x) => x.getAttribute('aria-label') || (x.innerText || '').trim() || '(无)') }; };
  // 编辑态的机械判据：有 contenteditable / ProseMirror
  const ed = { contenteditable: document.querySelectorAll('[contenteditable="true"]').length,
    proseMirror: document.querySelectorAll('.ProseMirror').length,
    inNode: Array.from(document.querySelectorAll('.ProseMirror')).filter((e) => e.closest('.react-flow__node')).length };
  return { classN: byClass.length, tidN: byTid.length, class: byClass.map(desc), tid: byTid.map(desc), edit: ed };
});

try {
  if (await selN() !== '0') { await p.keyboard.press('Escape'); await p.waitForTimeout(600); }
  await setZoom(60);
  out.start = { nodes: (await ids()).length, sel: await selN(), credits: await credits(), zoom: await zoomPct() };
  log('起点：', JSON.stringify(out.start));

  const pre0 = await ids();
  const rail = await p.evaluate(() => { const el = Array.from(document.querySelectorAll('button,[role="button"]'))
    .find((x) => /^文本$/.test(((x.getAttribute('aria-label') || '') + (x.innerText || '')).trim()));
    if (!el) return null; const r = el.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  await p.mouse.click(rail.x, rail.y); await p.waitForTimeout(3800);
  const A = (await ids()).filter((x) => !pre0.includes(x))[0];
  if (!A) throw new Error('新建失败');
  mine.push(A); await p.keyboard.press('Escape'); await p.waitForTimeout(800);
  log('自建：', A);

  // ── 受控复测 ②：逐档缩放，每档都断言前置 ──
  out.zoomGrids = [];
  for (const z of [60, 100, 40, 60]) {
    const s = await selectStrict(A);
    if (!s.ok) { out.zoomGrids.push({ zoom: z, fail: 'select' }); log(`@${z}% 选不中`); continue; }
    const r = await read();
    const sc = await p.evaluate(() => { const vp = document.querySelector('.react-flow__viewport');
      const m = (vp ? (vp.style.transform || '') : '').match(/scale\(([-\d.]+)\)/); return m ? Number(m[1]) : null; });
    const real = r.tid.filter((t) => t.n > 0);
    const row = { askedZoom: z, actualZoom: await zoomPct(), scale: sc, sel: s.sel, who: s.who, inViewport: s.inViewport,
      classN: r.classN, tidN: r.tidN, realToolbars: real.length,
      boxes: r.tid.map((t) => ({ box: t.box, n: t.n, hasTid: t.hasTid })),
      classOnly: r.class.filter((c) => !c.hasTid).map((c) => c.box),
      labels: real[0]?.labels, edit: r.edit };
    out.zoomGrids.push(row);
    log(`  想要 ${z}%｜实到 ${row.actualZoom}% scale=${sc}｜sel=${row.sel} 视口内=${row.inViewport}｜class=${row.classN} tid=${row.tidN}｜有按钮的=${row.realToolbars}｜${JSON.stringify(row.boxes)}`);
    log(`      按钮：${JSON.stringify(row.labels)}｜class 独有（无 testid）：${JSON.stringify(row.classOnly)}`);
    await p.keyboard.press('Escape'); await p.waitForTimeout(600);
  }

  // ── 受控复测 ③：编辑态 ──
  out.editTest = { steps: [] };
  await setZoom(60);
  const s1 = await selectStrict(A);
  if (s1.ok) {
    let r = await read();
    out.editTest.steps.push({ at: '选中后', sel: await selN(), edit: r.edit, tid: r.tid.map((t) => ({ box: t.box, n: t.n, labels: t.labels })) });
    log('选中后：edit=', JSON.stringify(r.edit), '｜tid=', JSON.stringify(r.tid.map((t) => ({ box: t.box, n: t.n }))));
    // 双击
    await p.mouse.dblclick(s1.pt.x, s1.pt.y); await p.waitForTimeout(1500);
    r = await read();
    out.editTest.steps.push({ at: '双击后', sel: await selN(), edit: r.edit, tid: r.tid.map((t) => ({ box: t.box, n: t.n, labels: t.labels })),
      classN: r.classN, class: r.class.map((c) => ({ box: c.box, n: c.n, labels: c.labels })) });
    log('双击后：edit=', JSON.stringify(r.edit), '｜tid=', JSON.stringify(r.tid.map((t) => ({ box: t.box, n: t.n }))));
    log('        class 版=', JSON.stringify(r.class.map((c) => ({ box: c.box, n: c.n }))));
    log('        class 上的按钮=', JSON.stringify(r.class.map((c) => c.labels)));
    await p.keyboard.press('Escape'); await p.waitForTimeout(900);
    r = await read();
    out.editTest.steps.push({ at: 'Esc 后', edit: r.edit, tid: r.tid.map((t) => ({ box: t.box, n: t.n })) });
    log('Esc 后：edit=', JSON.stringify(r.edit), '｜tid=', JSON.stringify(r.tid.map((t) => ({ box: t.box, n: t.n }))));
  }
  out.verdict = {
    page185_reproduced: out.zoomGrids.some((g) => (g.boxes || []).some((x) => x.box && x.box.startsWith('185'))),
    canvasValues: out.zoomGrids.map((g) => ({ z: g.actualZoom, scale: g.scale, boxes: (g.boxes || []).filter((x) => x.n > 0).map((x) => x.box) })),
    classWiderThanTid: out.zoomGrids.some((g) => (g.classOnly || []).length > 0),
    editModeReached: (out.editTest.steps || []).some((s) => (s.edit?.contenteditable || 0) > 0),
  };
  log('\n判定：', JSON.stringify(out.verdict));
} catch (e) { out.error = String(e); log('🔴', String(e)); }
finally {
  log('── 收尾');
  await setZoom(60);
  for (const id of mine) { if (!(await ids()).includes(id)) continue;
    const s = await selectStrict(id); if (!s.ok) { log('  ⚠️ 选不中', id); continue; }
    await rightClick(s.pt.x, s.pt.y); await clickMenuItem('^删除');
    log('  删', id, '→', (await ids()).includes(id) ? '🔴 还在' : '✅'); }
  if (await selN() !== '0') { await p.keyboard.press('Escape'); await p.waitForTimeout(600); }
  await setZoom(60);
  const left = (await ids()).filter((x) => mine.includes(x));
  out.cleanup = { mine, leftover: left, nodes: (await ids()).length };
  log('清理', mine.length, '→ 剩', left.length, left.length ? '🔴 ' + left.join(' ') : '✅', '｜画布', out.cleanup.nodes);
  if (!left.length && mine.length) { try { const led = JSON.parse(readFileSync(LEDGER, 'utf8'));
    const add = mine.filter((x) => !led.ids.includes(x));
    if (add.length) { led.ids = [...new Set([...led.ids, ...add])].sort();
      led.per_batch = { ...(led.per_batch || {}), 93: [...new Set([...(led.per_batch?.['93'] || []), ...mine])] };
      led.updated_at = new Date().toISOString().slice(0, 10); writeFileSync(LEDGER, JSON.stringify(led, null, 1)); log('已登记台账'); } } catch (e) { log('台账失败', String(e)); } }
  out.end = { credits: await credits(), zoom: await zoomPct() };
  writeFileSync(new URL('./_tmp-b93b.json', import.meta.url), JSON.stringify(out, null, 1));
  await b.close();
}
