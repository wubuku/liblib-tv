// Batch BI1d — 四态读数坐实：⊕ 是「悬停**或**选中」才显形，不只是选中。
//
// BI1c 的像素对比已经给出答案：
//   远离（未选中）→ 无 ⊕ ；悬停在口上（未选中）→ ⊕ 出现 ；选中 → ⊕ 出现
// 所以 BH2 记的「默认 opacity: 0」**是对的**，但「**选中**才显形」**说窄了** ——
// 悬停同样能让它显形，而 BH2 的状态梯度里没做「纯悬停」这一态。
//
// ⭐ 这也解释了 M-200 那张整页截图里为什么四个节点的 ⊕ 都在：
//    拍它时**鼠标正悬停在口上**（BI1 的态 2），不是「纯未选中」。
//    我一度据这张图判定「未选中也一直显示」—— 那是忘了鼠标在哪，属于
//    与 §30「悬停色 vs 开启色只差 0.05 透明度」完全同族的误判：
//    **拍完照不确认鼠标位置，截图就会替你撒谎。**
//
// 本轮把 L2 的 inline opacity 在**四个状态**上各读一次，
// 并输出两张正文用图：M-200（悬停态）与 M-201（远离态，⊕ 全部消失）。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBI1d';
const { browser, page } = await launch();
const ID = 'i-9nlG6HdjK2';

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1600);
  await fitView(page); await page.waitForTimeout(1800);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '四态读数坐实「悬停或选中」都显形' });

  // 锚定元素
  await page.evaluate((id) => {
    const n = [...document.querySelectorAll('.react-flow__node')].find((x) => x.getAttribute('data-id') === id);
    const h = n.querySelector('[data-handleid="source"]');
    window.__k = { n, h, l1: h.children[0], l2: h.children[0].children[0] };
  }, ID);

  /** 同时读「属性」「计算值」「鼠标位置」—— 每次读数都必须报鼠标在哪 */
  const read = (label) => page.evaluate((lab) => {
    const { n, l1, l2 } = window.__k;
    const r2 = l2.getBoundingClientRect(), r1 = l1.getBoundingClientRect();
    return { label: lab,
      selected: n.classList.contains('selected'),
      selCount: document.querySelectorAll('.react-flow__node.selected').length,
      l2AttrOpacity: (l2.getAttribute('style') || '').match(/opacity:\s*([^;"]*)/)?.[1] ?? null,
      l2ComputedOpacity: getComputedStyle(l2).opacity,
      l2Rect: [Math.round(r2.x), Math.round(r2.y), Math.round(r2.width), Math.round(r2.height)],
      l1Rect: [Math.round(r1.x), Math.round(r1.y), Math.round(r1.width), Math.round(r1.height)],
      l1ComputedW: getComputedStyle(l1).width,
    };
  }, label);

  const rows = [];

  // 态 1：鼠标停在画布左上角，远离一切
  await page.mouse.move(120, 120); await page.waitForTimeout(1800);
  rows.push(await read('① 鼠标远离（120,120）'));
  await shot(page, 'M-201-连接口-远离时不显示.png');

  // 态 2：悬停在**另一个节点**的口上 —— 本节点仍未被碰
  await page.evaluate(() => {
    const others = [...document.querySelectorAll('.react-flow__node')]
      .filter((x) => x.getAttribute('data-id') !== 'i-9nlG6HdjK2');
    for (const o of others) { const h = o.querySelector('[data-handleid="source"]'); if (h) { window.__o = h.children[0]; break; } }
    if (window.__o) { const r = window.__o.getBoundingClientRect();
      window.__op = [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }
  });
  const op = await page.evaluate(() => window.__op || null);
  if (op) {
    await page.mouse.move(op[0], op[1]); await page.waitForTimeout(1800);
    rows.push(await read('② 悬停在**别的**节点的口上'));
  }

  // 态 3：悬停本节点的口（仍未点选）
  const circ = await page.evaluate(() => { const r = window.__k.l1.getBoundingClientRect();
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
  await page.mouse.move(circ[0], circ[1]); await page.waitForTimeout(1800);
  rows.push(await read('③ 悬停本节点的口（未点选）'));
  await shot(page, 'M-200-连接口-悬停未选中.png');

  // 态 4：点选
  const body = await page.evaluate(() => { const r = window.__k.n.getBoundingClientRect();
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
  await page.mouse.click(body[0], body[1]); await page.waitForTimeout(2400);
  rows.push(await read('④ 已点选'));

  console.log('══════ 四态读数 ══════');
  console.log('  状态 | 选中数 | L2 属性 opacity | L2 计算 opacity');
  for (const r of rows) {
    console.log(`  ${r.label.padEnd(26)} | ${r.selCount} | ${String(r.l2AttrOpacity).padEnd(6)} | ${r.l2ComputedOpacity}`);
  }
  const ops = rows.map((r) => r.l2AttrOpacity);
  console.log(`  ⭐ 属性 opacity 的取值序列 = ${JSON.stringify(ops)}`);
  console.log(`  ⭐ 唯一取值 ${JSON.stringify([...new Set(ops)])}`);

  // ⭐ 关键对照：态 ③（悬停未选中）是不是已经变成 1
  const hoverOnly = rows.find((r) => r.label.includes('本节点的口'));
  console.log(`\n  ⭐ 悬停未选中就已经 opacity=${hoverOnly?.l2AttrOpacity} → ` +
    `${String(hoverOnly?.l2AttrOpacity) === '1' ? '⭐ 悬停即可显形，**不需要点选**' : '仍需点选'}`);
  const other = rows.find((r) => r.label.includes('别的'));
  console.log(`  ⭐ 悬停别的节点时本节点 opacity=${other?.l2AttrOpacity} → ` +
    `${other?.l2AttrOpacity === '0' ? '未点亮别的节点时它是灭的，说明是**逐节点**的' : '异常'}`);

  await logStep(B, {
    id: 'BI1d-port-icon-four-states',
    title: '四态坐实：⊕ 是「悬停或选中」都显形',
    target: 'BI1c 像素对比：远离无 ⊕、悬停口上有 ⊕、选中有 ⊕。'
      + '故 BH2 的「默认 opacity: 0」正确，但「选中才显形」说窄了。'
      + '本轮把 inline opacity 在四态上各读一次，并补「悬停别的节点」这一态，'
      + '确认是逐节点点亮而非全局。⭐ 每次读数都连鼠标位置一起报 —— '
      + 'M-200 那张整页截图里 ⊕ 全在，正是因为拍它时鼠标就停在口上。',
    evidence: { rows },
    visible_text: JSON.stringify(rows.map((r) => ({ 态: r.label, 选中: r.selCount,
      属性: r.l2AttrOpacity, 计算: r.l2ComputedOpacity }))).slice(0, 2000),
    shot: 'M-201-连接口-远离时不显示.png',
  });
  console.log('\nBI1d 完成');
} finally {
  await browser.close();
}
