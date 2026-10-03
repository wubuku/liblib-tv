// 批次 136 · d 轮：**「怎么删掉一条连线」的全部路径** —— 手册完全没有这一节。
//
// 🔑 c 轮已经确认三件事：
//   ① 边有**独立的选中态**：单击边后 `<g data-testid="reference-edge-interaction">` 的
//      `data-state` 从 `default` 翻成 `selected`，而**节点选中数仍是 0**
//      ⇒ 边的选中**不进** `.react-flow__node.selected`；
//   ② **右键边不弹任何菜单**（`[role=menu]` 为 `null`、`[role=menuitem]` **0** 个）
//      ⇒ 与节点不同，边**没有右键菜单**；
//   ③ 唯一已验证的删除路径是 `⌘Z`（焦点守卫通过后按）。
//
// 📌 本轮要找的是：**除了 ⌘Z，还有没有别的路**。具体三问：
//   ① 选中边之后，边周围**新增了哪些 testid**？有没有删除按钮 / 工具条？
//   ② 悬停边时新增的 testid 是什么（c/b 轮出现过 `canvas-node-tag-selector`，一直没归因）？
//   ③ 按 `Delete` / `Backspace` 能不能删？（先过 `keyGuard`；边没有子控件时焦点应在画布上）
//
// 🛡 共享画布纪律：终点是**边数回到 0**。每试一条路径当场读边数；
//   边数不为 0 就换下一条；全试完仍不为 0 才用 `⌘Z` 兜底。
import { writeFileSync } from 'node:fs';
import { openCanvas, readers, settle, keyGuard } from './jimeng-b135-lib.mjs';
import { readConnect, canvasPos } from './jimeng-b136-lib.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'd', 路径: [] };
const save = () => writeFileSync(new URL('./_tmp-b136d.json', import.meta.url), JSON.stringify(out, null, 1));
const 断言 = (名, 条件, 详情) => { const ok = !!!!条件; (out.护栏 = out.护栏 || []).push({ 名, 通过: ok, 详情 });
  log(`  ${ok ? '✅' : '⛔'} 断言·${名}：${JSON.stringify(详情)}`); save(); return ok; };
const 边数 = async () => (await readConnect(p)).边数;

const 全testid = () => R.testids();
const 差集 = async (base) => { const t = await 全testid(); return { 多: t.filter((x) => !base.includes(x)), 少: base.filter((x) => !t.includes(x)) }; };

// ---------------------------------------------------------------- ① 基线
out.start = { 状态行: await R.status(), zoom: await R.zoom() };
log('起点：', JSON.stringify(out.start));
await keyGuard(p);
await settle(p, R);
out.基线 = { 状态行: await R.status(), 节点数: (await R.ids()).length, testid种类: (await 全testid()).length };
out.基线ids = await R.ids();
out.基线testids = await 全testid();
out.基线canvas = await canvasPos(p);
log('基线：', JSON.stringify(out.基线));
save();
断言('起点边数 0', (await 边数()) === 0, {});

// ---------------------------------------------------------------- ② 建边
log('\n=== ② 建一条边 ===');
const plan = await p.evaluate(() => {
  const nodes = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
    const r = n.getBoundingClientRect();
    const h = n.querySelector('[data-testid="flow-node-source-handle"]');
    const hr = h ? h.getBoundingClientRect() : null;
    return { id: n.getAttribute('data-id'), 标题: (n.querySelector('[data-testid="flow-node-title"]') || {}).innerText || null,
      x: r.x, y: r.y, right: r.right, bottom: r.bottom,
      手柄中心: hr ? [Math.round(hr.x + hr.width / 2), Math.round(hr.y + hr.height / 2)] : null };
  });
  const 源 = nodes.find((n) => n.手柄中心 && n.手柄中心[0] > 4 && n.手柄中心[0] < innerWidth - 4 && n.手柄中心[1] > 4 && n.手柄中心[1] < innerHeight - 4);
  if (!源) return { ok: false, 原因: '没有手柄中心在视口内的源' };
  const 落 = nodes.filter((n) => n.id !== 源.id).map((n) => {
    const L = Math.max(n.x, 4), R2 = Math.min(n.right, innerWidth - 4), T = Math.max(n.y, 66), B2 = Math.min(n.bottom, innerHeight - 66);
    const 宽 = R2 - L, 高 = B2 - T;
    if (!(宽 > 20 && 高 > 20)) return null;
    return { id: n.id, 标题: n.标题, 可见面积: 宽 * 高, 落点: [Math.round((L + R2) / 2), Math.round((T + B2) / 2)] };
  }).filter(Boolean).sort((a, b) => b.可见面积 - a.可见面积);
  return { ok: true, 源: { id: 源.id, 标题: 源.标题, 手柄中心: 源.手柄中心 }, 落: 落[0] || null };
});
out.建边计划 = plan;
log('  ', JSON.stringify(plan));
save();
if (!plan.ok || !plan.落) { log('  ⛔ 无法建边'); await b.close(); process.exit(0); }
await p.mouse.move(plan.源.手柄中心[0], plan.源.手柄中心[1]); await p.waitForTimeout(300);
await p.mouse.down(); await p.waitForTimeout(250);
for (let i = 1; i <= 12; i++) {
  await p.mouse.move(Math.round(plan.源.手柄中心[0] + ((plan.落.落点[0] - plan.源.手柄中心[0]) * i) / 12),
                     Math.round(plan.源.手柄中心[1] + ((plan.落.落点[1] - plan.源.手柄中心[1]) * i) / 12));
  await p.waitForTimeout(55);
}
await p.waitForTimeout(500);
await p.mouse.up(); await p.waitForTimeout(2500);
await settle(p, R);
out.建边后 = { 边数: await 边数(), 选中: await R.selCount() };
log('  ', JSON.stringify(out.建边后));
save();
断言('边已建成', (await 边数()) === 1, { 边数: await 边数() });
if ((await 边数()) !== 1) { log('  ⛔ 没建出线'); await b.close(); process.exit(0); }

const 边中点 = await p.evaluate(() => { const e = document.querySelector('.react-flow__edge'); if (!e) return null;
  const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
out.边中点 = 边中点;
log('  边中点', JSON.stringify(边中点));

// ---------------------------------------------------------------- ③ 悬停：多出来的 testid 是什么
log('\n=== ③ 悬停在边上：读 testid 差集（归因 canvas-node-tag-selector） ===');
await p.mouse.move(边中点[0] + 3, 边中点[1]);   // 先挪开，避免直接压在边上
await p.waitForTimeout(1200);
out.未悬停差集 = await 差集(out.基线testids);
await p.mouse.move(边中点[0], 边中点[1]);
await p.waitForTimeout(1500);
out.悬停差集 = await 差集(out.基线testids);
out.悬停元素明细 = await p.evaluate((extra) => extra.map((t) => {
  const els = Array.from(document.querySelectorAll(`[data-testid="${t}"]`));
  return { testid: t, 实例数: els.length, 逐字: els.slice(0, 2).map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 40)),
    rect: els[0] ? (() => { const r = els[0].getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; })() : null,
    class: els[0] ? String(els[0].className || '').slice(0, 80) : null };
}), out.悬停差集.多);
log('  未悬停差集：', JSON.stringify(out.未悬停差集));
log('  悬停差集  ：', JSON.stringify(out.悬停差集.多));
for (const m of out.悬停元素明细) log('    ·', JSON.stringify(m));
save();

// ---------------------------------------------------------------- ④ 单击选中：周围有没有删除按钮
log('\n=== ④ 单击边选中：读选中态的 testid 差集与全部可见按钮 ===');
await p.mouse.click(边中点[0], 边中点[1]);
await p.waitForTimeout(1800);
out.选中态 = { dataState: await p.evaluate(() => { const g = document.querySelector('[data-testid="reference-edge-interaction"]'); return g ? g.getAttribute('data-state') : null; }),
  节点选中: await R.selCount(), 浮层: await R.overlays() };
out.选中差集 = await 差集(out.基线testids);
out.选中态全部testid = await 全testid();
out.选中态可见按钮 = await p.evaluate(() => Array.from(document.querySelectorAll('button,[role=button]')).filter((e) => {
  const r = e.getBoundingClientRect(); const s = getComputedStyle(e);
  return r.width > 1 && r.height > 1 && s.visibility !== 'hidden' && s.display !== 'none' && parseFloat(s.opacity) > 0.05; })
  .map((e) => { const r = e.getBoundingClientRect();
    return { testid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'), 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30),
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; }));
log('  data-state «' + out.选中态.dataState + '»｜节点选中 ' + out.选中态.节点选中 + '｜浮层 ' + out.选中态.浮层);
log('  选中态 testid 增量：', JSON.stringify(out.选中差集.多));
log('  选中态可见按钮 ' + out.选中态可见按钮.length + ' 个，逐字含「删除/移除」的那些：');
const 删类 = out.选中态可见按钮.filter((b) => /删除|移除|拆|断|disconnect|remove|delete/i.test(`${b.aria || ''}${b.逐字 || ''}${b.testid || ''}`));
for (const b of 删类) log('    ·', JSON.stringify(b));
out.删类按钮 = 删类;
log('  （全部按钮 testid 快照）', JSON.stringify(out.选中态可见按钮.map((b) => b.testid || b.aria || b.逐字).slice(0, 40)));
save();

// ---------------------------------------------------------------- ⑤ 逐条试删除路径
log('\n=== ⑤ 逐条试删除路径 ===');
const 试 = async (名, fn) => {
  const 前 = await 边数();
  const g0 = await 边数();
  let 详情 = null;
  try { 详情 = await fn(); } catch (e) { 详情 = { 异常: String(e.message).slice(0, 120) }; }
  await p.waitForTimeout(2000);
  await settle(p, R);
  const 后 = await 边数();
  const rec = { 路径: 名, 前边数: 前, 后边数: 后, 成功: 后 < 前, 详情 };
  out.路径.push(rec);
  log(`  ${后 < 前 ? '🎉' : '⛔'} ${名}：边数 ${前} → ${后}${详情 ? '｜' + JSON.stringify(详情) : ''}`);
  save();
  return 后 < 前;
};

for (const key of ['Delete', 'Backspace']) {
  if ((await 边数()) === 0) break;
  const g = await keyGuard(p);
  await 试(`按 ${key} 键`, async () => { if (!g.safe) return { 跳过: g.reason }; await p.keyboard.press(key); return { 焦点: g.where }; });
}
if ((await 边数()) > 0 && 删类.length) {
  const t = 删类[0];
  await 试(`点选中态边旁的「${t.aria || t.逐字 || t.testid}」按钮`, async () => { await p.mouse.click(t.rect[0] + t.rect[2] / 2, t.rect[1] + t.rect[3] / 2); return { 按钮: t }; });
}
if ((await 边数()) > 0) {
  const g = await keyGuard(p);
  await 试('兜底 ⌘Z', async () => { if (!g.safe) return { 跳过: g.reason }; await p.keyboard.press('Meta+z'); return { 焦点: g.where }; });
}
out.最终边数 = await 边数();
log('\n  最终边数 =', out.最终边数);
save();
断言('边数回到 0', (await 边数()) === 0, { 边数: await 边数() });

// ---------------------------------------------------------------- ⑥ 收尾
log('\n=== ⑥ 收尾 ===');
const endCanvas = await canvasPos(p);
const 移动 = Object.keys(out.基线canvas).filter((id) => JSON.stringify(out.基线canvas[id]) !== JSON.stringify(endCanvas[id]));
const ids = await R.ids(), t = await 全testid();
out.收尾 = { 状态行: await R.status(), 选中: await R.selCount(), 浮层: await R.overlays(), zoom: await R.zoom(),
  credits: await R.credits(), minimap: await R.minimap(), 节点数: ids.length, testid种类: t.length, 节点被移动: 移动,
  节点差集: { 多: ids.filter((x) => !out.基线ids.includes(x)), 少: out.基线ids.filter((x) => !ids.includes(x)) },
  testid差集: { 多: t.filter((x) => !out.基线testids.includes(x)), 少: out.基线testids.filter((x) => !t.includes(x)) } };
log('  ', JSON.stringify(out.收尾));
save();
断言('节点 canvas 坐标零位移', 移动.length === 0, { 移动 });
断言('节点 id 与基线逐个一致', out.收尾.节点差集.多.length === 0 && out.收尾.节点差集.少.length === 0, out.收尾.节点差集);
断言('静态 testid 与基线逐个一致', out.收尾.testid差集.多.length === 0 && out.收尾.testid差集.少.length === 0, out.收尾.testid差集);
save(); save();
log('\n✅ d 轮完成 → ./_tmp-b136d.json');
await b.close();
