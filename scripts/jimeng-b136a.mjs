// 批次 136 · a 轮：**拖拽建线的半程取证** —— 按下 → 拖动 → 读预览层 → **松在空白处取消**。
//
// 🔑 靶子：`10-tasks/connect-nodes.md:104` 记着上一次拖拽的结局 ——
//   「拖完**源节点变成选中态**（`1 selected`），但**节点自身没有被拖走**（canvas 位移 `[0,0]`），
//   **也没有建出连线**」。一次都没成功过，而这是整页文档的核心动作。
//
// 🛡 共享画布纪律：**不建边**。建边会留下撤不干净就永久污染别人画布的产物。
//   本轮只走半程，末步**松在空白的 pane 上**取消 —— 零副作用，
//   而这恰好能回答真正的问题：**到底有没有起拖**（有没有预览层、有没有候选高亮）。
//
// 📌 手册已定前提（批次 91，本轮逐条现算并断言，不靠记忆）：
//   ① **不先选中**（选中时手柄左右中点被 ⊕ 接管）
//   ② **手柄元素本体的 pe 永远是 `none`**，`auto` 在 `::before` 上 ⇒ 必须读伪元素
import { writeFileSync } from 'node:fs';
import { openCanvas, readers, settle, keyGuard } from './jimeng-b135-lib.mjs';
import { readConnect, findEmptyPane, canvasPos } from './jimeng-b136-lib.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'a', 检查点: [] };
const save = () => writeFileSync(new URL('./_tmp-b136a.json', import.meta.url), JSON.stringify(out, null, 1));
const 断言 = (名, 条件, 详情) => { const ok = !!!!条件; (out.护栏 = out.护栏 || []).push({ 名, 通过: ok, 详情 });
  log(`  ${ok ? '✅' : '⛔'} 断言·${名}：${JSON.stringify(详情)}`); save(); return ok; };

// ---------------------------------------------------------------- ① 基线
out.start = { 状态行: await R.status(), zoom: await R.zoom(), minimap: await R.minimap() };
log('起点：', JSON.stringify(out.start));
await keyGuard(p);
await settle(p, R);
out.基线 = { 状态行: await R.status(), 节点数: (await R.ids()).length, testid种类: (await R.testids()).length };
out.基线ids = await R.ids();
out.基线testids = await R.testids();
out.基线canvas = await canvasPos(p);
log('基线：', JSON.stringify(out.基线));
save();
断言('起点 0 选中', (await R.selCount()) === 0, { sel: await R.selCount() });

// ---------------------------------------------------------------- ② 找一个视口内、带 source 手柄、且手柄中心没被 ⊕ 占用的节点
log('\n=== ② 挑源节点：视口内 + 有 source 手柄 + 手柄中心命中的是手柄本身 ===');
const pick = await p.evaluate(() => {
  const nodes = Array.from(document.querySelectorAll('.react-flow__node'));
  const 候选 = [];
  for (const n of nodes) {
    const r = n.getBoundingClientRect();
    if (r.right < 40 || r.x > innerWidth - 40 || r.bottom < 70 || r.y > innerHeight - 70) continue;
    const h = n.querySelector('[data-testid="flow-node-source-handle"]');
    if (!h) continue;
    const hr = h.getBoundingClientRect();
    const cx = Math.round(hr.x + hr.width / 2), cy = Math.round(hr.y + hr.height / 2);
    const hit = document.elementFromPoint(cx, cy);
    候选.push({ id: n.getAttribute('data-id'), 标题: (n.querySelector('[data-testid="flow-node-title"]') || {}).innerText || null,
      节点rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      手柄rect: [Math.round(hr.x), Math.round(hr.y), Math.round(hr.width), Math.round(hr.height)],
      手柄中心: [cx, cy], 中心命中: hit ? hit.tagName + '.' + String(hit.className || '').split(' ')[0] : null,
      中心命中testid: hit ? hit.getAttribute('data-testid') : null });
  }
  return 候选;
});
out.候选源节点 = pick;
log('  候选数', pick.length);
for (const c of pick.slice(0, 6)) log('   ', JSON.stringify(c));
save();
const 好 = pick.find((c) => c.中心命中testid === 'flow-node-source-handle');
断言('存在「手柄中心命中 source 手柄本身」的候选（未被 ⊕ 占用）', !!好, { 候选数: pick.length, 命中testid样本: pick.slice(0, 3).map((c) => c.中心命中testid) });
if (!好) { log('  ⛔ 没有合格候选，本轮到此为止'); await b.close(); process.exit(0); }
const SRC = 好;
log('  选中源节点：', JSON.stringify(SRC));

// ---------------------------------------------------------------- ③ 拖前读数：确认 ::before 的 pe
log('\n=== ③ 拖前读数（手册批次 91 的两条前提现算） ===');
const pre = await readConnect(p);
out.拖前 = pre;
log('  source 手柄总数', pre.source手柄总数, '｜target 手柄总数', pre.target手柄总数, '｜⊕ 按钮数', pre.加号按钮数, '（应为 0：未选中）');
log('  source 手柄本体 pe =', pre.source手柄 && pre.source手柄.本体pe);
log('  source 手柄 ::before =', JSON.stringify(pre.source手柄 && pre.source手柄.before));
log('  source 手柄 ::after  =', JSON.stringify(pre.source手柄 && pre.source手柄.after));
log('  边数', pre.边数, '｜线预览层', pre.线预览层.length, '｜选中', JSON.stringify(pre.选中));
save();
断言('未选中时 ⊕ 按钮数为 0（起手点不会被 ⊕ 吃掉）', pre.加号按钮数 === 0, { 加号: pre.加号按钮数 });
断言('手柄本体 pe 是 none', pre.source手柄 && pre.source手柄.本体pe === 'none', { pe: pre.source手柄 && pre.source手柄.本体pe });
断言('手柄 ::before 的 pe 是 auto（真热区在伪元素上）', pre.source手柄 && pre.source手柄.before && pre.source手柄.before.pe === 'auto',
  { before: pre.source手柄 && pre.source手柄.before });

// ---------------------------------------------------------------- ④ 找一个目标节点当落点（另一个节点，任意类型，只读不改）
const 目标 = await p.evaluate(() => {
  const nodes = Array.from(document.querySelectorAll('.react-flow__node'));
  const c = nodes.map((n) => { const r = n.getBoundingClientRect();
    return { id: n.getAttribute('data-id'), 标题: (n.querySelector('[data-testid="flow-node-title"]') || {}).innerText || null,
      cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2), w: Math.round(r.width), h: Math.round(r.height),
      在视口内: r.right > 0 && r.x < innerWidth && r.bottom > 60 && r.y < innerHeight - 60 }; })
    .filter((x) => x.在视口内 && x.w > 40);
  return c;
});
out.候选落点 = 目标;
log('\n  候选落点数', 目标.length, '（样例', JSON.stringify(目标.slice(0, 3)), '）');
save();
const TGT = 目标.find((t) => t.id !== SRC.id);
if (!TGT) { log('  ⛔ 没有第二个可作落点的节点'); await b.close(); process.exit(0); }
log('  目标落点：', JSON.stringify(TGT));
const cancel = await findEmptyPane(p);
out.取消落点 = cancel;
log('  取消落点（空白 pane）：', JSON.stringify(cancel));
save();
if (!cancel) { log('  ⛔ 找不到空白取消落点'); await b.close(); process.exit(0); }

// ---------------------------------------------------------------- ⑤ 半程拖拽
log('\n=== ⑤ 按下 → 分步拖动 → 三个检查点读数 → 松在空白处取消 ===');
const snap = async (tag) => {
  const s = await readConnect(p);
  const 多 = s.testid.filter((x) => !out.基线testids.includes(x));
  const 少 = out.基线testids.filter((x) => !s.testid.includes(x));
  const rec = { tag, 边数: s.边数, 线预览层: s.线预览层, 节点class标记: s.节点class标记, 选中: s.选中,
    加号按钮数: s.加号按钮数, testid增量: 多, testid减量: 少 };
  out.检查点.push(rec);
  log(`\n  ── ${tag} ──`);
  log(`     边数 ${rec.边数}｜线预览层 ${rec.线预览层.length} 个 ${JSON.stringify(rec.线预览层)}`);
  log(`     节点 class 标记 ${JSON.stringify(rec.节点class标记)}｜选中 ${JSON.stringify(rec.选中)}｜⊕ ${rec.加号按钮数}`);
  log(`     testid 增量 ${JSON.stringify(多)}｜减量 ${JSON.stringify(少)}`);
  save();
  return rec;
};

await p.mouse.move(SRC.手柄中心[0], SRC.手柄中心[1]);
await p.waitForTimeout(400);
const hitAtDown = await p.evaluate(([x, y]) => { const h = document.elementFromPoint(x, y); return h ? h.tagName + '.' + String(h.className || '').split(' ')[0] + ' tid=' + h.getAttribute('data-testid') : null; }, SRC.手柄中心);
out.按下点命中 = hitAtDown;
log('  按下点命中：', hitAtDown);
await snap('按下前');

await p.mouse.down();
await p.waitForTimeout(300);
await snap('mousedown 后（未移动）');

// 分步拖到目标节点，中途取一个中间检查点
const 路径 = [];
for (let i = 1; i <= 10; i++) {
  const x = Math.round(SRC.手柄中心[0] + ((TGT.cx - SRC.手柄中心[0]) * i) / 10);
  const y = Math.round(SRC.手柄中心[1] + ((TGT.cy - SRC.手柄中心[1]) * i) / 10);
  路径.push([x, y]);
  await p.mouse.move(x, y);
  await p.waitForTimeout(60);
  if (i === 5) await snap('拖到一半');
}
await p.waitForTimeout(500);
await snap('悬停在目标节点上');

// ---------------------------------------------------------------- ⑥ 松在空白处取消
log('\n=== ⑥ 移到空白处并松手（取消） ===');
for (let i = 1; i <= 8; i++) {
  await p.mouse.move(Math.round(TGT.cx + ((cancel.x - TGT.cx) * i) / 8), Math.round(TGT.cy + ((cancel.y - TGT.cy) * i) / 8));
  await p.waitForTimeout(50);
}
await snap('移到空白处（仍未松手）');
await p.mouse.up();
await p.waitForTimeout(2000);
await snap('松手后 2s');
await settle(p, R);
await snap('settle 后');

// ---------------------------------------------------------------- ⑦ 零副作用核对
log('\n=== ⑦ 零副作用核对 ===');
const endCanvas = await canvasPos(p);
const 移动 = Object.keys(out.基线canvas).filter((id) => JSON.stringify(out.基线canvas[id]) !== JSON.stringify(endCanvas[id]));
const end = await readConnect(p);
out.副作用 = { 边数: end.边数, 节点被移动: 移动, 节点数: Object.keys(endCanvas).length,
  选中: end.选中, 浮层: await R.overlays(), zoom: await R.zoom(), minimap: await R.minimap() };
log('  ', JSON.stringify(out.副作用));
save();
断言('节点 canvas 坐标零位移', 移动.length === 0, { 移动 });
断言('边数仍为 0（没建出线）', end.边数 === 0, { 边数: end.边数 });
断言('节点数仍为 76', Object.keys(endCanvas).length === 76, { n: Object.keys(endCanvas).length });
save(); save();
log('\n✅ a 轮完成 → ./_tmp-b136a.json');
await b.close();
