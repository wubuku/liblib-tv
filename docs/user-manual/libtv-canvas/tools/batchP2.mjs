// Batch P2 —— 搞清楚节点参数面板怎么打开，以及「高级设置」到底展开的是什么。
//
// batchP 的结论：新建的节点停在**折叠态**（只显示「尝试：图生图 / 图片高清」），
// 三种节点里都找不到「高级设置」按钮。但 manifest 里早先的截图 visible_text 写着
// 「… 高级设置 语速 声调 音量」/「… 高级设置 智能引用 AutoLink」——
// 说明**参数面板打开后**才有「高级设置」。
//
// 所以这轮分两步走：
//   第一步：试几种打开方式（单击节点 / 双击 / 点预览图 / 点标题），看哪种能展开参数面板
//   第二步：面板打开后，再点「高级设置」，对比**元素数 / range / number / 文本长度**，
//           判定它到底是「折叠段标题」还是「点开才出现内容的开关」
//
// batchP 的教训：分不清「折叠」和「不存在」时，**先量再下结论**。
// 「找不到按钮」可能只是因为那个按钮在另一个状态下才挂载。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { nodeCount, fitView } from './canvas-ops.mjs';
import { openDropdown } from './canvas-dropdown.mjs';

const SPACE = '10354929';
const B = 'batchP2';
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
/** 节点卡片的完整快照 —— 判「展开」只看这些数，不靠 innerText 猜。 */
const snap = (idx) => page.evaluate((i) => {
  const n = [...document.querySelectorAll('.react-flow__node')][i];
  if (!n) return null;
  const pick = (e) => (e.getAttribute('aria-label') || e.getAttribute('placeholder') || (e.innerText || e.textContent || '').trim().replace(/\s+/g, ' ')).slice(0, 40);
  return {
    allElements: n.querySelectorAll('*').length,
    rect: (() => { const r = n.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; })(),
    text: (n.innerText || '').replace(/\s+/g, ' ').slice(0, 900),
    hasAdv: (n.innerText || '').includes('高级设置'),
    ranges: [...n.querySelectorAll('input[type="range"]')].map((e) => ({ aria: e.getAttribute('aria-label'), min: e.min, max: e.max, value: e.value })),
    numbers: [...n.querySelectorAll('input[type="number"]')].map((e) => ({ aria: e.getAttribute('aria-label'), value: e.value, min: e.min, max: e.max })),
    switches: [...n.querySelectorAll('[role="switch"],input[type="checkbox"]')].map((e) => ({ aria: e.getAttribute('aria-label'), checked: e.checked === true })),
    buttons: [...n.querySelectorAll('button')].map(pick).filter(Boolean),
    advRect: (() => { const e = [...n.querySelectorAll('button,div,span')].find((b) => (b.innerText || '').trim() === '高级设置');
      if (!e) return null; const b = e.getBoundingClientRect();
      return { tag: e.tagName, x: Math.round(b.x + b.width / 2), y: Math.round(b.y + b.height / 2),
        w: Math.round(b.width), h: Math.round(b.height), visible: b.width > 0 && b.height > 0 }; })(),
  };
}, idx);
const toasts = () => page.evaluate(() => [...document.querySelectorAll('[role="alert"],[class*="toast"]')]
  .filter((t) => t.getBoundingClientRect().width > 0).map((t) => (t.innerText || '').replace(/\s+/g, ' ').slice(0, 100)));

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4000 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '先找打开参数面板的方式，再判「高级设置」是折叠段还是开关' });

  await openDropdown(page, 1000);
  await page.getByRole('button', { name: '新建画布', exact: true }).first().click();
  await page.waitForTimeout(4500);
  await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(1500);
  await addNodeAt(findEmptySpot([]).x, findEmptySpot([]).y, '图片');
  await addNodeAt(findEmptySpot(await nodeList()).x, findEmptySpot(await nodeList()).y, '音频');
  await fitView(page, 1); await page.keyboard.press('Meta+-'); await page.waitForTimeout(1600);
  const list = await nodeList();
  console.log('节点:', JSON.stringify(list));

  // ── 第一步：试各种方式打开参数面板
  const img = list.find((n) => n.title.includes('图片节点'));
  const tries = [
    { name: '单击节点中央', act: async () => page.mouse.click(img.x + img.w / 2, img.y + img.h / 2) },
    { name: '单击节点标题', act: async () => page.mouse.click(img.x + 60, img.y + 20) },
    { name: '双击节点中央', act: async () => page.mouse.dblclick(img.x + img.w / 2, img.y + img.h / 2) },
  ];
  const found = [];
  for (const t of tries) {
    const b0 = await snap(img.i);
    await t.act(); await page.waitForTimeout(2200);
    const b1 = await snap(img.i);
    const opened = b1.hasAdv && !b0.hasAdv;
    console.log(`${t.name}: 元素 ${b0.allElements}→${b1.allElements}, 出现「高级设置」 ${b1.hasAdv}, 按钮 ${JSON.stringify(b1.buttons)}`);
    found.push({ how: t.name, opened, before: b0.allElements, after: b1.allElements, buttons: b1.buttons, hasAdv: b1.hasAdv });
    if (opened) { await shot(page, 'M-20-图片节点-参数面板打开.png'); break; }
  }
  await logStep(B, { id: 'P2a-open-panel', title: '节点参数面板怎么打开',
    target: tries.map((t) => t.name).join(' / '),
    evidence: { tries: found },
    visible_text: found.map((f) => `${f.how} → 元素 ${f.before}→${f.after}、出现「高级设置」${f.hasAdv}`).join('；'),
    shot: found.some((f) => f.opened) ? 'M-20-图片节点-参数面板打开.png' : undefined });

  // ── 第二步：面板打开后点「高级设置」，判定它是折叠段标题还是开关
  let s = await snap(img.i);
  if (!s.hasAdv) {
    // 兜底：点节点中央再试一次
    await page.mouse.click(img.x + img.w / 2, img.y + img.h / 2); await page.waitForTimeout(2200);
    s = await snap(img.i);
  }
  if (s.hasAdv && s.advRect && s.advRect.visible) {
    const before = s;
    console.log(`\n[图片] 面板已开，元素数 ${before.allElements}，按钮 ${JSON.stringify(before.buttons)}`);
    console.log(`  点前 ranges=${before.ranges.length} numbers=${before.numbers.length} switches=${before.switches.length}`);
    await page.mouse.click(s.advRect.x, s.advRect.y);
    await page.waitForTimeout(2800);
    const after = await snap(img.i);
    await shot(page, 'M-21-图片节点-高级设置展开.png');
    const d = { elements: after.allElements - before.allElements,
      ranges: after.ranges.length - before.ranges.length,
      numbers: after.numbers.length - before.numbers.length,
      switches: after.switches.length - before.switches.length };
    await logStep(B, { id: 'P2b-image-advanced', title: '图片节点「高级设置」点开前后',
      target: `点 (${s.advRect.x},${s.advRect.y}) 的「高级设置」（${s.advRect.tag}）`,
      evidence: { before: { allElements: before.allElements, text: before.text, ranges: before.ranges, numbers: before.numbers, switches: before.switches, buttons: before.buttons },
        after: { allElements: after.allElements, text: after.text, ranges: after.ranges, numbers: after.numbers, switches: after.switches, buttons: after.buttons }, delta: d, toast: await toasts() },
      visible_text: `点前元素 ${before.allElements} → 点后 ${after.allElements}（${d.elements >= 0 ? '+' : ''}${d.elements}）；` +
        `滑杆 ${before.ranges.length}→${after.ranges.length}、数字框 ${before.numbers.length}→${after.numbers.length}、开关 ${before.switches.length}→${after.switches.length}；` +
        `点前文本 ${JSON.stringify(before.text.slice(-160))}；点后文本 ${JSON.stringify(after.text.slice(-200))}`,
      shot: 'M-21-图片节点-高级设置展开.png' });
  } else {
    await logStep(B, { id: 'P2b-image-advanced', title: '图片节点「高级设置」', failed: true,
      visible_text: `面板仍打不开；hasAdv=${s.hasAdv} advRect=${JSON.stringify(s.advRect)} 按钮=${JSON.stringify(s.buttons)}` });
  }

  console.log('节点:', await N());
} finally {
  await browser.close();
}
