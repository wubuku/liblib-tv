// Batch P7 —— 参数面板右上角那个「⤢」到底是干什么的？
//
// batchP6 把滑杆拉进了视口（y=698/734/770），但截图里**根本看不见它们** ——
// 参数面板卡片的底边在 CSS y≈652，滑杆在 698+，
// 也就是**高级设置分区挂在卡片外面、被裁掉了**。
// 这解释了为什么 Audio 文档里「3 个滑杆」一直只存在于 innerText 里、没有截图佐证。
//
// 面板右上角有个「⤢」图标（batchP5 量到是 <BUTTON> 41×28）。
// batchP5 点它时用的是「候选列表里最后一个」这种定位，不可靠。
// 这轮按**位置**精确定位（面板卡片的右上角），点它，看卡片有没有变高、滑杆有没有现身。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { nodeCount, fitView } from './canvas-ops.mjs';
import { openDropdown } from './canvas-dropdown.mjs';

const SPACE = '10354929';
const B = 'batchP7';
const { browser, page } = await launch();

/** 同时量：节点本体、参数面板卡片、滑杆、以及卡片右上角那枚按钮。 */
const probe = () => page.evaluate(() => {
  const txt = (e) => (e.innerText || e.textContent || '').replace(/\s+/g, ' ').trim();
  const n = [...document.querySelectorAll('.react-flow__node')][0];
  const nr = n ? n.getBoundingClientRect() : null;
  // 参数面板卡片 = 节点下方、含「参考 / 描述你想要」的那块
  let card = null;
  for (const d of document.querySelectorAll('div')) {
    const b = d.getBoundingClientRect();
    if (b.width < 300 || b.height < 60) continue;
    if (!nr || b.y < nr.bottom - 30) continue;
    if (!/参考|描述你想要|Seed Audio|高级设置/.test(txt(d))) continue;
    if (!card || b.height < card.getBoundingClientRect().height) card = d;
  }
  const cr = card ? card.getBoundingClientRect() : null;
  const sliders = [...document.querySelectorAll('[class*="mantine-Slider-root"]')].map((e) => {
    const b = e.getBoundingClientRect();
    return { y: Math.round(b.y), bottom: Math.round(b.bottom), x: Math.round(b.x), w: Math.round(b.width) };
  }).sort((a, b) => a.y - b.y);
  // 卡片右上角的按钮：在卡片右上角 60×60 范围内
  let expander = null;
  if (cr) {
    const cands = [...document.querySelectorAll('button')].filter((e) => {
      const b = e.getBoundingClientRect();
      return b.x > cr.right - 70 && b.x < cr.right + 10 && b.y > cr.top - 10 && b.y < cr.top + 70
        && b.width > 8 && b.height > 8;
    });
    if (cands.length) {
      const b = cands[cands.length - 1].getBoundingClientRect();
      expander = { x: Math.round(b.x + b.width / 2), y: Math.round(b.y + b.height / 2),
        w: Math.round(b.width), h: Math.round(b.height),
        cls: (cands[cands.length - 1].className || '').toString().slice(0, 46),
        aria: cands[cands.length - 1].getAttribute('aria-label') || cands[cands.length - 1].title || null,
        inViewport: b.y >= 0 && b.bottom <= window.innerHeight };
    }
  }
  // 滑杆是否真的在卡片可视范围内
  const slidersVisible = sliders.length ? sliders.every((s) => cr && s.bottom <= cr.bottom + 2) : null;
  return {
    nodeRect: nr ? [Math.round(nr.x), Math.round(nr.y), Math.round(nr.width), Math.round(nr.height)] : null,
    cardRect: cr ? [Math.round(cr.x), Math.round(cr.y), Math.round(cr.width), Math.round(cr.height)] : null,
    cardText: card ? txt(card).slice(0, 220) : null,
    sliders, slidersInsideCard: slidersVisible,
    expander, viewportH: window.innerHeight,
  };
});

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4000 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '按位置精确定位面板右上角的「⤢」，看它是否展开高级设置' });

  await openDropdown(page, 1000);
  await page.getByRole('button', { name: '新建画布', exact: true }).first().click();
  await page.waitForTimeout(4500);
  await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(1500);
  await page.mouse.dblclick(700, 180); await page.waitForTimeout(1200);
  await page.locator('[data-guide-lockable-portal="true"], [data-canvas-menu-portal="true"]').first()
    .getByText('音频', { exact: false }).first().click({ timeout: 8000 });
  await page.waitForTimeout(2800);
  await fitView(page, 1);
  for (let i = 0; i < 4; i += 1) { await page.keyboard.press('Meta+-'); await page.waitForTimeout(700); }
  await page.waitForTimeout(1500);
  // 往上平移一点，给面板底部腾地方
  await page.keyboard.down('Space');
  await page.mouse.move(700, 600); await page.mouse.down(); await page.waitForTimeout(200);
  for (let i = 1; i <= 6; i += 1) { await page.mouse.move(700, 600 - i * 18, { steps: 2 }); await page.waitForTimeout(50); }
  await page.mouse.up(); await page.keyboard.up('Space'); await page.waitForTimeout(1500);

  const before = await probe();
  console.log('点之前:', JSON.stringify(before, null, 1));
  await shot(page, 'M-25-参数面板-点展开之前.png');

  let after = null;
  if (before.expander && before.expander.inViewport) {
    await page.mouse.click(before.expander.x, before.expander.y);
    await page.waitForTimeout(2800);
    after = await probe();
    console.log('点之后:', JSON.stringify({ card: after.cardRect, sliders: after.sliders, inside: after.slidersInsideCard }, null, 1));
    await shot(page, 'M-26-参数面板-点展开之后.png');
  }

  await logStep(B, { id: 'P7-panel-expander', title: '参数面板右上角「⤢」的作用',
    target: before.expander ? `点 (${before.expander.x},${before.expander.y}) 的面板右上角按钮` : '没找到该按钮',
    evidence: { before, after },
    visible_text: `参数面板卡片 ${JSON.stringify(before.cardRect)}，3 个滑杆在 y=${JSON.stringify(before.sliders.map((s) => s.y))}、` +
      `底边 ${JSON.stringify(before.sliders.map((s) => s.bottom))}，**是否落在卡片内 ${before.slidersInsideCard}**（卡片底边 ${before.cardRect?.[1] + before.cardRect?.[3]}）；` +
      `点之前卡片高 ${before.cardRect?.[3]}` + (after ? `，点之后卡片 ${JSON.stringify(after.cardRect)}、滑杆是否在卡内 ${after.slidersInsideCard}` : '，按钮没点到'),
    shot: after ? 'M-26-参数面板-点展开之后.png' : 'M-25-参数面板-点展开之前.png' });
  console.log('节点:', await nodeCount(page));
} finally {
  await browser.close();
}
