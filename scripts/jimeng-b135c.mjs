// 批次 135 · c 轮：**受控第二臂 —— 锁定缩放 60%，只改选中集（剂量-反应）。**
//
// 🔑 第一臂（b 轮）已经把「外层 `node-toolbar` 屏上宽度 = 1000 × scale」钉死。
//   剩下的问题只有一个：**那个 1000（canvas 宽）是什么决定的？**
//   两个候选：① 固定常量；② **选中集包围盒的 canvas 宽度**。
//   判法：锁死 60%，依次框选 2 / 3 / 4 / 6 个节点，看外层宽度怎么变。
//
// 🔴 b 轮自身失误（如实记）：`scale` 读成 `null` —— viewport 的 transform 是
//   `translate(x, y) scale(s)` 形态，我只写了 `matrix(...)` 正则。
//   连锁后果：换算表那一列全变成 0，还「算出」一个假的「四档恒定」。
//   ⇒ 立规（批次 129/130/131 同族第 4 次）：**读数异常先怀疑自己的读数**，
//     而且**派生量要单独断言非空**（「scale 不是 null」）再让它进表。
//
// 🆕 本轮附带一个结构性读数：多选条的**祖先链**。
//   `.react-flow__renderer` 是 `.react-flow__viewport` 的父级，所以
//   「父级是 renderer」= **不在**画布坐标系（生成面板，手册 §3.82 记的正是它），
//   「祖先里有 viewport」= **在**画布坐标系（会被 scale 乘上）。
//   ⇒ 若多选条在 viewport 内，批次 131「工具条不在画布坐标系里」就只对生成面板成立。
import { writeFileSync } from 'node:fs';
import { openCanvas, readers, settle, scanBox, doBox, readMultiToolbar, readNodeHandles, keyGuard } from './jimeng-b135-lib.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'c', 剂量: [] };
const save = () => writeFileSync(new URL('./_tmp-b135c.json', import.meta.url), JSON.stringify(out, null, 1));
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
log('基线：', JSON.stringify(out.基线), 'zoom «' + (await R.zoom()) + '»');
save();

// ---------------------------------------------------------------- ② 对照：每节点手柄 vs 多选手柄
log('\n=== ② 对照读数：每节点连接手柄（未选中态）vs 多选手柄 ===');
out.每节点手柄 = await readNodeHandles(p);
log('  flow-node-target-handle ', JSON.stringify(out.每节点手柄.target));
log('  flow-node-source-handle ', JSON.stringify(out.每节点手柄.source));
log('  🔑 60% 下每节点手柄是屏上 36×72（canvas 恒 60×120），而 b 轮多选手柄四档都是 60×120');
save();

// ---------------------------------------------------------------- ③ 剂量-反应
log('\n=== ③ 受控第二臂：锁定 60%，依次框选 2 / 3 / 4 / 6 个 ===');
// 🔴 c 轮第一版逐个问 planBoxExact(K) 全部失败；先**一次性扫出所有可达的 K**，
//   再挑其中 3 个做实测 —— 别在「构造性搜索」上反复碰壁。
const 扫描 = await scanBox(p);
out.可达K扫描 = 扫描;
log('  可达 K：', JSON.stringify(扫描.可达K));
save();
const 选定K = 扫描.可达K.filter((k) => k >= 2).slice(0, 3);
if (选定K.length < 2) { log('  ⛔ 可达 K 不足两个，本臂做不了'); await b.close(); process.exit(0); }
for (const K of 选定K) {
  await settle(p, R);
  const plan = { ok: true, 矩形: 扫描.矩形表[String(K)] };
  const hit = await doBox(p, plan.矩形);
  const m = await readMultiToolbar(p);
  const rec = { K, 矩形: plan.矩形, 按下点: hit, 实际选中: m.选中集.length,
    scale: m.scale, 包围盒canvas: m.包围盒canvas, 包围盒屏上: m.包围盒屏上,
    外层屏上: m.nodeToolbar最大 && m.nodeToolbar最大.w, 外层offsetWidth: m.nodeToolbaroffsetWidth,
    外层祖先链: m.nodeToolbar祖先链, 在viewport内: m.nodeToolbar在viewport内,
    内层: m.inner && m.inner.w, 计数项: m.count && m.count.w, 逐字: m.逐字, 按钮数: m.按钮数 };
  out.剂量.push(rec);
  const 外层canvas = rec.外层屏上 && rec.scale ? Math.round(rec.外层屏上 / rec.scale * 10) / 10 : null;
  log(`\n  ── 目标 ${K} 个，实际选中 ${rec.实际选中} ──  scale=${rec.scale}（${rec.scale === 0.6 ? '✅' : '⛔ 不是 60%'}）`);
  log(`     包围盒 canvas ${JSON.stringify(rec.包围盒canvas)}｜屏上 ${JSON.stringify(rec.包围盒屏上)}`);
  log(`     外层屏上 ${rec.外层屏上}｜offsetWidth ${rec.外层offsetWidth}｜换算 canvas ${外层canvas}`);
  log(`     内层 ${rec.内层}｜计数项 ${rec.计数项}｜逐字 «${rec.逐字}»`);
  log(`     祖先链 ${JSON.stringify(rec.外层祖先链)}`);
  log(`     在 .react-flow__viewport 内：${rec.在viewport内}`);
  save();
  断言(`K=${K} 实际选中恰好 ${K}`, rec.实际选中 === K, { K, 实际: rec.实际选中 });
  断言(`K=${K} scale 读数非 null 且为 0.6`, rec.scale === 0.6, { scale: rec.scale });
}

// ---------------------------------------------------------------- ④ 关系判据
log('\n=== ④ 判据：外层 canvas 宽度 == 选中集包围盒 canvas 宽度？ ===');
const 表 = out.剂量.filter((r) => r.外层屏上).map((r) => ({
  选中数: r.实际选中,
  外层屏上: r.外层屏上, 外层offsetWidth: r.外层offsetWidth,
  外层canvas: r.scale ? Math.round((r.外层屏上 / r.scale) * 10) / 10 : null,
  包围盒canvas宽: r.包围盒canvas ? r.包围盒canvas.w : null,
  包围盒屏上宽: r.包围盒屏上 ? r.包围盒屏上.w : null,
  差: (r.scale && r.包围盒canvas) ? Math.round(((r.外层屏上 / r.scale) - r.包围盒canvas.w) * 100) / 100 : null,
}));
out.关系判据 = 表;
for (const row of 表) log('  ' + JSON.stringify(row));
save();
const 差集 = 表.map((r) => r.差);
out.判定_外层canvas恒等于包围盒canvas宽 = 差集.length > 1 && 差集.every((d) => Math.abs(d) < 0.6);
log(`\n  🔑 「外层 canvas 宽 − 包围盒 canvas 宽」的逐档差：${JSON.stringify(差集)}`);
log(`  ${out.判定_外层canvas恒等于包围盒canvas宽 ? '✅ 恒等 ⇒ 外层宽度就是选中集包围盒的 canvas 宽度' : '⛔ 不恒等'}`);
const 外层canvas集合 = 表.map((r) => r.外层canvas);
log(`  外层 canvas 宽四档：${JSON.stringify(外层canvas集合)}（若恒定则是常量，若随选中数变则跟选中集走）`);
save();

// ---------------------------------------------------------------- ⑤ 归位
log('\n=== ⑤ 归位：清选中 → 重开小地图 → 收尾核对 ===');
await p.mouse.move(640, 702);
await p.mouse.click(640, 702);
await p.waitForTimeout(1500);
log('  清选中的落点命中：', await p.evaluate(() => { const h = document.elementFromPoint(640, 702); return h ? h.tagName + '.' + String(h.className || '').split(' ')[0] : null; }));
await settle(p, R);
const mm = await R.minimap();
if (mm && mm.ariaPressed !== 'true') {
  await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-display-toggle-minimap"]'); const r = e.getBoundingClientRect();
    for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2) for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) { const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y }; } return null; }).then(async (pt) => { if (pt) { await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1500); } });
}
const end = await (async () => { const ids = await R.ids(); const t = await R.testids();
  return { 状态行: await R.status(), 选中: await R.selCount(), 浮层: await R.overlays(), zoom: await R.zoom(), credits: await R.credits(),
    minimap: await R.minimap(), 节点数: ids.length, testid种类: t.length,
    节点差集: { 多: ids.filter((x) => !out.基线ids.includes(x)), 少: out.基线ids.filter((x) => !ids.includes(x)) },
    testid差集: { 多: t.filter((x) => !out.基线testids.includes(x)), 少: out.基线testids.filter((x) => !t.includes(x)) } }; })();
out.收尾 = end;
log('  ', JSON.stringify(end));
save();
save();
log('\n✅ c 轮完成 → ./_tmp-b135c.json');
await b.close();
