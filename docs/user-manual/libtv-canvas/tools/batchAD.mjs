// Batch AD —— 资产管理左抽屉工具行的那几枚控件，至今**一个都没点过**。
//
// M-02 那张图上写着「搜索 / 筛选 / 管理」，正文只当装饰描述了一遍。
// 具体没写的是：
//   · 🔍 那个搜索框 —— 在「画布」标签下搜的是**节点名**还是别的？实时过滤还是回车才生效？
//   · 「所有评级 ▾」 —— 下拉里有哪些档位？和节点上的评级是什么关系？
//   · 右端那枚列表切换图标 —— 切的是「列表 / 卡片 / 网格」哪几种视图？
//   · 「资产」标签下才有的「+」和「管理」—— 「管理」打开什么？（**不点创建/上传**，会写账户数据）
//
// 造点素材才有得搜：建 4 个节点（图片/视频/音频/文本），改几个不同的名字，
// 这样搜索和筛选才有可分辨的结果。
//
// 判据教训（第 14 节）：
//   · 工具行按钮大半是**纯图标**，先按 `aria-label` 兜一遍，再读 innerText；
//   · 抽屉开没开要查**容器**的实时坐标，不能拿「里面有行」当代理；
//   · 「列表切换」点开后可能有多个视图选项，逐个点开看，但**别在视图里做会写数据的操作**。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { nodeCount, fitView } from './canvas-ops.mjs';
import { openDropdown } from './canvas-dropdown.mjs';

const SPACE = '10354929';
const B = 'batchAD';
const { browser, page } = await launch();

const N = () => nodeCount(page);
const nodeTitles = () => page.evaluate(() =>
  [...document.querySelectorAll('.react-flow__node')].map((n) => (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 12)));
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
const closeDrawer = async () => { await page.mouse.click(900, 150).catch(() => {}); await page.waitForTimeout(900); };
const rows = () => page.evaluate(() => [...document.querySelectorAll('div.group\\/node')]
  .map((r) => (r.innerText || '').replace(/\s+/g, ' ').trim()));
const summary = () => page.evaluate(() => ([...document.querySelectorAll('[class*="mantine-Drawer-body"]')]
  .map((b) => (b.innerText || '').replace(/\s+/g, ' ').trim()).filter((t) => /共\s*\d+\s*节点|暂无|没有/.test(t))[0]) || null);
/** 抽屉里所有可见控件：文字 + aria-label + 坐标，纯图标按钮靠 aria 才认得出来。 */
const toolbar = () => page.evaluate(() => {
  const d = [...document.querySelectorAll('[class*="mantine-Drawer-content"]')]
    .find((x) => { const r = x.getBoundingClientRect(); return r.width > 200 && r.height > 300 && r.x < 400; });
  if (!d) return null;
  const pick = (e) => { const r = e.getBoundingClientRect();
    return { tag: e.tagName, t: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20),
      aria: e.getAttribute('aria-label'), ph: e.getAttribute('placeholder'), type: e.getAttribute('type'),
      cls: (e.className || '').toString().slice(0, 46),
      cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2),
      rect: [Math.round(r.width), Math.round(r.height)], disabled: e.disabled === true }; };
  return {
    inputs: [...d.querySelectorAll('input')].filter((e) => { const r = e.getBoundingClientRect(); return r.width > 20; }).map(pick),
    buttons: [...d.querySelectorAll('button,[role="button"],[role="tab"]')].filter((e) => { const r = e.getBoundingClientRect(); return r.width > 10; }).map(pick),
    tabs: [...d.querySelectorAll('[role="tab"]')].map(pick),
    selects: [...d.querySelectorAll('[role="combobox"],select')].map(pick),
  };
});
/** 展开在抽屉上方/外层的浮层（Mantine Popover / Menu），只读内容。 */
const floating = () => page.evaluate(() => [...document.querySelectorAll(
  '[class*="Popover-dropdown"],[class*="Menu-dropdown"],[class*="Dropdown-dropdown"]')]
  .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 40 && r.height > 12; })
  .map((e) => { const r = e.getBoundingClientRect();
    return { cls: (e.className || '').toString().slice(0, 34),
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 240),
      items: [...e.querySelectorAll('button,[role="option"],li,div')].filter((c) => {
        const cr = c.getBoundingClientRect();
        return cr.width > 30 && cr.height > 10 && cr.height < 44 && (c.innerText || '').trim().length <= 20 && !c.querySelector('div[style]');
      }).map((c) => { const cr = c.getBoundingClientRect();
        return { t: (c.innerText || '').trim(), cx: Math.round(cr.x + cr.width / 2), cy: Math.round(cr.y + cr.height / 2) }; })
        .filter((x, i, a) => a.findIndex((y) => y.t === x.t && y.cy === x.cy) === i) }; }));

async function addNode(x, y, label) {
  for (const [dx, dy] of [[0, 0], [0, 110], [0, -110], [120, 0]]) {
    await page.mouse.dblclick(x + dx, y + dy); await page.waitForTimeout(1100);
    const it = page.locator('[data-guide-lockable-portal="true"], [data-canvas-menu-portal="true"]').first()
      .getByText(label, { exact: true }).first();
    if (await it.count().catch(() => 0)) {
      const b = await N();
      await it.click({ timeout: 4000 }).catch(() => {}); await page.waitForTimeout(2400);
      if (await N() > b) return true;
    }
    await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(700);
  }
  return false;
}

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4000 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '资产管理工具行：搜索 / 评级筛选 / 视图切换 / 管理' });

  await openDropdown(page, 1000);
  await page.getByRole('button', { name: '新建画布', exact: true }).first().click();
  await page.waitForTimeout(4500);
  await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(1500);
  // 四个不同类型的节点：搜索时名字有区分度
  console.log('图片:', await addNode(430, 300, '图片'));
  console.log('音频:', await addNode(560, 300, '音频'));
  await fitView(page, 1); await page.waitForTimeout(1000);
  console.log('视频:', await addNode(700, 300, '视频'));
  console.log('文本:', await addNode(840, 300, '文本'));
  await fitView(page, 1); await page.waitForTimeout(1400);
  const titles = await nodeTitles();
  console.log('节点:', await N(), titles);

  if (!(await openDrawer())) throw new Error('抽屉打不开');
  const base = { rows: await rows(), summary: await summary(), toolbar: await toolbar() };
  await shot(page, 'M-55-资产管理-工具行控件全读.png');
  await logStep(B, { id: 'AD0-toolbar', title: '资产管理工具行到底有哪几枚控件（读 aria-label）',
    target: '打开抽屉，把里面所有 input / button / [role=tab] / [role=combobox] 连坐标一起 dump 出来',
    evidence: base,
    visible_text: `抽屉里**输入框** ${JSON.stringify(base.toolbar.inputs.map((i) => ({ t: i.t, ph: i.ph, aria: i.aria, rect: i.rect, cx: i.cx, cy: i.cy })))}；` +
      `**按钮** ${JSON.stringify(base.toolbar.buttons.map((b) => ({ t: b.t, aria: b.aria, rect: b.rect })))}；` +
      `**标签页** ${JSON.stringify(base.toolbar.tabs.map((t) => t.t))}；` +
      `**下拉** ${JSON.stringify(base.toolbar.selects.map((s) => ({ t: s.t, aria: s.aria, rect: s.rect })))}。` +
      `当前列表 ${JSON.stringify(base.rows)}，底部 ${JSON.stringify(base.summary)}`,
    shot: 'M-55-资产管理-工具行控件全读.png' });
  console.log('AD0:', JSON.stringify(base.toolbar, null, 1).slice(0, 1800));

  // ── AD1 搜索框
  try {
    const search = page.locator('[class*="mantine-Drawer-content"] input').first();
    if (!(await search.count().catch(() => 0))) throw new Error('找不到输入框');
    const ph = await search.getAttribute('placeholder');
    await search.click().catch(() => {});
    await page.keyboard.type('音频', { delay: 60 });
    await page.waitForTimeout(1600);
    const filtered = await rows();
    const sum1 = await summary();
    await shot(page, 'M-56-搜索-音频.png');
    // 再搜一个不存在的，确认是真过滤不是高亮
    await page.keyboard.press('Meta+a');
    await page.keyboard.type('不存在的名字xyz', { delay: 40 });
    await page.waitForTimeout(1600);
    const none = await rows();
    const sum2 = await summary();
    await shot(page, 'M-57-搜索-无结果.png');
    // 清空看回多少
    await page.keyboard.press('Meta+a'); await page.keyboard.press('Backspace');
    await page.waitForTimeout(1600);
    const cleared = await rows();
    await logStep(B, { id: 'AD1-search', title: '搜索框搜的是不是节点名、是不是实时过滤',
      target: `在抽屉第一个输入框里打字（placeholder=${JSON.stringify(ph)}），连搜两次再清空`,
      evidence: { placeholder: ph, all: titles, filtered, sum1, none, sum2, cleared },
      visible_text: `输入框 placeholder 是 ${JSON.stringify(ph)}。原始列表 ${JSON.stringify(titles)}（${titles.length} 行）。` +
        `输入「音频」→ 列表 ${JSON.stringify(filtered)}，底部 ${JSON.stringify(sum1)}；` +
        `输入「不存在的名字xyz」→ 列表 ${JSON.stringify(none)}，底部 ${JSON.stringify(sum2)}；` +
        `清空 → ${JSON.stringify(cleared)}。` +
        `→ **${none.length === 0 ? '真过滤，不是高亮' : '不是真过滤'}**，且**${filtered.length < titles.length && filtered.length > 0 ? '边打边筛（实时）' : '需回车才生效'}**`,
      shot: 'M-57-搜索-无结果.png' });
    console.log('AD1:', JSON.stringify({ ph, filtered, none, cleared, sum1, sum2 }));
  } catch (e) { await logStep(B, { id: 'AD1-search', title: '搜索框', failed: true, visible_text: String(e).slice(0, 300) }); console.log('AD1 失败', String(e).slice(0, 200)); }

  // ── AD2 「所有评级」下拉
  try {
    await closeDrawer(); if (!(await openDrawer())) throw new Error('抽屉打不开');
    const tb = await toolbar();
    const combo = tb.selects[0] || tb.buttons.find((b) => /评级/.test(b.t));
    if (!combo) throw new Error('找不到评级下拉；控件=' + JSON.stringify(tb.buttons.map((b) => b.t || b.aria)));
    await page.mouse.click(combo.cx, combo.cy); await page.waitForTimeout(1600);
    const pop = await floating();
    await shot(page, 'M-58-评级筛选下拉.png');
    const opt = pop?.[0]?.items?.find((i) => i.t && i.t !== combo.t.trim());
    let picked = null;
    if (opt) {
      const before = await rows();
      await page.mouse.click(opt.cx, opt.cy); await page.waitForTimeout(1800);
      const after = await rows();
      const afterTb = await toolbar();
      await shot(page, 'M-59-评级筛选-选中之后.png');
      picked = { opt: opt.t, before, after, comboLabel: afterTb.selects[0]?.t || afterTb.buttons.find((b) => /评级/.test(b.t))?.t };
    }
    // 收起来（点同一个按钮）
    const tb2 = await toolbar();
    const combo2 = tb2.selects[0] || tb2.buttons.find((b) => /评级/.test(b.t));
    if (combo2) { await page.mouse.click(combo2.cx, combo2.cy).catch(() => {}); await page.waitForTimeout(1200); }
    await logStep(B, { id: 'AD2-rating-filter', title: '「所有评级」下拉里有哪些档位、选中后筛出什么',
      target: `点开评级下拉 (${combo.cx},${combo.cy})，读选项并选一个非默认项`,
      evidence: { combo, pop, picked },
      visible_text: `评级下拉当前文案「${combo.t}」，控件尺寸 ${JSON.stringify(combo.rect)}。点开后浮层 ${JSON.stringify(pop)}。` +
        (picked ? `选了「${picked.opt}」：列表 ${picked.before.length} 行 → ${picked.after.length} 行 ${JSON.stringify(picked.after)}，下拉文案变成「${picked.comboLabel}」。` :
          '没有可点的选项。'),
      shot: 'M-59-评级筛选-选中之后.png' });
    console.log('AD2:', JSON.stringify({ pop, picked }));
  } catch (e) { await logStep(B, { id: 'AD2-rating-filter', title: '评级筛选', failed: true, visible_text: String(e).slice(0, 300) }); console.log('AD2 失败', String(e).slice(0, 200)); }

  // ── AD3 右端那枚视图切换图标
  try {
    await closeDrawer(); if (!(await openDrawer())) throw new Error('抽屉打不开');
    const tb = await toolbar();
    // 「管理」是文字，视图切换是纯图标 —— 排除掉文字已知的那几枚
    const known = /管理|资产|画布|定位到节点|更多操作/;
    const icon = tb.buttons.find((b) => !b.t && !known.test(b.aria || ''));
    if (!icon) throw new Error('找不到纯图标按钮；buttons=' + JSON.stringify(tb.buttons.map((b) => ({ t: b.t, aria: b.aria, rect: b.rect }))));
    await page.mouse.click(icon.cx, icon.cy); await page.waitForTimeout(1700);
    const pop = await floating();
    await shot(page, 'M-60-视图切换-点开.png');
    const items = pop?.[0]?.items || [];
    const results = [];
    for (const it of items.slice(0, 3)) {
      const r0 = await rows(); const s0 = await summary();
      const box = await drawerBox();
      await shot(page, `M-61-视图-${it.t}.png`);
      results.push({ item: it.t, rows: r0.length, rowText: r0, summary: s0, drawer: box });
      // 切回默认视图：从浮层里重新点同一个按钮不一定行，改成刷新重开抽屉
      await page.reload({ waitUntil: 'domcontentloaded' }); await page.waitForTimeout(6500);
      await closePromos(page).catch(() => {}); await page.waitForTimeout(1400);
      if (!(await openDrawer())) throw new Error('刷新后抽屉打不开');
      const tb2 = await toolbar();
      const icon2 = tb2.buttons.find((b) => !b.t && !known.test(b.aria || ''));
      if (icon2) { await page.mouse.click(icon2.cx, icon2.cy); await page.waitForTimeout(1400); }
    }
    await logStep(B, { id: 'AD3-view-switch', title: '抽屉右端那枚图标切的是哪几种视图',
      target: `点开纯图标按钮（aria=${JSON.stringify(icon.aria)}，${JSON.stringify(icon.rect)}）后逐个点开选项`,
      evidence: { icon, pop, results },
      visible_text: `那枚纯图标按钮的 aria-label 是 ${JSON.stringify(icon.aria)}，尺寸 ${JSON.stringify(icon.rect)}。` +
        `点开后浮层 ${JSON.stringify(pop)}。逐个切换的结果 ${JSON.stringify(results.map((r) => ({ 视图: r.item, 行数: r.rows, 底部: r.summary })))}。` +
        `→ **这枚按钮切换的是${results.length ? '「' + results.map((r) => r.item).join(' / ') + '」' : '（选项没读到）'}**`,
      shot: 'M-60-视图切换-点开.png' });
    console.log('AD3:', JSON.stringify({ icon: { aria: icon.aria, rect: icon.rect }, pop, results: results.map((r) => ({ i: r.item, n: r.rows })) }));
  } catch (e) { await logStep(B, { id: 'AD3-view-switch', title: '视图切换', failed: true, visible_text: String(e).slice(0, 300) }); console.log('AD3 失败', String(e).slice(0, 300)); }

  // ── AD4 「资产」标签下的「管理」按钮
  try {
    await closeDrawer(); if (!(await openDrawer())) throw new Error('抽屉打不开');
    const tabAsset = page.getByRole('tab', { name: '资产' }).first();
    if (await tabAsset.count().catch(() => 0)) await tabAsset.click();
    else await page.locator('[class*="mantine-Drawer-content"]').getByText('资产', { exact: true }).first().click();
    await page.waitForTimeout(1800);
    const tb = await toolbar();
    await shot(page, 'M-62-资产标签-工具行.png');
    const mgmt = tb.buttons.find((b) => /管理/.test(b.t));
    if (!mgmt) throw new Error('「资产」标签下没有「管理」按钮；buttons=' + JSON.stringify(tb.buttons.map((b) => b.t || b.aria)));
    await page.mouse.click(mgmt.cx, mgmt.cy); await page.waitForTimeout(2200);
    const pop = await floating();
    const bodyAfter = await page.evaluate(() => {
      const d = [...document.querySelectorAll('[class*="mantine-Drawer-content"]')]
        .find((x) => { const r = x.getBoundingClientRect(); return r.width > 200 && r.height > 300 && r.x < 400; });
      return d ? (d.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 300) : null; });
    await shot(page, 'M-63-点管理之后.png');
    await logStep(B, { id: 'AD4-manage', title: '「资产」标签的「管理」点开是什么',
      target: '切到「资产」标签后点「管理」',
      evidence: { toolbar: tb.buttons.map((b) => ({ t: b.t, aria: b.aria, rect: b.rect })), pop, bodyAfter },
      visible_text: `切到「资产」标签后工具行是 ${JSON.stringify(tb.buttons.map((b) => b.t || b.aria))}。` +
        `点「管理」(${mgmt.cx},${mgmt.cy}) 之后：浮层 ${JSON.stringify(pop)}；抽屉主体文案变成 ${JSON.stringify(bodyAfter)}。` +
        `**没有点「创建默认资产分类」「上传资产」「新建」任何一个 —— 都会写账户数据**`,
      shot: 'M-63-点管理之后.png' });
    console.log('AD4:', JSON.stringify({ pop, bodyAfter }));
  } catch (e) { await logStep(B, { id: 'AD4-manage', title: '「管理」按钮', failed: true, visible_text: String(e).slice(0, 300) }); console.log('AD4 失败', String(e).slice(0, 200)); }

  console.log('收尾节点:', await N());
} finally {
  await browser.close();
}
