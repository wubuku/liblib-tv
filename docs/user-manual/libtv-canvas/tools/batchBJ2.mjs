// Batch BJ2 — 坐实智能剪辑面板里那枚「①」卡片是不是刚连上的那个视频。
//
// BJ1 已经拍到两张对照图：
//   M-206（未连接）：面板里只有 `+参考` / 「描述想剪成什么效果」
//   M-207（已连接）：面板里**多出一枚 `①` 卡片**（带播放图标），蓝色连线也确实存在
// 且卡片上那句「空空如也，请连接视频节点后操作」**前后一字未变**。
//
// ⭐ 但「那枚 ① 就是刚连上的视频」目前只是**从画面推的**。这轮把它读实：
//   · 读它的完整 innerText / title / aria / alt / data-*；
//   · 读它挂着的源节点 id（如果 DOM 里有）；
//   · ⭐ 做一个**可逆的对照实验**：断开这条线 → 芯片应消失；再连回来 → 应恢复。
//     （断线：选中智能剪辑后用 ⌘L 切换，或直接拖走端口。**不做删除节点**。）
//   · 对照完**必须复原成连接状态**，并刷新确认。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBJ2';
const { browser, page } = await launch();
const CLIP = 'v-oZNpH99MtM';
const VID = 'v-v2hlWY4Br3';

const edges = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__edge')]
  .map((e) => e.getAttribute('aria-label')));

const cardText = () => page.evaluate((id) => {
  const n = [...document.querySelectorAll('.react-flow__node')].find((x) => x.getAttribute('data-id') === id);
  return n ? (n.innerText || '').replace(/\s+/g, ' ').trim() : null;
}, CLIP);

/** 智能剪辑选中后，那块参数面板（节点正下方那块）的逐字内容 + 里面所有可交互元素。 */
async function panelDump() {
  const sel = await page.evaluate((id) => {
    const n = [...document.querySelectorAll('.react-flow__node')].find((x) => x.getAttribute('data-id') === id);
    if (!n) return { err: 'no node' };
    const r = n.getBoundingClientRect();
    for (let fy = 0.18; fy <= 0.85; fy += 0.1) for (let fx = 0.08; fx <= 0.95; fx += 0.06) {
      const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
      const o = document.elementFromPoint(x, y);
      if (o && o.closest('.react-flow__node') === n) return { x, y };
    }
    return { err: 'no exclusive point' };
  }, CLIP);
  if (sel.err) return { err: sel.err };
  await page.mouse.click(sel.x, sel.y); await page.waitForTimeout(2600);
  const ok = await page.evaluate(() => ({
    n: document.querySelectorAll('.react-flow__node.selected').length,
    who: document.querySelector('.react-flow__node.selected')?.getAttribute('data-id') ?? null }));
  if (ok.n !== 1 || ok.who !== CLIP) return { err: `选中断言不过 ${JSON.stringify(ok)}` };

  return page.evaluate(() => {
    const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
    const all = [...document.querySelectorAll('body *')].filter((e) => !skip.has(e.tagName))
      .map((e) => { const r = e.getBoundingClientRect();
        return { e, t: (e.innerText || '').replace(/\s+/g, ' ').trim(), r }; })
      .filter((x) => x.r.width > 200 && x.r.height > 150 && x.t.length > 4 && x.r.y > 200);
    // 取面积最大的那块 = 参数面板
    all.sort((a, b) => b.r.width * b.r.height - a.r.width * a.r.height);
    const p = all[0];
    if (!p) return { err: 'no panel' };
    const items = [...p.e.querySelectorAll('*')].filter((e) => !skip.has(e.tagName))
      .map((e) => { const r = e.getBoundingClientRect();
        return { tag: e.tagName, t: (e.innerText || e.getAttribute('title') || '').replace(/\s+/g, ' ').trim().slice(0, 40),
          title: e.getAttribute('title'), alt: e.getAttribute('alt'), aria: e.getAttribute('aria-label'),
          data: [...e.attributes].filter((a) => a.name.startsWith('data-')).map((a) => `${a.name}=${a.value}`).join(' ').slice(0, 80),
          rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; })
      .filter((x) => x.rect[2] > 8 && x.rect[3] > 8 && x.rect[2] < 400 && x.rect[3] < 200)
      .filter((x) => x.t || x.title || x.alt || x.aria)
      .slice(0, 40);
    return { panelRect: [Math.round(p.r.x), Math.round(p.r.y), Math.round(p.r.width), Math.round(p.r.height)],
      panelText: p.t.slice(0, 300), items };
  });
}

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1600);
  await fitView(page); await page.waitForTimeout(2000);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '坐实 ① 芯片身份 + 断开/重连的可逆对照' });

  const out = {};

  // ═══ A. 当前（已连接）状态
  console.log('══════ A. 已连接状态 ══════');
  const eA = await edges();
  const cA = await cardText();
  console.log(`  连线 ${eA.length} 条：${JSON.stringify(eA)}`);
  console.log(`  卡片文案：${JSON.stringify(cA)}`);
  const pA = await panelDump();
  console.log(`  参数面板：${pA.err || JSON.stringify(pA.panelRect)}`);
  if (!pA.err) {
    console.log(`  面板逐字：${JSON.stringify(pA.panelText)}`);
    console.log(`  面板内元素 ${pA.items.length} 个：`);
    pA.items.forEach((i) => console.log(`    [${i.rect}] <${i.tag}> "${i.t}" title=${i.title} alt=${i.alt} aria=${i.aria} ${i.data}`));
  }
  out.connected = { edges: eA, card: cA, panel: pA };

  // ═══ B. 可逆对照：断开这条线
  console.log('\n══════ B. 对照：断开这条连线 ══════');
  await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  // 选中视频节点，用 ⌘L 切掉它与智能剪辑的连线（BG/E 验过 ⌘L 能加也能断）
  const vp = await page.evaluate((id) => {
    const n = [...document.querySelectorAll('.react-flow__node')].find((x) => x.getAttribute('data-id') === id);
    if (!n) return { err: 'no node' };
    const r = n.getBoundingClientRect();
    for (let fy = 0.18; fy <= 0.85; fy += 0.1) for (let fx = 0.08; fx <= 0.95; fx += 0.06) {
      const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
      const o = document.elementFromPoint(x, y);
      if (o && o.closest('.react-flow__node') === n) return { x, y };
    }
    return { err: 'no point' };
  }, VID);
  if (vp.err) { console.log('  ' + vp.err); } else {
    await page.mouse.click(vp.x, vp.y); await page.waitForTimeout(2400);
    const selNow = await page.evaluate(() => document.querySelector('.react-flow__node.selected')?.getAttribute('data-id'));
    console.log(`  选中：${selNow}`);
    await page.keyboard.down('Meta'); await page.keyboard.press('l'); await page.keyboard.up('Meta');
    await page.waitForTimeout(2800);
    const eB = await edges();
    console.log(`  ⌘L 后连线 ${eB.length} 条：${JSON.stringify(eB)}`);
    out.afterCut = { edges: eB, sel: selNow };
    const pB = await panelDump();
    console.log(`  断开后卡片文案：${JSON.stringify(await cardText())}`);
    if (!pB.err) {
      console.log(`  断开后面板逐字：${JSON.stringify(pB.panelText)}`);
      const hasChip = /①|✕|×/.test(pB.panelText) || pB.items.some((i) => /^\d+$/.test(i.t));
      console.log(`  ⭐ 面板里还有没有那枚 ① 卡片？ ${hasChip ? '有 ⚠️' : '**没有了** ✅'}`);
      out.cutPanel = { text: pB.panelText, hasChip };
      await shot(page, 'M-209-智能剪辑-断开后.png');
      out.shotCut = 'M-209-智能剪辑-断开后.png';
    }
  }

  // ═══ C. 复原：再连回来
  console.log('\n══════ C. 复原：把连线连回去 ══════');
  await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  const from = await page.evaluate((id) => {
    const n = [...document.querySelectorAll('.react-flow__node')].find((x) => x.getAttribute('data-id') === id);
    const h = n.querySelector('[data-handleid="source"]'); const r = h.children[0].getBoundingClientRect();
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
  }, VID);
  const to = await page.evaluate((id) => {
    const n = [...document.querySelectorAll('.react-flow__node')].find((x) => x.getAttribute('data-id') === id);
    const h = n.querySelector('[data-handleid="target"]'); const r = h.children[0].getBoundingClientRect();
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
  }, CLIP);
  await page.mouse.move(from[0], from[1]); await page.waitForTimeout(1200);
  await page.mouse.down(); await page.waitForTimeout(500);
  for (let i = 1; i <= 8; i++) { await page.mouse.move(from[0] + (to[0] - from[0]) * i / 8, from[1] + (to[1] - from[1]) * i / 8); await page.waitForTimeout(180); }
  await page.mouse.up(); await page.waitForTimeout(2600);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1400);
  const eC = await edges();
  console.log(`  连回后连线 ${eC.length} 条：${JSON.stringify(eC)}`);

  // 刷新确认落盘（BG4）
  await page.reload({ waitUntil: 'domcontentloaded' }); await page.waitForTimeout(6500);
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1800);
  await fitView(page); await page.waitForTimeout(2000);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  const eD = await edges();
  console.log(`  ⭐ 刷新后连线 ${eD.length} 条：${JSON.stringify(eD)}`);
  const pD = await panelDump();
  if (!pD.err) {
    console.log(`  复原后面板逐字：${JSON.stringify(pD.panelText)}`);
    out.restoredPanel = pD.panelText;
  }
  out.restored = { edges: eD, card: await cardText() };
  console.log(`  复原后卡片文案：${JSON.stringify(out.restored.card)}`);

  await logStep(B, {
    id: 'BJ2-chip-identity-and-control',
    title: '坐实 ① 芯片身份 + 断开/重连可逆对照',
    target: 'BJ1 从画面推出「面板里多出的 ① 卡片 = 刚连上的视频」。本轮读它的 title/alt/aria/data-*，'
      + '并做**可逆对照**：⌘L 断开 → 芯片应消失 → 再连回来 → 芯片恢复，最后刷新确认落盘。'
      + '⭐ 目的是让「芯片跟着连线走」成为**实验结论**，不是看图猜的。',
    evidence: out,
    visible_text: JSON.stringify({ 已连: out.connected?.panel?.panelText, 断开后: out.cutPanel?.text,
      断开后还有芯片: out.cutPanel?.hasChip, 复原后: out.restoredPanel,
      连线: out.restored?.edges, 卡片: out.restored?.card }).slice(0, 2500),
    shot: out.shotCut,
  });
  console.log('\nBJ2 完成');
} finally {
  await browser.close();
}
