// 批次 91 · B：**手柄**与 **⊕ 菜单钮**是两套东西 —— 导演台有前者、没有后者。
//
// a 轮实测（20 节点）：
//   source 手柄 19 个 / target 手柄 20 个
//   🔴 唯一缺 source 的是 **时间线节点**（`timeline`）—— 与本页「时间线只有 before ⊕」自洽
//   🔴 但 **导演台（external）src=1 tgt=1 —— 它有左右两个拖拽手柄**，
//      而批次 69 记的是「导演台**没有 ⊕**、从导演台发起连线**做不到**」。
//
// ⇒ 两种可能，必须分开：
//   (a) 手柄在但**拖不出任何东西**（装饰性/未接线）—— 那批次 69 的结论仍成立，
//       但要说清「有手柄 ≠ 能发起」；
//   (b) 手柄**能拖出 ⊕ 菜单** —— 那「导演台发起连线做不到」这句就**被推翻**。
//
// ⇒ **P2**：从导演台的出边手柄按下、拖到**空白画布**松手
//   （拖到空白 = 取消，不建线，见本页第 383 行那条实测）
//   ⇒ 观察：有没有弹出 ⊕ 菜单？有没有新建 edge？
//
// ⛔ 全程不把线连到任何节点上 ⇒ 不会新增 edge。松手前会先回读 edge 数。
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
const ID = 'node_pxvkay973v';   // 别人的导演台，只读不动

out.start = { edges: await edgeN(), sel: await selN(), credits: await credits(), zoom: await zoomPct() };
log('起点：', JSON.stringify(out.start));

// 先把导演台弄进视口（60% 下那六个基线节点都在视口外）
await p.keyboard.press('Meta+0'); await p.waitForTimeout(1700);
out.zoomAtFit = await zoomPct();

// 找一个「最上层就是导演台」的点
const pt = await p.evaluate((id) => {
  const n = document.querySelector(`.react-flow__node[data-id="${id}"]`); if (!n) return null;
  const r = n.getBoundingClientRect(); const hits = [];
  for (let fx = 0.12; fx <= 0.88; fx += 0.08) for (let fy = 0.12; fy <= 0.88; fy += 0.08) {
    const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
    const el = document.elementFromPoint(x, y);
    if (el && el.closest('.react-flow__node') === n) hits.push({ x, y });
  }
  return hits.length ? { ...hits[Math.floor(hits.length / 2)], rect: `${Math.round(r.width)}×${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`, hits: hits.length } : { rect: `${Math.round(r.width)}×${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`, hits: 0 };
}, ID);
out.pt = pt;
log('导演台落点：', JSON.stringify(pt));

if (!pt || !pt.hits) { out.verdict = { VOID: '⌘0 之后仍找不到属于导演台的落点' }; log('🔴 VOID'); }
else {
  // 选中它（点之前已证明落点属于谁 —— 批次 89 的教训）
  await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1000);
  const s1 = await selN();
  out.selState = { sel: s1, ids: await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id'))) };
  log('选中：', JSON.stringify(out.selState));
  if (s1 !== '1' || out.selState.ids[0] !== ID) { out.verdict = { VOID: `选中的是 ${JSON.stringify(out.selState.ids)}，不是导演台` }; log('🔴 VOID：', JSON.stringify(out.verdict)); }
  else {
    // 读出它左右两个手柄的屏上几何与可见性
    out.hs = await p.evaluate((id) => { const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
      return ['source', 'target'].map((k) => { const e = n.querySelector(`[data-testid="flow-node-${k}-handle"]`); if (!e) return { k, exists: false };
        const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
        return { k, exists: true, box: `${Math.round(r.width)}×${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
          pe: cs.pointerEvents, op: cs.opacity, vis: cs.visibility, z: cs.zIndex }; }); }, ID);
    log('手柄：', JSON.stringify(out.hs));
    out.plus = await p.evaluate((id) => { const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
      return Array.from(n.querySelectorAll('[data-testid$="connection-menu-button"]')).map((e) => e.getAttribute('aria-label')); }, ID);
    log('⊕ 菜单钮：', JSON.stringify(out.plus), '（批次 69 记的是 0 个）');

    // P2：从出边手柄拖到空白松手（松在空白 ⇒ 取消，不建线）
    const src = out.hs.find((h) => h.k === 'source' && h.exists);
    if (!src) { out.verdict = { VOID: '取不到出边手柄几何' }; log('🔴 VOID'); }
    else {
      const [bx, by] = src.box.split('@')[1].split(',').map(Number);
      const [bw, bh] = src.box.split('×')[0].split('×').map(Number);
      const from = { x: Math.round(bx + bw / 2), y: Math.round(by + bh / 2) };
      // 找一个远离任何节点的空白落点
      const blank = await p.evaluate(() => { const r = document.querySelector('.react-flow__pane'); if (!r) return null;
        const q = r.getBoundingClientRect();
        for (let fx = 0.08; fx <= 0.92; fx += 0.08) for (let fy = 0.08; fy <= 0.92; fy += 0.08) {
          const x = Math.round(q.x + q.width * fx), y = Math.round(q.y + q.height * fy);
          const el = document.elementFromPoint(x, y);
          if (el && el.closest('.react-flow__node') === null && el.closest('button') === null) return { x, y }; }
        return null; });
      out.drag = { from, blank };
      log('拖拽：', JSON.stringify(out.drag));
      if (!blank) { out.verdict = { VOID: '找不到空白落点' }; log('🔴 VOID'); }
      else {
        await p.mouse.move(from.x, from.y); await p.mouse.down();
        await p.waitForTimeout(300);
        await p.mouse.move((from.x + blank.x) / 2, (from.y + blank.y) / 2, { steps: 12 }); await p.waitForTimeout(500);
        out.midDrag = { edges: await edgeN(), menu: await p.evaluate(() => { const m = document.querySelector('[data-testid="canvas-context-menu"]');
          if (!m) return null; return { title: (m.querySelector('h2,[role="heading"]') || {}).innerText || null,
            items: Array.from(m.querySelectorAll('[role="menuitem"]')).map((i) => i.innerText.replace(/\s+/g, ' ').trim()) }; }) };
        log('拖到一半：', JSON.stringify(out.midDrag));
        await p.mouse.up(); await p.waitForTimeout(1200);
        out.afterDrop = { edges: await edgeN(), sel: await selN(),
          menu: await p.evaluate(() => { const m = document.querySelector('[data-testid="canvas-context-menu"]');
            return m ? Array.from(m.querySelectorAll('[role="menuitem"]')).map((i) => i.innerText.replace(/\s+/g, ' ').trim()) : null; }) };
        log('空白松手后：', JSON.stringify(out.afterDrop));
        out.verdict = { sourceHandleDraggable: !!(out.midDrag.menu || (out.afterDrop.menu && out.afterDrop.menu.length)),
          edgeCreated: Number(out.afterDrop.edges) > Number(out.start.edges), edgesBefore: out.start.edges, edgesAfter: out.afterDrop.edges };
        log('P2 判定：', JSON.stringify(out.verdict));
      }
    }
  }
}

// 收尾：取消选中 + 缩放归位
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
out.end = { edges: await edgeN(), sel: await selN(), zoom: z2, zoomStable: z1 === z2, credits: await credits() };
log('终态：', JSON.stringify(out.end), '｜缩放归位', z2 === 60 ? '✅' : '🔴', '｜edges 未变 =', out.end.edges === out.start.edges);
writeFileSync(new URL('./_tmp-b91b.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
