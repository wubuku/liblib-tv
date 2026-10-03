// 批次 136 · h 轮：**不插入任何中间点击**地把「点 × 能删」重验一遍。
//
// 🔴 g 轮抓到了**我自己实验设计的缺陷**：两个对照实验**串行**执行，
//   实验 A（点按钮外的点）把边**取消选中**了（`data-state` 从 `selected` 回 `default`），
//   **删除按钮随之消失** ⇒ 实验 B 点「热区中心」时按的其实是**空地**。
//   ⇒ 「点按钮角删不掉」这条**不成立** —— 它测的是「按钮已经不在了」。
//   📌 **立规：串行对照实验必须检查「前一步的副作用有没有把后一步的前置条件抽走」**；
//     「点 A 处无效」有三种可能：A 处不可点 / 目标已消失 / 状态已变 ——
//     **每次点之前都要重新断言前置条件**（这是批次 132「前置条件每轮现算并断言」的加强版：
//     不只是「每轮」，而是「每一次点击前」）。
//
// 📌 本轮序列**只有三步、零中间点击**：
//   建边 → 单击边中点（选中）→ **立刻**点 × 的中心 → 读边数。
//   e 轮其实也是这个序列，但中间夹了几次 `evaluate` 读数；本轮把读数全部挪到点击**之后**，
//   彻底排除「读数动作改变了状态」的可能。
import { writeFileSync } from 'node:fs';
import { openCanvas, readers, settle, keyGuard } from './jimeng-b135-lib.mjs';
import { readConnect, canvasPos } from './jimeng-b136-lib.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'h', 序列: [] };
const save = () => writeFileSync(new URL('./_tmp-b136h.json', import.meta.url), JSON.stringify(out, null, 1));
const 断言 = (名, 条件, 详情) => { const ok = !!!!条件; (out.护栏 = out.护栏 || []).push({ 名, 通过: ok, 详情 });
  log(`  ${ok ? '✅' : '⛔'} 断言·${名}：${JSON.stringify(详情)}`); save(); return ok; };
const 边数 = async () => (await readConnect(p)).边数;
const 态 = () => p.evaluate(() => { const g = document.querySelector('[data-testid="reference-edge-interaction"]'); return g ? g.getAttribute('data-state') : null; });
process.on('uncaughtException', async (e) => {
  console.error('💥 未捕获异常：', e && e.message);
  try { if ((await 边数()) > 0) { const g = await keyGuard(p); if (g.safe) { await p.keyboard.press('Meta+z'); await p.waitForTimeout(2000); } } } catch (_) {}
  await b.close(); process.exit(4);
});

await keyGuard(p);
await settle(p, R);
out.基线 = { 状态行: await R.status(), 节点数: (await R.ids()).length, testid种类: (await R.testids()).length };
out.基线ids = await R.ids();
out.基线testids = await R.testids();
out.基线canvas = await canvasPos(p);
log('基线：', JSON.stringify(out.基线));
save();
if ((await 边数()) !== 0) { console.error('⛔ 起点有残留边 —— 中止'); await b.close(); process.exit(3); }

const 步 = async (名, fn) => { const 前 = await 边数(); const r = await fn(); const 后 = await 边数();
  out.序列.push({ 步: 名, 前边数: 前, 后边数: 后 }); log(`  ${名}：边数 ${前} → ${后}${r ? '｜' + JSON.stringify(r) : ''}`); save(); return { 前, 后, r }; };

// ---- ① 建边（拖拽）
const plan = await p.evaluate(() => {
  const nodes = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
    const r = n.getBoundingClientRect();
    const h = n.querySelector('[data-testid="flow-node-source-handle"]');
    const hr = h ? h.getBoundingClientRect() : null;
    return { id: n.getAttribute('data-id'), x: r.x, y: r.y, right: r.right, bottom: r.bottom,
      手柄中心: hr ? [Math.round(hr.x + hr.width / 2), Math.round(hr.y + hr.height / 2)] : null };
  });
  const 源 = nodes.find((n) => n.手柄中心 && n.手柄中心[0] > 4 && n.手柄中心[0] < innerWidth - 4 && n.手柄中心[1] > 4 && n.手柄中心[1] < innerHeight - 4);
  if (!源) return null;
  const 落 = nodes.filter((n) => n.id !== 源.id).map((n) => {
    const L = Math.max(n.x, 4), R2 = Math.min(n.right, innerWidth - 4), T = Math.max(n.y, 66), B2 = Math.min(n.bottom, innerHeight - 66);
    const 宽 = R2 - L, 高 = B2 - T; if (!(宽 > 20 && 高 > 20)) return null;
    return { id: n.id, 面积: 宽 * 高, 落点: [Math.round((L + R2) / 2), Math.round((T + B2) / 2)] };
  }).filter(Boolean).sort((a, b) => b.面积 - a.面积);
  return { 源, 落: 落[0] || null };
});
out.计划 = plan;
await 步('① 从未选中节点的 source 热区拖到目标节点并松手', async () => {
  await p.mouse.move(plan.源.手柄中心[0], plan.源.手柄中心[1]); await p.waitForTimeout(300);
  await p.mouse.down(); await p.waitForTimeout(250);
  for (let i = 1; i <= 12; i++) {
    await p.mouse.move(Math.round(plan.源.手柄中心[0] + ((plan.落.落点[0] - plan.源.手柄中心[0]) * i) / 12),
                       Math.round(plan.源.手柄中心[1] + ((plan.落.落点[1] - plan.源.手柄中心[1]) * i) / 12));
    await p.waitForTimeout(55);
  }
  await p.waitForTimeout(500); await p.mouse.up(); await p.waitForTimeout(2500); await settle(p, R);
  return { 落点: plan.落.落点, 落点节点: plan.落.id };
});
断言('① 边已建成', (await 边数()) === 1, { 边数: await 边数() });
if ((await 边数()) !== 1) { log('⛔ 没建出线'); await b.close(); process.exit(0); }

// ---- ② 单击边中点（只读一次 data-state，然后立刻去点 ×）
const 边中点 = await p.evaluate(() => { const e = document.querySelector('.react-flow__edge'); const r = e.getBoundingClientRect();
  return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
out.边中点 = 边中点;
await p.mouse.click(边中点[0], 边中点[1]);
await p.waitForTimeout(1500);
out.选中态 = await 态();
log('  ② 单击边后 data-state «' + out.选中态 + '»');
断言('② 边被选中（data-state = selected）', out.选中态 === 'selected', { dataState: out.选中态 });

// ---- ③ 读 × 的坐标（只是一次读，不点）→ 立刻点它
const B = await p.evaluate(() => { const btn = document.querySelector('[data-testid="reference-edge-delete-control"]');
  if (!btn) return null; const r = btn.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
out.删除钮中心 = B;
log('  ③ 删除钮中心', JSON.stringify(B));
断言('③ × 按钮存在', !!B, { 删除钮中心: B });
// 🔑 点之前**重新断言前置条件**：按钮还在吗？边还选中吗？
out.点前复查 = await p.evaluate(() => {
  const btn = document.querySelector('[data-testid="reference-edge-delete-control"]');
  const g = document.querySelector('[data-testid="reference-edge-interaction"]');
  return { 按钮还在: !!btn, dataState: g ? g.getAttribute('data-state') : null };
});
log('  点删除钮之前复查：', JSON.stringify(out.点前复查));
断言('点 × 之前按钮仍在且边仍选中', out.点前复查.按钮还在 && out.点前复查.dataState === 'selected', out.点前复查);

await p.mouse.click(B[0], B[1]);
await p.waitForTimeout(2500);
await settle(p, R);
out.点后边数 = await 边数();
out.点后态 = await 态();
log('  ④ 点删除钮后：边数', out.点后边数, '｜data-state', out.点后态);
save();
断言('④ 点 删除钮中心后边被删掉', (await 边数()) === 0, { 边数: await 边数() });

// ---- ⑤ 收尾
if ((await 边数()) > 0) { const g = await keyGuard(p); if (g.safe) { await p.keyboard.press('Meta+z'); await p.waitForTimeout(2200); await settle(p, R); } }
const endCanvas = await canvasPos(p);
const 移动 = Object.keys(out.基线canvas).filter((id) => JSON.stringify(out.基线canvas[id]) !== JSON.stringify(endCanvas[id]));
const ids = await R.ids(), t = await R.testids();
out.收尾 = { 状态行: await R.status(), 选中: await R.selCount(), 浮层: await R.overlays(), zoom: await R.zoom(),
  credits: await R.credits(), minimap: await R.minimap(), 节点数: ids.length, testid种类: t.length, 边数: await 边数(), 节点被移动: 移动,
  节点差集: { 多: ids.filter((x) => !out.基线ids.includes(x)), 少: out.基线ids.filter((x) => !ids.includes(x)) },
  testid差集: { 多: t.filter((x) => !out.基线testids.includes(x)), 少: out.基线testids.filter((x) => !t.includes(x)) } };
log('  ', JSON.stringify(out.收尾));
save();
断言('边数 0、节点零位移、与基线逐个一致',
  (await 边数()) === 0 && 移动.length === 0
  && out.收尾.节点差集.多.length === 0 && out.收尾.节点差集.少.length === 0
  && out.收尾.testid差集.多.length === 0 && out.收尾.testid差集.少.length === 0, out.收尾);
save(); save();
log('\n✅ h 轮完成 → ./_tmp-b136h.json');
await b.close();
