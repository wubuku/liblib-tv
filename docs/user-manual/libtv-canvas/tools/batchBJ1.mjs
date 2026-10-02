// Batch BJ1 — 智能剪辑接上视频之后，参数条变成什么。
//
// 手册里 `智能剪辑` 一直是「空空如也，请连接视频节点后操作」的空态，
// 接上视频之后会变成什么**一个字都没写**。这是 create-nodes 的真实缺口。
//
// ⚠️ 安全边界：
//   · 连线只在**画布上落一条新连线**，不触发生成、不扣积分；
//   · 只连**这一条**，连完**刷新验证它落盘了**，并在 PROGRESS 记录画布现状
//     （BG4 的教训：拖动中数到的临时连线不算数，刷新后再数）；
//   · **不点任何「开始剪辑 / 执行」类按钮** —— 那会跑生成。
//
// ⭐ 判据纪律（BI3/BI4 刚吃过的亏）：
//   · 用**独占点**点节点，点完**断言选中数==1 且对象正确**；
//   · 端口用**父级 L2 的 inline opacity**判断显隐（BI1 的教训：svg 自身恒为 1）；
//   · 拖线前后都**刷新确认**连线真的落盘（BG4 的教训）。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep, fingerprint, diffPanels } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBJ1';
const { browser, page } = await launch();

const VID = 'v-v2hlWY4Br3';        // 视频节点 3（另一个，没连线的）
const CLIP = 'v-oZNpH99MtM';       // 智能剪辑 4

/** ⭐ 数连线：读 aria-label（BG 立的规矩），不读 data-id、不从坐标反推。 */
const edges = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__edge')]
  .map((e) => ({ id: e.getAttribute('data-id'), label: e.getAttribute('aria-label') })));

/** 智能剪辑卡片当前逐字文案。 */
const clipText = () => page.evaluate((id) => {
  const n = [...document.querySelectorAll('.react-flow__node')].find((x) => x.getAttribute('data-id') === id);
  return n ? (n.innerText || '').replace(/\s+/g, ' ').trim() : null;
}, CLIP);

async function selectNode(id, tries = 3) {
  for (let k = 0; k < tries; k++) {
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
      return { err: 'no exclusive point' };
    }, id);
    if (pt.err) return { ok: false, why: pt.err };
    await page.mouse.click(pt.x, pt.y); await page.waitForTimeout(2400);
    const sel = await page.evaluate(() => ({
      n: document.querySelectorAll('.react-flow__node.selected').length,
      who: document.querySelector('.react-flow__node.selected')?.getAttribute('data-id') ?? null }));
    if (sel.n === 1 && sel.who === id) return { ok: true, at: [pt.x, pt.y] };
  }
  return { ok: false, why: '选中断言不过' };
}

/** 取某个口的位置与它父级图标盒的 opacity（BI1 的教训：不读 svg 自身的）。 */
const portInfo = (nid, which) => page.evaluate(([id, w]) => {
  const n = [...document.querySelectorAll('.react-flow__node')].find((x) => x.getAttribute('data-id') === id);
  const h = n && n.querySelector(`[data-handleid="${w}"]`);
  if (!h) return { err: 'no handle' };
  const l1 = h.children[0], l2 = l1 && l1.children[0];
  const r = l1.getBoundingClientRect();
  return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2),
    iconOpacity: l2 ? (l2.getAttribute('style') || '').match(/opacity:\s*([^;"]*)/)?.[1] ?? null : null };
}, [nid, which]);

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1600);
  await fitView(page); await page.waitForTimeout(2000);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '视频 → 智能剪辑 连线前后，参数条逐字对比' });

  const out = {};

  // ═══ A. 连线前：智能剪辑长什么样
  console.log('══════ A. 连线前 ══════');
  await page.mouse.move(120, 120); await page.waitForTimeout(1500);
  const e0 = await edges();
  const t0 = await clipText();
  console.log(`  画布连线 ${e0.length} 条：${JSON.stringify(e0.map((e) => e.label))}`);
  console.log(`  智能剪辑卡片文案：${JSON.stringify(t0)}`);
  out.before = { edges: e0, clipText: t0 };

  // 选中它，看参数条
  const s0 = await selectNode(CLIP);
  console.log(`  选中智能剪辑：${s0.ok ? '✅ ' + s0.at : '✗ ' + s0.why}`);
  if (s0.ok) {
    const fp0 = await fingerprint(page);
    const panels0 = await page.evaluate(() => {
      const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
      return [...document.querySelectorAll('body *')].filter((e) => !skip.has(e.tagName))
        .map((e) => { const r = e.getBoundingClientRect();
          return { t: (e.innerText || '').replace(/\s+/g, ' ').trim(), r }; })
        .filter((x) => x.r.width > 150 && x.r.height > 60 && x.t.length > 4 && x.t.length < 300)
        .filter((x) => x.r.y > 400)
        .map((x) => ({ t: x.t, rect: [Math.round(x.r.x), Math.round(x.r.y), Math.round(x.r.width), Math.round(x.r.height)] }))
        .slice(0, 8);
    });
    console.log(`  选中后画面下半部的大块面板 ${panels0.length} 个：`);
    panels0.forEach((p) => console.log(`     [${p.rect}] "${p.t.slice(0, 90)}"`));
    await shot(page, 'M-206-智能剪辑-未连接空态.png');
    out.shot0 = 'M-206-智能剪辑-未连接空态.png';
    out.before.panels = panels0;
    out.before.fp = fp0;
    await page.keyboard.press('Escape'); await page.waitForTimeout(1400);
  }

  // ═══ B. 拉一条线：视频节点出口 → 智能剪辑入口
  console.log('\n══════ B. 拉线：视频节点 source → 智能剪辑 target ══════');
  const from = await portInfo(VID, 'source');
  const to = await portInfo(CLIP, 'target');
  console.log(`  视频出口：${JSON.stringify(from)}`);
  console.log(`  智能剪辑入口：${JSON.stringify(to)}`);
  if (from.err || to.err) { console.log('  !! 端口没取到'); out.drag = { err: 'no port' }; }
  else {
    await page.mouse.move(from.cx, from.cy); await page.waitForTimeout(1400);
    const fo = await portInfo(VID, 'source');
    console.log(`  悬停后出口图标 opacity = ${fo.iconOpacity}（BI1 判据：读父级 L2）`);

    await page.mouse.down(); await page.waitForTimeout(600);
    for (let i = 1; i <= 8; i++) {
      await page.mouse.move(from.cx + (to.cx - from.cx) * i / 8, from.cy + (to.cy - from.cy) * i / 8);
      await page.waitForTimeout(180);
    }
    await page.mouse.up(); await page.waitForTimeout(2600);

    const e1 = await edges();
    const t1 = await clipText();
    console.log(`  松手后连线 ${e1.length} 条：${JSON.stringify(e1.map((e) => e.label))}`);
    console.log(`  智能剪辑卡片文案：${JSON.stringify(t1)}`);
    out.drag = { from, to, hoverOpacity: fo.iconOpacity, edges: e1, clipText: t1 };
  }

  // ═══ C. ⭐ 刷新验证：临时连线不算数，刷新后才算数（BG4 的教训）
  console.log('\n══════ C. 刷新验证连线是否落盘 ══════');
  await page.reload({ waitUntil: 'domcontentloaded' }); await page.waitForTimeout(6500);
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1800);
  await fitView(page); await page.waitForTimeout(2000);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  const e2 = await edges();
  const t2 = await clipText();
  console.log(`  刷新后连线 ${e2.length} 条：${JSON.stringify(e2.map((e) => e.label))}`);
  console.log(`  刷新后智能剪辑文案：${JSON.stringify(t2)}`);
  out.afterReload = { edges: e2, clipText: t2, persisted: e2.length > e0.length };

  // ═══ D. 连上之后：选中智能剪辑，逐字读它的卡片与参数条
  console.log('\n══════ D. 连上之后的智能剪辑 ══════');
  await page.mouse.move(120, 120); await page.waitForTimeout(1400);
  const s1 = await selectNode(CLIP);
  console.log(`  选中：${s1.ok ? '✅' : '✗ ' + s1.why}`);
  if (s1.ok) {
    const panels1 = await page.evaluate(() => {
      const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
      return [...document.querySelectorAll('body *')].filter((e) => !skip.has(e.tagName))
        .map((e) => { const r = e.getBoundingClientRect();
          return { t: (e.innerText || '').replace(/\s+/g, ' ').trim(), r,
            kids: [...e.children].length }; })
        .filter((x) => x.r.width > 150 && x.r.height > 60 && x.t.length > 4 && x.t.length < 400 && x.r.y > 400)
        .map((x) => ({ t: x.t, kids: x.kids, rect: [Math.round(x.r.x), Math.round(x.r.y), Math.round(x.r.width), Math.round(x.r.height)] }))
        .slice(0, 10);
    });
    console.log(`  画面下半部大面板 ${panels1.length} 个：`);
    panels1.forEach((p) => console.log(`     [${p.rect}] kids=${p.kids} "${p.t.slice(0, 140)}"`));
    out.afterPanels = panels1;
    await shot(page, 'M-207-智能剪辑-连接后.png');
    out.shot1 = 'M-207-智能剪辑-连接后.png';
  }

  // 参数条逐枚悬停实名（BI4 的教训：先让参数条进视口）
  const z = await page.evaluate(() => {
    const e = [...document.querySelectorAll('button,[role="button"]')]
      .find((x) => x.getAttribute('aria-label') === '缩放选项');
    if (!e) return null; const r = e.getBoundingClientRect();
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
  });
  if (z) {
    await page.mouse.click(z[0], z[1]); await page.waitForTimeout(1600);
    const inp = await page.$('input[aria-label="缩放比例"]');
    if (inp) { await inp.fill('45'); await inp.press('Enter'); await page.waitForTimeout(2000); }
    await page.keyboard.press('Escape'); await page.waitForTimeout(1500);
  }
  const s2 = await selectNode(CLIP);
  if (s2.ok) {
    const cands = await page.evaluate(() => {
      const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
      return [...document.querySelectorAll('button,[role="button"]')].filter((e) => !skip.has(e.tagName))
        .map((e) => { const r = e.getBoundingClientRect();
          return { r, e }; })
        .filter((x) => x.r.width >= 20 && x.r.width <= 200 && x.r.height >= 20 && x.r.height <= 40
          && x.r.x > 0 && x.r.y > 0 && x.r.x + x.r.width < innerWidth && x.r.y + x.r.height < innerHeight)
        .map((x) => ({ text: (x.e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 22),
          aria: x.e.getAttribute('aria-label'),
          rect: [Math.round(x.r.x), Math.round(x.r.y), Math.round(x.r.width), Math.round(x.r.height)],
          cx: Math.round(x.r.x + x.r.width / 2), cy: Math.round(x.r.y + x.r.height / 2) }));
    });
    const names = [];
    for (const b of cands) {
      await page.mouse.move(b.cx, b.cy); await page.waitForTimeout(1400);
      const tip = await page.evaluate(() => [...document.querySelectorAll('[class*="Tooltip-tooltip"]')]
        .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
        .map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim())
        .filter((t) => t && !/按 ESC 退出|^新功能/.test(t)));
      const label = tip[0] || (b.text ? `文字「${b.text}」` : '（无名）');
      names.push({ ...b, tip, label });
      console.log(`    [${b.rect}] ${label}`);
    }
    out.barNames = names;
    console.log('  ⭐ 实名清单：', JSON.stringify(names.map((n) => n.label)));
    await shot(page, 'M-208-智能剪辑-连接后参数条.png');
    out.shot2 = 'M-208-智能剪辑-连接后参数条.png';
  }

  await logStep(B, {
    id: 'BJ1-smart-clip-connected',
    title: '智能剪辑接上视频之后变成什么',
    target: '手册里智能剪辑一直是「空空如也，请连接视频节点后操作」的空态，接上之后会怎样一字未写。'
      + '⭐ 连线必须**刷新后**再数（BG4：拖动中的临时连线会自己消失，不落盘）。'
      + '⚠️ 只连这一条，不点任何执行类按钮。',
    evidence: out,
    visible_text: JSON.stringify({ 前: out.before?.clipText, 后: out.afterReload?.clipText,
      连线前: out.before?.edges?.length, 连线后: out.afterReload?.edges?.length,
      落盘: out.afterReload?.persisted, 参数条: out.barNames?.map?.((n) => n.label) }).slice(0, 3000),
    shot: out.shot1,
  });
  console.log('\nBJ1 完成');
} finally {
  await browser.close();
}
