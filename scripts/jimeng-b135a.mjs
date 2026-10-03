// 批次 135 · a 轮：**可行性探针** —— 「只改缩放、锁定同一选中集」这件事页面让不让做？
//
// 🔑 靶子（手册里一处**归因已订正、但实验本身有缺陷**的结论）：
//   organize-group-layout.md:70 记「多选工具条宽度不是固定值：同一天两次实测分别为
//   511×40（缩放 74%）与 1298×40（缩放 100%），计数项也从 54×32 变成 256×40」。
//   批次 87 已经把归因订正成「宽度由**选中集**撑开」，理由是
//   511÷0.74=690.5 与 1298÷1=1298 差 1.88 倍，canvas 口径不自洽。
//   🔴 **但批次 87 那次受控对照自己写着「只改缩放，选中集跟着变」** ——
//     74% 那次选中 7 个、60% 那次选中 8 个。**选中集不是受控量**，
//     于是「随缩放」与「随选中集」两个解释**至今没被任何一次实验分开过**。
//   批次 131 在 60% 下量到多选条 `624×40`、且判定它**不在画布坐标系里**
//   （css 624 = 屏上 624，参照节点屏上 192×192 才是 0.6 倍）—— 指向「不随缩放」。
//
// 📌 本轮只做三件事：存基线 → 规划框选矩形 → **试一次「改缩放后选中集还在不在」**。
//   选中集能不能扛住缩放，是整个实验成立的前提；**先验它，再开做**。
import { writeFileSync } from 'node:fs';
import { openCanvas, readers, settle, planBox, doBox, readMultiToolbar, setZoom, keyGuard } from './jimeng-b135-lib.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'a' };
const save = () => writeFileSync(new URL('./_tmp-b135a.json', import.meta.url), JSON.stringify(out, null, 1));

// ---------------------------------------------------------------- ① 基线
out.start = { 状态行: await R.status(), 选中: await R.selCount(), zoom: await R.zoom(), credits: await R.credits(), 浮层: await R.overlays(), minimap: await R.minimap() };
log('起点：', JSON.stringify(out.start));
await keyGuard(p);
await settle(p, R);
out.基线 = { 状态行: await R.status(), 选中: await R.selCount(), zoom: await R.zoom(), testid种类: (await R.testids()).length, 节点数: (await R.ids()).length, minimap: await R.minimap() };
out.基线ids = await R.ids();
out.基线testids = await R.testids();
out.基线canvas = await R.canvasPos();
log('基线：', JSON.stringify(out.基线));
save();

out.手册断言 = {
  'organize-group-layout.md:70': '多选工具条 511×40（74%）与 1298×40（100%）；计数项 54×32 → 256×40',
  '批次87 自述': '「只改缩放，**选中集跟着变**，但分别记下」—— 74%/7个、60%/8个',
  '批次131 实测': '60% 下 8 节点：node-toolbar 624×40 屏上=css，判定不在画布坐标系里',
  '本次要分开的两条解释': ['宽度随画布缩放变', '宽度由选中集撑开'],
};
log('\n手册断言已归档：', JSON.stringify(out.手册断言, null, 1));
save();

// ---------------------------------------------------------------- ② 规划框选
log('\n=== ② 规划框选矩形 ===');
const plan = await planBox(p, 6);
out.框选计划 = plan;
log('  ', JSON.stringify(plan));
save();
if (!plan.ok) { log('  ⛔ 找不到 ≥6 个节点的框选矩形，本轮到此为止'); await b.close(); process.exit(0); }

// ---------------------------------------------------------------- ③ 执行框选
log('\n=== ③ 执行框选 ===');
const hit = await doBox(p, plan.矩形);
const afterSel = await readMultiToolbar(p);
out.框选后 = { 按下点命中: hit, 选中集: afterSel.选中集, 选中数: afterSel.选中集.length, 多选条: afterSel.nodeToolbar最大, 逐字: afterSel.逐字 };
log('  按下点命中', hit, '｜选中', afterSel.选中集.length, '个｜多选条', JSON.stringify(afterSel.nodeToolbar最大), '｜逐字 «' + afterSel.逐字 + '»');
save();

// ---------------------------------------------------------------- ④ 可行性探针：改缩放，选中集还在不在
log('\n=== ④ 可行性探针：只改缩放（60% → 100% → 60%），看选中集与工具条宽度 ===');
const 探针 = [];
for (const pct of [100, 60]) {
  const z = await setZoom(p, pct);
  const m = await readMultiToolbar(p);
  const 二次 = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
  const rec = { 设缩放: z, 读数: m, zoom连读第二次: 二次,
    选中集与首次相同: JSON.stringify(m.选中集) === JSON.stringify(afterSel.选中集) };
  探针.push(rec);
  log(`  ${pct}% → zoom回读 «${z.回读}»／连读 «${二次}»｜选中 ${m.选中集.length} 个（与首次相同：${rec.选中集与首次相同}）`);
  log(`     多选条 ${JSON.stringify(m.nodeToolbar最大)}`);
  log(`     surface ${JSON.stringify(m.surface)}｜inner ${JSON.stringify(m.inner)}｜count ${JSON.stringify(m.count)}`);
  log(`     多选手柄 ${JSON.stringify(m.多选手柄)}｜选中节点屏上 ${JSON.stringify(m.选中节点屏上)}`);
  save();
}
out.可行性探针 = 探针;
out.结论_选中集扛得住缩放 = 探针.every((r) => r.选中集与首次相同);
out.结论_宽度是否随缩放变 = (() => {
  const a = 探针[0].读数.nodeToolbar最大, c = 探针[1].读数.nodeToolbar最大;
  return { '100档': a, '60档': c, 相同: a && c && a.w === c.w && a.h === c.h };
})();
log('\n可行性结论：', JSON.stringify(out.结论_选中集扛得住缩放), JSON.stringify(out.结论_宽度是否随缩放变));

// ---------------------------------------------------------------- ⑤ 归位
log('\n=== ⑤ 归位：清选中、缩放回 60%、小地图重开 ===');
await p.mouse.click(640, 700).catch(() => {});
await p.evaluate(() => { const h = document.elementFromPoint(640, 700); return h ? h.tagName : null; });
await settle(p, R);
out.归位后 = await R.zoom();
log('  zoom 回读 «' + out.归位后 + '»');
save();
save();
log('\n✅ a 轮完成 → ' + './_tmp-b135a.json');
await b.close();
