// 批次 203 a 轮：补上批次 202 欠的那一格 —— **编辑态 `text-editor-toolbar` 在无头下**。
//
// 批次 202 的 ④ 之所以只拿到「选中态」：搜索定位后那个节点屏上是
//   `[−910, −242, 320, 320]`（**负坐标、不在视口内**）⇒ 双击进不了编辑态。
//   ⇒ 那一格（编辑态工具条）**仍然只有有头读数**（批次 194/195）。
//
// 📌 本轮换做法：**不点搜索**（点搜索会把节点挪走），而是
//   ① 扫出**当前视口内**的所有文本节点，选**一个屏上坐标为正且靠近中心**的；
//   ② 直接点它 → 断言 `选中数 ≥ 1` → 读选中态 testid；
//   ③ 双击它 → 断言 `编辑面数 = 1` → 读编辑态 testid。
//
// 🔴 每一步都带断言，断言不过就标**无效臂**并写明原因（立规 78）。
import fs from 'node:fs';
import { openCanvas, readers, settle, setZoom, endState } from './jimeng-b135-lib.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
const 基线 = { ids: await R.ids(), testids: await R.testids() };
const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b203a', 补的是: '批次 202 欠的「编辑态 text-editor-toolbar 在无头下」' };

await settle(p, R);
await setZoom(p, 26);   // 🔴 50% 下三个文本节点全跑到视口左侧外；26% 档三个都在视口内（实测）

// ① 找一个视口内、靠近中心的文本节点
const 候选 = await p.evaluate(() => {
  const ns = Array.from(document.querySelectorAll('.react-flow__node'));
  const 中线 = { x: innerWidth * 0.5, y: innerHeight * 0.5 };
  return ns.map((n) => {
    const r = n.getBoundingClientRect();
    const cx = r.x + r.width / 2, cy = r.y + r.height / 2;
    return { id: n.getAttribute('data-id'), aria: n.getAttribute('aria-label'),
      屏上: [r.x, r.y, r.width, r.height].map(Math.round),
      在视口内: r.x > 20 && r.right < innerWidth - 20 && r.y > 60 && r.bottom < innerHeight - 20,
      到中心距离: Math.round(Math.hypot(cx - 中线.x, cy - 中线.y)) };
  }).filter((x) => /文本|text/i.test(x.aria || '') && x.在视口内)
    .sort((a, b) => a.到中心距离 - b.到中心距离);
});
log('视口内的文本节点（按离中心近排序）：');
for (const c of 候选.slice(0, 5)) log('  ', c.id, c.aria, JSON.stringify(c.屏上), '距离', c.到中心距离);

if (!候选.length) { out.中止 = '视口内没有文本节点'; }
else {
  const T = 候选[0];
  out.用哪个节点 = { id: T.id, aria: T.aria, 屏上: T.屏上 };
  const 正文点 = [Math.round(T.屏上[0] + T.屏上[2] / 2), Math.round(T.屏上[1] + T.屏上[3] * 0.55)];

  // ② 选中态
  await p.mouse.click(正文点[0], 正文点[1]); await p.waitForTimeout(1400);
  out.选中态 = await p.evaluate(() => ({
    选中数: document.querySelectorAll('.react-flow__node.selected').length,
    nodeToolbar: document.querySelectorAll('[data-testid="node-toolbar"]').length,
    textEditorToolbar: document.querySelectorAll('[data-testid="text-editor-toolbar"]').length,
    编辑面数: document.querySelectorAll('.tiptap.ProseMirror').length,
  }));
  out.选中态.断言 = { 判据: '选中数 ≥ 1 且 编辑面数 = 0', 通过: out.选中态.选中数 >= 1 && out.选中态.编辑面数 === 0 };
  log('选中态：', JSON.stringify(out.选中态), '→', out.选中态.断言.通过 ? '✅' : '🔴 无效臂');

  // ③ 编辑态：双击正文
  await p.mouse.dblclick(正文点[0], 正文点[1]); await p.waitForTimeout(2200);
  out.编辑态 = await p.evaluate((id) => {
    const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
    const g = (sel) => { const e = document.querySelector(sel); if (!e) return null;
      const r = e.getBoundingClientRect(); return [r.x, r.y, r.width, r.height].map((z) => Math.round(z * 100) / 100); };
    return {
      编辑面数: document.querySelectorAll('.tiptap.ProseMirror').length,
      节点内contenteditable: document.querySelectorAll('.react-flow__node [contenteditable]').length,
      nodeToolbar: document.querySelectorAll('[data-testid="node-toolbar"]').length,
      textEditorToolbar: document.querySelectorAll('[data-testid="text-editor-toolbar"]').length,
      编辑态工具条屏上: g('[data-testid="text-editor-toolbar"]'),
      选中态工具条屏上: g('[data-testid="node-toolbar"]'),
      编辑面屏上: g('.tiptap.ProseMirror'),
      节点屏上: (() => { const r = n.getBoundingClientRect(); return [r.x, r.y, r.width, r.height].map(Math.round); })(),
      焦点: (() => { const a = document.activeElement; return a ? a.tagName : null; })(),
      编辑面在节点内: (() => { const e = document.querySelector('.tiptap.ProseMirror');
        return e ? !!e.closest('.react-flow__node') : null; })(),
    };
  }, T.id);
  out.编辑态.断言 = { 判据: '编辑面数 = 1 且 节点内contenteditable = 0', 通过: out.编辑态.编辑面数 === 1 && out.编辑态.节点内contenteditable === 0 };
  log('编辑态：', JSON.stringify(out.编辑态), '→', out.编辑态.断言.通过 ? '✅' : '🔴 无效臂');

  // 📌 与批次 194/195 的有头读数逐条比对
  out.比对 = [
    { 项: '编辑面数', 有头批次194: 1, 无头本轮: out.编辑态.编辑面数 },
    { 项: '节点内contenteditable', 有头批次194: 0, 无头本轮: out.编辑态.节点内contenteditable },
    { 项: '编辑面在节点内', 有头批次194: false, 无头本轮: out.编辑态.编辑面在节点内 },
    { 项: '焦点', 有头批次194: 'DIV', 无头本轮: out.编辑态.焦点 },
    { 项: 'text-editor-toolbar 实例数', 有头批次194: 1, 无头本轮: out.编辑态.textEditorToolbar },
    { 项: 'node-toolbar 实例数（编辑态）', 有头批次194: 0, 无头本轮: out.编辑态.nodeToolbar },
  ];
  out.比对结论 = out.比对.map((r) => ({ ...r, 一致: String(r.有头批次194) === String(r.无头本轮) }));
  log('与有头逐条比对：');
  for (const r of out.比对结论) log(`   ${r.一致 ? '✅' : '🔴'} ${r.项}：有头 ${r.有头批次194} / 无头 ${r.无头本轮}`);

  await p.keyboard.press('Escape'); await p.waitForTimeout(900);
  await p.keyboard.press('Escape'); await p.waitForTimeout(900);
}

fs.writeFileSync('/tmp/b203a.json', JSON.stringify(out, null, 1));
// 收尾：清选中 + 视口复位
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
