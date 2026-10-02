// Batch BK2 — 修掉 BK1 里的三个假绿灯。
//
// BK1 报「7 种条件全部无变化」，但逐条看下来其中三条**根本没执行**：
//   ② 「双选 ⌘L」：连点两个节点 = **切换选中**，第二个点把第一个顶掉了。
//      读数自证：`{"n":1,"who":["v-oZNpH99MtM"]}` —— 压根没选出两个。
//   ③ 「选中连线 ⌘L」：用 `path.getPointAtLength()` 拿坐标，那是 **SVG 用户坐标**，
//      不是屏幕坐标。脚本自己打了 `no point on edge` —— `elementFromPoint` 什么都没命中。
//   ⑥ 悬停连线中点：同一个坑，读数是 `tag: null` —— 那个点上**什么都没有**。
//
// ⚠️ 这三条如果照 BK1 的样子写进手册，就是**三条假绿灯**：
//     把「没做」当成「做了没反应」。BG4 已经在同一个坑上栽过一次
//     （「从 path 的 d 反推端点，距离 969~1325 全错」）。
//
// 本轮修法：
//   · **屏幕坐标**用 `getScreenCTM()` + `DOMPoint.matrixTransform()` 转，不要用用户坐标；
//   · **多选**用 `Shift` + 点击，不是连点两次；
//   · 每条试验都加一个**自证字段**：`executed`（真的点/按了吗）与 `hit`（落点上是谁），
//     没执行就报 `executed:false`，**不许报成「无变化」**。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBK2';
const { browser, page } = await launch();
const VID = 'v-v2hlWY4Br3';
const CLIP = 'v-oZNpH99MtM';

const edges = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__edge')]
  .map((e) => e.getAttribute('aria-label')));

const selInfo = () => page.evaluate(() => ({
  n: document.querySelectorAll('.react-flow__node.selected').length,
  who: [...document.querySelectorAll('.react-flow__node.selected')].map((e) => e.getAttribute('data-id')),
  edgeSel: [...document.querySelectorAll('.react-flow__edge')]
    .filter((e) => e.classList.contains('selected') || e.getAttribute('aria-selected') === 'true')
    .map((e) => e.getAttribute('aria-label')),
}));

const nodePoint = (id) => page.evaluate((nid) => {
  const n = [...document.querySelectorAll('.react-flow__node')].find((x) => x.getAttribute('data-id') === nid);
  if (!n) return { err: 'no node' };
  const r = n.getBoundingClientRect();
  if (r.width < 10) return { err: 'offscreen' };
  for (let fy = 0.18; fy <= 0.85; fy += 0.1) for (let fx = 0.08; fx <= 0.95; fx += 0.06) {
    const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
    const o = document.elementFromPoint(x, y);
    if (o && o.closest('.react-flow__node') === n) return { x, y };
  }
  return { err: 'no point' };
}, id);

/** ⭐ 把 path 上的一个点换算成**屏幕坐标**（BK1 栽的就是这一步）。 */
const edgeScreenPoint = (which = 0, frac = 0.5) => page.evaluate(([idx, f]) => {
  const es = [...document.querySelectorAll('.react-flow__edge path')];
  const p = es[idx];
  if (!p) return { err: 'no path' };
  const L = p.getTotalLength();
  const pt = p.getPointAtLength(L * f);
  const m = p.getScreenCTM();
  if (!m) return { err: 'no CTM' };
  const s = new DOMPoint(pt.x, pt.y).matrixTransform(m);
  const x = Math.round(s.x), y = Math.round(s.y);
  const o = document.elementFromPoint(x, y);
  return { x, y, hitTag: o ? o.tagName : null,
    hitInEdge: !!(o && (o.closest('.react-flow__edge') || (typeof o.className?.baseVal === 'string'
      && o.className.baseVal.includes('react-flow__edge')))) };
}, [which, frac]);

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1600);
  await fitView(page); await page.waitForTimeout(2000);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '修坐标换算 + 修多选，并给每条试验加自证字段' });

  const out = { trials: [] };
  const base = await edges();
  console.log('基线连线：', JSON.stringify(base));

  const trial = async (label, fn) => {
    const before = await edges();
    const r = await fn();                       // { executed, note?, hit? }
    await page.waitForTimeout(2400);
    const after = await edges();
    const changed = JSON.stringify(before) !== JSON.stringify(after);
    const executed = r?.executed === true;
    const verdict = !executed ? '⚠️ **未执行**' : (changed ? '⭐ 变了' : '无变化');
    console.log(`  ${label}：${before.length} → ${after.length} 条  ${verdict}${r?.note ? '  ' + r.note : ''}`);
    out.trials.push({ label, executed, before: before.length, after: after.length, changed, note: r?.note, hit: r?.hit });
    return { changed, executed };
  };

  // ① 连线上的屏幕坐标换算（先单独验这一步本身对不对）
  console.log('\n--- ① 先验「用户坐标 → 屏幕坐标」这个换算本身 ---');
  const p1 = await edgeScreenPoint(1, 0.5);
  console.log('  第 2 条连线中点：', JSON.stringify(p1));
  if (p1.err) console.log('  ⛔ 换算失败：', p1.err);
  else console.log(`  ⭐ 换算后落在 <${p1.hitTag}>，在连线内 = ${p1.hitInEdge}`);
  out.coordCheck = p1;

  // ② Shift 多选两个端点
  console.log('\n--- ② Shift 多选两个端点再按 ⌘L ---');
  await trial('Shift 多选 ⌘L', async () => {
    const a = await nodePoint(VID);
    if (a.err) return { executed: false, note: '上游 ' + a.err };
    await page.mouse.click(a.x, a.y); await page.waitForTimeout(2000);
    const b = await nodePoint(CLIP);
    if (b.err) return { executed: false, note: '下游 ' + b.err };
    await page.keyboard.down('Shift');
    await page.mouse.click(b.x, b.y);
    await page.keyboard.up('Shift');
    await page.waitForTimeout(2000);
    const s = await selInfo();
    console.log('   选中读数：', JSON.stringify(s));
    if (s.n !== 2) return { executed: false, note: `只选中 ${s.n} 个，多选没成立`, hit: s };
    await page.keyboard.down('Meta'); await page.keyboard.press('l'); await page.keyboard.up('Meta');
    return { executed: true, hit: s };
  });

  // ③ 点连线本身（用换算后的屏幕坐标）
  console.log('\n--- ③ 点中连线本身再按 ⌘L ---');
  await trial('选中连线 ⌘L', async () => {
    if (p1.err) return { executed: false, note: '坐标换算失败：' + p1.err };
    await page.mouse.click(p1.x, p1.y); await page.waitForTimeout(2200);
    const s = await selInfo();
    console.log('   选中读数：', JSON.stringify(s));
    if (!s.edgeSel.length) return { executed: false, note: '点中了但连线没进选中态', hit: s };
    await page.keyboard.down('Meta'); await page.keyboard.press('l'); await page.keyboard.up('Meta');
    return { executed: true, hit: s };
  });

  // ④ 悬停连线：先确认那个点上真的有东西
  console.log('\n--- ④ 悬停连线中点（先验落点上是谁）---');
  const hov = await (async () => {
    if (p1.err) return { err: p1.err };
    await page.mouse.move(p1.x, p1.y); await page.waitForTimeout(2000);
    return page.evaluate(([x, y]) => {
      const o = document.elementFromPoint(x, y);
      return { tag: o ? o.tagName : null,
        inEdge: !!(o && o.closest('.react-flow__edge')),
        cls: o ? (typeof o.className === 'string' ? o.className
          : (o.className && o.className.baseVal) || '').slice(0, 70) : null,
        stroke: (() => { const p = document.querySelector('.react-flow__edge path');
          if (!p) return null; const cs = getComputedStyle(p);
          return { stroke: cs.stroke, width: cs.strokeWidth, pointerEvents: cs.pointerEvents }; })(),
        tip: [...document.querySelectorAll('[class*="Tooltip-tooltip"]')]
          .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
          .map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim()) };
    }, [p1.x, p1.y]);
  })();
  console.log('  ', JSON.stringify(hov));
  out.hover = hov;

  // ⑤ 复测：选中下游按 ⌘L（BK1 的①，这次带自证）
  console.log('\n--- ⑤ 复测：选中下游按 ⌘L（带自证）---');
  await trial('下游 ⌘L（复测）', async () => {
    const b = await nodePoint(CLIP);
    if (b.err) return { executed: false, note: b.err };
    await page.mouse.click(b.x, b.y); await page.waitForTimeout(2200);
    const s = await selInfo();
    if (s.n !== 1 || s.who[0] !== CLIP) return { executed: false, note: '选中断言不过 ' + JSON.stringify(s) };
    await page.keyboard.down('Meta'); await page.keyboard.press('l'); await page.keyboard.up('Meta');
    return { executed: true, hit: s };
  });

  // ── 收尾
  console.log('\n══════ 收尾核对 ══════');
  await page.mouse.move(120, 780); await page.waitForTimeout(1200);
  const fin = await edges();
  const same = JSON.stringify(fin) === JSON.stringify(base);
  console.log(`  最终 ${fin.length} 条：${JSON.stringify(fin)}`);
  console.log(`  ⭐ 与基线一致？ ${same ? '✅ 画布已复原' : '⚠️ 画布变了 —— 需要复原'}`);
  out.final = { edges: fin, sameAsBase: same };

  const valid = out.trials.filter((t) => t.executed);
  const invalid = out.trials.filter((t) => !t.executed);
  console.log(`\n  ⭐ 有效试验 ${valid.length} 条，其中变了 ${valid.filter((t) => t.changed).length} 条`);
  console.log(`  ⚠️ 未执行 ${invalid.length} 条：${JSON.stringify(invalid.map((t) => ({ 条件: t.label, 原因: t.note })))}`);
  out.validCount = valid.length;
  out.changedCount = valid.filter((t) => t.changed).length;
  out.invalid = invalid.map((t) => ({ label: t.label, note: t.note }));

  await logStep(B, {
    id: 'BK2-fix-false-greens',
    title: '修掉 BK1 的三个假绿灯：坐标换算 + 多选 + 自证字段',
    target: 'BK1 报「7 种条件全无变化」，但其中三条根本没执行：'
      + '②连点两个节点是切换选中不是多选（读数 n:1 自证）；'
      + '③⑥用 path.getPointAtLength() 拿的是 SVG 用户坐标不是屏幕坐标，'
      + 'elementFromPoint 什么都没命中（BK4 已在同一坑栽过一次）。'
      + '本轮改用 getScreenCTM()+DOMPoint 换算、Shift 多选，并给每条试验加 executed/hit 自证字段，'
      + '**没执行就报未执行，不许报成「无反应」**。',
    evidence: out,
    visible_text: JSON.stringify({ 基线: base.length, 换算自检: out.coordCheck,
      试验: out.trials?.map?.((t) => ({ 条件: t.label, 执行了: t.executed, 前: t.before, 后: t.after })),
      有效: out.validCount, 变了: out.changedCount, 未执行: out.invalid,
      悬停: out.hover, 收尾一致: out.final?.sameAsBase }).slice(0, 3000),
  });
  console.log('\nBK2 完成');
} finally {
  await browser.close();
}
