// 批次 203 c 轮：拿到**编辑态**在无头下的读数（a 轮那条是无效臂）。
//
// a 轮为什么无效：26% 档下节点只有 `83×83` 屏上 ⇒ **双击没进编辑态**
//   （读数：`编辑面数 0` / `text-editor-toolbar 0` / `nodeToolbar 2`，还是选中态）
//   而批次 194/195 的编辑态都是在 **50%** 档拍的 ⇒ 50% 才是能编辑的档。
//   📌 但 50% 档下三个文本节点**全在视口左侧外**（实测 `[-175,19]` / `[-155,39]` / `[-135,59]`）。
//
// ⇒ 本轮：**50% 档 + 搜索精确定位**（把节点取景到 `474`），再双击。
//
// 🔴 修掉批次 202b 埋的坑：那段代码在「按 testid 精确匹配失败」时
//   **fallback 到第一条**，于是搜「文本 3」却点到了**音频 68**。
//   本轮**没有 fallback**：匹配不到就标**无效臂**并写明（立规 78）。
import fs from 'node:fs';
import { openCanvas, readers, settle, setZoom, endState } from './jimeng-b135-lib.mjs';

const TARGET = 'node_5gftn3dnt1';          // 「文本 3」
const TARGET_TID = 'canvas-search-result-node_5gftn3dnt1';
const { b, p } = await openCanvas();
const R = readers(p);
const 基线 = { ids: await R.ids(), testids: await R.testids() };
const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b203c', 目标: TARGET, 修的坑: '202b 的 fallback 点了错误的第一行' };

await settle(p, R);
await setZoom(p, 50);

// —— 诊断：搜「文本」，看结果面板里到底有没有目标行 ——
const 搜 = async (词) => {
  const 钮 = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-panel-launcher"][aria-label="搜索"]')
    || Array.from(document.querySelectorAll('button')).find((x) => (x.getAttribute('aria-label') || '') === '搜索');
    if (!e) return null; const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
  if (!钮) return { 中止: '找不到搜索钮' };
  await p.mouse.click(钮[0], 钮[1]); await p.waitForTimeout(1400);
  await p.evaluate(() => { const e = document.querySelector('input[aria-label*="搜索"],input[type="text"]');
    if (e) { Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(e, '');
      e.dispatchEvent(new Event('input', { bubbles: true })); } });
  await p.keyboard.type(词, { delay: 80 });
  await p.waitForTimeout(2200);
  return await p.evaluate((tid) => ({
    总条数: document.querySelectorAll('[data-testid^="canvas-search-result-node_"]').length,
    全部: Array.from(document.querySelectorAll('[data-testid^="canvas-search-result-node_"]')).map((e) => e.getAttribute('data-testid')),
    命中目标: !!document.querySelector(`[data-testid="${tid}"]`),
  }), TARGET_TID);
};

out.搜文本 = await 搜('文本');
log('搜「文本」：', JSON.stringify(out.搜文本));
if (!out.搜文本.命中目标) { out.搜文本3 = await 搜('文本 3'); log('搜「文本 3」：', JSON.stringify(out.搜文本3)); }
else { await p.keyboard.press('Escape'); await p.waitForTimeout(900); }

// —— 定位：点**精确匹配**的那一行（无 fallback）——
const 点位 = await p.evaluate((tid) => {
  const e = document.querySelector(`[data-testid="${tid}"]`);
  if (!e) return { 找到: false };
  const r = e.getBoundingClientRect();
  return { 找到: true, 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], 屏上: [r.x, r.y, r.width, r.height].map(Math.round) };
}, TARGET_TID);
out.点位 = 点位;

if (!点位.找到) {
  out.无效臂 = { 原因: '结果面板里没有目标行（没有 fallback 兜底）' };
  log('🔴 无效臂：', out.无效臂.原因);
} else {
  await p.mouse.click(点位.点[0], 点位.点[1]);
  await p.waitForTimeout(3000); // 等取景收敛
  out.定位后 = await p.evaluate((id) => {
    const n = document.querySelector(`.react-flow__node[data-id="${id}"]`); if (!n) return { 找不到: true };
    const r = n.getBoundingClientRect();
    return { 选中: n.classList.contains('selected'), 屏上: [r.x, r.y, r.width, r.height].map(Math.round),
      在视口内: r.x > 10 && r.right < innerWidth - 10 && r.y > 60 && r.bottom < innerHeight - 10,
      正文中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height * 0.55)] };
  }, TARGET);
  log('定位后：', JSON.stringify(out.定位后));
  await p.keyboard.press('Escape'); await p.waitForTimeout(900); // 只关面板，节点保持选中

  if (out.定位后.在视口内) {
    const [cx, cy] = out.定位后.正文中心;
    await p.mouse.dblclick(cx, cy); await p.waitForTimeout(2400);
    out.编辑态 = await p.evaluate((id) => {
      const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
      const g = (sel) => { const e = document.querySelector(sel); if (!e) return null;
        const r = e.getBoundingClientRect(); return [r.x, r.y, r.width, r.height].map((z) => Math.round(z * 100) / 100); };
      return { 编辑面数: document.querySelectorAll('.tiptap.ProseMirror').length,
        节点内contenteditable: document.querySelectorAll('.react-flow__node [contenteditable]').length,
        nodeToolbar: document.querySelectorAll('[data-testid="node-toolbar"]').length,
        textEditorToolbar: document.querySelectorAll('[data-testid="text-editor-toolbar"]').length,
        编辑态工具条屏上: g('[data-testid="text-editor-toolbar"]'),
        编辑面屏上: g('.tiptap.ProseMirror'),
        节点屏上: n ? (() => { const r = n.getBoundingClientRect(); return [r.x, r.y, r.width, r.height].map(Math.round); })() : null,
        焦点: (() => { const a = document.activeElement; return a ? a.tagName : null; })(),
        编辑面在节点内: (() => { const e = document.querySelector('.tiptap.ProseMirror'); return e ? !!e.closest('.react-flow__node') : null; })() };
    }, TARGET);
    out.编辑态.断言 = { 判据: '编辑面数 = 1', 通过: out.编辑态.编辑面数 === 1 };
    log('编辑态：', JSON.stringify(out.编辑态), '→', out.编辑态.断言.通过 ? '✅' : '🔴 无效臂');

    if (out.编辑态.断言.通过) {
      out.比对 = [
        { 项: '编辑面数', 有头: 1, 无头: out.编辑态.编辑面数 },
        { 项: '节点内contenteditable', 有头: 0, 无头: out.编辑态.节点内contenteditable },
        { 项: '编辑面在节点内', 有头: false, 无头: out.编辑态.编辑面在节点内 },
        { 项: '焦点', 有头: 'DIV', 无头: out.编辑态.焦点 },
        { 项: 'text-editor-toolbar 实例数', 有头: 1, 无头: out.编辑态.textEditorToolbar },
        { 项: 'node-toolbar 实例数（编辑态）', 有头: 0, 无头: out.编辑态.nodeToolbar },
      ].map((r) => ({ ...r, 一致: String(r.有头) === String(r.无头) }));
      log('与有头逐条比对：');
      for (const r of out.比对) log(`   ${r.一致 ? '✅' : '🔴'} ${r.项}：有头 ${r.有头} / 无头 ${r.无头}`);
    }
    await p.keyboard.press('Escape'); await p.waitForTimeout(900);
  } else out.跳过编辑态 = '定位后不在视口内';
}

fs.writeFileSync('/tmp/b203c.json', JSON.stringify(out, null, 1));
await p.evaluate(() => { const ns = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getBoundingClientRect());
  for (let x = 40; x < innerWidth - 340; x += 40) for (let y = 100; y < innerHeight - 120; y += 40) {
    const h = document.elementFromPoint(x, y);
    if (h && h.classList && h.classList.contains('react-flow__pane') && !ns.some((r) => x >= r.x && x <= r.right && y >= r.y && y <= r.bottom)) return { x, y }; }
  return null; }).then((s) => { if (s) return p.mouse.click(s.x, s.y); });
await p.waitForTimeout(900);
await setZoom(p, 26);
out.收尾 = await endState(p, R, 基线);
log('收尾：', JSON.stringify(out.收尾));
await b.close();
