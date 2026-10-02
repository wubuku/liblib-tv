// 批次 93 · C：两件 b 轮没答成的事。
//
// ⚠️ **b 轮自伤（循环设计 bug）**：
//     `selectStrict` 的候选缩放列表第一项是 `[await zoomPct()]` —— **就是当前缩放**，
//     于是它第一轮就成功返回，**后面的 100% / 40% 根本没试**。
//     日志里「想要 100%｜实到 60%」就是它露出来的。
//     ⇒ **候选列表的第一项不能是「什么都不做」**，否则后面全是死代码。
//     本轮改成：先明确 setZoom 到目标档，再在同一档内重扫落点。
//
// 🔑 **问题 1（ID 双轨的真实形状）**：
//     a 轮 class 命中 **3**、testid 命中 **2**；b 轮又显示「三个 class 元素**都带** data-testid」——
//     两轮读数不可能同时成立，除非**那第三个元素带的是别的 data-testid 值**。
//     ⇒ 把三个元素的 `data-testid` 逐字打出来，一次说清。
//
// 🔑 **问题 2（工具条随缩放怎么变）**：a 轮 60% 是 `192×40`、100%/40% 是 `0×0`。
//     `0×0` 到底是「工具条真的没有内容」还是「节点不在视口内被折叠」——
//     本轮**每档都断言 `sel === 1` 且节点完全在视口内**再读。
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
const scaleNow = async () => { const rd = () => p.evaluate(() => { const vp = document.querySelector('.react-flow__viewport');
    const m = (vp ? (vp.style.transform || '') : '').match(/scale\(([-\d.]+)\)/); return m ? Number(m[1]) : null; });
  const a = await rd(); await p.waitForTimeout(500); const c = await rd(); return a !== null && a === c ? a : null; };
const setZoom = async (t0) => { for (let t = 1; t <= 3; t++) { if (await zoomPct() === t0) return true;
  await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(800);
  const has = await p.evaluate(() => !!document.querySelector('input[data-testid="canvas-zoom-percent-input"]'));
  if (!has) { await p.keyboard.press('Escape'); await p.waitForTimeout(500); continue; }
  await p.evaluate((v) => { const i = document.querySelector('input[data-testid="canvas-zoom-percent-input"]');
    Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(i, String(v));
    i.dispatchEvent(new Event('input', { bubbles: true })); i.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
    i.dispatchEvent(new Event('change', { bubbles: true })); i.blur(); }, t0);
  await p.waitForTimeout(1500); await p.keyboard.press('Escape'); await p.waitForTimeout(800);
  const a = await zoomPct(); await p.waitForTimeout(900); const c = await zoomPct();
  if (a === t0 && a === c) return true; }
  return false; };

/** 在**当前缩放**下找一个属于 id 的落点，并把前置一起返回 */
const probe = (id) => p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return { gone: true };
  const r = n.getBoundingClientRect();
  const inVp = r.left >= 0 && r.top >= 0 && r.right <= 1280 && r.bottom <= 720;
  let pt = null;
  for (let fx = 0.03; fx <= 0.97 && !pt; fx += 0.03) for (let fy = 0.03; fy <= 0.97 && !pt; fy += 0.03) {
    const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
    if (x < 0 || y < 0 || x > 1280 || y > 720) continue;
    const el = document.elementFromPoint(x, y);
    if (el && el.closest('.react-flow__node') === n) pt = { x, y }; }
  return { pt, inVp, box: `${Math.round(r.width)}×${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}` }; }, id);

/** 逐字打出 class 命中与 testid 命中的关系 */
const idShapes = () => p.evaluate(() => {
  const cls = Array.from(document.querySelectorAll('.react-flow__node-toolbar'));
  const tid = Array.from(document.querySelectorAll('[data-testid="node-toolbar"]'));
  const d = (e) => { const r = e.getBoundingClientRect();
    return { tid: e.getAttribute('data-testid'), box: `${Math.round(r.width)}×${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
      n: e.querySelectorAll('button,[role="button"]').length,
      inNode: !!e.closest('.react-flow__node'),
      nodeId: e.closest('.react-flow__node') ? e.closest('.react-flow__node').getAttribute('data-id') : null }; };
  return { class: cls.map(d), tid: tid.map(d),
    classWithTid: cls.filter((e) => e.getAttribute('data-testid') === 'node-toolbar').length,
    classWithOtherTid: cls.filter((e) => { const t = e.getAttribute('data-testid'); return t && t !== 'node-toolbar'; }).map(d),
    classWithoutTid: cls.filter((e) => !e.getAttribute('data-testid')).length };
});

const rightClick = async (x, y) => { await p.mouse.move(x, y); await p.waitForTimeout(150);
  await p.mouse.down({ button: 'right' }); await p.waitForTimeout(220); await p.mouse.up({ button: 'right' }); await p.waitForTimeout(1100); };
const clickMenuItem = async (src) => { const ok = await p.evaluate((s) => { const m = document.querySelector('[data-testid="canvas-context-menu"]'); if (!m) return false;
  const it = Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => new RegExp(s).test(x.innerText.replace(/\s+/g, ' ').trim())); if (it) { it.click(); return true; } return false; }, src);
  await p.waitForTimeout(1600); return ok; };

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
  mine.push(A); await p.keyboard.press('Escape'); await p.waitForTimeout(900);
  log('自建：', A);

  // ── 问题 1：ID 形状（先在 60% 选中态下读） ──
  out.shapes = [];
  for (const z of [60, 100, 40]) {
    if (!await setZoom(z)) { log(`拨不到 ${z}%`); continue; }
    // 在这一档内找落点并选中
    let sel = null;
    for (let k = 0; k < 3 && !sel; k++) { const pr = await probe(A);
      if (pr.pt) { await p.mouse.click(pr.pt.x, pr.pt.y); await p.waitForTimeout(1100);
        const s = await selN(); const who = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
        if (s === '1' && who[0] === A) sel = { pt: pr.pt, inVp: pr.inVp }; else { await p.keyboard.press('Escape'); await p.waitForTimeout(500); } } }
    if (!sel) { out.shapes.push({ asked: z, actual: await zoomPct(), fail: 'select' }); log(`@${z}% 选不中`); continue; }
    const sh = await idShapes(); const sc = await scaleNow();
    const real = sh.class.filter((c) => c.n > 0);
    out.shapes.push({ asked: z, actual: await zoomPct(), scale: sc, inViewport: sel.inVp,
      classN: sh.class.length, tidN: sh.tid.length, classWithTid: sh.classWithTid,
      classWithOtherTid: sh.classWithOtherTid, classWithoutTid: sh.classWithoutTid,
      class: sh.class, realBoxes: real.map((c) => ({ box: c.box, n: c.n, tid: c.tid, nodeId: c.nodeId })) });
    log(`  想要 ${z}%｜实到 ${await zoomPct()}% scale=${sc}｜视口内=${sel.inVp}`);
    log(`     class=${sh.class.length}（其中 data-testid=node-toolbar 的 ${sh.classWithTid} 个｜别的 testid ${sh.classWithOtherTid.length} 个｜无 testid ${sh.classWithoutTid} 个）｜tid=${sh.tid.length}`);
    for (const c of sh.class) log(`       class 元素：tid=${JSON.stringify(c.tid)} ${c.box} 按钮${c.n} 在节点${c.nodeId ? '内' : '外'}`);
    log(`     有按钮的：${JSON.stringify(real.map((c) => c.box))}`);
    await p.keyboard.press('Escape'); await p.waitForTimeout(700);
  }
  out.verdict = {
    page185: out.shapes.some((s) => (s.realBoxes || []).some((c) => c.box.startsWith('185'))),
    page192: out.shapes.some((s) => (s.realBoxes || []).some((c) => c.box.startsWith('192'))),
    boxesByZoom: out.shapes.map((s) => ({ z: s.actual, scale: s.scale, boxes: (s.realBoxes || []).map((c) => c.box) })),
    classN: out.shapes.map((s) => s.classN), tidN: out.shapes.map((s) => s.tidN),
  };
  log('\n判定：', JSON.stringify(out.verdict));
} catch (e) { out.error = String(e); log('🔴', String(e)); }
finally {
  log('── 收尾');
  await setZoom(60);
  for (const id of mine) { if (!(await ids()).includes(id)) continue;
    let gone = false;
    for (let k = 0; k < 3 && !gone; k++) { const pr = await probe(id); if (pr.pt) {
      await p.mouse.click(pr.pt.x, pr.pt.y); await p.waitForTimeout(1000);
      const s = await selN(); const who = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
      if (s === '1' && who[0] === id) { await rightClick(pr.pt.x, pr.pt.y); await clickMenuItem('^删除'); gone = !(await ids()).includes(id); }
      else await p.keyboard.press('Escape'); } }
    log('  删', id, '→', gone ? '✅' : '🔴 还在'); }
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
  writeFileSync(new URL('./_tmp-b93c.json', import.meta.url), JSON.stringify(out, null, 1));
  await b.close();
}
