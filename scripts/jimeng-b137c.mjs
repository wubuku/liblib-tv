// 批次 137 · c 轮：两件收尾的事 —— ①**音频面板按钮数 9 vs 10** 的差异；②重验「空白处松手」。
//
// 🔴 ① **本批撞出一处待查差异**：批次 131 记「单选 1 个音频节点 ⇒ 10 个按钮」，逐字列了
//   展开音频生成器 40×40 / 添加参考 48×48 / 引用参考 24×24 / 创作类型 80×32 /
//   选择模型 135×32 / 音频生成 80×32 / 音色库 68×32 / 引用参考 32×32 /
//   显示折扣详情 46×20 / 生成 32×32；
//   而本批 b 轮在**刚新建的空音频节点**上只读到 **9 个**，**少的正是「展开音频生成器 `40×40`」**。
//   🔑 两个样本的差别是「**画布上已有的**节点」vs「**刚新建的**节点」。
//   ⇒ 本轮**不改批次 131 的结论**，而是把两种样本各读一遍，看差异是否真的由「新建 vs 已有」引起。
//   📌 这正是批次 134 立过的规的镜像：**要推翻一条结论前先确认它当初的适用范围** ——
//     这次不是推翻，而是**两个适用范围各说各的**。
//
// ⚠️ ② 批次 136 明确留了一个未决观测：`:104` 记「拖到空白处松手 → 源节点变选中」，
//   而批次 136 在 `(8,660)` 没复现。本轮用**三个不同空白落点**各做一次，
//   看「源节点是否变选中」是一般规律还是落点相关。
//   **不建边**（松在空白处本就不建边），所以本轮没有需要归位的产物。
import { writeFileSync } from 'node:fs';
import { openCanvas, readers, settle, keyGuard } from './jimeng-b135-lib.mjs';
import { readConnect } from './jimeng-b136-lib.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'c' };
const save = () => writeFileSync(new URL('./_tmp-b137c.json', import.meta.url), JSON.stringify(out, null, 1));
const 断言 = (名, 条件, 详情) => { const ok = !!!!条件; (out.护栏 = out.护栏 || []).push({ 名, 通过: ok, 详情 });
  log(`  ${ok ? '✅' : '⛔'} 断言·${名}：${JSON.stringify(详情).slice(0, 260)}`); save(); return ok; };

await keyGuard(p);
await settle(p, R);
out.基线 = { 状态行: await R.status(), 节点数: (await R.ids()).length, testid种类: (await R.testids()).length };
out.基线ids = await R.ids();
out.基线testids = await R.testids();
log('基线：', JSON.stringify(out.基线));
save();
断言('起点 0 选中、0 边', (await R.selCount()) === 0 && (await readConnect(p)).边数 === 0, { 边数: (await readConnect(p)).边数 });

// ---------------------------------------------------------------- ① 两种音频节点的按钮数
log('\n=== ① 音频面板按钮数：画布上「已有」的节点 vs b 轮「新建」的节点 ===');
const 读面板 = () => p.evaluate(() => {
  const box = (e) => { if (!e) return null; const r = e.getBoundingClientRect(); return [Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10]; };
  const f = document.querySelector('[data-testid="audio-generation-form"]');
  const n = document.querySelector('.react-flow__node.selected');
  return { 面板存在: !!f, 面板矩形: box(f), 面板逐字: f ? (f.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 60) : null,
    按钮: f ? Array.from(f.querySelectorAll('button,[role=button]')).map((b) => ({ 逐字: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 24), aria: b.getAttribute('aria-label'), 尺寸: box(b) })) : [],
    选中节点: n ? { id: n.getAttribute('data-id'), 标题: (n.querySelector('[data-testid="flow-node-title"]') || {}).innerText || null, class: n.className, 有无内容: !!n.querySelector('audio, video, img, canvas') } : null,
    全部form: Array.from(new Set(Array.from(document.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')).filter((t) => /form/i.test(t)))) };
});
out.b轮新建节点的按钮 = JSON.parse((await (await import('node:fs')).promises.readFile('./scripts/_tmp-b137b.json', 'utf8'))).本轮.取证.各档[0].快照.generationForm族[0].按钮;
log('  b 轮（新建节点）按钮数', out.b轮新建节点的按钮.length, '：', JSON.stringify(out.b轮新建节点的按钮.map((b) => b.aria || b.逐字)));

// 选一个画布上**已有**的音频节点
const 候选 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node'))
  .filter((n) => n.classList.contains('react-flow__node-audio'))
  .map((n) => { const r = n.getBoundingClientRect();
    const L = Math.max(r.x, 4), R2 = Math.min(r.right, innerWidth - 4), T = Math.max(r.y, 66), B2 = Math.min(r.bottom, innerHeight - 66);
    const 宽 = R2 - L, 高 = B2 - T; if (!(宽 > 30 && 高 > 30)) return null;
    return { id: n.getAttribute('data-id'), 标题: (n.querySelector('[data-testid="flow-node-title"]') || {}).innerText || null,
      可见面积: 宽 * 高, 落点: [Math.round((L + R2) / 2), Math.round((T + B2) / 2)] }; })
  .filter(Boolean).sort((a, b) => b.可见面积 - a.可见面积));
out.已有音频节点候选 = 候选.slice(0, 3);
log('  已有音频节点候选：', JSON.stringify(候选.slice(0, 3)));
save();
const 已有 = 候选[0];
if (已有) {
  // 📌 落点先校验**不是 button / [role=button]**（本册硬规矩：单选态面板里就带着「生成」）
  const 命中 = await p.evaluate(([x, y]) => { const h = document.elementFromPoint(x, y);
    return h ? { tag: h.tagName, testid: h.getAttribute('data-testid'), aria: h.getAttribute('aria-label'),
      是按钮: h.tagName === 'BUTTON' || h.getAttribute('role') === 'button' } : null; }, 已有.落点);
  out.已有节点落点命中 = 命中;
  log('  落点命中：', JSON.stringify(命中));
  断言('落点不是 button（不碰「生成」）', 命中 && !命中.是按钮, 命中);
  await p.mouse.click(已有.落点[0], 已有.落点[1]);
  await p.waitForTimeout(2000);
  await settle(p, R);
  out.已有节点面板 = await 读面板();
  log('  已有节点面板：', JSON.stringify(out.已有节点面板.选中节点), '｜面板', JSON.stringify(out.已有节点面板.面板矩形));
  log('  按钮数', out.已有节点面板.按钮.length, '：', JSON.stringify(out.已有节点面板.按钮.map((b) => b.aria || b.逐字)));
  log('  全部 form testid：', JSON.stringify(out.已有节点面板.全部form));
  save();
  out.按钮数对比 = { b轮新建: out.b轮新建节点的按钮.length, 已有节点: out.已有节点面板.按钮.length,
    差: out.b轮新建节点的按钮.map((b) => b.aria || b.逐字).filter((a) => !out.已有节点面板.按钮.some((c) => (c.aria || c.逐字) === a)),
    反向差: out.已有节点面板.按钮.map((b) => b.aria || b.逐字).filter((a) => !out.b轮新建节点的按钮.some((c) => (c.aria || c.逐字) === a)) };
  log('\n  🔑 对比：', JSON.stringify(out.按钮数对比, null, 1));
  save();
  // 取消选中
  await p.mouse.move(640, 700); await p.mouse.click(640, 700); await p.waitForTimeout(1200); await settle(p, R);
}

// ---------------------------------------------------------------- ② 空白处松手，三个落点
log('\n=== ② 空白处松手：三个不同落点各做一次（不建边，无产物需归位） ===');
out.空白松手 = [];
for (const pt of [[8, 660], [640, 700], [900, 120]]) {
  const 合规 = await p.evaluate(([x, y]) => { const h = document.elementFromPoint(x, y);
    const nodes = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getBoundingClientRect());
    const 在节点上 = nodes.some((r) => x >= r.x && x <= r.right && y >= r.y && y <= r.bottom);
    return { 命中: h ? h.tagName + '.' + String(h.className || '').split(' ')[0] : null, 是pane: !!(h && h.classList && h.classList.contains('react-flow__pane')), 在节点上 }; }, pt);
  if (!合规.是pane || 合规.在节点上) { log(`  落点 ${JSON.stringify(pt)} 不合规（${JSON.stringify(合规)}），跳过`); continue; }
  // 起手：未选中节点的 source 热区
  const src = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
    const h = n.querySelector('[data-testid="flow-node-source-handle"]'); if (!h) return null;
    const r = h.getBoundingClientRect(); const c = [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
    return c[0] > 4 && c[0] < innerWidth - 4 && c[1] > 4 && c[1] < innerHeight - 4 ? { id: n.getAttribute('data-id'), c } : null;
  }).filter(Boolean)[0]);
  if (!src) { log('  找不到可用源手柄，跳过'); continue; }
  const 前选中 = await R.selCount();
  await p.mouse.move(src.c[0], src.c[1]); await p.waitForTimeout(250);
  await p.mouse.down(); await p.waitForTimeout(200);
  for (let i = 1; i <= 10; i++) { await p.mouse.move(Math.round(src.c[0] + ((pt[0] - src.c[0]) * i) / 10), Math.round(src.c[1] + ((pt[1] - src.c[1]) * i) / 10)); await p.waitForTimeout(45); }
  await p.waitForTimeout(400);
  const 拖中 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__connectionline,.react-flow__connection')).length);
  await p.mouse.up(); await p.waitForTimeout(2200); await settle(p, R);
  const rec = { 落点: pt, 落点合规: 合规, 源: src.id, 拖动中有预览层: 拖中 > 0,
    松手后选中节点数: await R.selCount(), 源是否被选中: await p.evaluate((id) => { const n = document.querySelector('.react-flow__node[data-id="' + id + '"]'); return !!(n && n.classList.contains('selected')); }, src.id),
    边数: (await readConnect(p)).边数, 状态行: await R.status(),
    松手后浮层: await p.evaluate(() => Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox]')).filter((m) => m.getBoundingClientRect().width > 1).map((m) => m.getAttribute('data-testid') || m.getAttribute('aria-label'))) };
  out.空白松手.push(rec);
  log(`  落点 ${JSON.stringify(pt)}：预览层 ${rec.拖动中有预览层 ? '有' : '无'}｜松手后选中 ${rec.松手后选中节点数}（源被选中：${rec.源是否被选中}）｜边数 ${rec.边数}｜浮层 ${JSON.stringify(rec.松手后浮层)}`);
  save();
  // 取消可能出现的选中
  await p.mouse.move(640, 700); await p.mouse.click(640, 700); await p.waitForTimeout(1000); await settle(p, R);
}
out.结论_空白松手是否让源节点变选中 = out.空白松手.map((r) => r.源是否被选中);
log('\n  🔑 三个落点的「源是否被选中」：', JSON.stringify(out.结论_空白松手是否让源节点变选中));
save();

// ---------------------------------------------------------------- 收尾
log('\n=== 收尾 ===');
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
log('  ', JSON.stringify(out.收尾));
save();
断言('边数 0、节点 76、testid 与基线一致', out.收尾.边数 === 0 && out.收尾.节点数 === 76
  && out.收尾.节点差集.多.length === 0 && out.收尾.节点差集.少.length === 0
  && out.收尾.testid差集.多.length === 0 && out.收尾.testid差集.少.length === 0, out.收尾);
save(); save();
log('\n✅ c 轮完成 → ./_tmp-b137c.json');
await b.close();
