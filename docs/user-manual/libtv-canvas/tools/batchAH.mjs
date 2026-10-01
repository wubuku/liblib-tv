// Batch AH —— 只补 AG 剩下的那一件事：把组建出来，问「展开/收起全部分组」。
//
// AG 的分组为什么失败：`page.mouse.click()` 配 `keyboard.down('Shift')`，
// Playwright 发的是**独立的按下/抬起**，React Flow 收不到「shift 处于按下状态」这个信息，
// 于是第二次点击只是把选中态**换**成了第 2 个节点 —— `selectedAfterShiftClick: 1` 就是证据。
// `⌘G` 也因此作用在单选上，什么都不会发生（`groupNodes: 0`）。
//
// 这次换成 batchE3 已经坐实过的 `Shift`+空白拖拽框选，
// 外加一条对照组：`⌘A` 全选后按 `⌘G`。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { nodeCount } from './canvas-ops.mjs';
import { openDropdown } from './canvas-dropdown.mjs';

const SPACE = '10354929';
const B = 'batchAH';
const { browser, page } = await launch();

const N = () => nodeCount(page);
const nodeList = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => {
  const r = n.getBoundingClientRect();
  return { title: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 10),
    rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
}));
const drawerBox = () => page.evaluate(() => {
  const d = [...document.querySelectorAll('[class*="mantine-Drawer-content"]')]
    .find((x) => { const r = x.getBoundingClientRect(); return r.width > 200 && r.height > 300 && r.x < 400; });
  if (!d) return null;
  return { x: d.getBoundingClientRect().x };
});
const opener = page.locator('[data-academy-guide-anchor="workspace-asset-management"]');
const openDrawer = async () => {
  const b = await drawerBox();
  if (b && b.x > -50) return true;
  await opener.first().click({ timeout: 6000 }); await page.waitForTimeout(2600);
  return (await drawerBox())?.x > -50;
};
const closeDrawer = async () => { await page.mouse.click(880, 110).catch(() => {}); await page.waitForTimeout(900); };
const floating = () => page.evaluate(() => [...document.querySelectorAll('[class*="Menu-dropdown"],[class*="Popover-dropdown"]')]
  .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 40 && r.height > 12; })
  .map((e) => ({ text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 160),
    items: [...e.querySelectorAll('[role="menuitem"],button')].filter((c) => {
      const cr = c.getBoundingClientRect();
      return cr.width > 24 && cr.height > 8 && cr.height < 46 && (c.innerText || '').trim().length <= 24;
    }).map((c) => { const cr = c.getBoundingClientRect();
      return { t: (c.innerText || '').trim(), cx: Math.round(cr.x + cr.width / 2), cy: Math.round(cr.y + cr.height / 2) }; }) })));
/** 展示设置菜单；force=true 时先确保菜单是关的（处理「上一轮点完菜单还开着」）。 */
async function displaySetting(pick) {
  const btn = await page.evaluate(() => {
    const d = [...document.querySelectorAll('[class*="mantine-Drawer-content"]')]
      .find((x) => { const r = x.getBoundingClientRect(); return r.width > 200 && r.height > 300 && r.x < 400; });
    const e = d && [...d.querySelectorAll('button')].find((b) => b.getAttribute('aria-label') === '展示设置');
    if (!e) return null;
    const r = e.getBoundingClientRect();
    return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) };
  });
  if (!btn) throw new Error('找不到「展示设置」');
  // 先探一次当前是不是开着
  let open = (await floating()).length > 0;
  if (open) { await page.mouse.click(btn.cx, btn.cy); await page.waitForTimeout(1100); open = (await floating()).length > 0; }
  if (!open) { await page.mouse.click(btn.cx, btn.cy); await page.waitForTimeout(1500); }
  const pop = await floating();
  const it = pop[0]?.items.find((x) => x.t === pick);
  if (!it) throw new Error(`菜单里没有「${pick}」；读到 ${JSON.stringify(pop[0]?.items.map((x) => x.t))}`);
  await page.mouse.click(it.cx, it.cy); await page.waitForTimeout(1800);
  return { menu: pop[0]?.items.map((x) => x.t) };
}
const drawerBody = () => page.evaluate(() => {
  const d = [...document.querySelectorAll('[class*="mantine-Drawer-content"]')]
    .find((x) => { const r = x.getBoundingClientRect(); return r.width > 200 && r.height > 300 && r.x < 400; });
  if (!d) return null;
  return { rows: [...d.querySelectorAll('div.group\\/node')].map((r) => (r.innerText || '').replace(/\s+/g, ' ').trim()),
    text: (d.innerText || '').replace(/\s+/g, ' ').trim() };
});
async function freeSpot() {
  await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(450);
  const ns = await nodeList();
  if (!ns.length) return [760, 320];
  const right = Math.max(...ns.map((n) => n.rect[0] + n.rect[2]));
  const bottom = Math.max(...ns.map((n) => n.rect[1] + n.rect[3]));
  for (const [x, y] of [[Math.min(right + 360, 1370), 260], [Math.min(right + 360, 1370), 540],
    [700, Math.min(bottom + 280, 720)], [1150, Math.min(bottom + 280, 720)], [430, Math.min(bottom + 280, 720)]]) {
    if (!ns.some((n) => x > n.rect[0] - 40 && x < n.rect[0] + n.rect[2] + 40 && y > n.rect[1] - 40 && y < n.rect[1] + n.rect[3] + 40)
        && x > 400 && y > 140 && y < 740) return [x, y];
  }
  return null;
}
async function addNode(item) {
  for (let r = 0; r < 3; r += 1) {
    const spot = await freeSpot();
    if (!spot) return false;
    await page.mouse.dblclick(spot[0], spot[1]); await page.waitForTimeout(1100);
    const it = page.locator('[data-guide-lockable-portal="true"], [data-canvas-menu-portal="true"]').first()
      .getByText(item, { exact: false }).first();
    if (await it.count().catch(() => 0)) {
      const b = await N();
      await it.click({ timeout: 4000 }).catch(() => {}); await page.waitForTimeout(2300);
      if (await N() > b) return true;
    }
    await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(700);
  }
  return false;
}

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4000 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '⌘A + ⌘G 建组 → 展开/收起全部分组' });

  await openDropdown(page, 1000);
  await page.getByRole('button', { name: '新建画布', exact: true }).first().click();
  await page.waitForTimeout(4500);
  await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(1500);
  for (const item of ['图片', '音频', '文本']) console.log(`建 ${item}:`, await addNode(item), await N());

  // ⌘A 全选 → ⌘G 成组
  await closeDrawer();
  await page.mouse.click(700, 90); await page.waitForTimeout(700);   // 点空白，焦点回画布
  await page.keyboard.press('Meta+a'); await page.waitForTimeout(900);
  const selAll = await page.locator('.react-flow__node.selected').count();
  await page.keyboard.press('Meta+g'); await page.waitForTimeout(2000);
  const g1 = await page.evaluate(() => ({
    groupNodes: document.querySelectorAll('.react-flow__node-group').length,
    selected: document.querySelectorAll('.react-flow__node.selected').length,
    labels: [...document.querySelectorAll('.react-flow__node')].map((n) => (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 12)).filter((t) => /Group|组/.test(t)),
  }));
  await shot(page, 'M-82-成组之后.png');
  console.log('⌘A 选中', selAll, '⌘G 后', JSON.stringify(g1));

  const before = (await (async () => { if (!(await openDrawer())) return null; return drawerBody(); })());
  const steps = [];
  if (before) {
    await shot(page, 'M-83-列表-成组之后.png');
    for (const pick of ['收起全部分组', '展开全部分组', '收起全部分组', '展开全部分组']) {
      try {
        const r = await displaySetting(pick);
        const b = await drawerBody();
        steps.push({ pick, menu: r.menu, rows: b.rows, text: b.text });
        await shot(page, `M-84-${pick}-${steps.length}.png`);
      } catch (e) { steps.push({ pick, err: String(e).slice(0, 180) }); await page.mouse.press('Escape').catch(() => {}); await page.waitForTimeout(800); }
    }
  }
  await logStep(B, { id: 'AH1-group-expand-collapse', title: '有组的时候「展开/收起全部分组」对列表做了什么',
    target: '⌘A 全选 → ⌘G 成组 → 在「展示设置」里 收起/展开 各两轮',
    evidence: { selAll, g1, before, steps },
    visible_text: `⌘A 选中 ${selAll} 个节点，按 ⌘G 后：分组节点 ${g1.groupNodes} 个，仍选中 ${g1.selected} 个，标签 ${JSON.stringify(g1.labels)}。` +
      `成组后的列表 ${JSON.stringify(before?.rows)}，主体「${(before?.text || '').slice(0, 160)}」。` +
      steps.map((s) => s.err ? `**${s.pick}** 没测成：${s.err}` :
        `**${s.pick}** → 行 ${JSON.stringify(s.rows)}，主体「${(s.text || '').slice(0, 150)}」`).join('\n') +
      `\n→ **${steps.filter((s) => !s.err).every((s) => JSON.stringify(s.rows) === JSON.stringify(before?.rows)) ? '在这张画布上，展开/收起全部分组对列表行没有可见影响' : '有可见差别'}**`,
    shot: 'M-84-收起全部分组-1.png' });
  console.log('AH1:', JSON.stringify({ selAll, g1, before, steps }).slice(0, 2600));

  console.log('收尾节点:', await N());
} finally {
  await browser.close();
}
