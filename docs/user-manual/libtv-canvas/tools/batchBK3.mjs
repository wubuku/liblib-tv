// Batch BK3 — 断线入口实测：连线上的「剪刀」。
//
// BK2 查连线悬停时读到落点是 `DIV.scissors-enter` —— **class 名直接写着剪刀**，
// 这几乎就是「断开连线」的入口。BK1/BK2 用 `⌘L` 试了 7 种条件全部无效
// （其中 3 条是假绿灯，已在 BK2 修掉并复测）。
//
// 本轮：
//   ① 量那枚剪刀：默认态/悬停态的 rect、opacity、显示与否、能不能被点到；
//   ② ⭐ **实点它**，看连线是否真的消失（读 `aria-label`，BG 的规矩）；
//   ③ ⭐ **复原**：用 BJ1 验证过的拖线手法把连线连回去，刷新确认落盘；
//      收尾必须与基线**逐条一致**，不一致就明确报出来。
//
// ⚠️ 试的是本轮自己加的那条 `v-v2hlWY4Br3 → v-oZNpH99MtM`，
//    不是更早的那条 —— 万一复原失败，损失可控。
//    绝不执行 ⌘A+⌫（会删光节点）。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBK3';
const { browser, page } = await launch();
const VID = 'v-v2hlWY4Br3';
const CLIP = 'v-oZNpH99MtM';
const TARGET_EDGE = 'Edge from v-v2hlWY4Br3 to v-oZNpH99MtM';

const edges = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__edge')]
  .map((e) => e.getAttribute('aria-label')));

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

const portPoint = (id, which) => page.evaluate(([nid, w]) => {
  const n = [...document.querySelectorAll('.react-flow__node')].find((x) => x.getAttribute('data-id') === nid);
  const h = n && n.querySelector(`[data-handleid="${w}"]`);
  if (!h) return { err: 'no handle' };
  const r = h.children[0].getBoundingClientRect();
  return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
}, [id, which]);

/** 目标连线中点的**屏幕**坐标（BK2 的换算法）。 */
const edgePoint = (label) => page.evaluate((want) => {
  const e = [...document.querySelectorAll('.react-flow__edge')].find((x) => x.getAttribute('aria-label') === want);
  const p = e && e.querySelector('path');
  if (!p) return { err: 'no path' };
  const L = p.getTotalLength(); const pt = p.getPointAtLength(L / 2);
  const s = new DOMPoint(pt.x, pt.y).matrixTransform(p.getScreenCTM());
  const x = Math.round(s.x), y = Math.round(s.y);
  const o = document.elementFromPoint(x, y);
  return { x, y, hitTag: o ? o.tagName : null, hitCls: o ? (typeof o.className === 'string' ? o.className : (o.className?.baseVal ?? '')).slice(0, 60) : null };
}, label);

/** 读那枚剪刀的完整状态。 */
const scissors = () => page.evaluate(() => {
  const all = [...document.querySelectorAll('[class*="scissors"]')];
  return all.map((e) => {
    const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    return { cls: (typeof e.className === 'string' ? e.className : '').slice(0, 80),
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      opacity: cs.opacity, visibility: cs.visibility, display: cs.display,
      pointerEvents: cs.pointerEvents, cursor: cs.cursor,
      cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2),
      innerHTML: e.innerHTML.slice(0, 160) };
  });
});

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1600);
  await fitView(page); await page.waitForTimeout(2000);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '连线上的剪刀：量它、点它、复原' });

  const out = {};
  const base = await edges();
  console.log('基线连线：', JSON.stringify(base));
  out.base = base;

  // ① 剪刀的默认态 / 悬停态
  console.log('\n══════ ① 剪刀读数 ══════');
  await page.mouse.move(120, 780); await page.waitForTimeout(1800);
  const sFar = await scissors();
  console.log(`  鼠标远离时：找到 ${sFar.length} 个带 scissors 的元素`);
  sFar.forEach((s) => console.log(`    "${s.cls}" rect=${JSON.stringify(s.rect)} opacity=${s.opacity} vis=${s.visibility} cursor=${s.cursor}`));

  const ep = await edgePoint(TARGET_EDGE);
  console.log(`  目标连线中点屏幕坐标：${JSON.stringify(ep)}`);
  if (ep.err) { console.log('⛔ 取不到连线中点'); out.err = ep; throw new Error(ep.err); }

  await page.mouse.move(ep.x, ep.y); await page.waitForTimeout(2000);
  const sNear = await scissors();
  console.log(`  悬停在连线上时：找到 ${sNear.length} 个`);
  sNear.forEach((s) => console.log(`    "${s.cls}" rect=${JSON.stringify(s.rect)} opacity=${s.opacity} vis=${s.visibility} pe=${s.pointerEvents} cursor=${s.cursor} 中心=(${s.cx},${s.cy})`));
  out.scissorsFar = sFar;
  out.scissorsNear = sNear;
  await shot(page, 'M-209-连线-悬停出剪刀.png');
  out.shot0 = 'M-209-连线-悬停出剪刀.png';

  // ② ⭐ 实点剪刀
  console.log('\n══════ ② 实点剪刀 ══════');
  const target = sNear.find((s) => s.rect[2] > 0 && s.rect[3] > 0 && s.opacity !== '0' && s.pointerEvents !== 'none')
    || sNear[0];
  if (!target) { console.log('⛔ 没有可点的剪刀'); }
  else {
    const own = await page.evaluate(([x, y]) => {
      const o = document.elementFromPoint(x, y);
      return { tag: o ? o.tagName : null,
        cls: o ? (typeof o.className === 'string' ? o.className : (o.className?.baseVal ?? '')).slice(0, 60) : null,
        inScissors: !!(o && o.closest('[class*="scissors"]')) };
    }, [target.cx, target.cy]);
    console.log(`  落点归属：${JSON.stringify(own)} ${own.inScissors ? '✅' : '⚠️'}`);
    console.log(`  点 (${target.cx}, ${target.cy})`);
    await page.mouse.click(target.cx, target.cy);
    await page.waitForTimeout(2800);
    const after = await edges();
    console.log(`  ⭐ 点完连线 ${after.length} 条：${JSON.stringify(after)}`);
    const gone = !after.includes(TARGET_EDGE);
    console.log(`  ⭐ 目标连线还在吗？ ${gone ? '**没了 —— 剪刀确实能断线**' : '还在 —— 剪刀没起作用'}`);
    out.cut = { before: base.length, after: after.length, gone, edges: after, own };
    await shot(page, 'M-210-连线-剪刀断开后.png');
    out.shot1 = 'M-210-连线-剪刀断开后.png';
  }

  // ③ 复原：拖回去
  console.log('\n══════ ③ 复原：把连线连回去 ══════');
  const stillGone = !(await edges()).includes(TARGET_EDGE);
  if (stillGone) {
    const from = await portPoint(VID, 'source');
    const to = await portPoint(CLIP, 'target');
    console.log(`  拖 ${JSON.stringify(from)} → ${JSON.stringify(to)}`);
    await page.mouse.move(from[0], from[1]); await page.waitForTimeout(1200);
    await page.mouse.down(); await page.waitForTimeout(500);
    for (let i = 1; i <= 8; i++) { await page.mouse.move(from[0] + (to[0] - from[0]) * i / 8, from[1] + (to[1] - from[1]) * i / 8); await page.waitForTimeout(180); }
    await page.mouse.up(); await page.waitForTimeout(2600);
    await page.keyboard.press('Escape'); await page.waitForTimeout(1400);
  } else {
    console.log('  连线本来就在，跳过拖回');
  }

  // 刷新确认落盘（BG4）
  await page.reload({ waitUntil: 'domcontentloaded' }); await page.waitForTimeout(6500);
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1800);
  await fitView(page); await page.waitForTimeout(2000);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  const fin = await edges();
  const same = JSON.stringify(fin) === JSON.stringify(base);
  console.log(`  刷新后 ${fin.length} 条：${JSON.stringify(fin)}`);
  console.log(`  ⭐ 与基线逐条一致？ ${same ? '✅ 画布已完全复原' : '⚠️ 不一致'}`);
  out.final = { edges: fin, sameAsBase: same };
  if (same) console.log('  📷 复原态与基线相同，无需另拍');

  await logStep(B, {
    id: 'BK3-scissors-disconnect',
    title: '连线上的「剪刀」：断线入口实测与复原',
    target: 'BK2 悬停连线时读到落点是 DIV.scissors-enter —— class 名直接写着剪刀。'
      + 'BK1/BK2 用 ⌘L 试了 7 种条件全部无效（其中 3 条假绿灯已修）。'
      + '本轮量剪刀、实点它看连线是否消失，再用拖线复原并刷新确认。'
      + '⚠️ 试的是本轮自己加的那条线，且绝不执行 ⌘A+⌫。',
    evidence: out,
    visible_text: JSON.stringify({ 基线: out.base, 远离时剪刀: out.scissorsFar?.map?.((s) => ({ cls: s.cls, rect: s.rect, op: s.opacity })),
      悬停时剪刀: out.scissorsNear?.map?.((s) => ({ cls: s.cls, rect: s.rect, op: s.opacity, cursor: s.cursor })),
      点完: out.cut, 复原一致: out.final?.sameAsBase }).slice(0, 3000),
    shot: out.shot0,
  });
  console.log('\nBK3 完成');
} finally {
  await browser.close();
}
