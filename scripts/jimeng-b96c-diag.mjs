// 批次 96 · c 轮诊断：**选择工具下单击节点居然没选中**（格 ② 失败），
// 基线丢了必须先查清楚 —— 不查就往下走，整轮结论都会建在流沙上。
//
// 已知事实：适配画布后（23%，`scale 0.234098`），`pointAt` 给的落点 `{x:274, y:160}`
// **通过了 `elementFromPoint` 归属校验**（最顶层元素的 `.closest('.react-flow__node')`
// 就是目标节点），但 `p.mouse.click` 之后 `selected` 恒 0。
//
// 「归属校验通过」与「点得中」不是一回事。可能的方向（逐条查，不猜）：
//   D1 落点上最顶层的元素是该节点里的某个**不可交互层**（`pointer-events:none` 的装饰）
//   D2 该节点**被别的节点盖住**，只是盖住的那部分恰好属于本节点的 rect
//   D3 节点 rect 与实际可点区域**不一致**（例如节点内容高度小于容器）
//   D4 适配动画未停，读到的 rect 是动画中途的
//   D5 该节点在当前工具下本就不可选（例如它其实是别的类型）
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };
const TID = 'node_3bfb9r79qe';

const zoomLabel = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]');
  return e ? e.getAttribute('aria-label') : null; });
const scaleNow = () => p.evaluate(() => { const e = document.querySelector('.react-flow__viewport');
  const m = e && /scale\(([\d.]+)\)/.exec(e.style.transform || ''); return m ? Number(m[1]) : null; });

await p.keyboard.press('Meta+0');
await p.waitForTimeout(2200);
out.fit = { zoom: await zoomLabel(), scale: await scaleNow() };
log('适配后：', JSON.stringify(out.fit));

// D4：读两次 rect，看是否静止
out.rectTwice = [];
for (let k = 0; k < 3; k++) {
  const r = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    if (!n) return null; const b = n.getBoundingClientRect();
    return { x: Math.round(b.x), y: Math.round(b.y), w: Math.round(b.width), h: Math.round(b.height),
      t: document.querySelector('.react-flow__viewport').style.transform }; }, TID);
  out.rectTwice.push(r); await p.waitForTimeout(600);
}
log('rect 连读三次：', JSON.stringify(out.rectTwice), '｜静止 =',
  JSON.stringify(out.rectTwice[0]) === JSON.stringify(out.rectTwice[2]));

// D1/D2/D3：落点上最顶层的元素到底是什么
out.stack = await p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  const r = n.getBoundingClientRect();
  const rows = [];
  for (const f of [0.5, 0.3, 0.7, 0.2, 0.8, 0.1, 0.9]) {
    const x = Math.round(r.x + r.width * f), y = Math.round(r.y + r.height * f);
    if (x < 2 || y < 2 || x > 1278 || y > 718) { rows.push({ f, x, y, note: '越界' }); continue; }
    const e = document.elementFromPoint(x, y);
    const owner = e ? e.closest('.react-flow__node') : null;
    const chain = [];
    let c = e;
    while (c && chain.length < 6) { chain.push(c.tagName + (c.getAttribute('class') ? '.' + String(c.getAttribute('class')).split(' ')[0] : '')); c = c.parentElement; }
    rows.push({ f, x, y,
      topTag: e ? e.tagName : null, topClass: e ? String(e.getAttribute('class') || '').slice(0, 50) : null,
      topPE: e ? getComputedStyle(e).pointerEvents : null,
      ownerId: owner ? owner.getAttribute('data-id') : null,
      isSelf: owner ? owner.getAttribute('data-id') === i : false,
      chain });
  }
  return { rect: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) },
    classes: n.className, transform: n.style.transform, rows };
}, TID);
log('落点栈：');
out.stack.rows.forEach((r) => log(`   f=${r.f} @${r.x},${r.y} top=${r.topTag}.${(r.topClass || '').slice(0, 24)} pe=${r.topPE} owner=${r.ownerId} SELF=${r.isSelf}`));

// D5：类型 + 是不是基线节点
out.nodeInfo = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  return { aria: n.getAttribute('aria-label'), cls: n.className, text: n.innerText.replace(/\s+/g, ' ').trim().slice(0, 40),
    pe: getComputedStyle(n).pointerEvents, vis: getComputedStyle(n).visibility, op: getComputedStyle(n).opacity }; }, TID);
log('节点：', JSON.stringify(out.nodeInfo));

// 实点一次，并把 elementFromPoint 在点击前后都记下来
const selfRow = out.stack.rows.find((r) => r.isSelf) || out.stack.rows[0];
out.clickAt = { x: selfRow.x, y: selfRow.y };
log('实点：', JSON.stringify(out.clickAt));
await p.mouse.move(out.clickAt.x, out.clickAt.y); await p.waitForTimeout(300);
out.beforeClickTop = await p.evaluate((c) => { const e = document.elementFromPoint(c.x, c.y);
  return e ? { tag: e.tagName, cls: String(e.getAttribute('class') || '').slice(0, 60), text: (e.innerText || '').slice(0, 20) } : null; }, out.clickAt);
await p.mouse.click(out.clickAt.x, out.clickAt.y);
await p.waitForTimeout(1400);
out.afterClick = await p.evaluate((c) => {
  const e = document.elementFromPoint(c.x, c.y);
  const o = e && e.closest('.react-flow__node');
  return { sel: document.body.innerText.match(/(\d+) selected/)?.[1] ?? '0',
    selectedIds: Array.from(document.querySelectorAll('.react-flow__node.selected')).map((x) => x.getAttribute('data-id')),
    topNow: e ? { tag: e.tagName, cls: String(e.getAttribute('class') || '').slice(0, 60) } : null,
    ownerNow: o ? o.getAttribute('data-id') : null,
    pointer: (() => { const t = document.querySelector('[data-testid="canvas-pointer-tool-toggle"]');
      return { aria: t ? t.getAttribute('aria-label') : null, pressed: t ? t.getAttribute('aria-pressed') : null }; })() };
}, out.clickAt);
log('点前顶层：', JSON.stringify(out.beforeClickTop));
log('点后：', JSON.stringify(out.afterClick));

// 换一个节点试试：如果别的节点能选中，说明是这个节点的问题；如果都不能，问题在工具态或全局
out.tryOther = await p.evaluate(() => {
  const cands = Array.from(document.querySelectorAll('.react-flow__node')).filter((n) => {
    const r = n.getBoundingClientRect();
    return r.width > 12 && r.right > 4 && r.bottom > 4 && r.left < 1276 && r.top < 716
      && document.elementFromPoint(Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2))?.closest('.react-flow__node') === n; });
  return cands.slice(0, 6).map((n) => { const r = n.getBoundingClientRect();
    return { id: n.getAttribute('data-id'), aria: n.getAttribute('aria-label'),
      x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
});
log('可点的候选节点：', JSON.stringify(out.tryOther));
if (out.tryOther[0]) {
  await p.mouse.click(out.tryOther[0].x, out.tryOther[0].y);
  await p.waitForTimeout(1300);
  out.otherResult = await p.evaluate(() => ({
    sel: document.body.innerText.match(/(\d+) selected/)?.[1] ?? '0',
    selectedIds: Array.from(document.querySelectorAll('.react-flow__node.selected')).map((x) => x.getAttribute('data-id')),
    pointer: (() => { const t = document.querySelector('[data-testid="canvas-pointer-tool-toggle"]');
      return { aria: t ? t.getAttribute('aria-label') : null, pressed: t ? t.getAttribute('aria-pressed') : null }; })() }));
  log('点候选节点结果：', JSON.stringify(out.otherResult));
}

writeFileSync(new URL('./_tmp-b96c-diag.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
