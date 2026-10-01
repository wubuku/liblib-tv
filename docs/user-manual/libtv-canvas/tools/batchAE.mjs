// Batch AE —— 补救 batchAD 的两个打歪的探针，并把工具行补全。
//
// AD0 其实已经把「画布」标签工具行的三枚控件坐实了：
//   `搜索节点`（32×32, cx=24）· 一枚没有 aria 的 ≔ 图标（32×32, cx=60）·
//   `所有评级`（80×32, cx=120）· `展示设置`（右端）
//
// AD1 打歪在哪：`[class*="mantine-Drawer-content"] input` 的**第一个**是抽屉顶部那个
// 工作区名称输入框（y≈48），不是搜索框 —— `placeholder=null` 就是征兆。
// 搜索框根本没出现，因为 **`搜索节点` 是按钮不是输入框，得先点它**。
//
// AD3 打歪在哪：`tb.buttons.find(b => !b.t && !known.test(b.aria))` 取的是**第一个**纯图标按钮，
// 也就是 `搜索节点`（cx=24），而我要问的是**最右**那枚 `展示设置`。
//
// 另外 AD 那轮只建出 1 个节点（音频/视频/文本都失败）——
// 中途 fitView 把画布放大到 211%，后面写的落点全砸在已有节点上。
// 这一轮每建一个就重算一次可用落点，不中途 fitView。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { nodeCount } from './canvas-ops.mjs';
import { openDropdown } from './canvas-dropdown.mjs';

const SPACE = '10354929';
const B = 'batchAE';
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
const rows = () => page.evaluate(() => [...document.querySelectorAll('div.group\\/node')]
  .map((r) => (r.innerText || '').replace(/\s+/g, ' ').trim()));
const bodyText = () => page.evaluate(() => {
  const d = [...document.querySelectorAll('[class*="mantine-Drawer-content"]')]
    .find((x) => { const r = x.getBoundingClientRect(); return r.width > 200 && r.height > 300 && r.x < 400; });
  return d ? (d.innerText || '').replace(/\s+/g, ' ').trim() : null;
});
/** 抽屉工具行全部控件，按 x 排序。 */
const toolbar = () => page.evaluate(() => {
  const d = [...document.querySelectorAll('[class*="mantine-Drawer-content"]')]
    .find((x) => { const r = x.getBoundingClientRect(); return r.width > 200 && r.height > 300 && r.x < 400; });
  if (!d) return [];
  const pick = (e) => { const r = e.getBoundingClientRect();
    return { tag: e.tagName, t: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 16),
      aria: e.getAttribute('aria-label'), ph: e.getAttribute('placeholder'),
      cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2),
      w: Math.round(r.width), h: Math.round(r.height),
      svg: !!e.querySelector('svg'), html: (e.innerHTML || '').slice(0, 90) }; };
  return [...d.querySelectorAll('button,input,[role="tab"],[role="combobox"]')]
    .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 8 && r.x < 400; })
    .map(pick).sort((a, b) => a.cx - b.cx);
});
const floating = () => page.evaluate(() => [...document.querySelectorAll(
  '[class*="Popover-dropdown"],[class*="Menu-dropdown"],[class*="Dropdown-dropdown"]')]
  .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 40 && r.height > 12; })
  .map((e) => { const r = e.getBoundingClientRect();
    return { cls: (e.className || '').toString().slice(0, 36),
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 260),
      items: [...e.querySelectorAll('button,[role="option"],li,label,div')].filter((c) => {
        const cr = c.getBoundingClientRect();
        return cr.width > 24 && cr.height > 8 && cr.height < 46 && (c.innerText || '').trim().length <= 24 && !c.querySelector('div[style]');
      }).map((c) => { const cr = c.getBoundingClientRect();
        return { t: (c.innerText || '').trim(), cx: Math.round(cr.x + cr.width / 2), cy: Math.round(cr.y + cr.height / 2),
          checked: c.getAttribute('aria-checked'), role: c.getAttribute('role') }; })
        .filter((x, i, a) => a.findIndex((y) => y.t === x.t && y.cy === x.cy) === i) }; }));
/** 抽屉里所有可见输入框 —— 用来判断「搜索框到底出没出现」。 */
const inputs = () => page.evaluate(() => {
  const d = [...document.querySelectorAll('[class*="mantine-Drawer-content"]')]
    .find((x) => { const r = x.getBoundingClientRect(); return r.width > 200 && r.height > 300 && r.x < 400; });
  if (!d) return [];
  return [...d.querySelectorAll('input')].filter((e) => { const r = e.getBoundingClientRect(); return r.width > 20; })
    .map((e) => { const r = e.getBoundingClientRect();
      return { v: e.value, ph: e.placeholder, aria: e.getAttribute('aria-label'), type: e.type,
        rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; });
});

async function addNode(item) {
  // 程序化求解落点：避开已有节点，且避开左侧抽屉（x>420）
  for (const [x, y] of [[520, 250], [520, 420], [700, 250], [700, 420], [880, 250], [880, 420], [520, 600], [700, 600]]) {
    const ns = await nodeList();
    const clash = ns.some((n) => x > n.rect[0] - 30 && x < n.rect[0] + n.rect[2] + 30
                                 && y > n.rect[1] - 30 && y < n.rect[1] + n.rect[3] + 30);
    if (clash) continue;
    await page.mouse.dblclick(x, y); await page.waitForTimeout(1100);
    const it = page.locator('[data-guide-lockable-portal="true"], [data-canvas-menu-portal="true"]').first()
      .getByText(item, { exact: true }).first();
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
  await beginBatch(B, { note: '补救 AD：搜索按钮、≔ 图标、展示设置、管理；建 4 个节点' });

  await openDropdown(page, 1000);
  await page.getByRole('button', { name: '新建画布', exact: true }).first().click();
  await page.waitForTimeout(4500);
  await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(1500);
  for (const item of ['图片', '音频', '视频', '文本']) {
    const ok = await addNode(item);
    console.log(`建 ${item}:`, ok, '节点数', await N());
  }
  const titles = (await nodeList()).map((n) => n.title);
  console.log('节点:', await N(), titles);

  if (!(await openDrawer())) throw new Error('抽屉打不开');
  const base = { toolbar: await toolbar(), inputs: await inputs(), rows: await rows(), body: await bodyText() };
  await shot(page, 'M-64-工具行-四枚控件.png');
  await logStep(B, { id: 'AE0-toolbar', title: '「画布」标签工具行完整清单（按 aria-label 读）',
    target: '打开抽屉，把抽屉内所有 button / input / [role=tab] / [role=combobox] 按 x 排序读出来',
    evidence: base,
    visible_text: `画布上 ${titles.length} 个节点：${JSON.stringify(titles)}。抽屉工具行从左到右 ${JSON.stringify(base.toolbar.map((t) => ({ 文案: t.t, aria: t.aria, 尺寸: [t.w, t.h], 中心: [t.cx, t.cy], 有图标: t.svg })))}；` +
      `抽屉内输入框 ${JSON.stringify(base.inputs)}；列表 ${JSON.stringify(base.rows)}`,
    shot: 'M-64-工具行-四枚控件.png' });
  console.log('AE0:', JSON.stringify(base.toolbar.map((t) => ({ t: t.t, aria: t.aria, c: [t.cx, t.cy], s: [t.w, t.h] }))));

  // ── AE1 「搜索节点」：先点按钮，再看输入框出没出来
  try {
    const tb = await toolbar();
    const sb = tb.find((b) => b.aria === '搜索节点');
    if (!sb) throw new Error('找不到「搜索节点」按钮；工具行=' + JSON.stringify(tb.map((t) => t.aria || t.t)));
    const before = { inputs: await inputs(), rows: await rows() };
    await page.mouse.click(sb.cx, sb.cy); await page.waitForTimeout(1500);
    const afterInputs = await inputs();
    await shot(page, 'M-65-点搜索节点之后.png');
    let typed = null;
    const box = afterInputs.find((i) => i.cy > 100 && i.cy < 300 && i.rect[2] > 80);
    if (box) {
      await page.mouse.click(box.cx, box.cy);
      await page.keyboard.type('音频', { delay: 60 });
      await page.waitForTimeout(1600);
      const r1 = await rows();
      await shot(page, 'M-66-搜索-输入音频.png');
      await page.keyboard.press('Meta+a');
      await page.keyboard.type('节点', { delay: 60 });
      await page.waitForTimeout(1600);
      const r2 = await rows();
      await page.keyboard.press('Meta+a');
      await page.keyboard.type('zzz不存在', { delay: 50 });
      await page.waitForTimeout(1600);
      const r3 = await rows();
      await shot(page, 'M-67-搜索-无结果.png');
      await page.keyboard.press('Meta+a'); await page.keyboard.press('Backspace');
      await page.waitForTimeout(1400);
      const r4 = await rows();
      typed = { box, onAudio: r1, onNode: r2, onNone: r3, cleared: r4 };
    }
    await logStep(B, { id: 'AE1-search', title: '「搜索节点」点开是什么、搜的是不是节点名',
      target: `点 aria-label="搜索节点" 的按钮 (${sb.cx},${sb.cy})，再在弹出的输入框里打字`,
      evidence: { sb, before, afterInputs, typed },
      visible_text: `点之前抽屉里的输入框 ${JSON.stringify(before.inputs)}。` +
        `点「搜索节点」(${sb.cx},${sb.cy}) 之后：输入框变成 ${JSON.stringify(afterInputs)} → ` +
        `**${afterInputs.length > before.inputs.length ? '搜索框是点开后才出现的' : '输入框一直在，点它没有展开新东西'}**。` +
        (typed ? `在 (${typed.box.cx},${typed.box.cy}) 的输入框打字：「音频」→ ${JSON.stringify(typed.onAudio)}；` +
          `「节点」→ ${JSON.stringify(typed.onNode)}；「zzz不存在」→ ${JSON.stringify(typed.onNone)}；清空 → ${JSON.stringify(typed.cleared)}。` +
          `→ **${typed.onNone.length === 0 ? '真过滤（搜不到就清空）' : '不是真过滤'}**` : '没找到可输入的框，搜索没测成。'),
      shot: 'M-66-搜索-输入音频.png' });
    console.log('AE1:', JSON.stringify({ afterInputs, typed: typed && { onAudio: typed.onAudio, onNode: typed.onNode, onNone: typed.onNone, cleared: typed.cleared } }));
  } catch (e) { await logStep(B, { id: 'AE1-search', title: '「搜索节点」', failed: true, visible_text: String(e).slice(0, 300) }); console.log('AE1 失败', String(e).slice(0, 250)); }

  // ── AE2 那枚没有 aria 的 ≔ 图标
  try {
    await closeDrawer(); if (!(await openDrawer())) throw new Error('抽屉打不开');
    const tb = await toolbar();
    const icons = tb.filter((b) => b.aria === '搜索节点' || b.aria === '展示设置' || (b.t && /评级/.test(b.t)));
    const other = tb.find((b) => !icons.includes(b));
    if (!other) throw new Error('找不到那枚匿名图标；工具行=' + JSON.stringify(tb.map((t) => t.aria || t.t)));
    await page.mouse.click(other.cx, other.cy); await page.waitForTimeout(1600);
    const pop = await floating();
    const bodyNow = await bodyText();
    await shot(page, 'M-68-匿名图标-点开之后.png');
    await logStep(B, { id: 'AE2-anon-icon', title: '工具行里那枚没有 aria-label 的图标点开是什么',
      target: `点 (${other.cx},${other.cy}) 那枚 ${other.w}×${other.h} 的匿名按钮`,
      evidence: { other, pop, body: bodyNow },
      visible_text: `那枚按钮 aria-label=${JSON.stringify(other.aria)}、文案 ${JSON.stringify(other.t)}、尺寸 ${other.w}×${other.h}，` +
        `innerHTML 前 90 字符 ${JSON.stringify(other.html)}。点开后：浮层 ${JSON.stringify(pop)}；抽屉主体 ${JSON.stringify((bodyNow || '').slice(0, 200))}。`,
      shot: 'M-68-匿名图标-点开之后.png' });
    console.log('AE2:', JSON.stringify({ other: { aria: other.aria, t: other.t, s: [other.w, other.h], html: other.html }, pop }));
  } catch (e) { await logStep(B, { id: 'AE2-anon-icon', title: '匿名图标', failed: true, visible_text: String(e).slice(0, 300) }); console.log('AE2 失败', String(e).slice(0, 250)); }

  // ── AE3 「展示设置」—— 最右那枚
  try {
    await closeDrawer(); if (!(await openDrawer())) throw new Error('抽屉打不开');
    const tb = await toolbar();
    const vs = tb.find((b) => b.aria === '展示设置');
    if (!vs) throw new Error('找不到「展示设置」；工具行=' + JSON.stringify(tb.map((t) => t.aria || t.t)));
    const beforeRows = await rows();
    await page.mouse.click(vs.cx, vs.cy); await page.waitForTimeout(1700);
    const pop = await floating();
    await shot(page, 'M-69-展示设置-点开.png');
    const items = pop?.[0]?.items || [];
    const results = [];
    for (const it of items) {
      await page.mouse.click(vs.cx, vs.cy); await page.waitForTimeout(1200);
      // 浮层可能每次重开，重新读实时坐标（不能复用旧坐标）
      const pop2 = await floating();
      const target = pop2?.[0]?.items?.find((x) => x.t === it.t);
      if (!target) { results.push({ item: it.t, err: '重开后找不到该项' }); continue; }
      await page.mouse.click(target.cx, target.cy); await page.waitForTimeout(1700);
      const r = await rows();
      const b = await bodyText();
      await shot(page, `M-70-展示设置-${it.t}.png`);
      results.push({ item: it.t, role: target.role, checked: target.checked, rowCount: r.length, rows: r, body: (b || '').slice(0, 160) });
    }
    await logStep(B, { id: 'AE3-display-settings', title: '「展示设置」里有哪些开关、逐个打开是什么效果',
      target: `点 aria-label="展示设置" 的按钮 (${vs.cx},${vs.cy})，把每个选项都点一遍并看列表变化`,
      evidence: { vs, pop, beforeRows, results },
      visible_text: `「展示设置」(${vs.cx},${vs.cy}) 点开后浮层 ${JSON.stringify(pop)}，共 ${items.length} 个选项。` +
        `逐个点开的结果 ${JSON.stringify(results.map((r) => ({ 选项: r.item, 行数: r.rowCount, 勾选: r.checked, 说明: r.err })))}。` +
        `打开前列表 ${JSON.stringify(beforeRows)}。`,
      shot: 'M-69-展示设置-点开.png' });
    console.log('AE3:', JSON.stringify({ pop, results: results.map((r) => ({ i: r.item, n: r.rowCount, c: r.checked, e: r.err })) }));
  } catch (e) { await logStep(B, { id: 'AE3-display-settings', title: '「展示设置」', failed: true, visible_text: String(e).slice(0, 300) }); console.log('AE3 失败', String(e).slice(0, 250)); }

  // ── AE4 「资产」标签：搜索 / 批量操作 / 筛选 / 创建 / 管理 各自点开是什么
  try {
    await closeDrawer(); if (!(await openDrawer())) throw new Error('抽屉打不开');
    const tabAsset = page.getByRole('tab', { name: '资产' }).first();
    if (await tabAsset.count().catch(() => 0)) await tabAsset.click();
    else await page.locator('[class*="mantine-Drawer-content"]').getByText('资产', { exact: true }).first().click();
    await page.waitForTimeout(1800);
    const baseAsset = { toolbar: await toolbar(), body: await bodyText() };
    await shot(page, 'M-71-资产标签-工具行.png');
    const probe = {};
    for (const aria of ['搜索', '筛选', '批量操作', '创建', '资产管理']) {
      await page.locator('[class*="mantine-Drawer-content"]').getByText('资产', { exact: true }).first()
        .click().catch(() => {});
      await page.waitForTimeout(1200);
      const tb = await toolbar();
      const btn = tb.find((b) => b.aria === aria);
      if (!btn) { probe[aria] = { err: '按钮不在' }; continue; }
      await page.mouse.click(btn.cx, btn.cy); await page.waitForTimeout(1600);
      const pop = await floating();
      const bodyNow = await bodyText();
      const inputsNow = await inputs();
      await shot(page, `M-72-资产-${aria}.png`);
      probe[aria] = { btn: { t: btn.t, aria: btn.aria, s: [btn.w, btn.h], c: [btn.cx, btn.cy] },
        pop, body: (bodyNow || '').slice(0, 200), inputs: inputsNow };
      // 收起来：Esc 只在没有输入框焦点时用
      await page.keyboard.press('Escape').catch(() => {});
      await page.waitForTimeout(900);
    }
    await logStep(B, { id: 'AE4-asset-toolbar', title: '「资产」标签下五枚按钮各自点开是什么',
      target: '切到「资产」标签，逐个点 `搜索` / `筛选` / `批量操作` / `创建` / `管理`（aria-label）并读浮层',
      evidence: { baseAsset, probe },
      visible_text: `「资产」标签工具行 ${JSON.stringify(baseAsset.toolbar.map((t) => ({ 文案: t.t, aria: t.aria, 尺寸: [t.w, t.h] })))}，` +
        `主体 ${JSON.stringify((baseAsset.body || '').slice(0, 160))}。` +
        Object.entries(probe).map(([k, v]) => `**${k}** → ${v.err ? `按钮不在；` : `浮层 ${JSON.stringify(v.pop)}；抽屉主体 ${JSON.stringify(v.body)}；输入框 ${JSON.stringify(v.inputs)}；`}`).join(' ') +
        `**「创建默认资产分类」「上传资产」一个都没点 —— 会写账户数据**`,
      shot: 'M-71-资产标签-工具行.png' });
    console.log('AE4:', JSON.stringify(probe).slice(0, 2200));
  } catch (e) { await logStep(B, { id: 'AE4-asset-toolbar', title: '资产标签工具行', failed: true, visible_text: String(e).slice(0, 300) }); console.log('AE4 失败', String(e).slice(0, 250)); }

  console.log('收尾节点:', await N());
} finally {
  await browser.close();
}
