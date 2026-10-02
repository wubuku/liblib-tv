// Batch BI5 — 消除 BI4 留下的那个疑点。
//
// BI4 的阳性对照：先点「提示词优化」读到「提示词为空，请输入内容后点击」，
// 再点「翻译提示词」**读到一模一样的 5 条、同样的坐标**。
// 两种解释都讲得通：
//   (a) 翻译提示词给的是同一条提示；
//   (b) 第一次的提示条**没被清掉**，第二次读到的是它的残留。
// BI4 确实在两次之间调了 `clearToasts()`，但那只是**清提示条**的通用工具，
// 并没有证明它当场清干净了 —— **没有基线读数，就分不开 (a) 和 (b)**。
//
// ⭐ 治法：**把顺序倒过来**，并且在**第一次点击之前**先读一次基线。
//   基线 0 条 → 点翻译 → 读到 N 条 ⇒ (a) 成立。
//   基线 0 条 → 点翻译 → 读到 0 条 ⇒ (b) 被排除，是翻译真不给提示。
// 每一步都把当前页面上的提示条**逐条**列出来（不只是条数），
// 出现时间/位置不同都能看出来。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBI5';
const { browser, page } = await launch();

/** 列出页面上所有「提示条」候选：顶部 160px 内、含关键字的可见元素。 */
const hints = () => page.evaluate(() => {
  const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
  return [...document.querySelectorAll('body *')].filter((e) => !skip.has(e.tagName))
    .map((e) => { const r = e.getBoundingClientRect();
      return { t: (e.innerText || '').replace(/\s+/g, ' ').trim(), r,
        cls: (typeof e.className === 'string' ? e.className : '').slice(0, 46) }; })
    .filter((x) => x.r.width > 0 && x.r.height > 0 && x.r.y < 160 && x.r.y > 0
      && x.t.length < 60 && /提示词|为空|请输入|翻译/.test(x.t))
    .map((x) => ({ t: x.t, cls: x.cls, rect: [Math.round(x.r.x), Math.round(x.r.y), Math.round(x.r.width), Math.round(x.r.height)] }));
});

const readTip = async (x, y) => {
  await page.mouse.move(x, y); await page.waitForTimeout(1500);
  return page.evaluate(() => [...document.querySelectorAll('[class*="Tooltip-tooltip"]')]
    .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
    .map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim())
    .filter((t) => t && !/按 ESC 退出|^新功能/.test(t)));
};

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1600);
  await fitView(page); await page.waitForTimeout(1800);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '倒序 + 基线读数，排除提示条残留' });

  const out = {};

  // 选视频节点
  const s = await page.evaluate(() => {
    const n = [...document.querySelectorAll('.react-flow__node')].find((x) => x.getAttribute('data-id') === 'v-eMpqKtiLlx');
    if (!n) return { err: 'no node' };
    const r = n.getBoundingClientRect();
    for (let fy = 0.18; fy <= 0.85; fy += 0.1) for (let fx = 0.08; fx <= 0.95; fx += 0.06) {
      const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
      const o = document.elementFromPoint(x, y);
      if (o && o.closest('.react-flow__node') === n) return { x, y };
    }
    return { err: 'no exclusive point' };
  });
  if (s.err) throw new Error(s.err);
  await page.mouse.click(s.x, s.y); await page.waitForTimeout(2600);
  const sel = await page.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
  console.log('视频节点选中数 =', sel);
  if (sel !== 1) throw new Error('没能选中视频节点');

  // 认按钮
  const cand = await page.evaluate(() => {
    const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
    return [...document.querySelectorAll('button,[role="button"]')].filter((e) => !skip.has(e.tagName))
      .map((e) => { const r = e.getBoundingClientRect();
        return { e, r }; })
      .filter((x) => x.r.width >= 28 && x.r.width <= 40 && x.r.height >= 28 && x.r.height <= 40
        && x.r.x > 0 && x.r.y > 0 && x.r.x + x.r.width < innerWidth && x.r.y + x.r.height < innerHeight)
      .map((x) => ({ cx: Math.round(x.r.x + x.r.width / 2), cy: Math.round(x.r.y + x.r.height / 2),
        rect: [Math.round(x.r.x), Math.round(x.r.y), Math.round(x.r.width), Math.round(x.r.height)] }));
  });
  let tr = null, op = null;
  for (const b of cand) {
    const t = await readTip(b.cx, b.cy);
    if (/翻译/.test(t.join(' '))) tr = b;
    if (/提示词优化/.test(t.join(' '))) op = b;
  }
  console.log('认到 翻译提示词 =', JSON.stringify(tr), ' 提示词优化 =', JSON.stringify(op));
  if (!tr) throw new Error('没认到「翻译提示词」');
  out.buttons = { tr, op };

  // ═══ 关键：基线 → 点翻译 → 读；再点提示词优化 → 读
  console.log('\n══════ 倒序验证（先点翻译）══════');
  await page.mouse.move(720, 200); await page.waitForTimeout(1500);

  const h0 = await hints();
  console.log(`  基线（点击前）：提示条候选 ${h0.length} 条 ${JSON.stringify(h0.map((x) => x.t))}`);

  await page.mouse.click(tr.cx, tr.cy); await page.waitForTimeout(3200);
  const h1 = await hints();
  console.log(`  点「翻译提示词」后：${h1.length} 条`);
  h1.forEach((x) => console.log(`     "${x.t}"  cls=${x.cls}  rect=${JSON.stringify(x.rect)}`));

  const verdict1 = h1.length > 0;
  console.log(`  ⭐ 结论 ${verdict1 ? '**(a) 翻译提示词自己就会弹提示** —— 不是残留' : '**读不到提示** —— 需再查是不是读法或时序问题'}`);

  // 清掉，再点对照
  await clearToasts(page); await page.waitForTimeout(2000);
  await page.mouse.move(300, 300); await page.waitForTimeout(1200);
  const h2 = await hints();
  console.log(`\n  清理后复查：${h2.length} 条 ${JSON.stringify(h2.map((x) => x.t))}  ← 确认真的清干净了`);
  if (op) {
    await page.mouse.click(op.cx, op.cy); await page.waitForTimeout(3200);
    const h3 = await hints();
    console.log(`  点「提示词优化」后：${h3.length} 条`);
    h3.forEach((x) => console.log(`     "${x.t}"  cls=${x.cls}  rect=${JSON.stringify(x.rect)}`));
    out.control = { before: h2.length, after: h3.length, items: h3 };
  }

  out.baseline = h0;
  out.afterTranslate = h1;
  out.afterClear = h2;
  out.verdict = verdict1 ? '翻译提示词自己弹提示' : '翻译提示词未读到提示';
  console.log(`\n  ⭐ 最终判定：${out.verdict}`);
  console.log(`  ⭐ 两次提示文字是否逐字相同：${JSON.stringify(h1.map((x) => x.t)) === JSON.stringify(out.control?.after ? out.control.items.map((x) => x.t) : [])}`);

  await logStep(B, {
    id: 'BI5-reverse-order-baseline',
    title: '倒序 + 基线读数：排除提示条残留',
    target: 'BI4 两次点击读到一模一样的提示，无法区分「翻译自己弹」与「读到上次残留」。'
      + '本轮把顺序倒过来，并在首次点击前读基线；两次之间清空后**复查**是否真的清干净。',
    evidence: out,
    visible_text: JSON.stringify({ 基线: out.baseline?.length, 翻译后: out.afterTranslate?.map?.((x) => x.t),
      清理后: out.afterClear?.length, 对照后: out.control?.after, 判定: out.verdict }).slice(0, 2000),
  });
  console.log('\nBI5 完成');
} finally {
  await browser.close();
}
