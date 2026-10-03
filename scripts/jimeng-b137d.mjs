// 批次 137 · d 轮：把「空白处松手之后那个 `1 selected` 到底是谁」记清楚。
//
// 🔑 c 轮已经拿到关键读数，但差最后一颗钉子：
//   两个合规落点都出现「**松手后选中数 = 1**」，而**源节点明确未被选中**（逐个查过 class）。
//   ⇒ `:104` 把「`1 selected`」解读成「**源**节点变成选中态」，这两件事**不是同一件**。
//   本轮把**被选中的那个 id** 记下来，并查它与「源节点」「落点」的关系。
//
// 🔴 c 轮收尾有残留（`1 selected`、testid 185）：它的「取消选中」点在 `(640,700)`，
//   **而那个点落在节点上** ⇒ 点了反而选中了一个节点。
//   ⇒ 立规：**「取消选中」这个动作的落点，也必须先校验命中 `.react-flow__pane`** ——
//     同一个错误形状（批次 131 b 轮：点控件 vs 点空白用反了）。
import { writeFileSync } from 'node:fs';
import { openCanvas, readers, settle, keyGuard } from './jimeng-b135-lib.mjs';
import { readConnect } from './jimeng-b136-lib.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'd' };
const save = () => writeFileSync(new URL('./_tmp-b137d.json', import.meta.url), JSON.stringify(out, null, 1));
const 断言 = (名, 条件, 详情) => { const ok = !!!!条件; (out.护栏 = out.护栏 || []).push({ 名, 通过: ok, 详情 });
  log(`  ${ok ? '✅' : '⛔'} 断言·${名}：${JSON.stringify(详情).slice(0, 260)}`); save(); return ok; };

const 空白点 = () => p.evaluate(() => {
  const nodes = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getBoundingClientRect());
  for (let y = 700; y >= 80; y -= 4) for (let x = 8; x <= innerWidth - 8; x += 4) {
    const h = document.elementFromPoint(x, y);
    if (h && h.classList && h.classList.contains('react-flow__pane')
      && !nodes.some((r) => x >= r.x && x <= r.right && y >= r.y && y <= r.bottom)) return { x, y };
  }
  return null;
});
const 选中详情 = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => {
  const r = n.getBoundingClientRect();
  return { id: n.getAttribute('data-id'), 标题: (n.querySelector('[data-testid="flow-node-title"]') || {}).innerText || null,
    矩形: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    class: n.className }; }));

await keyGuard(p);
await settle(p, R);
out.基线 = { 状态行: await R.status(), 节点数: (await R.ids()).length, testid种类: (await R.testids()).length, 选中: await R.selCount() };
out.基线ids = await R.ids();
out.基线testids = await R.testids();
log('基线：', JSON.stringify(out.基线));
save();

// ---- 先把 c 轮留下的选中清掉（**落点必须先校验命中 pane**）
const 清点 = await 空白点();
out.清选点 = 清点;
log('清选用的空白点：', JSON.stringify(清点));
save();
if (清点) {
  await p.mouse.click(清点.x, 清点.y);
  await p.waitForTimeout(1500);
  await settle(p, R);
}
out.清理后 = { 选中: await R.selCount(), testid种类: (await R.testids()).length, 状态行: await R.status() };
log('清理后：', JSON.stringify(out.清理后));
save();
断言('残留选中已清掉', out.清理后.选中 === 0, out.清理后);

// ---- 重做「空白处松手」，记下被选中的 id
log('\n=== 空白处松手 ×3，记下被选中的到底是哪一个节点 ===');
out.试验 = [];
for (let k = 0; k < 3; k++) {
  const pt = await 空白点();
  if (!pt) { log('  找不到空白点，停止'); break; }
  // 记下**路径上会经过哪些节点**
  const src = await p.evaluate(() => {
    const arr = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
      const h = n.querySelector('[data-testid="flow-node-source-handle"]'); if (!h) return null;
      const r = h.getBoundingClientRect(); const c = [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
      return c[0] > 4 && c[0] < innerWidth - 4 && c[1] > 4 && c[1] < innerHeight - 4 ? { id: n.getAttribute('data-id'), c, 节点rect: (() => { const q = n.getBoundingClientRect(); return [Math.round(q.x), Math.round(q.y), Math.round(q.right), Math.round(q.bottom)]; })() } : null;
    }).filter(Boolean);
    return arr[0] || null;
  });
  if (!src) { log('  无可用源手柄，停止'); break; }
  // 落点合规复核
  const 合规 = await p.evaluate(([x, y]) => { const h = document.elementFromPoint(x, y);
    const nodes = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getBoundingClientRect());
    return { 命中: h ? h.tagName + '.' + String(h.className || '').split(' ')[0] : null,
      是pane: !!(h && h.classList && h.classList.contains('react-flow__pane')),
      在节点上: nodes.some((r) => x >= r.x && x <= r.right && y >= r.y && y <= r.bottom) }; }, [pt.x, pt.y]);
  if (!合规.是pane || 合规.在节点上) { log(`  第 ${k + 1} 次落点不合规（${JSON.stringify(合规)}）`); continue; }

  await p.mouse.move(src.c[0], src.c[1]); await p.waitForTimeout(250);
  await p.mouse.down(); await p.waitForTimeout(200);
  for (let i = 1; i <= 10; i++) { await p.mouse.move(Math.round(src.c[0] + ((pt.x - src.c[0]) * i) / 10), Math.round(src.c[1] + ((pt.y - src.c[1]) * i) / 10)); await p.waitForTimeout(45); }
  await p.waitForTimeout(400);
  const 拖中 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__connectionline,.react-flow__connection')).length);
  await p.mouse.up(); await p.waitForTimeout(2200); await settle(p, R);
  const 选 = await 选中详情();
  const rec = { 第几次: k + 1, 落点: pt, 落点合规: 合规, 源: src.id, 源节点rect: src.节点rect,
    拖动中有预览层: 拖中 > 0, 松手后选中: 选, 选中数: 选.length,
    选中的是不是源: 选.length === 1 ? 选[0].id === src.id : null,
    边数: (await readConnect(p)).边数, 状态行: await R.status() };
  out.试验.push(rec);
  log(`\n  ── 第 ${k + 1} 次，落点 ${pt.x},${pt.y} ──`);
  log(`     拖动中有预览层：${rec.拖动中有预览层 ? '有' : '无'}`);
  log(`     松手后选中数 ${rec.选中数}｜被选中的是源吗：${rec.选中的是不是源}`);
  log(`     被选中详情：${JSON.stringify(选)}`);
  log(`     边数 ${rec.边数}｜${rec.状态行}`);
  save();
  // 归位：点一个**已校验合规**的空白点
  const 清 = await 空白点();
  if (清) { await p.mouse.click(清.x, 清.y); await p.waitForTimeout(1200); await settle(p, R); }
}
out.结论 = {
  三次里预览层都出现过: out.试验.length ? out.试验.every((r) => r.拖动中有预览层) : null,
  三次都没建边: out.试验.length ? out.试验.every((r) => r.边数 === 0) : null,
  选中数序列: out.试验.map((r) => r.选中数),
  被选中的都是源吗: out.试验.map((r) => r.选中的是不是源),
  被选中的节点标题: out.试验.map((r) => r.松手后选中.map((s) => s.标题)),
};
log('\n  🔑 结论：', JSON.stringify(out.结论, null, 1));
save();

// ---- 收尾
const mm = await R.minimap();
if (mm && mm.ariaPressed !== 'true') {
  const pt = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-display-toggle-minimap"]'); const r = e.getBoundingClientRect();
    for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2) for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) { const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y }; } return null; });
  if (pt) { await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1500); }
}
await settle(p, R);
const ids = await R.ids(), t = await R.testids();
out.收尾 = { 状态行: await R.status(), 边数: (await readConnect(p)).边数, 选中: await R.selCount(), 浮层: await R.overlays(),
  zoom: await R.zoom(), credits: await R.credits(), minimap: await R.minimap(), 节点数: ids.length, testid种类: t.length,
  节点差集: { 多: ids.filter((x) => !out.基线ids.includes(x)), 少: out.基线ids.filter((x) => !ids.includes(x)) },
  testid差集: { 多: t.filter((x) => !out.基线testids.includes(x)), 少: out.基线testids.filter((x) => !t.includes(x)) } };
log('  收尾：', JSON.stringify(out.收尾));
save();
断言('收尾干净：0 边 / 0 选中 / 节点与 testid 均与基线一致', out.收尾.边数 === 0 && out.收尾.选中 === 0
  && out.收尾.节点差集.多.length === 0 && out.收尾.节点差集.少.length === 0
  && out.收尾.testid差集.多.length === 0 && out.收尾.testid差集.少.length === 0, out.收尾);
save(); save();
log('\n✅ d 轮完成 → ./_tmp-b137d.json');
await b.close();
