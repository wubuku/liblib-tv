// Batch P —— 收掉 AUDIT 待回走清单第 12 条：图片 / 视频节点的「高级设置」展开后是什么。
//
// Batch G 的结论是「按钮在但没观察到展开」，并且写的原因是「取证时节点处于折叠态」。
// 但那句话有个漏洞：**没观察到展开**和**节点处于折叠态**是两回事，
// 前者是观测结果，后者是当时的猜测。这轮要把两者分开。
//
// 三种可能，这轮分别验：
//   A. 按钮其实没点到（节点卡片被别的元素盖住 / 坐标算错）→ 加前置命中校验
//   B. 点了确实展开，只是展开区在卡片**下方溢出**、不在 innerText 的取样范围里
//      → 前后对比节点的**完整 DOM 元素数 + 滚动高度**，不只看 innerText
//   C. 点了真的不展开（产品行为）→ 如实写「点了没反应」
//
// 另外顺手把「整组执行」以外还没碰过的节点内交互补一补：
// 每个节点卡片里除了「高级设置」还有哪些按钮，一并读出来。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { nodeCount, fitView, readNodeControls } from './canvas-ops.mjs';
import { openDropdown } from './canvas-dropdown.mjs';

const SPACE = '10354929';
const B = 'batchP';
const { browser, page } = await launch();

const N = () => nodeCount(page);
const nodeList = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n, i) => {
  const r = n.getBoundingClientRect();
  return { i, title: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 16),
    x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) };
}));

const GAP = 40, SAFE_TOP = 120, SAFE_BOTTOM = 600;
function findEmptySpot(list, minX = 160) {
  for (let y = SAFE_TOP; y <= SAFE_BOTTOM; y += 20) for (let x = minX; x <= 900; x += 20) {
    if (!list.some((n) => x > n.x - GAP && x < n.x + n.w + GAP && y > n.y - GAP && y < n.y + n.h + GAP)) return { x, y };
  }
  return { x: minX, y: SAFE_TOP };
}
async function addNodeAt(x, y, item) {
  await page.mouse.dblclick(x, y); await page.waitForTimeout(1000);
  await page.locator('[data-guide-lockable-portal="true"], [data-canvas-menu-portal="true"]').first()
    .getByText(item, { exact: false }).first().click({ timeout: 6000 });
  await page.waitForTimeout(2200);
}

/** 节点卡片的完整结构快照：元素数、滚动高度、可见文本、range/数字框数量。 */
const cardSnapshot = (idx) => page.evaluate((i) => {
  const n = [...document.querySelectorAll('.react-flow__node')][i];
  if (!n) return null;
  const pick = (e) => (e.getAttribute('aria-label') || e.getAttribute('placeholder') || (e.innerText || e.textContent || '').trim().replace(/\s+/g, ' ')).slice(0, 40);
  return {
    allElements: n.querySelectorAll('*').length,
    clientH: n.clientHeight, scrollH: n.scrollHeight,
    rect: (() => { const r = n.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; })(),
    text: (n.innerText || '').replace(/\s+/g, ' ').slice(0, 900),
    ranges: [...n.querySelectorAll('input[type="range"]')].map((e) => ({ aria: e.getAttribute('aria-label'), min: e.min, max: e.max, value: e.value, step: e.step })),
    numbers: [...n.querySelectorAll('input[type="number"]')].map((e) => ({ aria: e.getAttribute('aria-label'), value: e.value, min: e.min, max: e.max })),
    selects: [...n.querySelectorAll('[role="combobox"]')].map((e) => pick(e)),
    buttons: [...n.querySelectorAll('button')].map(pick).filter(Boolean),
    // 「高级设置」这一枚按钮的实时坐标
    adv: (() => {
      const e = [...n.querySelectorAll('button')].find((b) => (b.innerText || '').trim() === '高级设置');
      if (!e) return null;
      const b = e.getBoundingClientRect();
      return { x: Math.round(b.x + b.width / 2), y: Math.round(b.y + b.height / 2),
        w: Math.round(b.width), h: Math.round(b.height), visible: b.width > 0 && b.height > 0,
        // 该点上最顶层的是谁 —— 若不是这个按钮，说明被别的元素盖住了
        topAtPoint: (() => { const t = document.elementFromPoint(b.x + b.width / 2, b.y + b.height / 2);
          return t ? `${t.tagName}.${(t.className || '').toString().slice(0, 30)}` : null; })() };
    })(),
  };
}, idx);

/** 滚一下卡片内部，确认展开区是不是在「需要滚动才能看到」的位置。 */
async function scrollCardIntoView(idx) {
  return page.evaluate((i) => {
    const n = [...document.querySelectorAll('.react-flow__node')][i];
    if (!n) return null;
    const before = n.scrollTop;
    n.scrollTop = n.scrollHeight;
    return { scrollTopBefore: before, scrollTopAfter: n.scrollTop, scrollH: n.scrollHeight, clientH: n.clientHeight };
  }, idx);
}

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4000 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '图片/视频节点「高级设置」到底是没点到、展开区溢出、还是真的不展开' });

  await openDropdown(page, 1000);
  await page.getByRole('button', { name: '新建画布', exact: true }).first().click();
  await page.waitForTimeout(4500);
  await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(1500);
  await addNodeAt(findEmptySpot([]).x, findEmptySpot([]).y, '图片');
  await addNodeAt(findEmptySpot(await nodeList()).x, findEmptySpot(await nodeList()).y, '视频');
  await addNodeAt(findEmptySpot(await nodeList()).x, findEmptySpot(await nodeList()).y, '音频');
  await fitView(page, 1); await page.keyboard.press('Meta+-'); await page.waitForTimeout(1600);
  const list = await nodeList();
  console.log('节点:', JSON.stringify(list));

  for (const want of ['图片', '视频', '音频']) {
    const idx = list.findIndex((n) => n.title.includes(want === '图片' ? '图片节点' : want === '视频' ? '视频节点' : '音频节点'));
    if (idx < 0) { console.log('找不到', want, '节点'); continue; }
    try {
      const before = await cardSnapshot(idx);
      console.log(`\n[${want}] 元素数 ${before.allElements} scrollH/clientH ${before.scrollH}/${before.clientH}`);
      console.log(`  高级设置按钮: ${JSON.stringify(before.adv)}`);
      if (!before.adv) { await logStep(B, { id: `P-${want}-no-btn`, title: `${want}节点没有「高级设置」按钮`, visible_text: '卡片里所有按钮：' + JSON.stringify(before.buttons) }); continue; }
      if (!before.adv.visible) { await logStep(B, { id: `P-${want}-hidden`, title: `${want}节点「高级设置」按钮不可见`, visible_text: JSON.stringify(before.adv) }); continue; }

      await page.mouse.click(before.adv.x, before.adv.y);
      await page.waitForTimeout(2600);
      const after = await cardSnapshot(idx);
      const scrolled = await scrollCardIntoView(idx);
      await page.waitForTimeout(600);
      const afterScroll = await cardSnapshot(idx);
      await shot(page, `M-20-高级设置-${want}节点.png`);

      const grew = after.allElements - before.allElements;
      const textGrew = after.text.length - before.text.length;
      const newControls = {
        ranges: after.ranges.length - before.ranges.length,
        numbers: after.numbers.length - before.numbers.length,
        selects: after.selects.length - before.selects.length,
      };
      const verdict = grew > 0 ? `展开（元素 +${grew}）`
        : (scrolled && scrolled.scrollH > scrolled.clientH ? '卡片内部还有未展示内容' : '点了没反应');
      await logStep(B, { id: `P-${want}-advanced`, title: `${want}节点「高级设置」展开实测`,
        target: `点 (${before.adv.x},${before.adv.y}) 的「高级设置」`,
        evidence: { hitTest: before.adv, before: { allElements: before.allElements, scrollH: before.scrollH, clientH: before.clientH, ranges: before.ranges, numbers: before.numbers, selects: before.selects, buttons: before.buttons },
          after: { allElements: after.allElements, scrollH: after.scrollH, clientH: after.clientH, ranges: after.ranges, numbers: after.numbers, selects: after.selects, buttons: after.buttons },
          afterScrollTop: afterScroll.text.slice(0, 400), scrollProbe: scrolled, delta: { elements: grew, text: textGrew, ...newControls } },
        visible_text: `判定：**${verdict}**。点前元素数 ${before.allElements}，点后 ${after.allElements}（${grew >= 0 ? '+' : ''}${grew}）；` +
          `scrollHeight ${before.scrollH} → ${after.scrollH}（clientHeight ${before.clientH} → ${after.clientH}）；` +
          `滑杆 ${before.ranges.length}→${after.ranges.length}、数字框 ${before.numbers.length}→${after.numbers.length}、下拉 ${before.selects.length}→${after.selects.length}；` +
          `命中检测（该点最顶层元素）${JSON.stringify(before.adv.topAtPoint)}；滚到底部后文本 ${JSON.stringify(afterScroll.text.slice(0, 240))}`,
        shot: `M-20-高级设置-${want}节点.png` });
      if (grew > 0) {
        console.log(`  [${want}] ✅ 展开：ranges=${JSON.stringify(after.ranges)} numbers=${JSON.stringify(after.numbers)} selects=${JSON.stringify(after.selects)}`);
      }
    } catch (e) { await logStep(B, { id: `P-${want}`, title: `${want}节点「高级设置」`, failed: true, visible_text: String(e).slice(0, 300) }); }
  }

  console.log('节点:', await N());
} finally {
  await browser.close();
}
