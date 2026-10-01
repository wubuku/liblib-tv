// Batch H —— 只查一件事：组操作条上「⊞ 布局下拉」和「添加到工具箱」点开到底是什么。
//
// 前两轮（batchF/F2、batchG2/H6、batchG3/I2、I3）全都没查到，失败原因同一个：
// **⌘G 成组之后我又去按 Esc / ⌘0 / ⌘-**，组的选中态一丢，那条操作条整个从 DOM 里消失，
// 于是后续按文案找「整组执行」「添加到工具箱」全都找不到。
//
// 这一轮纪律很简单：**成组后一个字都不按，只读、只点。**
// 顺序：建节点 → 框选 → ⌘G → 立刻读操作条 → 立刻点两个动作 → 读结果 → ⌘⇧G 解组收尾。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep, fingerprint, diffPanels } from './scenario.mjs';
import { nodeCount, fitView } from './canvas-ops.mjs';
import { openDropdown } from './canvas-dropdown.mjs';

const SPACE = '10354929';
const B = 'batchH';
const { browser, page } = await launch();

const N = () => nodeCount(page);
const nodesOf = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => {
  const r = n.getBoundingClientRect();
  return { title: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 14),
    isGroup: /group/i.test(n.className || '') || /group/i.test(n.getAttribute('data-id') || ''),
    x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) };
}));

const GAP = 40, SAFE_TOP = 90, SAFE_BOTTOM = 720;
function findEmptySpot(list, minX = 120) {
  for (let y = SAFE_TOP; y <= SAFE_BOTTOM; y += 20) for (let x = minX; x <= 1300; x += 20) {
    if (!list.some((n) => x > n.x - GAP && x < n.x + n.w + GAP && y > n.y - GAP && y < n.y + n.h + GAP)) return { x, y };
  }
  return { x: minX, y: SAFE_TOP };
}
async function addNodeAt(x, y, item) {
  await page.mouse.dblclick(x, y); await page.waitForTimeout(1000);
  await page.locator('[data-guide-lockable-portal="true"], [data-canvas-menu-portal="true"]').first()
    .getByText(item, { exact: false }).first().click({ timeout: 6000 });
  await page.waitForTimeout(2000);
}
/** 组操作条上的每一枚动作（叶子 div/span），按 x 排。这是唯一可靠的读法。 */
const toolbarLeaves = () => page.evaluate(() => {
  const g = [...document.querySelectorAll('.react-flow__node')].find((n) => /group/i.test(n.className || '') || /group/i.test(n.getAttribute('data-id') || ''));
  if (!g) return { present: false, why: '没有组节点' };
  const r = g.getBoundingClientRect();
  const sel = g.classList.contains('selected');
  const leaves = [...g.querySelectorAll('div,span')].filter((e) => {
    const b = e.getBoundingClientRect();
    return b.width > 0 && b.height > 0 && b.y < r.y + 60 && b.y > r.y - 80 && b.width < 200 && !e.querySelector('div,span');
  }).map((e) => { const b = e.getBoundingClientRect();
    return { t: (e.getAttribute('aria-label') || e.title || e.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 14),
      x: Math.round(b.x + b.width / 2), y: Math.round(b.y + b.height / 2),
      w: Math.round(b.width), h: Math.round(b.height), op: +getComputedStyle(e).opacity }; })
    .sort((a, b) => a.x - b.x);
  return { present: true, groupSelected: sel, groupRect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], leaves };
});
/** 点一枚动作，然后抓「点开后才出现」的东西。 */
async function clickAndDiff(c) {
  const before = await fingerprint(page);
  await page.mouse.click(c.x, c.y);
  await page.waitForTimeout(2400);
  const fresh = diffPanels(before, await fingerprint(page));
  const pop = await page.evaluate(() => {
    const els = [...document.querySelectorAll('[role="menu"],[role="listbox"],[role="dialog"],[class*="Popover"],[class*="Dropdown"],[class*="Modal"],[class*="Drawer"]')]
      .filter((d) => { const r = d.getBoundingClientRect(); return r.width > 40 && r.height > 20; });
    return els.length ? els.map((e) => ({ cls: (e.className || '').toString().slice(0, 40), text: (e.innerText || '').replace(/\s+/g, ' ').slice(0, 260) })) : null;
  });
  return { fresh: fresh.map((f) => ({ sig: f.sig, all: f.all.slice(0, 260), buttons: f.buttons })), pop };
}
/** 工具箱条目数探针。 */
const toolboxCount = () => page.evaluate(() =>
  [...new Set((document.body.innerText || '').match(/【预设】[^\n【]*/g) || [])].length);

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4000 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '成组后不按任何键，直接读操作条并点开两个动作' });

  await openDropdown(page, 1000);
  await page.getByRole('button', { name: '新建画布', exact: true }).first().click();
  await page.waitForTimeout(4500);
  await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(1500);
  await addNodeAt(findEmptySpot([]).x, findEmptySpot([]).y, '文本');
  await addNodeAt(findEmptySpot(await nodesOf()).x, findEmptySpot(await nodesOf()).y, '音频');
  await fitView(page, 1); await page.keyboard.press('Meta+-'); await page.waitForTimeout(1400);
  console.log('节点:', JSON.stringify((await nodesOf()).map((n) => n.title)));

  // 框选 → 成组，之后不再碰键盘
  const plain = (await nodesOf()).filter((n) => !n.isGroup);
  const x0 = Math.min(...plain.map((n) => n.x)) - 14, y0 = Math.min(...plain.map((n) => n.y)) - 14;
  const x1 = Math.max(...plain.map((n) => n.x + n.w)) + 14, y1 = Math.max(...plain.map((n) => n.y + n.h)) + 14;
  await page.keyboard.down('Shift');
  await page.mouse.move(40, 80); await page.mouse.down(); await page.waitForTimeout(150);
  await page.mouse.move(x0, y0, { steps: 10 }); await page.mouse.move(x1, y1, { steps: 12 });
  await page.mouse.up(); await page.keyboard.up('Shift'); await page.waitForTimeout(1500);
  const picked = await page.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
  await page.keyboard.press('Meta+g'); await page.waitForTimeout(2600);
  console.log('成组后选中数:', picked, '→ 节点', await N());

  const bar = await toolbarLeaves();
  console.log('操作条:', JSON.stringify(bar));

  // ── H1 ⊞ 布局下拉：「整组执行」左边那枚无文案小元素
  try {
    const runIdx = bar.leaves.findIndex((l) => l.t === '整组执行');
    if (runIdx < 0) throw new Error('操作条里没有「整组执行」，整条读数不可信');
    const left = bar.leaves.slice(0, runIdx).filter((l) => l.w >= 10 && l.w <= 40).pop();
    if (!left) throw new Error('「整组执行」左边没有小尺寸元素');
    const r = await clickAndDiff(left);
    await shot(page, 'M-08-组操作条-布局下拉.png');
    await logStep(B, { id: 'H1-layout-dropdown', title: '组操作条 ⊞ 布局下拉',
      target: `点「整组执行」左边那枚 ${left.w}×${left.h} 的无文案元素 (${left.x},${left.y})`,
      evidence: { groupSelected: bar.groupSelected, clicked: left, newPanels: r.fresh, popups: r.pop },
      visible_text: `点击 (${left.x},${left.y}) 尺寸 ${left.w}×${left.h}；新出现的面板 ${JSON.stringify(r.fresh.map((f) => f.all.slice(0, 200)))}；弹层 ${JSON.stringify(r.pop)}`,
      shot: 'M-08-组操作条-布局下拉.png' });
    await page.keyboard.press('Escape').catch(() => {});
    await page.waitForTimeout(1000);
  } catch (e) { await logStep(B, { id: 'H1-layout-dropdown', title: '组操作条 ⊞ 布局下拉', failed: true, visible_text: String(e).slice(0, 200) }); }

  // ── H2 「添加到工具箱」：点开前后数工具箱条目
  try {
    const bar2 = await toolbarLeaves();
    const btn = bar2.leaves.find((l) => l.t === '添加到工具箱');
    if (!btn) throw new Error('成组后操作条里没有「添加到工具箱」');
    const before = await toolboxCount();
    const r = await clickAndDiff(btn);
    const after = await toolboxCount();
    await shot(page, 'M-06-添加到工具箱后.png');
    await logStep(B, { id: 'H2-add-to-toolbox', title: '组操作条「添加到工具箱」',
      target: `点 (${btn.x},${btn.y}) 的「添加到工具箱」`,
      evidence: { button: btn, toolBoxCountBefore: before, toolBoxCountAfter: after, newPanels: r.fresh, popups: r.pop,
        toast: await page.evaluate(() => [...document.querySelectorAll('[role="alert"],[class*="toast"],[class*="Toast"]')]
          .filter((t) => t.getBoundingClientRect().width > 0).map((t) => (t.innerText || '').replace(/\s+/g, ' ').slice(0, 120))) },
      visible_text: `点击成功；弹出内容 ${JSON.stringify(r.pop)}；新面板 ${JSON.stringify(r.fresh.map((f) => f.all.slice(0, 200)))}；工具箱条目 ${before} → ${after}；提示 ${JSON.stringify(await page.evaluate(() => [...document.querySelectorAll('[role="alert"]')].map((t) => (t.innerText || '').slice(0, 80))))}`,
      shot: 'M-06-添加到工具箱后.png' });
    await page.keyboard.press('Escape').catch(() => {});
    await page.waitForTimeout(1000);
  } catch (e) { await logStep(B, { id: 'H2-add-to-toolbox', title: '组操作条「添加到工具箱」', failed: true, visible_text: String(e).slice(0, 200) }); }

  // 收尾：解组，把组拆回去
  await page.keyboard.press('Meta+Shift+KeyG').catch(() => {});
  await page.waitForTimeout(1800);
  console.log('解组后节点:', await N(), '分组:', (await nodesOf()).filter((n) => n.isGroup).length);
} finally {
  await browser.close();
}
