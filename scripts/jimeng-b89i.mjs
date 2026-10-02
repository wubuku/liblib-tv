// 批次 89 · I：P1f 的第三次尝试 —— 先证明落点属于谁，再点。
//
// 🔴 **g/h 两轮都栽在同一处**（本页 792 那条「重叠的节点上，『矩形中心』不是
//     『点这个节点』」的现场复现）：
//     h 轮逐字读出被选中的是 **`node_gp499g9p3m`（音频 5）**，而我点的是导演台的矩形中心。
//     ⇒ g 轮那个「11×11 三态相同」**根本没测到选中态**（读到的是又一个静息态），
//     所以 P1f 至今**未定**，不能写成「两态相同」。
//
// ⇒ 本轮的修法：**点之前先用 `document.elementFromPoint` 证明落点最上层是谁**。
//     网格扫描导演台矩形，找一个「最上层节点 === 导演台」的点；
//     找不到就**记 VOID 并如实说明为什么找不到**，不硬点。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };
const selCount = async () => p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]);
const zoomPct = async () => p.evaluate(() => { const e = document.querySelector('button[aria-label^="Zoom options"]'); return e ? Number((e.getAttribute('aria-label').match(/(\d+)%/) || [])[1]) : null; });
const selIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
const readTag = (id) => p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { found: false };
  const t = n.querySelector('[data-testid="flow-node-selected-tag"]'); if (!t) return { found: false, why: '无 tag' };
  const r = t.getBoundingClientRect();
  return { found: true, tag: `${Math.round(r.width)}×${Math.round(r.height)}`,
    counter: getComputedStyle(t).getPropertyValue('--octo-canvas-node-chrome-counter-scale').trim() }; }, id);
const ID = 'node_pxvkay973v';

await p.keyboard.press('Meta+0'); await p.waitForTimeout(1700);
out.zoomAtFit = await zoomPct();

// 网格扫描：找一个「elementFromPoint 最上层就是导演台」的点
out.scan = await p.evaluate((id) => {
  const n = document.querySelector(`.react-flow__node[data-id="${id}"]`); if (!n) return { ok: false, why: '节点不在 DOM' };
  const r = n.getBoundingClientRect();
  const hits = []; let covered = 0, total = 0;
  for (let fx = 0.12; fx <= 0.88; fx += 0.08) for (let fy = 0.12; fy <= 0.88; fy += 0.08) {
    const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
    const el = document.elementFromPoint(x, y); if (!el) continue;
    const top = el.closest('.react-flow__node');
    const who = top ? top.getAttribute('data-id') : '(非节点:' + el.tagName + ')';
    total++;
    if (who === id) hits.push({ x, y }); else covered++;
  }
  return { ok: hits.length > 0, hits, covered, total, rect: `${Math.round(r.width)}×${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}` };
}, ID);
log('落点扫描：', JSON.stringify(out.scan).slice(0, 400));

if (!out.scan.ok) {
  out.verdict = { VOID: `导演台矩形内 ${out.scan.total} 个采样点全部被别的节点/元素盖住（covered=${out.scan.covered}），本轮不测「选中态」` };
  log('🔴 VOID：', JSON.stringify(out.verdict));
} else {
  const pt = out.scan.hits[Math.floor(out.scan.hits.length / 2)];
  out.pt = pt;
  out.rest = { sel: await selCount(), ...(await readTag(ID)) };
  log('① 静息：', JSON.stringify(out.rest), '落点', JSON.stringify(pt));

  await p.mouse.click(pt.x, pt.y);
  await p.waitForTimeout(1300);
  const got = await selIds();
  out.selectedIds = got;
  log('② 点后被选中的节点：', JSON.stringify(got));
  if (!got.includes(ID)) {
    out.verdict = { VOID: `elementFromPoint 说落点属于导演台，实际选中 ${JSON.stringify(got)} —— 判据与结果不符，本轮不出结论` };
    log('🔴 VOID：', JSON.stringify(out.verdict));
  } else {
    out.selected = { sel: await selCount(), ...(await readTag(ID)) };
    log('③ 选中：', JSON.stringify(out.selected));
    await p.keyboard.press('Escape'); await p.waitForTimeout(1200);
    const back = await selIds();
    out.back = { sel: await selCount(), ids: back, ...(await readTag(ID)) };
    log('④ 取消：', JSON.stringify(out.back));
    out.verdict = { rest: out.rest.tag, selected: out.selected.tag, back: out.back.tag,
      counterRest: out.rest.counter, counterSel: out.selected.counter,
      twoState: out.rest.tag !== out.selected.tag, restored: out.back.tag === out.rest.tag };
    log('P1f 判定：', JSON.stringify(out.verdict));
  }
}

for (let k = 1; k <= 3 && await zoomPct() !== 60; k++) {
  await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(800);
  if (!await p.evaluate(() => !!document.querySelector('input[data-testid="canvas-zoom-percent-input"]'))) { await p.keyboard.press('Escape'); await p.waitForTimeout(500); continue; }
  await p.evaluate(() => { const i = document.querySelector('input[data-testid="canvas-zoom-percent-input"]');
    Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(i, '60');
    i.dispatchEvent(new Event('input', { bubbles: true })); i.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
    i.dispatchEvent(new Event('change', { bubbles: true })); i.blur(); });
  await p.waitForTimeout(1300); await p.keyboard.press('Escape'); await p.waitForTimeout(600);
}
const z1 = await zoomPct(); await p.waitForTimeout(900); const z2 = await zoomPct();
out.end = { zoom: z2, zoomStable: z1 === z2, sel: await selCount() };
log('终态：', JSON.stringify(out.end), '｜缩放归位', z2 === 60 ? '✅' : '🔴');
writeFileSync(new URL('./_tmp-b89i.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
