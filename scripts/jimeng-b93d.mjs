// 批次 93 · D：把工具条的**按钮**逐档量出来 —— 宽度到底由什么决定。
//
// c 轮已把三档的**前置全部断言过**（`sel === 1` 且节点完全在视口内）：
//   40% → `160×40`   60% → `192×40`   100% → `320×40`
//
// 🔴 **由此看出批次 85 的一条既有结论有问题**：
//     批次 85 写「文本浮动工具条 canvas 恒 `320×67`」，
//     那是用 **192÷0.6 = 320**、**40÷0.6 = 67** 算出来的。
//     但三档的**屏上高度恒为 40** ⇒ 高度根本没有 canvas 恒值，
//     那个 `67` 是**把屏上恒值除以 scale** 得来的。
//     宽度则三档各不相同（160 / 192 / 320），除以 scale 得 400 / 320 / 320 —— 也不恒。
//
// ⇒ **P**：逐档读三个按钮各自的屏上尺寸与 aria。
//   若图标按钮（全屏/下载）**屏上恒 32×32**、而带文字的「背景色」随缩放变，
//   那么宽度的构成就清楚了，而且**契约要按「哪一部分」分开写**，
//   不能给整条工具条一个数字。
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
  if (a === t0 && a === c) return true; } return false; };
const probe = (id) => p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return { gone: true };
  const r = n.getBoundingClientRect();
  const inVp = r.left >= 0 && r.top >= 0 && r.right <= 1280 && r.bottom <= 720;
  let pt = null;
  for (let fx = 0.03; fx <= 0.97 && !pt; fx += 0.03) for (let fy = 0.03; fy <= 0.97 && !pt; fy += 0.03) {
    const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
    if (x < 0 || y < 0 || x > 1280 || y > 720) continue;
    const el = document.elementFromPoint(x, y);
    if (el && el.closest('.react-flow__node') === n) pt = { x, y }; }
  return { pt, inVp }; }, id);
const selectStrict = async (id) => { for (let k = 0; k < 3; k++) { const pr = await probe(id);
  if (pr.pt) { await p.mouse.click(pr.pt.x, pr.pt.y); await p.waitForTimeout(1100);
    const s = await selN(); const who = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
    if (s === '1' && who[0] === id) return { ok: true, inVp: pr.inVp };
    await p.keyboard.press('Escape'); await p.waitForTimeout(500); } }
  return { ok: false }; };
/** 真身 = 有按钮的那个 node-toolbar */
const readReal = () => p.evaluate(() => {
  const all = Array.from(document.querySelectorAll('[data-testid="node-toolbar"]'));
  const real = all.find((e) => e.querySelectorAll('button,[role="button"]').length > 0);
  if (!real) return { found: false, allBoxes: all.map((e) => { const r = e.getBoundingClientRect(); return `${Math.round(r.width)}×${Math.round(r.height)}`; }) };
  const r = real.getBoundingClientRect(); const cs = getComputedStyle(real);
  const kids = Array.from(real.children).map((c) => { const q = c.getBoundingClientRect();
    return { tag: c.tagName, aria: c.getAttribute('aria-label'), box: `${Math.round(q.width)}×${Math.round(q.height)}`, x: Math.round(q.x) }; });
  const btns = Array.from(real.querySelectorAll('button,[role="button"]')).map((x) => { const q = x.getBoundingClientRect();
    return { aria: x.getAttribute('aria-label'), text: (x.innerText || '').trim(), box: `${Math.round(q.width)}×${Math.round(q.height)}`, x: Math.round(q.x) }; });
  return { found: true, box: `${Math.round(r.width)}×${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
    pad: cs.padding, gap: cs.gap, display: cs.display, kids, btns };
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

  out.grids = [];
  for (const z of [40, 60, 100]) {
    if (!await setZoom(z)) { log(`拨不到 ${z}%`); continue; }
    const s = await selectStrict(A);
    if (!s.ok) { out.grids.push({ asked: z, actual: await zoomPct(), fail: 'select' }); log(`@${z}% 选不中`); continue; }
    const r = await readReal(); const sc = await scaleNow();
    const row = { asked: z, actual: await zoomPct(), scale: sc, sel: await selN(), inVp: s.inVp, ...r };
    out.grids.push(row);
    log(`\n  @${z}%（实到 ${row.actual}%，scale=${sc}，sel=${row.sel}，视口内=${s.inVp}）`);
    log(`    工具条 ${row.box}｜padding=${row.pad} gap=${row.gap} display=${row.display}`);
    log(`    按钮：${JSON.stringify(row.btns)}`);
    log(`    子元素：${JSON.stringify(row.kids)}`);
    if (sc && row.btns) for (const b2 of row.btns) { const m = b2.box.match(/([\d.]+)×([\d.]+)/);
      if (m) log(`       ${b2.aria} 屏上 ${b2.box} → canvas ${Math.round(Number(m[1]) / sc)}×${Math.round(Number(m[2]) / sc)}`); }
    await p.keyboard.press('Escape'); await p.waitForTimeout(700);
  }
  out.verdict = {
    heightScreenConstant: new Set(out.grids.map((g) => g.box && g.box.split('×')[1])).size === 1,
    heights: out.grids.map((g) => g.box),
    iconButtons: out.grids.map((g) => ({ z: g.actual, 全屏: g.btns?.find((x) => x.aria === '全屏')?.box, 下载: g.btns?.find((x) => x.aria === '下载')?.box, 背景色: g.btns?.find((x) => x.aria === '背景色')?.box })),
  };
  log('\n判定：', JSON.stringify(out.verdict));
} catch (e) { out.error = String(e); log('🔴', String(e)); }
finally {
  log('── 收尾');
  await setZoom(60);
  for (const id of mine) { if (!(await ids()).includes(id)) continue;
    const s = await selectStrict(id); if (!s.ok) { log('  ⚠️ 选不中', id); continue; }
    const pr = await probe(id); await rightClick(pr.pt.x, pr.pt.y); await clickMenuItem('^删除');
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
  writeFileSync(new URL('./_tmp-b93d.json', import.meta.url), JSON.stringify(out, null, 1));
  await b.close();
}
