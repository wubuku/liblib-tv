// 批次 91 · E：手柄的**热区在伪元素上** —— 所以读手柄元素的 pe 永远是 `none`。
//
// d 轮拿到对照，却**推翻了 P4**：
//   音频 6 选中态：source `36×72 pe=none op=1`，⊕ **2** 个
//   导演台  选中态：source `14×28 pe=none op=none`→ 实为 `op=0`，⊕ **0** 个
//   ⇒ **`pointer-events` 两边都是 `none`，它不是判别式**。
//
// 🔑 而本页第 515 行早就写了：手柄 class 是一长串 Tailwind 工具类，
//    里面含 **`before:` / `after:`** ——「热区与字形」。
//    ⇒ 热区极可能挂在**伪元素**上；元素本体 `pe:none`，伪元素才 `auto`。
//    ⇒ 于是「读元素的 pe 判手柄能不能拖」**永远读到 none**，是判据选错了对象。
//
// ⇒ **P5**：对两类节点分别读 `getComputedStyle(el, '::before'/'::after')` 的
//   `pointer-events` / `content` / 几何；对比导演台与音频。
//   若伪元素上 pe 不同 ⇒ **这才是判「能不能从它发起连线」的正确读数**。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };
const edgeN = async () => p.evaluate(() => (document.body.innerText.match(/(\d+) edges?/) || [])[1]);
const selN = async () => p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]);
const credits = async () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-commerce-entry"]'); return e ? e.getAttribute('aria-label') : null; });
const zoomPct = async () => p.evaluate(() => { const e = document.querySelector('button[aria-label^="Zoom options"]'); return e ? Number((e.getAttribute('aria-label').match(/(\d+)%/) || [])[1]) : null; });
if (await selN() !== '0') { await p.keyboard.press('Escape'); await p.waitForTimeout(700); }

// 选中一个音频（对照组）与导演台（实验组）
const cands = await p.evaluate(() => {
  const out2 = [];
  for (const n of document.querySelectorAll('.react-flow__node')) { const r = n.getBoundingClientRect();
    if (!(r.left >= 0 && r.top >= 0 && r.right <= 1280 && r.bottom <= 720)) continue;
    const hits = [];
    for (let fx = 0.15; fx <= 0.85; fx += 0.1) for (let fy = 0.15; fy <= 0.85; fy += 0.1) {
      const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
      const el = document.elementFromPoint(x, y); if (el && el.closest('.react-flow__node') === n) hits.push({ x, y }); }
    if (!hits.length) continue;
    out2.push({ id: n.getAttribute('data-id'), aria: (n.getAttribute('aria-label') || '').slice(0, 22),
      type: (String(n.className || '').match(/react-flow__node-([a-z]+)/) || [])[1] || '?', pt: hits[Math.floor(hits.length / 2)] }); }
  return out2; });
const audio = cands.find((c) => c.type === 'audio');
log('可点候选：' + cands.map((c) => c.type).join(',') + (audio ? '' : '（无音频候选）'));

// 导演台：在 60% 下多半在视口外 ⇒ ⌘0 之后再点
await p.keyboard.press('Meta+0'); await p.waitForTimeout(1700);
const dirPt = await p.evaluate((id) => { const n = document.querySelector(`.react-flow__node[data-id="${id}"]`); if (!n) return null;
  const r = n.getBoundingClientRect(); const hits = [];
  for (let fx = 0.12; fx <= 0.88; fx += 0.08) for (let fy = 0.12; fy <= 0.88; fy += 0.08) {
    const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
    const el = document.elementFromPoint(x, y); if (el && el.closest('.react-flow__node') === n) hits.push({ x, y }); }
  return hits.length ? hits[Math.floor(hits.length / 2)] : null; }, 'node_pxvkay973v');

const readDeep = (id) => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return null;
  const r = { type: (String(n.className || '').match(/react-flow__node-([a-z]+)/) || [])[1] || '?',
    aria: (n.getAttribute('aria-label') || '').slice(0, 22), sel: String(n.className).includes(' selected'),
    plus: Array.from(n.querySelectorAll('[data-testid$="connection-menu-button"]')).map((e) => e.getAttribute('aria-label')), h: {} };
  for (const k of ['source', 'target']) {
    const e = n.querySelector(`[data-testid="flow-node-${k}-handle"]`); if (!e) { r.h[k] = null; continue; }
    const q = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    const pe = {};
    for (const ps of ['::before', '::after']) { const s = getComputedStyle(e, ps);
      pe[ps] = { content: s.content, pe: s.pointerEvents, pos: s.position, w: s.width, h: s.height,
        left: s.left, top: s.top, bg: s.backgroundColor, op: s.opacity, z: s.zIndex }; }
    r.h[k] = { box: `${Math.round(q.width)}×${Math.round(q.height)}@${Math.round(q.x)},${Math.round(q.y)}`,
      elPe: cs.pointerEvents, elOp: cs.opacity, cls: String(e.className || ''), pe, center: [Math.round(q.x + q.width / 2), Math.round(q.y + q.height / 2)] };
  }
  return r;
}, id);

out.rows = [];
if (dirPt) {
  await p.mouse.click(dirPt.x, dirPt.y); await p.waitForTimeout(1100);
  const ids = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
  if (ids[0] === 'node_pxvkay973v') { out.rows.push(await readDeep('node_pxvkay973v')); log('✔ 导演台已选中'); }
  else log('⚠️ 导演台点选未生效：' + JSON.stringify(ids));
  await p.keyboard.press('Escape'); await p.waitForTimeout(800);
}
if (audio) {
  await p.mouse.click(audio.pt.x, audio.pt.y); await p.waitForTimeout(1100);
  const ids = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
  if (ids[0] === audio.id) { out.rows.push(await readDeep(audio.id)); log('✔ 音频已选中 ' + audio.aria); }
  else log('⚠️ 音频点选未生效：' + JSON.stringify(ids));
}

for (const r of out.rows) {
  log(`\n══ ${r.type}（${r.aria}）selected=${r.sel}｜⊕ ${r.plus.length}`);
  for (const k of ['source', 'target']) { const h = r.h[k]; if (!h) { log(`   ${k}: （无）`); continue; }
    log(`   ${k}: el ${h.box} elPe=${h.elPe} elOp=${h.elOp}`);
    log(`        ::before pe=${h.pe['::before'].pe} content=${h.pe['::before'].content} w=${h.pe['::before'].w} h=${h.pe['::before'].h} pos=${h.pe['::before'].pos} left=${h.pe['::before'].left} top=${h.pe['::before'].top}`);
    log(`        ::after  pe=${h.pe['::after'].pe} content=${h.pe['::after'].content} w=${h.pe['::after'].w} h=${h.pe['::after'].h} pos=${h.pe['::after'].pos} left=${h.pe['::after'].left} top=${h.pe['::after'].top}`);
  }
  log(`   class：${(r.h.source ? r.h.source.cls : '').slice(0, 150)}`);
}
out.verdict = out.rows.map((r) => ({ type: r.type, plus: r.plus.length, elOp: r.h.source?.elOp,
  beforePe: r.h.source?.pe['::before'].pe, afterPe: r.h.source?.pe['::after'].pe }));
log('\n判定：' + JSON.stringify(out.verdict));

await p.keyboard.press('Escape'); await p.waitForTimeout(600);
for (let k = 0; k < 3 && await zoomPct() !== 60; k++) {
  await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(800);
  if (!await p.evaluate(() => !!document.querySelector('input[data-testid="canvas-zoom-percent-input"]'))) { await p.keyboard.press('Escape'); await p.waitForTimeout(500); continue; }
  await p.evaluate(() => { const i = document.querySelector('input[data-testid="canvas-zoom-percent-input"]');
    Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(i, '60');
    i.dispatchEvent(new Event('input', { bubbles: true })); i.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
    i.dispatchEvent(new Event('change', { bubbles: true })); i.blur(); });
  await p.waitForTimeout(1300); await p.keyboard.press('Escape'); await p.waitForTimeout(600);
}
const z1 = await zoomPct(); await p.waitForTimeout(900); const z2 = await zoomPct();
out.end = { edges: await edgeN(), sel: await selN(), zoom: z2, credits: await credits() };
log('终态：' + JSON.stringify(out.end) + `｜缩放归位 ${z2 === 60 ? '✅' : '🔴'}`);
writeFileSync(new URL('./_tmp-b91e.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
