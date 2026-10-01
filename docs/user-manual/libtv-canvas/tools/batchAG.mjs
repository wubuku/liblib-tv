// Batch AG —— 只为一件事：把「展开全部分组 / 收起全部分组」问明白。
//
// AD、AE、AF 三轮连续三次只建出 1 个节点，每次都当成「建不出来」。
// AF 终于查到真因，和 `exact: true` 无关：**8 个候选落点全在同一条 x 带里** ——
// 第一个图片节点在 100% 缩放下宽 622px，加上挂在它下面的参数面板，
// 整条 x∈[460,1082] 的竖带都被占满，后 7 个候选点不是砸在节点上就是砸在参数面板上，
// 双击打不开「添加节点」面板（打开的是节点自己的编辑区）。
//
// 教训：**「连续三次失败」时该怀疑的不是产品，是自己的候选点集。**
// 候选点如果都落在同一个矩形里，那不是搜索，是撞墙。
//
// 这一轮的建点器：先按 Esc 收掉参数面板，再量所有节点的包围盒，
// 从「右侧 / 下方」两个方向求解空位，右边塞不下就往下堆。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { nodeCount } from './canvas-ops.mjs';
import { openDropdown } from './canvas-dropdown.mjs';

const SPACE = '10354929';
const B = 'batchAG';
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
  return { x: r.x };
});
const opener = page.locator('[data-academy-guide-anchor="workspace-asset-management"]');
const openDrawer = async () => {
  const b = await drawerBox();
  if (b && b.x > -50) return true;
  await opener.first().click({ timeout: 6000 }); await page.waitForTimeout(2600);
  const b2 = await drawerBox();
  return !!(b2 && b2.x > -50);
};
const closeDrawer = async () => { await page.mouse.click(880, 120).catch(() => {}); await page.waitForTimeout(900); };
const floating = () => page.evaluate(() => [...document.querySelectorAll(
  '[class*="Popover-dropdown"],[class*="Menu-dropdown"],[class*="Dropdown-dropdown"]')]
  .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 40 && r.height > 12; })
  .map((e) => ({ text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 200),
    items: [...e.querySelectorAll('button,[role="menuitem"]')].filter((c) => {
      const cr = c.getBoundingClientRect();
      return cr.width > 24 && cr.height > 8 && cr.height < 46 && (c.innerText || '').trim().length <= 24;
    }).map((c) => { const cr = c.getBoundingClientRect();
      return { t: (c.innerText || '').trim(), cx: Math.round(cr.x + cr.width / 2), cy: Math.round(cr.y + cr.height / 2) }; }) })));
async function displaySetting(pick) {
  const btn = await page.evaluate(() => {
    const d = [...document.querySelectorAll('[class*="mantine-Drawer-content"]')]
      .find((x) => { const r = x.getBoundingClientRect(); return r.width > 200 && r.height > 300 && r.x < 400; });
    if (!d) return null;
    const e = [...d.querySelectorAll('button')].find((b) => b.getAttribute('aria-label') === '展示设置');
    if (!e) return null;
    const r = e.getBoundingClientRect();
    return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) };
  });
  if (!btn) throw new Error('找不到「展示设置」');
  await page.mouse.click(btn.cx, btn.cy); await page.waitForTimeout(1500);
  const pop = await floating();
  const it = pop[0]?.items.find((x) => x.t === pick);
  if (!it) throw new Error(`菜单里没有「${pick}」；读到 ${JSON.stringify(pop[0]?.items.map((x) => x.t))}`);
  await page.mouse.click(it.cx, it.cy); await page.waitForTimeout(1700);
  return { menu: pop[0]?.items.map((x) => x.t), it };
}
/** 列表主体的完整读数：行 + 所有可见条目文字（不预设 class）。 */
const drawerBody = () => page.evaluate(() => {
  const d = [...document.querySelectorAll('[class*="mantine-Drawer-content"]')]
    .find((x) => { const r = x.getBoundingClientRect(); return r.width > 200 && r.height > 300 && r.x < 400; });
  if (!d) return null;
  const rows = [...d.querySelectorAll('div.group\\/node')].map((r) => (r.innerText || '').replace(/\s+/g, ' ').trim());
  const items = [...d.querySelectorAll('div')].filter((e) => {
    const r = e.getBoundingClientRect();
    const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
    return r.y > 180 && r.y < 760 && r.width > 100 && t.length > 0 && t.length < 40
      && ![...e.children].some((c) => (c.innerText || '').replace(/\s+/g, ' ').trim() === t);
  }).map((e) => { const r = e.getBoundingClientRect();
    return { t: (e.innerText || '').replace(/\s+/g, ' ').trim(),
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      cls: (e.className || '').toString().slice(0, 46) }; });
  return { rows, items, text: (d.innerText || '').replace(/\s+/g, ' ').trim() };
});

/** 收掉参数面板，再量节点包围盒，从右侧/下方求解空位。 */
async function freeSpot() {
  await page.keyboard.press('Escape').catch(() => {});
  await page.waitForTimeout(500);
  const ns = await nodeList();
  if (!ns.length) return [760, 320];
  const right = Math.max(...ns.map((n) => n.rect[0] + n.rect[2]));
  const bottom = Math.max(...ns.map((n) => n.rect[1] + n.rect[3]));
  const cands = [
    [Math.min(right + 360, 1370), 260],
    [Math.min(right + 360, 1370), 520],
    [700, Math.min(bottom + 280, 720)],
    [1150, Math.min(bottom + 280, 720)],
    [430, Math.min(bottom + 280, 720)],
  ];
  for (const [x, y] of cands) {
    const clash = ns.some((n) => x > n.rect[0] - 40 && x < n.rect[0] + n.rect[2] + 40
      && y > n.rect[1] - 40 && y < n.rect[1] + n.rect[3] + 40);
    if (!clash && x > 400 && y > 140 && y < 740) return [x, y];
  }
  return null;
}

async function addNode(item) {
  for (let round = 0; round < 3; round += 1) {
    const spot = await freeSpot();
    if (!spot) return false;
    const [x, y] = spot;
    await page.mouse.dblclick(x, y); await page.waitForTimeout(1100);
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
  await beginBatch(B, { note: '摆开 4 个节点并成组，问「展开/收起全部分组」' });

  await openDropdown(page, 1000);
  await page.getByRole('button', { name: '新建画布', exact: true }).first().click();
  await page.waitForTimeout(4500);
  await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(1500);
  for (const item of ['图片', '音频', '视频', '文本']) {
    const spot = await freeSpot();
    const ok = await addNode(item);
    console.log(`建 ${item}:`, ok, '落点', spot, '节点数', await N());
  }
  let ns = await nodeList();
  console.log('节点:', await N(), ns.map((n) => ({ t: n.title, r: n.rect })));

  // 成组：点第一个，Shift+点第二个，⌘G
  let grouped = null;
  if (ns.length >= 2) {
    await page.mouse.click(ns[0].rect[0] + 40, ns[0].rect[1] + 18); await page.waitForTimeout(800);
    await page.keyboard.down('Shift');
    await page.mouse.click(ns[1].rect[0] + 40, ns[1].rect[1] + 18);
    await page.keyboard.up('Shift'); await page.waitForTimeout(1000);
    const sel = await page.locator('.react-flow__node.selected').count();
    const groupBtn = await page.evaluate(() => {
      const b = [...document.querySelectorAll('button,[role="button"]')]
        .find((x) => (x.innerText || '').trim() === '成组' && x.getBoundingClientRect().width > 10);
      if (!b) return null;
      const r = b.getBoundingClientRect();
      return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) };
    });
    if (groupBtn) { await page.mouse.click(groupBtn.cx, groupBtn.cy); await page.waitForTimeout(1800); }
    else { await page.keyboard.press('Meta+g'); await page.waitForTimeout(1800); }
    const groups = await page.evaluate(() => ({
      groupNodes: document.querySelectorAll('.react-flow__node-group').length,
      anyGroupCls: [...document.querySelectorAll('.react-flow__node')].map((n) => n.className.toString()).filter((c) => /group/i.test(c)).slice(0, 3),
      labelled: [...document.querySelectorAll('.react-flow__node')].map((n) => (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 14)).filter((t) => /Group|组/.test(t)),
    }));
    grouped = { selectedAfterShiftClick: sel, usedGroupButton: !!groupBtn, ...groups };
    await shot(page, 'M-79-成组之后.png');
  }
  console.log('成组:', JSON.stringify(grouped));
  ns = await nodeList();

  if (!(await openDrawer())) throw new Error('抽屉打不开');
  const before = await drawerBody();
  await shot(page, 'M-80-列表-成组之后.png');

  const steps = [];
  for (const pick of ['收起全部分组', '展开全部分组', '收起全部分组']) {
    try {
      const r = await displaySetting(pick);
      const b = await drawerBody();
      steps.push({ pick, menu: r.menu, rows: b.rows, itemCount: b.items.length, text: b.text });
      await shot(page, `M-81-${pick}.png`);
    } catch (e) { steps.push({ pick, err: String(e).slice(0, 180) }); }
  }
  await logStep(B, { id: 'AG1-expand-collapse-groups', title: '「展开/收起全部分组」到底对什么起作用',
    target: '摆开 4 个节点并把前两个成组，再在「展示设置」里 收起 → 展开 → 收起，各读一次列表主体',
    evidence: { nodes: ns.map((n) => ({ t: n.title, r: n.rect })), grouped, before, steps },
    visible_text: `画布上 ${ns.length} 个节点 ${JSON.stringify(ns.map((n) => n.title))}；成组结果 ${JSON.stringify(grouped)}。` +
      `初始列表 ${JSON.stringify(before.rows)}（主体可读条目 ${before.items.length} 个：${JSON.stringify(before.items.map((i) => i.t).slice(0, 12))}）。` +
      steps.map((s) => s.err ? `**${s.pick}** 没测成：${s.err}` :
        `**${s.pick}** → 列表行 ${JSON.stringify(s.rows)}，可读条目 ${s.itemCount} 个 ${JSON.stringify(s.items ? s.items.map((i) => i.t).slice(0, 12) : [])}${s.itemCount !== undefined ? '' : ''}，主体「${(s.text || '').slice(0, 180)}」`).join('\n') +
      `→ **${steps.every((s) => JSON.stringify(s.rows) === JSON.stringify(before.rows)) ? '三步下来列表行数没变过 —— 要么本来就都是展开态，要么这个菜单项在这张画布上无效' : '三步之间有差别'}**`,
    shot: 'M-81-收起全部分组.png' });
  console.log('AG1:', JSON.stringify(steps, null, 1).slice(0, 2500));

  console.log('收尾节点:', await N());
} finally {
  await browser.close();
}
