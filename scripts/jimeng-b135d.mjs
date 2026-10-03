// 批次 135 · d 轮：**两类连接手柄的结构差异** —— 手册里两个 `60×120` 分属两个量。
//
// 🔑 c 轮已得公式：**多选条屏上宽 = (选中集包围盒 canvas 宽 + 80) × 缩放**（三档差恒为 80）。
//   祖先链证明它挂在 `.react-flow__renderer` 下、**不在** `.react-flow__viewport` 里
//   ⇒ 它**抵消了画布的自动缩放，改成手工乘 scale**。这是与生成面板同源、但与
//   「每节点手柄」完全不同的第三种机制。
//
// 🔴 c 轮同时撞出一个**手册里的量纲陷阱**：
//   `20-reference.md:1470` 记 `flow-node-multi-selection-source-handle` = `60×120`；
//   而 AUDIT.md / PROGRESS.md 里那条被反复确认的契约是「**canvas 恒 60×120**」，
//   指的却是 **`flow-node-{target,source}-handle`（每节点）**。
//   b 轮四档实测：**多选手柄 40/60/100/200% 全部 `60×120`**（屏上恒定），
//   **每节点手柄 60% 下屏上是 `36×72`**（76/74 个实例，逐字相同）。
//   ⇒ **两个 `60×120` 一个是屏上量、一个是 canvas 量**，混用会得出相反结论。
//   本轮读两者的**祖先链 + offsetWidth**，把「在不在画布坐标系里」钉成结构性事实。
import { writeFileSync } from 'node:fs';
import { openCanvas, readers, settle, scanBox, doBox, setZoom, keyGuard } from './jimeng-b135-lib.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'd', 手柄: [] };
const save = () => writeFileSync(new URL('./_tmp-b135d.json', import.meta.url), JSON.stringify(out, null, 1));

/** 读某个 testid 的全部实例：屏上矩形 + offsetWidth + 祖先链 + 在不在 viewport 内。 */
const describe = (tid) => p.evaluate((t) => {
  const a = Array.from(document.querySelectorAll(`[data-testid="${t}"]`));
  if (!a.length) return { testid: t, 实例数: 0 };
  const sizes = {};
  for (const e of a) { const r = e.getBoundingClientRect(); const k = `${Math.round(r.width * 10) / 10}×${Math.round(r.height * 10) / 10}`; sizes[k] = (sizes[k] || 0) + 1; }
  const e = a[0];
  const chain = []; for (let n = e; n && n !== document.body; n = n.parentElement) chain.push(String(n.className || '').split(' ')[0] || n.tagName);
  return { testid: t, 实例数: a.length, 尺寸分布: sizes, offsetWidth: e.offsetWidth, offsetHeight: e.offsetHeight,
    自身transform: e.style.transform || getComputedStyle(e).transform,
    祖先链前4: chain.slice(0, 4), 在viewport内: !!e.closest('.react-flow__viewport') };
}, tid);

await keyGuard(p);
await settle(p, R);
out.基线 = { 状态行: await R.status(), 节点数: (await R.ids()).length, testid种类: (await R.testids()).length, zoom: await R.zoom() };
out.基线ids = await R.ids();
out.基线testids = await R.testids();
log('基线：', JSON.stringify(out.基线));
save();

// ---------------------------------------------------------------- ① 未选中态：每节点手柄
log('\n=== ① 未选中态（0 个选中）：每节点连接手柄 ===');
out.每节点手柄_未选中 = { target: await describe('flow-node-target-handle'), source: await describe('flow-node-source-handle') };
log('  target ', JSON.stringify(out.每节点手柄_未选中.target));
log('  source ', JSON.stringify(out.每节点手柄_未选中.source));
save();

// ---------------------------------------------------------------- ② 框选后逐档读两类手柄
log('\n=== ② 框选 6 个 → 四档读两类手柄 ===');
const 扫描 = await scanBox(p);
const K = 6;
if (!扫描.矩形表[String(K)]) { log('  ⛔ 找不到 6 个的矩形'); await b.close(); process.exit(0); }
const hit = await doBox(p, 扫描.矩形表[String(K)]);
log('  按下点', hit, '｜选中', (await p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length)));

for (const pct of [60, 40, 100, 200, 60]) {
  if (pct !== 60 || (await R.zoom()) !== 'Zoom options, 60%') { if (pct !== 60) await setZoom(p, pct); }
  const z = await R.zoom();
  const m = await describe('flow-node-multi-selection-source-handle');
  const t = await describe('flow-node-target-handle');
  const tb = await p.evaluate(() => { const a = Array.from(document.querySelectorAll('[data-testid="node-toolbar"]'))
      .sort((x, y) => (y.getBoundingClientRect().width * y.getBoundingClientRect().height) - (x.getBoundingClientRect().width * x.getBoundingClientRect().height))[0];
    const chain = []; for (let n = a; n && n !== document.body; n = n.parentElement) chain.push(String(n.className || '').split(' ')[0] || n.tagName);
    return { 屏上宽: a ? a.getBoundingClientRect().width : null, offsetWidth: a ? a.offsetWidth : null, 祖先链前3: chain.slice(0, 3), 在viewport内: a ? !!a.closest('.react-flow__viewport') : null }; });
  const rec = { 档: pct, zoom: z, 多选手柄: m, 每节点target手柄: { 实例数: t.实例数, 尺寸分布: t.尺寸分布, offsetWidth: t.offsetWidth, 在viewport内: t.在viewport内 }, 多选条: tb };
  out.手柄.push(rec);
  log(`\n  ── ${pct}%  zoom «${z}»`);
  log(`     多选手柄  屏上 ${Object.keys(m.尺寸分布).join('/')}｜offset ${m.offsetWidth}×${m.offsetHeight}｜在viewport内 ${m.在viewport内}｜祖先链 ${JSON.stringify(m.祖先链前4)}`);
  log(`     每节点手柄 屏上 ${Object.keys(t.尺寸分布).join('/')}（${t.实例数} 个）｜offset ${t.offsetWidth}×${t.offsetHeight}｜在viewport内 ${t.在viewport内}｜祖先链 ${JSON.stringify(t.祖先链前4)}`);
  log(`     多选条    屏上宽 ${tb.屏上宽}｜offsetWidth ${tb.offsetWidth}｜在viewport内 ${tb.在viewport内}｜祖先链 ${JSON.stringify(tb.祖先链前3)}`);
  save();
}

// ---------------------------------------------------------------- ③ 判据
const 多选 = out.手柄.map((r) => r.多选手柄.尺寸分布 && Object.keys(r.多选手柄.尺寸分布)[0]);
const 每节 = out.手柄.map((r) => r.每节点target手柄.尺寸分布 && Object.keys(r.每节点target手柄.尺寸分布)[0]);
out.判定_多选手柄屏上恒定 = new Set(多选).size === 1 && 多选[0] === '60×120';
out.判定_每节点手柄随缩放变 = new Set(每节).size > 1;
log(`\n  🔑 多选手柄四档：${JSON.stringify(多选)} → ${out.判定_多选手柄屏上恒定 ? '✅ 屏上恒 60×120' : '⛔'}`);
log(`  🔑 每节点手柄四档：${JSON.stringify(每节)} → ${out.判定_每节点手柄随缩放变 ? '✅ 随缩放变（canvas 恒 60×120）' : '⛔ 屏上恒定'}`);
const vp = out.手柄.map((r) => r.多选手柄.在viewport内);
log(`  🔑 多选手柄在 .react-flow__viewport 内：${JSON.stringify(vp)}`);
save();

// ---------------------------------------------------------------- ④ 归位
log('\n=== ④ 归位 ===');
await p.mouse.move(640, 702); await p.mouse.click(640, 702); await p.waitForTimeout(1500);
await settle(p, R);
const mm = await R.minimap();
if (mm && mm.ariaPressed !== 'true') {
  const pt = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-display-toggle-minimap"]'); const r = e.getBoundingClientRect();
    for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2) for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) { const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y }; } return null; });
  if (pt) { await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1500); }
}
const ids = await R.ids(); const t2 = await R.testids();
out.收尾 = { 状态行: await R.status(), 选中: await R.selCount(), 浮层: await R.overlays(), zoom: await R.zoom(), credits: await R.credits(),
  minimap: await R.minimap(), 节点数: ids.length, testid种类: t2.length,
  节点差集: { 多: ids.filter((x) => !out.基线ids.includes(x)), 少: out.基线ids.filter((x) => !ids.includes(x)) },
  testid差集: { 多: t2.filter((x) => !out.基线testids.includes(x)), 少: out.基线testids.filter((x) => !t2.includes(x)) } };
log('  ', JSON.stringify(out.收尾));
save(); save();
log('\n✅ d 轮完成 → ./_tmp-b135d.json');
await b.close();
