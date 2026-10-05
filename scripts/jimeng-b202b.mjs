// 批次 202 b 轮：补验 a 轮那条**无效臂** —— 文本节点选中态的 `node-toolbar`。
//
// a 轮 ④ 那条读数是 `nodeToolbar: 0 / textEditorToolbar: 0 / 选中数: 0` ——
// 🔴 **选中数就是 0** ⇒ 点击**根本没选中**节点（当时画布 50%，该节点不在可点位置）
//   ⇒ 那是**无效臂**（立规 78），**不能**读成「无头下 `node-toolbar` 不存在」。
//
// 本轮：先把缩放放到能看见该节点的位置，**先断言选中数 ≥1** 再读工具条 testid。
//   顺便把编辑态的 `text-editor-toolbar` 也验一遍（批次 194 发现的那条）。
import fs from 'node:fs';
import { openCanvas, readers, settle, setZoom, endState } from './jimeng-b135-lib.mjs';

const SELF = 'node_5gftn3dnt1';   // 「文本 3」
const { b, p } = await openCanvas();
const R = readers(p);
const 基线 = { ids: await R.ids(), testids: await R.testids() };
const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b202b', 节点: SELF, 补的是: 'a 轮 ④ 的无效臂' };

await settle(p, R);

// 先找该节点，把它移到视口中央：放大到 100% 后用搜索定位（手册记的路径）
await setZoom(p, 100);
const 搜索钮 = await p.evaluate(() => {
  const e = document.querySelector('[data-testid="canvas-panel-launcher"][aria-label="搜索"]')
    || Array.from(document.querySelectorAll('button')).find((x) => (x.getAttribute('aria-label') || '') === '搜索');
  if (!e) return null; const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
if (!搜索钮) { out.中止 = '找不到搜索钮'; }
else {
  await p.mouse.click(搜索钮[0], 搜索钮[1]); await p.waitForTimeout(1500);
  await p.evaluate(() => { const e = document.querySelector('input[aria-label*="搜索"],input[type="text"]');
    if (e) { Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(e, '');
      e.dispatchEvent(new Event('input', { bubbles: true })); } });
  await p.keyboard.type('文本 3', { delay: 90 }); await p.waitForTimeout(2200);
  const 行 = await p.evaluate((id) => {
    const e = document.querySelector(`[data-testid="canvas-search-result-node_${id.replace('node_', '')}"]`)
      || document.querySelector('[data-testid^="canvas-search-result-node_"]');
    if (!e) return null; const r = e.getBoundingClientRect();
    return { testid: e.getAttribute('data-testid'), 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] };
  }, SELF);
  out.点的行 = 行 && 行.testid;
  if (行) { await p.mouse.click(行.点[0], 行.点[1]); await p.waitForTimeout(2600); }
  await p.keyboard.press('Escape'); await p.waitForTimeout(1000);
}

out.定位后 = await p.evaluate((id) => {
  const n = document.querySelector(`.react-flow__node[data-id="${id}"]`); if (!n) return { 找不到: true };
  const r = n.getBoundingClientRect();
  return { 选中: n.classList.contains('selected'), aria: n.getAttribute('aria-label'),
    屏上: [r.x, r.y, r.width, r.height].map(Math.round),
    在视口内: r.right > 0 && r.x < innerWidth && r.bottom > 0 && r.y < innerHeight };
}, SELF);
log('定位后：', JSON.stringify(out.定位后));

// —— 选中态工具条（先断言选中数 ≥ 1）——
out.选中态 = await p.evaluate(() => ({
  选中数: document.querySelectorAll('.react-flow__node.selected').length,
  nodeToolbar: document.querySelectorAll('[data-testid="node-toolbar"]').length,
  textEditorToolbar: document.querySelectorAll('[data-testid="text-editor-toolbar"]').length,
}));
out.选中态.断言 = { 判据: '选中数 ≥ 1', 通过: out.选中态.选中数 >= 1 };
log('选中态：', JSON.stringify(out.选中态), '| 断言', out.选中态.断言.通过 ? '✅' : '🔴 无效臂');

// —— 编辑态工具条（双击进编辑态）——
if (out.定位后.在视口内) {
  const pt = await p.evaluate((id) => { const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
    const r = n.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height * 0.55)]; }, SELF);
  await p.mouse.dblclick(pt[0], pt[1]); await p.waitForTimeout(2000);
  out.编辑态 = await p.evaluate(() => ({
    编辑面数: document.querySelectorAll('.tiptap.ProseMirror').length,
    节点内contenteditable: document.querySelectorAll('.react-flow__node [contenteditable]').length,
    nodeToolbar: document.querySelectorAll('[data-testid="node-toolbar"]').length,
    textEditorToolbar: document.querySelectorAll('[data-testid="text-editor-toolbar"]').length,
    焦点: (() => { const a = document.activeElement; return a ? a.tagName + '[' + ((a.getAttribute && a.getAttribute('aria-label')) || (a.className && String(a.className).slice(0, 20)) || '') + ']' : null; })(),
  }));
  out.编辑态.断言 = { 判据: '编辑面数 = 1', 通过: out.编辑态.编辑面数 === 1 };
  log('编辑态：', JSON.stringify(out.编辑态), '| 断言', out.编辑态.断言.通过 ? '✅' : '🔴 无效臂');
  await p.keyboard.press('Escape'); await p.waitForTimeout(900);
}

fs.writeFileSync('/tmp/b202b.json', JSON.stringify(out, null, 1));
// 收尾：清选中 + 视口复位 26%
await p.evaluate(() => { const n = document.querySelector('.react-flow__node.selected');
  if (n) { const r = n.getBoundingClientRect();
    for (let x = 40; x < innerWidth - 340; x += 40) for (let y = 100; y < innerHeight - 120; y += 40) {
      const h = document.elementFromPoint(x, y);
      if (h && h.classList && h.classList.contains('react-flow__pane')) { return { x, y }; } } } return null; }).then((s) => { if (s) return p.mouse.click(s.x, s.y); });
await p.waitForTimeout(900);
await setZoom(p, 26);
out.收尾 = await endState(p, R, 基线);
log('收尾：', JSON.stringify(out.收尾));
await b.close();
