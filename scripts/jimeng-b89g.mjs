// 批次 89 · G：重做 P1f —— 上一轮因为**落点不在视口内**而整轮作废。
//
// 🔴 **f 轮自伤**：`inViewport: false`，`sel` 三次都是 0 ⇒ 鼠标点击落在画布外，
//     节点**从未被选中**。而脚本照样输出了
//     `verdict: "选中态与静息态相同"` ——
//     **一次没发生的实验，被打印成了一条「两态相同」的结论。**
//     这与批次 88「静息态没静息」是同一条纪律的第三次复发，
//     而本页（批次 65、1276）早就写着「越整齐的读数越要怀疑」。
//     ⇒ 修法（本脚本已内建）：**每个读数都断言 `sel`**，不符就记 VOID 而不是结论。
//
// ⚠️ 60% 缩放下**那六个基线节点全都落在视口外**（视口正对着别人那批音频节点），
//     所以必须先 ⌘0 适配才能点到导演台；收尾要**回读确认**缩放已归位 60%。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };
const selCount = async () => p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]);
const credits = async () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-commerce-entry"]'); return e ? e.getAttribute('aria-label') : null; });
const zoomPct = async () => p.evaluate(() => { const e = document.querySelector('button[aria-label^="Zoom options"]'); return e ? Number((e.getAttribute('aria-label').match(/(\d+)%/) || [])[1]) : null; });
const readScale = async () => { const rd = () => p.evaluate(() => { const vp = document.querySelector('.react-flow__viewport');
    const m = (vp ? (vp.style.transform || '') : '').match(/scale\(([-\d.]+)\)/); return m ? Number(m[1]) : null; });
  const a = await rd(); await p.waitForTimeout(500); const c = await rd(); return { scale: a, stable: a !== null && a === c }; };

const readTag = async (id) => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { found: false, why: '节点不在 DOM' };
  const t = n.querySelector('[data-testid="flow-node-selected-tag"]');
  if (!t) return { found: false, why: '节点内无该 testid' };
  const r = t.getBoundingClientRect(); const nr = n.getBoundingClientRect();
  return { found: true, tag: `${Math.round(r.width)}×${Math.round(r.height)}`,
    counter: getComputedStyle(t).getPropertyValue('--octo-canvas-node-chrome-counter-scale').trim(),
    nodeSelected: String(n.className).includes(' selected'), nodeBox: `${Math.round(nr.width)}×${Math.round(nr.height)}`,
    inViewport: nr.right > 0 && nr.bottom > 0 && nr.left < 1280 && nr.top < 720 };
}, id);

const ID = 'node_pxvkay973v';  // 别人的导演台，只读不动
out.start = { sel: await selCount(), zoom: await zoomPct(), credits: await credits() };
log('起点：', JSON.stringify(out.start));

// ⌘0 适配到全体节点
await p.keyboard.press('Meta+0');
await p.waitForTimeout(1600);
const sc = await readScale();
out.fitView = { ...sc, zoom: await zoomPct() };
log('⌘0 后：', JSON.stringify(out.fitView));

const box = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return null;
  const r = n.getBoundingClientRect();
  return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2),
    rect: `${Math.round(r.width)}×${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
    inViewport: r.right > 0 && r.bottom > 0 && r.left < 1280 && r.top < 720 }; }, ID);
out.box = box;
log('导演台落点：', JSON.stringify(box));

if (!box || !box.inViewport) { out.verdict = { VOID: '⌘0 之后导演台仍不在视口内，本轮不测' }; log('🔴 VOID：', JSON.stringify(out.verdict)); }
else {
  out.rest = { sel: await selCount(), ...(await readTag(ID)) };
  log('① 静息：', JSON.stringify(out.rest));

  await p.mouse.click(box.x, box.y);
  await p.waitForTimeout(1200);
  const s1 = await selCount();
  out.selState = { sel: s1 };
  if (s1 !== '1') { out.verdict = { VOID: `点击后 sel=${s1}，未选中 ⇒ 实验未发生，不出结论` }; log('🔴 VOID：', JSON.stringify(out.verdict)); }
  else {
    out.selected = { sel: s1, ...(await readTag(ID)) };
    log('② 选中：', JSON.stringify(out.selected));
    await p.keyboard.press('Escape');
    await p.waitForTimeout(1200);
    const s2 = await selCount();
    out.back = { sel: s2, ...(await readTag(ID)) };
    log('③ 取消选中：', JSON.stringify(out.back));
    if (s2 !== '0') log('   ⚠️ Escape 后 sel =', s2, '（未归零，第三次读数不作结论）');
    out.verdict = { rest: out.rest.tag, selected: out.selected.tag, back: out.back.tag,
      twoState: out.rest.tag !== out.selected.tag, restored: out.back.tag === out.rest.tag };
    log('P1f 判定：', JSON.stringify(out.verdict));
  }
}

// 收尾：缩放归位 60%，并回读确认
for (let k = 1; k <= 3; k++) {
  if (await zoomPct() === 60) break;
  await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(800);
  const has = await p.evaluate(() => !!document.querySelector('input[data-testid="canvas-zoom-percent-input"]'));
  if (!has) { await p.keyboard.press('Escape'); await p.waitForTimeout(500); continue; }
  await p.evaluate(() => { const i = document.querySelector('input[data-testid="canvas-zoom-percent-input"]');
    Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(i, '60');
    i.dispatchEvent(new Event('input', { bubbles: true })); i.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
    i.dispatchEvent(new Event('change', { bubbles: true })); i.blur(); });
  await p.waitForTimeout(1300); await p.keyboard.press('Escape'); await p.waitForTimeout(600);
}
const z1 = await zoomPct(); await p.waitForTimeout(900); const z2 = await zoomPct();
out.end = { sel: await selCount(), zoom: z2, zoomStable: z1 === z2, credits: await credits() };
log('终态：', JSON.stringify(out.end), '｜缩放归位 =', z2 === 60 ? '✅' : '🔴', '｜积分未变 =', out.start.credits === out.end.credits);
writeFileSync(new URL('./_tmp-b89g.json', import.meta.url), JSON.stringify(out, null, 1));
log('已写 _tmp-b89g.json');
await b.close();
