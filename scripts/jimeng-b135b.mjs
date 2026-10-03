// 批次 135 · b 轮：**受控第一臂 —— 锁定同一选中集，只改缩放，四档。**
//
// 🔑 a 轮已经把「选中集扛不扛得住缩放」验成 `true`（60→100→60 两次都逐个相同），
//   所以本轮可以做真正单自变量的实验。四档取 **40% / 60% / 100% / 200%**：
//   40% 与 200% 是两端，把「随缩放」与「屏上恒定」两种解释彻底分开 ——
//   1/0.4 = 2.5 与 1/2 = 0.5 差 5 倍，不可能两者同时成立。
//
// 🔴 a 轮已经撞出两件事，本轮要一并结清：
//   ① 批次 131 判定「多选工具条不在画布坐标系里」⇒ 由此推出「不随缩放」——
//      a 轮实测外层 `600×40`@60% → `1000×40`@100%，**比值恰是 1/0.6**。
//      ⇒ **「这个元素没有自己的 0.6 缩放因子」≠「它与缩放无关」**（本批头号产出）。
//   ② `20-reference.md:1470` 把多选手柄记成裸 `60×120`，而
//      **每节点**的 `flow-node-{target,source}-handle` 是「canvas 恒 60×120」
//      （屏上 60%→`36×72`）。a 轮两档读数都是 `60×120` ⇒ **这两个 60×120 是两个量**。
//      本轮加 40%/200% 两档把它钉死。
//
// 📌 护栏：只框选、只改缩放、只读数。**不拖动任何节点、不连线、不点任何按钮。**
//   缩放一律走**输入框**（菜单没有 60% 档）；每档连读两次 zoom aria。
import { writeFileSync } from 'node:fs';
import { openCanvas, readers, settle, planBox, doBox, readMultiToolbar, setZoom, keyGuard } from './jimeng-b135-lib.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'b', 档位: [] };
const save = () => writeFileSync(new URL('./_tmp-b135b.json', import.meta.url), JSON.stringify(out, null, 1));
const 断言 = (名, 条件, 详情) => { const ok = !!条件; out.护栏 = out.护栏 || []; out.护栏.push({ 名, 通过: ok, 详情 });
  log(`  ${ok ? '✅' : '⛔'} 断言·${名}：${JSON.stringify(详情)}`); save(); return ok; };

// ---------------------------------------------------------------- ① 基线
out.start = { 状态行: await R.status(), zoom: await R.zoom(), minimap: await R.minimap() };
log('起点：', JSON.stringify(out.start));
await keyGuard(p);
await settle(p, R);
out.基线 = { 状态行: await R.status(), 节点数: (await R.ids()).length, testid种类: (await R.testids()).length, zoom: await R.zoom() };
out.基线ids = await R.ids();
out.基线testids = await R.testids();
log('基线：', JSON.stringify(out.基线));
save();

// ---------------------------------------------------------------- ② 框选 6 个
log('\n=== ② 框选 6 个节点（按下点必须命中 pane）===');
const plan = await planBox(p, 6);
out.框选计划 = plan;
log('  ', JSON.stringify(plan));
save();
if (!plan.ok) { log('  ⛔ 找不到 ≥6 个节点的框选矩形'); await b.close(); process.exit(0); }
const hit = await doBox(p, plan.矩形);
const 首档 = await readMultiToolbar(p);
out.首档 = 首档;
log(`  按下点 ${hit}｜选中 ${首档.选中集.length} 个（${首档.选中集.join(',')}）`);
log(`  scale=${首档.scale}｜包围盒canvas ${JSON.stringify(首档.包围盒canvas)}｜包围盒屏上 ${JSON.stringify(首档.包围盒屏上)}`);
log(`  外层 ${JSON.stringify(首档.nodeToolbar最大)}`);
log(`  内层 ${JSON.stringify(首档.inner)}｜计数项 ${JSON.stringify(首档.count)}`);
log(`  多选手柄 ${JSON.stringify(首档.多选手柄)}｜多选连接菜单按钮 ${JSON.stringify(首档.多选连接菜单按钮)}`);
save();
断言('选中集恰好 6 个', 首档.选中集.length === 6, { n: 首档.选中集.length });
断言('首档 scale 实测为 0.6', 首档.scale === 0.6, { scale: 首档.scale });

// ---------------------------------------------------------------- ③ 四档受控扫
log('\n=== ③ 四档受控扫：锁定同一选中集，只改缩放 ===');
const 目标档 = [40, 100, 200, 60];
for (const pct of 目标档) {
  const z = await setZoom(p, pct);
  const m = await readMultiToolbar(p);
  const 二次 = await R.zoom();
  const rec = { 目标: pct, 设缩放: z, zoom连读: [z.回读, 二次], 读数: m,
    选中集与首档相同: JSON.stringify(m.选中集) === JSON.stringify(首档.选中集) };
  out.档位.push(rec);
  log(`\n  ── ${pct}% ──  zoom «${z.回读}»／连读 «${二次}»  scale=${m.scale}`);
  log(`     选中 ${m.选中集.length} 个（与首档相同：${rec.选中集与首档相同}）｜节点屏上 ${JSON.stringify(m.选中节点屏上[0])}`);
  log(`     包围盒 canvas ${JSON.stringify(m.包围盒canvas)}｜屏上 ${JSON.stringify(m.包围盒屏上)}`);
  log(`     外层 node-toolbar  ${m.nodeToolbar最大 ? m.nodeToolbar最大.w + '×' + m.nodeToolbar最大.h : null}`);
  log(`     内层 selection-context-toolbar ${m.inner ? m.inner.w + '×' + m.inner.h : null}｜计数项 ${m.count ? m.count.w + '×' + m.count.h : null}`);
  log(`     多选手柄 ${m.多选手柄 ? m.多选手柄.w + '×' + m.多选手柄.h : null}｜连接菜单按钮 ${m.多选连接菜单按钮 ? m.多选连接菜单按钮.w + '×' + m.多选连接菜单按钮.h : null}`);
  log(`     按钮数 ${m.按钮数}｜逐字 «${m.逐字}»`);
  save();
}
断言('四档全程选中集逐个未变', out.档位.every((r) => r.选中集与首档相同), out.档位.map((r) => [r.目标, r.选中集与首档相同]));

// ---------------------------------------------------------------- ④ 换算表
log('\n=== ④ 换算：外层宽度 / 各元素 在四档之间的关系 ===');
const 表 = [['档', 'scale', '外层', '外层÷(1/scale)', '内层', '计数项', '多选手柄', '包围盒canvas宽', '包围盒屏上宽']];
for (const r of out.档位) {
  const m = r.读数, w = m.nodeToolbar最大 ? m.nodeToolbar最大.w : null;
  表.push([r.目标, m.scale, w, w ? Math.round(w * m.scale * 10) / 10 : null,
    m.inner ? m.inner.w : null, m.count ? m.count.w : null,
    m.多选手柄 ? m.多选手柄.w + '×' + m.多选手柄.h : null,
    m.包围盒canvas ? m.包围盒canvas.w : null, m.包围盒屏上 ? m.包围盒屏上.w : null]);
}
out.换算表 = 表;
for (const row of 表) log('  ' + row.map((c) => String(c).padEnd(12)).join(''));
save();

// 关键判定：外层宽度 ÷ (1/scale) 是否在四档恒定？
const 外层canvas = 表.slice(1).map((r) => r[3]).filter((x) => x !== null);
const 恒定 = 外层canvas.length > 1 && Math.max(...外层canvas) - Math.min(...外层canvas) < 1;
out.判定_外层在canvas口径下恒定 = 恒定;
log(`\n  🔑 外层宽度换算成 canvas（× scale）后：${JSON.stringify(外层canvas)} → ${恒定 ? '✅ 四档恒定 ⇒ 它是 canvas 恒定、屏上随缩放' : '⛔ 不恒定'}`);

// 内层 / 计数项 / 手柄是否屏上恒定
for (const [名, 取] of [['内层', (m) => m.inner && m.inner.w], ['计数项', (m) => m.count && m.count.w], ['多选手柄宽', (m) => m.多选手柄 && m.多选手柄.w], ['多选手柄高', (m) => m.多选手柄 && m.多选手柄.h]]) {
  const vals = out.档位.map((r) => 取(r.读数));
  const same = vals.every((v) => v === vals[0]);
  out[`判定_${名}屏上恒定`] = same;
  log(`  ${名}：${JSON.stringify(vals)} → ${same ? '✅ 屏上恒定' : '⛔ 随缩放变'}`);
}
save();

// ---------------------------------------------------------------- ⑤ 归位
log('\n=== ⑤ 归位：清选中 → 缩放回 60% → 重开小地图 ===');
await p.mouse.move(640, 702);
await p.mouse.click(640, 702);
await p.waitForTimeout(1500);
const 点位 = await p.evaluate(([x, y]) => { const h = document.elementFromPoint(x, y); return h ? h.tagName + '.' + String(h.className || '').split(' ')[0] : null; }, [640, 702]);
out.清选中的落点 = 点位;
log('  清选中的落点命中：', 点位);
await settle(p, R);
out.归位 = { 状态行: await R.status(), zoom: await R.zoom(), 选中: await R.selCount() };
log('  ', JSON.stringify(out.归位));
save();
save();
log('\n✅ b 轮完成 → ./_tmp-b135b.json');
await b.close();
