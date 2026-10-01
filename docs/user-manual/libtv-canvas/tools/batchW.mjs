// Batch W —— 「更多操作」到底在什么条件下才出现。
//
// batchV 已经排除了一个可能：**不是「多节点时才折叠」** ——
// 删到只剩 1 个节点，「更多操作」/「定位到节点」依然是 **0 个**。
//
// 它给的线索在行 HTML 里：
//   <div class="group/node relative flex h-11 w-full items-center gap-0.5 rounded-[10px]
//               py-1 pr-1 text-[14px] transition-none hover:bg-canvas-controls-hover">
//     <span class="size-6 shrink-0" aria-hidden="true"></span>
//     <button class="flex min-w-0 flex-1 items-center gap-0.5 rounded-lg py-0 pl-0 pr-0 …">节点名</button>
//
// 两处要害：
//   1. class 里有 **`group/node`** —— 这是 Tailwind 的 group 模式，
//      意味着子元素大概率用 `opacity-0 group-hover/node:opacity-100` 这类写法藏起来；
//   2. 那个 button 是 **`pr-0`**，右侧没有留白 —— 动作按钮要放的话只能挤在行尾。
//
// 而 batchV 悬停的是**行中心**（命中的是节点名 SPAN）。这轮把**行内多个位置**都悬停一遍：
// 左 / 中 / 右 1/4 / 右 1/8 / 整行最右缘，并读每种情况下行内的实际可见元素。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { nodeCount } from './canvas-ops.mjs';
import { openDropdown } from './canvas-dropdown.mjs';

const SPACE = '10354929';
const B = 'batchW';
const { browser, page } = await launch();

/** 行内所有可见叶子元素的清单（用来数「动作按钮」冒没冒出来）。 */
const rowLeaves = () => page.evaluate(() => {
  const txt = (e) => (e.innerText || e.textContent || '').replace(/\s+/g, ' ').trim();
  const row = [...document.querySelectorAll('div.group\\/node')][0];
  if (!row) return null;
  const b = row.getBoundingClientRect();
  const leaves = [...row.querySelectorAll('*')].map((e) => {
    const r = e.getBoundingClientRect();
    return { tag: e.tagName, cls: (e.className || '').toString().slice(0, 46),
      text: txt(e).slice(0, 16), aria: e.getAttribute('aria-label'), title: e.getAttribute('title'),
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      opacity: +getComputedStyle(e).opacity, vis: getComputedStyle(e).visibility,
      display: getComputedStyle(e).display };
  }).filter((e) => e.rect[2] > 0 && e.rect[3] > 0);
  return { rowRect: [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)],
    rowClass: (row.className || '').toString().slice(0, 90),
    rowText: txt(row), leaves };
});

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4000 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '悬停行内多个位置，看「更多操作」在哪个热区出现' });

  await openDropdown(page, 1000);
  await page.getByRole('button', { name: '新建画布', exact: true }).first().click();
  await page.waitForTimeout(4500);
  await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(1500);
  await page.mouse.dblclick(500, 300); await page.waitForTimeout(1200);
  await page.locator('[data-guide-lockable-portal="true"], [data-canvas-menu-portal="true"]').first()
    .getByText('图片', { exact: false }).first().click({ timeout: 8000 });
  await page.waitForTimeout(2600);
  console.log('节点:', await nodeCount(page));

  const opener = page.locator('[data-academy-guide-anchor="workspace-asset-management"]');
  await opener.first().click({ timeout: 6000 });
  await page.waitForTimeout(2800);

  // 确认抽屉开着
  const open0 = await page.evaluate(() => /共 \d+ 节点/.test(document.body.innerText || ''));
  console.log('抽屉已开:', open0);

  const base = await rowLeaves();
  if (!base) throw new Error('找不到 div.group\\/node 行');
  console.log('\n行 rect:', JSON.stringify(base.rowRect));
  console.log('行 class:', base.rowClass);
  console.log('未悬停时行内元素:');
  for (const l of base.leaves) console.log(`   <${l.tag}> op=${l.opacity} ${l.display} 「${l.text || l.aria || ''}」 ${JSON.stringify(l.rect)} ${l.cls.slice(0, 40)}`);

  // 悬停行内不同位置
  const [rx, ry, rw, rh] = base.rowRect;
  const spots = [
    ['最左 1/8', rx + rw * 0.06, ry + rh / 2],
    ['中心', rx + rw / 2, ry + rh / 2],
    ['右 3/4', rx + rw * 0.75, ry + rh / 2],
    ['右 7/8', rx + rw * 0.875, ry + rh / 2],
    ['最右缘 -4px', rx + rw - 4, ry + rh / 2],
    ['右上角', rx + rw - 10, ry + 4],
  ];
  const results = [];
  for (const [name, x, y] of spots) {
    // 先移开再移入，确保真的产生 hover 变化
    await page.mouse.move(900, 500); await page.waitForTimeout(500);
    await page.mouse.move(x, y, { steps: 4 }); await page.waitForTimeout(1500);
    const s = await rowLeaves();
    const acts = s.leaves.filter((l) => /更多|定位|操作|菜单|更多操作/.test(l.text + (l.aria || '') + (l.title || ''))
      || (l.text === '' && l.rect[2] >= 10 && l.rect[2] <= 40 && l.rect[3] >= 10 && l.rect[3] <= 40 && l.opacity > 0.5));
    const visibleTexts = s.leaves.filter((l) => l.text).map((l) => l.text);
    const top = await page.evaluate(([px, py]) => {
      const t = document.elementFromPoint(px, py);
      return t ? `${t.tagName}.${(t.className || '').toString().slice(0, 30)}「${(t.innerText || '').trim().slice(0, 12)}」` : null;
    }, [Math.round(x), Math.round(y)]);
    console.log(`\n悬停「${name}」(${Math.round(x)},${Math.round(y)}):`);
    console.log(`   该点最顶层: ${top}`);
    console.log(`   行内可见文案: ${JSON.stringify(visibleTexts)}`);
    console.log(`   疑似动作按钮(op>0.5 且 10~40px): ${JSON.stringify(acts.map((a) => [a.tag, a.text, a.aria, a.rect, a.cls.slice(0, 30)]))}`);
    results.push({ name, x: Math.round(x), y: Math.round(y), top, visibleTexts,
      actions: acts.map((a) => ({ tag: a.tag, text: a.text, aria: a.aria, rect: a.rect, cls: a.cls })) });
    if (acts.length) { await shot(page, 'M-34-资产管理-悬停出现动作.png'); }
  }

  const best = results.find((r) => r.actions.length);
  await logStep(B, { id: 'W-more-actions', title: '资产管理行内动作按钮在哪个热区出现',
    target: `对同一行依次悬停 ${spots.map((s) => s[0]).join(' / ')}`,
    evidence: { rowClass: base.rowClass, rowRect: base.rowRect, rowText: base.rowText,
      beforeHover: base.leaves.length, results },
    visible_text: `行 class 含 **group/node**（Tailwind group 模式），行内 button 是 **pr-0**（右侧无留白）。` +
      `未悬停时行内可见文案 ${JSON.stringify(base.leaves.filter((l) => l.text).map((l) => l.text))}；` +
      results.map((r) => `${r.name}(${r.x},${r.y}) → 可见文案 ${JSON.stringify(r.visibleTexts)}、动作候选 ${r.actions.length} 个`).join('；'),
    shot: best ? 'M-34-资产管理-悬停出现动作.png' : undefined });
  console.log('\n最终节点:', await nodeCount(page));
} finally {
  await browser.close();
}
