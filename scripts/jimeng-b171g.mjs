// 批次 171 g 轮：修 f 轮（f 轮把平移循环套在所有档位上，连 1280 都失败了 —— 自伤）。
//
// 本轮改用**确定性做法**：直接改 `.react-flow__viewport` 的 transform，
// 把选中的节点算到「左栏右侧的确定位置」，再点 Add tags。
// 📌 改 transform 只动**视图态**，不碰任何节点数据；收尾按「适配画布」复原。
//
// 也顺手记一个诊断：在窄视口下 Add tags 到底**在不在屏上、被谁挡着** ——
// 「打不开」要区分「按钮不在屏上」与「按钮在但被盖住」，否则又是一次「没测到写成另一种行为」。
import fs from 'node:fs';
import { openCanvas, readers } from './jimeng-b135-lib.mjs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const { b, p: shared } = await openCanvas();
const p = shared;
const R = readers(p);
const rec = { 批次: '171g' };

const pin = async (page, w, h) => {
  await page.context().newCDPSession(page).then(async (s) => {
    await s.send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: 2, mobile: false });
  });
  await page.waitForTimeout(900);
  const vp = await page.evaluate(() => [innerWidth, innerHeight]);
  if (vp[0] !== w || vp[1] !== h) throw new Error(`钉视口失败 ${JSON.stringify(vp)}`);
};

/** 选一个节点（点标题，b 轮实测只有标题能选中），返回它的 data-id。 */
const 选节点 = async (page) => {
  const cands = await page.evaluate(() => {
    const out = [];
    for (const t of document.querySelectorAll('.react-flow__node [data-testid="flow-node-title"]')) {
      const r = t.getBoundingClientRect();
      const cx = r.x + r.width / 2, cy = r.y + r.height / 2;
      if (cx < 4 || cy < 4 || cx > innerWidth - 4 || cy > innerHeight - 4) continue;
      const hit = document.elementFromPoint(cx, cy);
      if (hit && hit.closest('.react-flow__node')
          && !hit.closest('[data-testid="flow-node-target-handle"],[data-testid="flow-node-source-handle"]')) {
        out.push([Math.round(cx), Math.round(cy)]);
      }
    }
    return out;
  });
  if (!cands.length) return null;
  await page.mouse.click(cands[0][0], cands[0][1]);
  await page.waitForTimeout(800);
  return page.evaluate(() => {
    const s = document.querySelector('.react-flow__node.selected');
    return s ? s.getAttribute('data-id') : null;
  });
};

/** 直接改 viewport transform，把选中节点挪到 (目标x, 目标y)。 */
const 挪到 = (page, id, tx, ty) => page.evaluate(([i, x, y]) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  const vp = document.querySelector('.react-flow__viewport');
  if (!n || !vp) return null;
  const r = n.getBoundingClientRect();
  const cur = vp.style.transform;                       // translate(x px, y px) scale(z)
  const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)\s*scale\(([-\d.]+)\)/.exec(cur);
  if (!m) return { 失败: 'transform 解析不了', cur };
  const dx = (x - (r.x + r.width / 2)) / parseFloat(m[3]);
  const dy = (y - (r.y + r.height / 2)) / parseFloat(m[3]);
  vp.style.transform = `translate(${parseFloat(m[1]) + dx}px, ${parseFloat(m[2]) + dy}px) scale(${m[3]})`;
  const r2 = n.getBoundingClientRect();
  return { 原: cur, 新: vp.style.transform, 节点盒: [Math.round(r2.x), Math.round(r2.y), Math.round(r2.width), Math.round(r2.height)] };
}, [id, tx, ty]);

/** 诊断：Add tags 按钮在不在屏上、被谁挡着。 */
const 诊断 = (page) => page.evaluate(() => {
  const e = document.querySelector('[data-testid="flow-node-selected-tag"]');
  if (!e) return { 存在: false };
  const r = e.getBoundingClientRect();
  const cx = r.x + r.width / 2, cy = r.y + r.height / 2;
  const hit = document.elementFromPoint(cx, cy);
  return {
    存在: true, 盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    在屏上: cx >= 0 && cy >= 0 && cx <= innerWidth && cy <= innerHeight,
    视口: [innerWidth, innerHeight],
    命中: hit ? { tag: hit.tagName, testid: hit.getAttribute('data-testid'),
      cls: (hit.getAttribute('class') || '').split(/\s+/).slice(0, 3).join(' '),
      在按钮内: !!hit.closest('[data-testid="flow-node-selected-tag"]') } : null,
  };
});

const 读 = (page) => page.evaluate(() => {
  const e = document.querySelector('.max-w-canvas-tag-selector');
  if (!e) return null;
  const cs = getComputedStyle(e);
  const r = e.getBoundingClientRect();
  const btns = Array.from(e.querySelectorAll('button')).map((b) => {
    const q = b.getBoundingClientRect();
    return { aria: b.getAttribute('aria-label'), 盒: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)],
      完全在可视区内: q.left >= r.left - 0.5 && q.right <= r.right + 0.5 };
  });
  return { 布局宽: e.offsetWidth, 布局高: e.offsetHeight, 变换后: [Math.round(r.width), Math.round(r.height)],
    computed: { w: cs.width, h: cs.height, maxW: cs.maxWidth },
    scrollW: e.scrollWidth, clientW: e.clientWidth, 可横向滚动: e.scrollWidth > e.clientWidth + 0.5,
    按钮数: btns.length, 被裁: btns.filter((x) => !x.完全在可视区内).map((x) => x.aria) };
});

const tab = await b.contexts()[0].newPage();
await tab.goto(shared.url(), { waitUntil: 'domcontentloaded' });
await tab.waitForSelector('.react-flow__node', { timeout: 60000 });
await tab.waitForTimeout(3500);

rec.档位 = [];
for (const [w, h] of [[1280, 720], [300, 720], [256, 720], [250, 720], [220, 720], [200, 720], [180, 720], [160, 720]]) {
  await pin(tab, w, h);
  await tab.keyboard.press('Escape'); await tab.waitForTimeout(250);
  const id = await 选节点(tab);
  if (!id) { rec.档位.push({ 视口: [w, h], 打开: false, 原因: '选不中节点' }); console.log(`  ${w}×${h}: ❌ 选不中节点`); continue; }
  // 目标 x：左栏 160 右侧 + 60；y：视口中线
  const 目标x = Math.min(w - 60, 220);
  const 目标y = Math.round(h / 2);
  const moved = await 挪到(tab, id, 目标x, 目标y);
  await tab.waitForTimeout(400);
  const dg = await 诊断(tab);
  let row = { 视口: [w, h], 节点: id, 挪动: moved, 诊断: dg };
  if (dg.存在 && dg.在屏上 && dg.命中 && dg.命中.在按钮内) {
    await tab.mouse.click(dg.盒[0] + dg.盒[2] / 2, dg.盒[1] + dg.盒[3] / 2);
    let last = -1, stable = 0;
    for (let i = 0; i < 20; i++) {
      await tab.waitForTimeout(220);
      const ww = await tab.evaluate(() => { const e = document.querySelector('.max-w-canvas-tag-selector'); return e ? e.offsetWidth : -1; });
      if (ww > 0 && ww === last) { stable++; if (stable >= 2) break; } else stable = 0;
      last = ww;
    }
    const d = await 读(tab);
    if (d) {
      const 预测宽 = Math.min(224, Math.max(0, w - 32));
      Object.assign(row, { 打开: true, 布局: [d.布局宽, d.布局高], computed: d.computed,
        滚动: d.可横向滚动, scrollW: d.scrollW, clientW: d.clientW, 按钮数: d.按钮数, 被裁: d.被裁, 预测宽 });
      console.log(`  ${w}×${h}: 布局 ${d.布局宽}×${d.布局高}（预测宽 ${预测宽} ${d.布局宽 === 预测宽 ? '✅' : '❌'}）` +
        ` scrollW=${d.scrollW}/client=${d.clientW} 滚动=${d.可横向滚动} 按钮数=${d.按钮数} 被裁=${JSON.stringify(d.被裁)}`);
    } else { row.原因 = '点了没开'; console.log(`  ${w}×${h}: ❌ 点了没开`); }
  } else {
    row.打开 = false; row.原因 = `按钮不可点（在屏上=${dg.在屏上}，命中=${dg.命中 && dg.命中.testid || dg.命中 && dg.命中.cls}）`;
    console.log(`  ${w}×${h}: ❌ ${row.原因}｜按钮盒=${JSON.stringify(dg.盒)} 视口=${JSON.stringify(dg.视口)}`);
  }
  rec.档位.push(row);
  await tab.keyboard.press('Escape'); await tab.waitForTimeout(300);
}
await tab.close();
console.log('\n共享页签复位:', JSON.stringify(await pinViewport(shared)));
rec.收尾 = { status: await R.status(), sel: await R.selCount(), credits: await R.credits() };
console.log('收尾:', JSON.stringify(rec.收尾));
fs.writeFileSync(new URL('./_tmp-b171g.json', import.meta.url), JSON.stringify(rec, null, 1));
await b.close();
