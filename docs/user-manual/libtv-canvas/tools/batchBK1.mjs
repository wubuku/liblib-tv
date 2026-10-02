// Batch BK1 — `⌘L` 到底是不是连线的开关。
//
// 起因：BJ2 想做「断开 → 芯片消失」的可逆对照，选中已连线的**视频节点**按 `⌘L`，
// **连线数没变（仍是 2 条）**。于是「⌘L 能断线」这条一直没人验过，
// 而 connect-nodes 正文把 `⌘L` 当成连线操作在教。
//
// ⭐ 这轮系统地扫一遍「什么条件下 `⌘L` 会断线」：
//   ① 选中**下游**节点（智能剪辑）再按 —— BJ2 试的是**上游**（视频）
//   ② **两个都选**（框选）再按
//   ③ 单独点**连线本身**再按
//   ④ 连按两次（是否自己开又关）
//   ⑤ `⌘⇧L` / `⌥L` 等变体
//   ⑥ 连线上是否另有**右键 / 悬停**的删除入口
// 每一步都**先报当前连线数**（基线），按完再报一次，**变化要归零复原**。
//
// ⚠️ 边界：`⌘A`+`⌫` 会删光节点，**永不执行**。
//    若某步真的断了线，本轮**必须把它连回去**（BJ1 的复原手法已验证可行）。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBK1';
const { browser, page } = await launch();
const VID = 'v-v2hlWY4Br3';
const CLIP = 'v-oZNpH99MtM';

const edges = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__edge')]
  .map((e) => e.getAttribute('aria-label')));

const selInfo = () => page.evaluate(() => ({
  n: document.querySelectorAll('.react-flow__node.selected').length,
  who: [...document.querySelectorAll('.react-flow__node.selected')].map((e) => e.getAttribute('data-id')),
  edgeSel: document.querySelectorAll('.react-flow__edge.selected, .react-flow__edge[aria-selected="true"]').length,
}));

async function pick(id) {
  const pt = await page.evaluate((nid) => {
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
  if (pt.err) return pt;
  await page.mouse.click(pt.x, pt.y); await page.waitForTimeout(2200);
  return pt;
}

/** 画布中心偏上一块空白处，用来点空白取消选中。 */
const blank = () => page.evaluate(() => {
  for (let y = 60; y < 260; y += 20) for (let x = 700; x < 1200; x += 20) {
    const o = document.elementFromPoint(x, y);
    if (o && !o.closest('.react-flow__node') && o.closest('.react-flow')) return [x, y];
  }
  return null;
});

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1600);
  await fitView(page); await page.waitForTimeout(2000);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '⌘L 断线与否的系统扫描（6 种条件）' });

  const out = { trials: [] };
  const base = await edges();
  console.log('基线连线：', JSON.stringify(base));

  const trial = async (label, fn) => {
    const before = await edges();
    await fn();
    await page.waitForTimeout(2400);
    const after = await edges();
    const changed = JSON.stringify(before) !== JSON.stringify(after);
    console.log(`  ${label}：${before.length} → ${after.length} 条 ${changed ? '⭐ **变了**' : '无变化'}`);
    out.trials.push({ label, before: before.length, after: after.length, changed, labels: after });
    return changed;
  };

  // ① 选中下游（智能剪辑）按 ⌘L
  console.log('\n--- ① 选中下游节点（智能剪辑）按 ⌘L ---');
  await trial('选中下游 ⌘L', async () => {
    const pt = await pick(CLIP);
    if (pt.err) { console.log('   ' + pt.err); return; }
    const s = await selInfo(); console.log('   选中：', JSON.stringify(s));
    await page.keyboard.down('Meta'); await page.keyboard.press('l'); await page.keyboard.up('Meta');
  });

  // ② 两个都选再按
  console.log('\n--- ② 框选两个端点再按 ⌘L ---');
  await trial('双选 ⌘L', async () => {
    const a = await pick(VID); const b = await pick(CLIP);
    console.log('   两个点：', JSON.stringify(a), JSON.stringify(b));
    const s = await selInfo(); console.log('   选中：', JSON.stringify(s));
    await page.keyboard.down('Meta'); await page.keyboard.press('l'); await page.keyboard.up('Meta');
  });

  // ③ 点连线本身
  console.log('\n--- ③ 点中连线本身再按 ⌘L ---');
  await trial('选中连线 ⌘L', async () => {
    const p = await page.evaluate(() => {
      const p = document.querySelector('.react-flow__edge path');
      if (!p) return { err: 'no path' };
      const L = p.getTotalLength();
      for (let i = 1; i < 9; i++) {
        const pt = p.getPointAtLength((L * i) / 10);
        const x = Math.round(pt.x), y = Math.round(pt.y);
        const o = document.elementFromPoint(x, y);
        if (o && (o.closest('.react-flow__edge') || o.classList.contains('react-flow__edge'))) return { x, y };
      }
      return { err: 'no point on edge' };
    });
    if (p.err) { console.log('   ' + p.err); return; }
    console.log('   连线上落点：', JSON.stringify(p));
    await page.mouse.click(p.x, p.y);
    const s = await selInfo(); console.log('   选中：', JSON.stringify(s));
    await page.keyboard.down('Meta'); await page.keyboard.press('l'); await page.keyboard.up('Meta');
  });

  // ④ 连按两次
  console.log('\n--- ④ 对下游连按两次 ⌘L ---');
  await trial('下游 ⌘L 两次', async () => {
    const pt = await pick(CLIP);
    if (pt.err) return;
    for (let k = 0; k < 2; k++) {
      await page.keyboard.down('Meta'); await page.keyboard.press('l'); await page.keyboard.up('Meta');
      await page.waitForTimeout(2000);
      console.log(`   第 ${k + 1} 次后：${(await edges()).length} 条`);
    }
  });

  // ⑤ 变体键
  console.log('\n--- ⑤ 变体键 ---');
  for (const [k, label] of [['Meta+Shift', '⌘⇧L'], ['Meta+Alt', '⌘⌥L'], ['Alt', '⌥L']]) {
    await trial(`下游 ${label}`, async () => {
      const pt = await pick(CLIP);
      if (pt.err) return;
      const keys = k.split('+');
      for (const m of keys) await page.keyboard.down(m === 'Meta' ? 'Meta' : m === 'Shift' ? 'Shift' : 'Alt');
      await page.keyboard.press('l');
      for (const m of keys.slice().reverse()) await page.keyboard.up(m === 'Meta' ? 'Meta' : m === 'Shift' ? 'Shift' : 'Alt');
    });
  }

  // ⑥ 连线上的删除入口：悬停看有没有按钮 / tooltip
  console.log('\n--- ⑥ 连线本身有没有删除入口 ---');
  const bp = await page.evaluate(() => {
    const p = document.querySelector('.react-flow__edge path');
    if (!p) return { err: 'no path' };
    const L = p.getTotalLength(); const pt = p.getPointAtLength(L / 2);
    return [Math.round(pt.x), Math.round(pt.y)];
  });
  if (!bp.err) {
    await page.mouse.move(bp[0], bp[1]); await page.waitForTimeout(1800);
    const h = await page.evaluate(([x, y]) => {
      const o = document.elementFromPoint(x, y);
      return { tag: o ? o.tagName : null, inEdge: !!(o && o.closest('.react-flow__edge')),
        cls: o ? (typeof o.className === 'string' ? o.className : '').slice(0, 60) : null,
        tip: [...document.querySelectorAll('[class*="Tooltip-tooltip"]')]
          .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
          .map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim()) };
    }, bp);
    console.log('   悬停连线中点：', JSON.stringify(h));
    out.edgeHover = h;
  }

  // ── 收尾：确认画布回到基线
  console.log('\n══════ 收尾核对 ══════');
  await page.mouse.move(120, 780); await page.waitForTimeout(1000);
  const fin = await edges();
  console.log(`  最终连线 ${fin.length} 条：${JSON.stringify(fin)}`);
  const sameAsBase = JSON.stringify(fin) === JSON.stringify(base);
  console.log(`  ⭐ 与基线一致？ ${sameAsBase ? '✅ 是（画布已复原）' : '⚠️ 否 —— 画布状态变了'}`);
  out.final = { edges: fin, sameAsBase };

  console.log('\n  ⭐ 汇总：');
  for (const t of out.trials) console.log(`     ${t.label.padEnd(14)} ${t.before} → ${t.after}  ${t.changed ? '变了' : '无变化'}`);
  out.anyChanged = out.trials.some((t) => t.changed);

  await logStep(B, {
    id: 'BK1-cmdL-disconnect',
    title: '⌘L 到底能不能断线：6 种条件全扫',
    target: 'BJ2 的可逆对照卡在断线这一步。本轮系统扫 6 种条件：选下游 / 双选 / 点连线本身 / '
      + '连按两次 / 三个变体键 / 连线上的删除入口。每步都先报基线连线数。'
      + '⚠️ 绝不执行 ⌘A+⌫（会删光节点）。',
    evidence: out,
    visible_text: JSON.stringify({ 基线: base.length, 试验: out.trials?.map?.((t) => ({ 条件: t.label, 前: t.before, 后: t.after, 变: t.changed })),
      悬停连线: out.edgeHover, 收尾一致: out.final?.sameAsBase, 有任何变化: out.anyChanged }).slice(0, 2500),
  });
  console.log('\nBK1 完成');
} finally {
  await browser.close();
}
