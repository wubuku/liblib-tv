// Batch P4 —— 只为回答一个问题：**音频节点的 3 个滑杆，是打开面板就有，还是要再点一次？**
//
// 手册现在写的是「音频节点点了会展开 3 滑杆 + 3 数字框（语速/声调/音量）」。
// 但 batchP2/P3 已经证明两件相反的事：
//   · 「高级设置」在 DOM 里是 `<div cursor:grab>`，**不是按钮**，点它没有任何交互语义；
//   · 视频 / 图片节点的「高级设置」内容，**打开面板就已经全在**，不需要点。
// 所以那句「点了会展开」很可能也是我自己点歪造出来的。
//
// batchP3 里音频读不到，是因为三个节点在视口里互相重叠、
// Playwright 的可操作性校验直接抛了 TimeoutError（**这正是它该做的事** ——
// 说明「元素被盖住时必须报错」这条纪律是对的）。
// 这轮**一张新画布只放一个音频节点**，从根上排除遮挡。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { nodeCount, fitView } from './canvas-ops.mjs';
import { openDropdown } from './canvas-dropdown.mjs';

const SPACE = '10354929';
const B = 'batchP4';
const { browser, page } = await launch();

const panel = (idx) => page.evaluate((i) => {
  const n = [...document.querySelectorAll('.react-flow__node')][i];
  if (!n) return null;
  const r = n.getBoundingClientRect();
  const text = (n.innerText || '').replace(/\s+/g, ' ').trim();
  const k = text.indexOf('高级设置');
  return {
    allElements: n.querySelectorAll('*').length,
    rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    text, advancedSection: k >= 0 ? text.slice(k) : null,
    ranges: [...n.querySelectorAll('input[type="range"]')].map((e) => ({ aria: e.getAttribute('aria-label'), min: e.min, max: e.max, step: e.step, value: e.value })),
    numbers: [...n.querySelectorAll('input[type="number"]')].map((e) => ({ aria: e.getAttribute('aria-label'), value: e.value, min: e.min, max: e.max, step: e.step })),
    switches: [...n.querySelectorAll('[role="switch"],input[type="checkbox"]')].map((e) => ({ aria: e.getAttribute('aria-label'), checked: e.checked === true || e.getAttribute('aria-checked') === 'true' })),
    labels: [...n.querySelectorAll('label,[class*="label"]')].map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim()).filter(Boolean).slice(0, 30),
  };
}, idx);

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4000 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '一张画布只放一个音频节点，判定滑杆是默认就有还是要点' });

  await openDropdown(page, 1000);
  await page.getByRole('button', { name: '新建画布', exact: true }).first().click();
  await page.waitForTimeout(4500);
  await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(1500);

  // 唯一的节点，放哪儿都不会被压住
  await page.mouse.dblclick(420, 300); await page.waitForTimeout(1200);
  await page.locator('[data-guide-lockable-portal="true"], [data-canvas-menu-portal="true"]').first()
    .getByText('音频', { exact: false }).first().click({ timeout: 8000 });
  await page.waitForTimeout(2600);
  console.log('节点数:', await nodeCount(page));

  await fitView(page, 1); await page.keyboard.press('Meta+-'); await page.waitForTimeout(1600);

  // 折叠态
  const collapsed = await panel(0);
  console.log(`折叠态: 元素 ${collapsed.allElements} 文本 ${JSON.stringify(collapsed.text)}`);

  // 单击打开参数面板
  await page.locator('.react-flow__node').nth(0).click({ position: { x: 200, y: 200 }, timeout: 8000 });
  await page.waitForTimeout(2600);
  const opened = await panel(0);
  await shot(page, 'M-22-音频节点-面板打开.png');
  console.log(`\n打开后: 元素 ${opened.allElements}`);
  console.log(`  全文: ${JSON.stringify(opened.text)}`);
  console.log(`  高级设置分区: ${JSON.stringify(opened.advancedSection)}`);
  console.log(`  滑杆 ${JSON.stringify(opened.ranges)}`);
  console.log(`  数字框 ${JSON.stringify(opened.numbers)}`);

  const hasSlidersRightAway = opened.ranges.length > 0;
  const verdict = hasSlidersRightAway
    ? `**打开参数面板后滑杆就已经在，不需要再点任何东西**（${opened.ranges.length} 滑杆 + ${opened.numbers.length} 数字框）`
    : '**打开面板后没有滑杆**，滑杆在别处（可能需要点别的控件）';

  await logStep(B, { id: 'P4-audio-advanced', title: '音频节点「高级设置」滑杆：默认就有还是要点',
    target: '单击唯一的音频节点打开参数面板，**不点任何其他东西**，直接读滑杆/数字框',
    evidence: { collapsed: { allElements: collapsed.allElements, text: collapsed.text },
      opened: { allElements: opened.allElements, text: opened.text, advancedSection: opened.advancedSection,
        ranges: opened.ranges, numbers: opened.numbers, switches: opened.switches, labels: opened.labels, rect: opened.rect } },
    visible_text: `判定：${verdict}。折叠态元素 ${collapsed.allElements} 个（文本「${collapsed.text}」）；` +
      `单击打开后元素 ${opened.allElements} 个；高级设置分区 ${JSON.stringify(opened.advancedSection)}；` +
      `滑杆 ${JSON.stringify(opened.ranges)}；数字框 ${JSON.stringify(opened.numbers)}；开关 ${JSON.stringify(opened.switches)}`,
    shot: 'M-22-音频节点-面板打开.png' });

  console.log('节点:', await nodeCount(page));
} finally {
  await browser.close();
}
