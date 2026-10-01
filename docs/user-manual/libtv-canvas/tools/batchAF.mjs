// Batch AF —— Batch AD/AE 之后剩下的三块：
//
//   ① 建节点一直失败（AD、AE 两轮都只建出 1 个图片节点）。
//      原因找到了：两轮都用 `getByText(item, { exact: true })`，
//      而 batchY 等成功的那几轮用的是 **`{ exact: false }`** ——
//      「添加节点」面板里那一项的文本不止是「音频」两个字，`exact: true` 直接匹配不到。
//      **连续两轮只建出一个节点，两轮都没去查为什么 —— 又是「怪产品」的老毛病。**
//
//   ② 「宫格展示」切过去之后长什么样、切回来行不行。
//      AE3 里 `div.group/node` 数归零了 —— 那是**我的选择器在宫格视图下不适用**，
//      不是列表空了。这一轮把宫格视图的 DOM 结构读出来。
//
//   ③ 「展开全部分组 / 收起全部分组」到底对什么起作用。
//      得先有组。这一轮建 4 个节点、成一个组，才问得出这个问题。
//
//   ④ 「资产」标签的 筛选 / 批量操作 / 创建 / 管理 四枚按钮。
//      AE4 只测到 `搜索`（会展开 placeholder="搜索资产" 的框），
//      后三轮全报「按钮不在」—— 因为每轮开头都点一次「资产」标签把状态打回去了。
//      这一轮**每测完一枚就刷新页面**，不复用任何状态。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { nodeCount } from './canvas-ops.mjs';
import { openDropdown } from './canvas-dropdown.mjs';

const SPACE = '10354929';
const B = 'batchAF';
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
  const r = d.getBoundingClientRect();
  return { x: r.x, y: r.y, w: r.width, h: r.height };
});
const opener = page.locator('[data-academy-guide-anchor="workspace-asset-management"]');
const openDrawer = async () => {
  const b = await drawerBox();
  if (b && b.x > -50) return true;
  await opener.first().click({ timeout: 6000 }); await page.waitForTimeout(2600);
  const b2 = await drawerBox();
  return !!(b2 && b2.x > -50);
};
const closeDrawer = async () => { await page.mouse.click(900, 130).catch(() => {}); await page.waitForTimeout(900); };
const listBody = () => page.evaluate(() => {
  const d = [...document.querySelectorAll('[class*="mantine-Drawer-content"]')]
    .find((x) => { const r = x.getBoundingClientRect(); return r.width > 200 && r.height > 300 && r.x < 400; });
  if (!d) return null;
  // 列表主体的所有直接后代行，不预设 class —— 宫格视图下行元素结构可能完全不同
  const rows = [...d.querySelectorAll('div.group\\/node')].map((r) => (r.innerText || '').replace(/\s+/g, ' ').trim());
  const grid = [...d.querySelectorAll('[class*="grid"]')]
    .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 150 && r.height > 60 && r.y > 180; })
    .map((e) => ({ cls: (e.className || '').toString().slice(0, 60),
      rect: [Math.round(e.getBoundingClientRect().x), Math.round(e.getBoundingClientRect().y),
        Math.round(e.getBoundingClientRect().width), Math.round(e.getBoundingClientRect().height)],
      kids: [...e.children].map((c) => ({ t: (c.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 14),
        rect: [Math.round(c.getBoundingClientRect().width), Math.round(c.getBoundingClientRect().height)] })).slice(0, 10) }));
  return { rows, grid, text: (d.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 220) };
});
const btnBy = (aria) => page.evaluate((a) => {
  const d = [...document.querySelectorAll('[class*="mantine-Drawer-content"]')]
    .find((x) => { const r = x.getBoundingClientRect(); return r.width > 200 && r.height > 300 && r.x < 400; });
  if (!d) return null;
  const e = [...d.querySelectorAll('button')].find((b) => b.getAttribute('aria-label') === a);
  if (!e) return null;
  const r = e.getBoundingClientRect();
  return { t: (e.innerText || '').replace(/\s+/g, ' ').trim(), cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2),
    w: Math.round(r.width), h: Math.round(r.height), disabled: e.disabled === true };
}, aria);
const floating = () => page.evaluate(() => [...document.querySelectorAll(
  '[class*="Popover-dropdown"],[class*="Menu-dropdown"],[class*="Dropdown-dropdown"]')]
  .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 40 && r.height > 12; })
  .map((e) => { const r = e.getBoundingClientRect();
    return { cls: (e.className || '').toString().slice(0, 36), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 260),
      items: [...e.querySelectorAll('button,[role="option"],li,label,div')].filter((c) => {
        const cr = c.getBoundingClientRect();
        return cr.width > 24 && cr.height > 8 && cr.height < 46 && (c.innerText || '').trim().length <= 24 && !c.querySelector('div[style]');
      }).map((c) => { const cr = c.getBoundingClientRect();
        return { t: (c.innerText || '').trim(), cx: Math.round(cr.x + cr.width / 2), cy: Math.round(cr.y + cr.height / 2) }; })
        .filter((x, i, a) => a.findIndex((y) => y.t === x.t && y.cy === x.cy) === i) }; }));
/** 点开「展示设置」并选一项；每次都重开重读坐标（浮层坐标不能复用）。 */
async function displaySetting(pick) {
  const btn = await btnBy('展示设置');
  if (!btn) throw new Error('找不到「展示设置」');
  await page.mouse.click(btn.cx, btn.cy); await page.waitForTimeout(1500);
  const pop = await floating();
  const it = pop?.[0]?.items?.find((x) => x.t === pick);
  if (!it) throw new Error(`菜单里没有「${pick}」；读到 ${JSON.stringify(pop?.[0]?.items?.map((x) => x.t))}`);
  await page.mouse.click(it.cx, it.cy); await page.waitForTimeout(1700);
  return { pop, it };
}

async function addNode(item) {
  for (const [x, y] of [[520, 250], [520, 430], [720, 250], [720, 430], [900, 250], [900, 430], [520, 610], [720, 610]]) {
    const ns = await nodeList();
    if (ns.some((n) => x > n.rect[0] - 30 && x < n.rect[0] + n.rect[2] + 30 && y > n.rect[1] - 30 && y < n.rect[1] + n.rect[3] + 30)) continue;
    await page.mouse.dblclick(x, y); await page.waitForTimeout(1100);
    const it = page.locator('[data-guide-lockable-portal="true"], [data-canvas-menu-portal="true"]').first()
      .getByText(item, { exact: false }).first();     // ← 修：不能用 exact:true
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
  await beginBatch(B, { note: '宫格展示 / 展开收起全部分组 / 资产标签四枚按钮' });

  await openDropdown(page, 1000);
  await page.getByRole('button', { name: '新建画布', exact: true }).first().click();
  await page.waitForTimeout(4500);
  await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(1500);
  for (const item of ['图片', '音频', '视频', '文本']) {
    console.log(`建 ${item}:`, await addNode(item), '节点数', await N());
  }
  const ns = await nodeList();
  const titles = ns.map((n) => n.title);
  console.log('节点:', await N(), titles);

  // 成组：点第一个，Shift+点第二个，⌘G
  let grouped = null;
  if (ns.length >= 2) {
    await page.mouse.click(ns[0].rect[0] + 40, ns[0].rect[1] + 20); await page.waitForTimeout(700);
    await page.keyboard.down('Shift');
    await page.mouse.click(ns[1].rect[0] + 40, ns[1].rect[1] + 20);
    await page.keyboard.up('Shift'); await page.waitForTimeout(900);
    const sel = await page.locator('.react-flow__node.selected').count();
    await page.keyboard.press('Meta+g'); await page.waitForTimeout(1800);
    const groups = await page.locator('.react-flow__node-group, [class*="react-flow__node-group"]').count();
    grouped = { selectedAfterShiftClick: sel, groupsAfterMetaG: groups };
    await shot(page, 'M-73-成组之后.png');
  }
  console.log('成组:', JSON.stringify(grouped));

  // ── AF1 宫格展示
  try {
    if (!(await openDrawer())) throw new Error('抽屉打不开');
    const before = await listBody();
    const { pop, it } = await displaySetting('宫格展示');
    const after = await listBody();
    await shot(page, 'M-74-宫格展示.png');
    let back = null;
    try { await displaySetting('列表展示'); back = await listBody(); await shot(page, 'M-75-切回列表展示.png'); } catch (e) { back = { err: String(e).slice(0, 160) }; }
    await logStep(B, { id: 'AF1-grid-view', title: '「宫格展示」切过去是什么样、切回来行不行',
      target: '点开「展示设置」→ 宫格展示，读列表主体结构；再切回列表展示',
      evidence: { grouped, before, after, back },
      visible_text: `画布上 ${titles.length} 个节点 ${JSON.stringify(titles)}，成组情况 ${JSON.stringify(grouped)}。` +
        `切之前：列表行 ${JSON.stringify(before.rows)}，抽屉文案「${before.text}」。` +
        `切到宫格展示之后：\`div.group/node\` 行数 ${after.rows.length}（${JSON.stringify(after.rows)}），` +
        `**但抽屉文案仍然是「${after.text}」**；列表区里的网格容器 ${JSON.stringify(after.grid)}。` +
        `切回列表展示：${back.err ? `**${back.err}**` : `列表行 ${JSON.stringify(back.rows)}，文案「${back.text}」`}。` +
        `→ **${after.rows.length === 0 && /共 \\d+ 节点/.test(after.text) ? '宫格视图下列出的元素 class 变了，节点并没有消失' : '需人工判断'}**`,
      shot: 'M-74-宫格展示.png' });
    console.log('AF1:', JSON.stringify({ before: before.rows, after: after.rows, afterText: after.text, grid: after.grid, back: back.rows }));
  } catch (e) { await logStep(B, { id: 'AF1-grid-view', title: '宫格展示', failed: true, visible_text: String(e).slice(0, 300) }); console.log('AF1 失败', String(e).slice(0, 250)); }

  // ── AF2 展开 / 收起全部分组
  try {
    await closeDrawer(); if (!(await openDrawer())) throw new Error('抽屉打不开');
    const before = await listBody();
    const r1 = await displaySetting('展开全部分组');
    const afterExpand = await listBody();
    await shot(page, 'M-76-展开全部分组.png');
    const r2 = await displaySetting('收起全部分组');
    const afterCollapse = await listBody();
    await shot(page, 'M-77-收起全部分组.png');
    await logStep(B, { id: 'AF2-expand-collapse-groups', title: '「展开/收起全部分组」对列表做了什么',
      target: '点「展示设置」→ 展开全部分组，再 → 收起全部分组，各读一次列表主体',
      evidence: { before, menu: r1.pop, afterExpand, menu2: r2.pop, afterCollapse },
      visible_text: `成组情况 ${JSON.stringify(grouped)}。` +
        `操作前列表 ${JSON.stringify(before.rows)}，文案「${before.text}」；` +
        `展开全部分组之后 ${JSON.stringify(afterExpand.rows)}，文案「${afterExpand.text}」；` +
        `收起全部分组之后 ${JSON.stringify(afterCollapse.rows)}，文案「${afterCollapse.text}」。` +
        `→ **${JSON.stringify(before.rows) === JSON.stringify(afterExpand.rows) && JSON.stringify(before.rows) === JSON.stringify(afterCollapse.rows) ? '这轮看不出差别（可能是组没建成，或本来就都是展开态）' : '有差别'}**`,
      shot: 'M-76-展开全部分组.png' });
    console.log('AF2:', JSON.stringify({ before: before.rows, exp: afterExpand.rows, col: afterCollapse.rows }));
  } catch (e) { await logStep(B, { id: 'AF2-expand-collapse-groups', title: '展开收起分组', failed: true, visible_text: String(e).slice(0, 300) }); console.log('AF2 失败', String(e).slice(0, 250)); }

  // ── AF3 资产标签的四枚按钮：每枚测完刷新，绝不复用状态
  const probe = {};
  for (const aria of ['筛选', '批量操作', '创建', '资产管理']) {
    try {
      await page.reload({ waitUntil: 'domcontentloaded' }); await page.waitForTimeout(6500);
      await closePromos(page).catch(() => {}); await page.waitForTimeout(1400);
      if (!(await openDrawer())) { probe[aria] = { err: '刷新后抽屉打不开' }; continue; }
      await page.locator('[class*="mantine-Drawer-content"]').getByText('资产', { exact: true }).first().click();
      await page.waitForTimeout(1800);
      const btn = await btnBy(aria);
      if (!btn) { probe[aria] = { err: '按钮不在' }; continue; }
      const before = (await listBody()).text;
      await page.mouse.click(btn.cx, btn.cy); await page.waitForTimeout(1800);
      const pop = await floating();
      const after = await listBody();
      await shot(page, `M-78-资产-${aria}.png`);
      probe[aria] = { btn, pop, before: (before || '').slice(0, 140), after: (after.text || '').slice(0, 200) };
    } catch (e) { probe[aria] = { err: String(e).slice(0, 200) }; }
    console.log(`AF3 ${aria}:`, JSON.stringify(probe[aria]).slice(0, 500));
  }
  await logStep(B, { id: 'AF3-asset-buttons', title: '「资产」标签的 筛选 / 批量操作 / 创建 / 管理 各点开是什么',
    target: '每枚按钮都**刷新页面后重新进入**再点，避免上一轮的状态污染',
    evidence: probe,
    visible_text: Object.entries(probe).map(([k, v]) => `**${k}**（${JSON.stringify(v.btn || {})}）→ ` +
      `${v.err ? `没测成：${v.err}` : `浮层 ${JSON.stringify(v.pop)}；抽屉文案「${v.before}」→「${v.after}」`}`).join('\n') +
      `\n\n**「创建默认资产分类」「上传资产」两枚大按钮一个都没点 —— 都会写账户数据。**`,
    shot: 'M-78-资产-资产管理.png' });

  console.log('收尾节点:', await N());
} finally {
  await browser.close();
}
