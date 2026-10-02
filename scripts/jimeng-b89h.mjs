// 批次 89 · H：两条读数打架时，去读**原始值**。
//
// g 轮输出里有一处自相矛盾：
//     ② 选中：{"sel":"1", …, "nodeSelected":false}
//
// `sel` 是从状态行正则读出来的「1 selected」，
// `nodeSelected` 是我在节点 className 里找 `' selected'` 得到的 false。
// 两者必有一个的判据不对 —— 这正是本页 1276 那条「尺子坏了，但读数看起来很干净」。
//
// ⇒ 本轮不推断，**直接把 className 原文打出来**（静息 / 选中各一份，逐字对照）。
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
const ID = 'node_pxvkay973v';

const raw = () => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  const s = document.querySelectorAll('.react-flow__node.selected');
  const sel = document.querySelector('.react-flow__node.selected');
  return { cls: n ? n.className : null, clsAttr: n ? n.getAttribute('class') : null,
    selectedAttr: n ? n.getAttribute('data-selected') : null,
    ariaSelected: n ? n.getAttribute('aria-selected') : null,
    // 文档里**带 selected class** 的节点（权威口径，不靠我的 includes）
    selectedCount: s.length, selectedIds: Array.from(s).map((x) => x.getAttribute('data-id')),
    selectedClsSample: sel ? String(sel.className).slice(0, 120) : null,
    statusLine: (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0] };
}, ID);

await p.keyboard.press('Meta+0'); await p.waitForTimeout(1600);
const box = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return null;
  const r = n.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2), inViewport: r.left >= 0 && r.top >= 0 && r.right <= 1280 && r.bottom <= 720 }; }, ID);
log('落点：', JSON.stringify(box));
out.rest = { sel: await selCount(), ...(await raw()) };
log('① 静息 className：', out.rest.cls);
log('  带 selected class 的节点数：', out.rest.selectedCount, JSON.stringify(out.rest.selectedIds));

if (box && box.inViewport) {
  await p.mouse.click(box.x, box.y);
  await p.waitForTimeout(1300);
  out.sel = { sel: await selCount(), ...(await raw()) };
  log('② 选中 className：', out.sel.cls);
  log('  带 selected class 的节点数：', out.sel.selectedCount, JSON.stringify(out.sel.selectedIds));
  await p.keyboard.press('Escape'); await p.waitForTimeout(1100);
  out.back = { sel: await selCount(), ...(await raw()) };
  log('③ 取消 className：', out.back.cls);
  out.verdict = { restHasSelected: /(^|\s)selected(\s|$)/.test(out.rest.cls || ''),
    selHasSelected: /(^|\s)selected(\s|$)/.test(out.sel.cls || ''),
    restAuthoritative: out.rest.selectedCount, selAuthoritative: out.sel.selectedCount };
  log('判定：', JSON.stringify(out.verdict));
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
out.end = { zoom: await zoomPct(), sel: await selCount() };
log('终态：', JSON.stringify(out.end));
writeFileSync(new URL('./_tmp-b89h.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
