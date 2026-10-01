// Batch I —— 组操作条最后两个悬案：「添加到工具箱」和「⊞ 布局下拉」。
//
// batchH 失败的两个原因，这轮分别处理：
//
// 1. H2 找不到按钮 —— batchH 在 H1 结尾按了 Escape，组的选中态一丢，
//    操作条整个从 DOM 消失。**这轮顺序反过来：先做「添加到工具箱」，中途一个键都不按。**
// 2. 布局下拉的菜单渲染到了 y=-99（视口外）—— batchH 把节点建在画布顶部，
//    组操作条贴着视口上沿，弹层向上翻转后整个溢出到屏幕外。
//    **这轮把节点建在画布中部**，给弹层留出向下的展开空间。
//
// 另外 H1 之前只读了 innerText（空），这轮直接 dump outerHTML，
// 看清楚 `grid grid-cols-5 gap-3` 里到底装的是什么（图标 / SVG / aria-label）。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep, fingerprint, diffPanels } from './scenario.mjs';
import { nodeCount, fitView } from './canvas-ops.mjs';
import { openDropdown } from './canvas-dropdown.mjs';

const SPACE = '10354929';
const B = 'batchI';
const { browser, page } = await launch();

const N = () => nodeCount(page);
const nodesOf = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => {
  const r = n.getBoundingClientRect();
  return { title: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 14),
    isGroup: /group/i.test(n.className || '') || /group/i.test(n.getAttribute('data-id') || ''),
    x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) };
}));

// 起手点放中部：SAFE_TOP 从 90 抬到 300，让组操作条下方有 ~200px 展开余地
const GAP = 40, SAFE_TOP = 300, SAFE_BOTTOM = 640;
function findEmptySpot(list, minX = 200) {
  for (let y = SAFE_TOP; y <= SAFE_BOTTOM; y += 20) for (let x = minX; x <= 1000; x += 20) {
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

/** 组操作条上的每一枚动作（叶子 div/span），按 x 排。组操作条不是 <button>，只能这么读。 */
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
      w: Math.round(b.width), h: Math.round(b.height), op: +getComputedStyle(e).opacity,
      cls: (e.className || '').toString().slice(0, 30) }; })
    .sort((a, b) => a.x - b.x);
  return { present: true, groupSelected: sel, groupRect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], leaves };
});

/** 点一枚动作，然后抓「点开后才出现」的东西（DOM 差集 + 弹层 + 提示）。 */
async function clickAndDiff(c) {
  const before = await fingerprint(page);
  await page.mouse.click(c.x, c.y);
  await page.waitForTimeout(2600);
  const fresh = diffPanels(before, await fingerprint(page));
  const pop = await page.evaluate(() => {
    const els = [...document.querySelectorAll('[role="menu"],[role="listbox"],[role="dialog"],[class*="Popover"],[class*="Dropdown"],[class*="Modal"],[class*="Drawer"],[class*="Tooltip"]')]
      .filter((d) => { const r = d.getBoundingClientRect(); return r.width > 40 && r.height > 20; });
    return els.length ? els.map((e) => ({ cls: (e.className || '').toString().slice(0, 40), text: (e.innerText || '').replace(/\s+/g, ' ').slice(0, 260) })) : null;
  });
  return { fresh: fresh.map((f) => ({ sig: f.sig, all: f.all.slice(0, 260), buttons: f.buttons })), pop };
}

/** 工具箱条目数探针：「我的工具箱」里每条都带【预设】后缀。 */
const toolboxCount = () => page.evaluate(() =>
  [...new Set((document.body.innerText || '').match(/【预设】[^\n【]*/g) || [])].length);
const toasts = () => page.evaluate(() => [...document.querySelectorAll('[role="alert"],[class*="toast"],[class*="Toast"],[class*="toaster"]')]
  .filter((t) => t.getBoundingClientRect().width > 0)
  .map((t) => (t.innerText || '').replace(/\s+/g, ' ').slice(0, 140)));

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4000 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '节点建在画布中部留出弹层空间；先「添加到工具箱」再布局下拉，中间不按任何键' });

  await openDropdown(page, 1000);
  await page.getByRole('button', { name: '新建画布', exact: true }).first().click();
  await page.waitForTimeout(4500);
  await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(1500);
  await addNodeAt(findEmptySpot([]).x, findEmptySpot([]).y, '文本');
  await addNodeAt(findEmptySpot(await nodesOf()).x, findEmptySpot(await nodesOf()).y, '音频');
  await fitView(page, 1); await page.keyboard.press('Meta+-'); await page.waitForTimeout(1400);
  console.log('节点:', JSON.stringify((await nodesOf()).map((n) => [n.title, n.x, n.y])));

  // 框选 → ⌘G 成组，之后不再碰键盘
  const plain = (await nodesOf()).filter((n) => !n.isGroup);
  const x0 = Math.min(...plain.map((n) => n.x)) - 14, y0 = Math.min(...plain.map((n) => n.y)) - 14;
  const x1 = Math.max(...plain.map((n) => n.x + n.w)) + 14, y1 = Math.max(...plain.map((n) => n.y + n.h)) + 14;
  console.log('框选矩形:', x0, y0, x1, y1);
  await page.keyboard.down('Shift');
  await page.mouse.move(40, 200); await page.mouse.down(); await page.waitForTimeout(150);
  await page.mouse.move(x0, y0, { steps: 10 }); await page.mouse.move(x1, y1, { steps: 12 });
  await page.mouse.up(); await page.keyboard.up('Shift'); await page.waitForTimeout(1500);
  const picked = await page.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
  await page.keyboard.press('Meta+g'); await page.waitForTimeout(2600);
  console.log('成组后选中数:', picked, '→ 节点', await N());

  const bar = await toolbarLeaves();
  console.log('操作条 groupRect:', JSON.stringify(bar.groupRect), 'selected:', bar.groupSelected);
  console.log('操作条:', JSON.stringify(bar.leaves.map((l) => [l.t, l.x, l.y, l.op])));
  await shot(page, 'M-08-组操作条全景.png');

  // ── I1 添加到工具箱（放第一位，避免前一步把选中态弄丢）
  try {
    const btn = bar.leaves.find((l) => l.t === '添加到工具箱');
    if (!btn) throw new Error('成组后操作条里没有「添加到工具箱」；实际读到 ' + JSON.stringify(bar.leaves.map((l) => l.t)));
    const before = await toolboxCount();
    const r = await clickAndDiff(btn);
    const after = await toolboxCount();
    const bar2 = await toolbarLeaves();
    await shot(page, 'M-06-添加到工具箱后.png');
    await logStep(B, { id: 'I1-add-to-toolbox', title: '组操作条「添加到工具箱」',
      target: `点 (${btn.x},${btn.y}) 的「添加到工具箱」`,
      evidence: { button: btn, groupStillSelected: bar2.groupSelected, toolBoxCountBefore: before, toolBoxCountAfter: after,
        newPanels: r.fresh, popups: r.pop, toast: await toasts() },
      visible_text: `点击前工具箱【预设】条目 ${before} 条，点击后 ${after} 条；弹出内容 ${JSON.stringify(r.pop)}；新面板 ${JSON.stringify(r.fresh.map((f) => f.all.slice(0, 200)))}；提示 ${JSON.stringify(await toasts())}；点完组是否仍选中 ${bar2.groupSelected}`,
      shot: 'M-06-添加到工具箱后.png' });
  } catch (e) { await logStep(B, { id: 'I1-add-to-toolbox', title: '组操作条「添加到工具箱」', failed: true, visible_text: String(e).slice(0, 300) }); }

  // ── I2 ⊞ 布局下拉：dump outerHTML，看清 grid grid-cols-5 里装的是什么
  try {
    const bar3 = await toolbarLeaves();
    const runIdx = bar3.leaves.findIndex((l) => l.t === '整组执行');
    if (runIdx < 0) throw new Error('操作条里没有「整组执行」；实际读到 ' + JSON.stringify(bar3.leaves.map((l) => l.t)));
    const left = bar3.leaves.slice(0, runIdx).filter((l) => l.w >= 10 && l.w <= 40).pop();
    if (!left) throw new Error('「整组执行」左边没有小尺寸元素');
    const r = await clickAndDiff(left);
    // 关键读数：弹层的内部结构 + 每个子元素的文本/aria/尺寸
    const deep = await page.evaluate(() => {
      const cands = [...document.querySelectorAll('div')].filter((d) => /grid-cols-5/.test(d.className || ''));
      if (!cands.length) return null;
      const root = cands[0];
      const rr = root.getBoundingClientRect();
      const kids = [...root.querySelectorAll('*')].slice(0, 60).map((e) => { const b = e.getBoundingClientRect();
        return { tag: e.tagName, cls: (e.className || '').toString().slice(0, 28),
          aria: e.getAttribute('aria-label'), title: e.getAttribute('title'),
          txt: (e.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 24),
          rect: [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)] };
      }).filter((k) => k.rect[2] > 0 && k.rect[3] > 0);
      return { rootRect: [Math.round(rr.x), Math.round(rr.y), Math.round(rr.width), Math.round(rr.height)],
        inViewport: rr.y >= 0 && rr.y + rr.height <= window.innerHeight, kidCount: kids.length, kids };
    });
    await shot(page, 'M-09-组操作条-布局下拉展开.png');
    await logStep(B, { id: 'I2-layout-dropdown', title: '组操作条 ⊞ 布局下拉',
      target: `点「整组执行」左边那枚 ${left.w}×${left.h} 的无文案元素 (${left.x},${left.y})`,
      evidence: { groupSelected: bar3.groupSelected, clicked: left, newPanels: r.fresh, popups: r.pop, deep },
      visible_text: `点击 (${left.x},${left.y})；弹层 ${JSON.stringify(r.pop)}；新面板 ${JSON.stringify(r.fresh.map((f) => f.sig))}；` +
        (deep ? `grid 根 ${JSON.stringify(deep.rootRect)} 是否在视口内 ${deep.inViewport}；子元素 ${deep.kidCount} 个：${JSON.stringify(deep.kids.slice(0, 20))}` : '没有找到 grid-cols-5 容器'),
      shot: 'M-09-组操作条-布局下拉展开.png' });
  } catch (e) { await logStep(B, { id: 'I2-layout-dropdown', title: '组操作条 ⊞ 布局下拉', failed: true, visible_text: String(e).slice(0, 300) }); }

  console.log('收尾前节点:', await N());
} finally {
  await browser.close();
}
