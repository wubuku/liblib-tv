// Batch P8 —— 高级设置到底能不能被看到？逐条排除三种可能。
//
// 已坐实（batchP5/P6/P7）：
//   · 节点本体 [542,119,356,356]
//   · 参数面板卡片在节点下方
//   · 「高级设置 语速 声调 音量」分区在 DOM 里，3 个 Mantine 滑杆在 y=723/759/795
//   · 但每一张截图里，滑杆所在的位置**什么都没有** —— 面板卡片在那之前就结束了
//
// 三种可能，这轮一次一个：
//   A. 面板内部可滚动，滑杆在折叠线以下 → 滚一下就出现
//   B. 滑杆所在容器 visibility/height 为 0 → 查 computed style
//   C. 需要先把节点面板「铺开」才算显示 → 找那个 ⤢（用图标特征而不是「卡片右上角」定位，
//      batchP7 就是因为「卡片」选错了元素才没找到它）
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { nodeCount, fitView } from './canvas-ops.mjs';
import { openDropdown } from './canvas-dropdown.mjs';

const SPACE = '10354929';
const B = 'batchP8';
const { browser, page } = await launch();

/** 从滑杆往上找它的所有祖先，看哪一层把它裁掉了。 */
const ancestorChain = () => page.evaluate(() => {
  const s = document.querySelector('[class*="mantine-Slider-root"]');
  if (!s) return null;
  const chain = [];
  let e = s;
  for (let i = 0; i < 14 && e && e !== document.body; i += 1) {
    const b = e.getBoundingClientRect();
    const cs = getComputedStyle(e);
    chain.push({
      i, tag: e.tagName, cls: (e.className || '').toString().slice(0, 38),
      rect: [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)],
      overflow: `${cs.overflow}/${cs.overflowY}`,
      visibility: cs.visibility, display: cs.display, opacity: cs.opacity,
      scrollH: e.scrollHeight, clientH: e.clientHeight,
      scrollable: e.scrollHeight > e.clientHeight + 2,
    });
    e = e.parentElement;
  }
  return chain;
});

/** 找所有内部可滚动的容器（scrollHeight > clientHeight），按能露出滑杆的程度排序。 */
const scrollables = () => page.evaluate(() => {
  const s = document.querySelector('[class*="mantine-Slider-root"]');
  const sb = s ? s.getBoundingClientRect() : null;
  return [...document.querySelectorAll('div')].filter((e) => {
    const cs = getComputedStyle(e);
    if (!(cs.overflowY === 'auto' || cs.overflowY === 'scroll')) return false;
    return e.scrollHeight > e.clientHeight + 2;
  }).map((e) => { const b = e.getBoundingClientRect();
    return { cls: (e.className || '').toString().slice(0, 40), rect: [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)],
      scrollH: e.scrollHeight, clientH: e.clientHeight, scrollTop: e.scrollTop,
      coversSlider: sb ? (b.y <= sb.y && b.bottom >= sb.bottom) : null,
      deltaToSlider: sb ? Math.round(sb.y - b.bottom) : null }; })
    .sort((a, b) => (b.coversSlider === a.coversSlider ? 0 : b.coversSlider ? 1 : -1));
});

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4000 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '滑杆为何看不见：内部滚动 / 被裁 / 需要铺开' });

  await openDropdown(page, 1000);
  await page.getByRole('button', { name: '新建画布', exact: true }).first().click();
  await page.waitForTimeout(4500);
  await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(1500);
  await page.mouse.dblclick(700, 160); await page.waitForTimeout(1200);
  await page.locator('[data-guide-lockable-portal="true"], [data-canvas-menu-portal="true"]').first()
    .getByText('音频', { exact: false }).first().click({ timeout: 8000 });
  await page.waitForTimeout(2800);
  await fitView(page, 1);
  for (let i = 0; i < 5; i += 1) { await page.keyboard.press('Meta+-'); await page.waitForTimeout(650); }
  await page.waitForTimeout(1500);
  await page.keyboard.down('Space');
  await page.mouse.move(700, 600); await page.mouse.down(); await page.waitForTimeout(200);
  for (let i = 1; i <= 6; i += 1) { await page.mouse.move(700, 600 - i * 16, { steps: 2 }); await page.waitForTimeout(50); }
  await page.mouse.up(); await page.keyboard.up('Space'); await page.waitForTimeout(1500);

  const chain = await ancestorChain();
  console.log('滑杆的祖先链（自下而上）:');
  for (const c of chain || []) console.log(`  #${c.i} <${c.tag}> ${c.cls} rect=${JSON.stringify(c.rect)} overflow=${c.overflow} vis=${c.visibility} scrollH/clientH=${c.scrollH}/${c.clientH} 可滚=${c.scrollable}`);
  const sc = await scrollables();
  console.log('\n可滚动容器:', JSON.stringify(sc, null, 1));

  // A：把「盖住滑杆」的可滚动容器滚到底
  const target = sc.find((x) => x.coversSlider) || sc[0];
  let after = null;
  if (target) {
    const info = await page.evaluate((cls) => {
      const e = [...document.querySelectorAll('div')].find((d) => (d.className || '').toString().slice(0, 40) === cls);
      if (!e) return null;
      const b = e.getBoundingClientRect();
      const before = e.scrollTop;
      e.scrollTop = e.scrollHeight;
      return { cls, rect: [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)], scrollTopBefore: before, scrollTopAfter: e.scrollTop };
    }, target.cls);
    await page.waitForTimeout(900);
    const nowSlider = await page.evaluate(() => {
      const s = document.querySelector('[class*="mantine-Slider-root"]');
      if (!s) return null; const b = s.getBoundingClientRect();
      return { y: Math.round(b.y), inViewport: b.y >= 0 && b.bottom <= window.innerHeight };
    });
    after = { scrolled: info, sliderNow: nowSlider };
    console.log('\n滚了之后:', JSON.stringify(after));
    await shot(page, 'M-27-参数面板-滚到底之后.png');
  }

  await logStep(B, { id: 'P8-why-invisible', title: '「高级设置」为什么在 DOM 里却看不见',
    target: target ? `把可滚动容器 ${target.cls.slice(0, 30)} 滚到底` : '页面里没有可滚动容器',
    evidence: { ancestorChain: chain, scrollables: sc, after },
    visible_text: `滑杆祖先链里 ` +
      (chain || []).filter((c) => c.scrollable || c.overflow !== 'visible/visible').slice(0, 4)
        .map((c) => `#${c.i} overflow=${c.overflow} scrollH/clientH=${c.scrollH}/${c.clientH} 可滚=${c.scrollable}`).join('；') +
      `；可滚动容器 ${sc.length} 个 ${JSON.stringify(sc.map((x) => [x.cls.slice(0, 24), x.scrollH, x.clientH, x.coversSlider]))}` +
      (after ? `；滚到底后滑杆 ${JSON.stringify(after.sliderNow)}` : ''),
    shot: after ? 'M-27-参数面板-滚到底之后.png' : undefined });
  console.log('节点:', await nodeCount(page));
} finally {
  await browser.close();
}
