// Batch Z —— 查两件事，都来自 batchY 的自相矛盾：
//
//   ① 「复制」按下去，`.react-flow__node` 数量没变（1 → 1），
//      但资产管理抽屉里已经多出一行「取证重命名 - 副本」，还写着「共 2 节点」。
//      副本到底在哪？候选：出了视口被虚拟化 / 没进 React Flow 状态要刷新才有 /
//      类名不是 .react-flow__node。batchY 的判据是错的，不是产品没做。
//      决定性实验：**复制完刷新页面再数**。
//
//   ② 「删除」按下去节点立刻消失，脚本里没看到确认弹窗。
//      但「点完立刻消失」也可能是我等 2400ms 期间弹窗自己关了。
//      要证明的是：**点完 200ms 内有没有确认层**。
//      顺带试 ⌘Z 能不能撤销——手册要不要写「删除不可撤销」。
//
// 判据沿用老规矩：菜单读 innerText（Menu 有文字），控件读 aria-label。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { nodeCount, fitView } from './canvas-ops.mjs';
import { openDropdown } from './canvas-dropdown.mjs';

const SPACE = '10354929';
const B = 'batchZ';
const { browser, page } = await launch();

const N = () => nodeCount(page);
const nodeList = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => {
  const r = n.getBoundingClientRect();
  return { id: n.getAttribute('data-id'), title: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 18),
    rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
}));
/** 画布容器里到底挂了多少东西 —— 不预设类名，把 nodes 容器直接 dump 出来。 */
const dumpNodes = () => page.evaluate(() => {
  const host = document.querySelector('.react-flow__nodes');
  if (!host) return { err: '没有 .react-flow__nodes 容器' };
  const kids = [...host.children].map((c) => { const r = c.getBoundingClientRect();
    return { tag: c.tagName, cls: (c.className || '').toString().slice(0, 60),
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; });
  const vp = document.querySelector('.react-flow__viewport');
  const pane = document.querySelector('.react-flow__pane');
  return { kids, viewport: vp ? vp.style.transform : null,
    paneScroll: pane ? [pane.scrollWidth, pane.scrollHeight] : null,
    hostStyle: host.getAttribute('style') };
});
const drawerRows = () => page.evaluate(() => {
  const rows = [...document.querySelectorAll('div.group\\/node')].map((r) => (r.innerText || '').replace(/\s+/g, ' ').trim());
  const body = [...document.querySelectorAll('[class*="mantine-Drawer-body"]')]
    .map((b) => (b.innerText || '').replace(/\s+/g, ' ').trim()).filter((t) => /共\s*\d+\s*节点/.test(t));
  return { rows, summary: body[0] || null };
});
const opener = page.locator('[data-academy-guide-anchor="workspace-asset-management"]');
const openDrawer = async () => {
  if (await page.evaluate(() => !!document.querySelector('div.group\\/node'))) return true;
  await opener.first().click({ timeout: 6000 }); await page.waitForTimeout(2600);
  return await page.evaluate(() => !!document.querySelector('div.group\\/node'));
};
const openRowMenu = (idx = 0) => page.evaluate((i) => {
  const row = document.querySelectorAll('div.group\\/node')[i];
  if (!row) return { err: '没有第 ' + i + ' 行' };
  const btn = [...row.querySelectorAll('button')].find((b) => b.getAttribute('aria-label') === '更多操作');
  if (!btn) return { err: '该行没有「更多操作」按钮' };
  const b = btn.getBoundingClientRect();
  return { cx: Math.round(b.x + b.width / 2), cy: Math.round(b.y + b.height / 2), rowText: (row.innerText || '').trim() };
}, idx);
const readMenu = () => page.evaluate(() => {
  const m = document.querySelector('[class*="mantine-Menu-dropdown"]');
  if (!m) return null;
  return [...m.querySelectorAll('button,[role="menuitem"],li,div')].filter((e) => {
    const r = e.getBoundingClientRect();
    return r.width > 40 && r.height > 16 && r.height < 46 && (e.innerText || '').trim().length <= 12 && !e.querySelector('div[style]');
  }).map((e) => { const r = e.getBoundingClientRect();
    return { t: (e.innerText || '').trim(), cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; })
    .filter((x, i, a) => a.findIndex((y) => y.t === x.t && y.cy === x.cy) === i);
});
const clickMenu = async (label) => {
  const m0 = await openRowMenu(0);
  if (m0.err) throw new Error(m0.err);
  await page.mouse.click(m0.cx, m0.cy); await page.waitForTimeout(1800);
  const menu = await readMenu();
  const it = menu?.find((i) => i.t === label);
  if (!it) throw new Error(`菜单里没有「${label}」；读到 ${JSON.stringify(menu?.map((i) => i.t))}`);
  await page.mouse.click(it.cx, it.cy);
  return it;
};
/** 有没有盖住视口的浮层（真遮罩 .mantine-Modal-overlay，不是永远存在的空壳 .mantine-Modal-root）。 */
const overlayScan = () => page.evaluate(() => {
  const ov = [...document.querySelectorAll('.mantine-Modal-overlay,[role="dialog"]')]
    .filter((d) => { const r = d.getBoundingClientRect(); return r.width > 60 && r.height > 40; })
    .map((d) => ({ cls: (d.className || '').toString().slice(0, 40), role: d.getAttribute('role'),
      rect: [Math.round(d.getBoundingClientRect().width), Math.round(d.getBoundingClientRect().height)],
      text: (d.innerText || '').replace(/\s+/g, ' ').slice(0, 200) }));
  return { overlays: ov, danger: ov.some((o) => /确定|确认|取消|删除|撤销|恢复/.test(o.text)) };
});

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4000 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '查「复制」副本去哪了 +「删除」有无二次确认' });

  await openDropdown(page, 1000);
  await page.getByRole('button', { name: '新建画布', exact: true }).first().click();
  await page.waitForTimeout(4500);
  await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(1500);
  for (const [x, y] of [[500, 300], [500, 390], [500, 210]]) {
    const ns = await nodeList();
    if (ns.some((n) => x > n.rect[0] - 20 && x < n.rect[0] + n.rect[2] + 20 && y > n.rect[1] - 20 && y < n.rect[1] + n.rect[3] + 20)) continue;
    await page.mouse.dblclick(x, y); await page.waitForTimeout(1000);
    const it = page.locator('[data-guide-lockable-portal="true"], [data-canvas-menu-portal="true"]').first()
      .getByText('图片', { exact: false }).first();
    if (await it.count().catch(() => 0)) { await it.click({ timeout: 4000 }).catch(() => {}); await page.waitForTimeout(2200); }
    if (await N() > 0) break;
    await page.keyboard.press('Escape').catch(() => {});
  }
  await fitView(page, 1); await page.waitForTimeout(1200);
  const start = { count: await N(), nodes: await nodeList(), dump: await dumpNodes() };
  console.log('起点:', JSON.stringify(start, null, 1).slice(0, 700));

  // ── Z1 复制：点完立刻查，再 ⌘0，再刷新
  let z1 = {};
  try {
    if (!(await openDrawer())) throw new Error('抽屉打不开');
    const beforeRows = await drawerRows();
    await clickMenu('复制');
    await page.waitForTimeout(1200);
    const immediate = { count: await N(), dump: await dumpNodes(), drawer: await drawerRows() };
    await shot(page, 'M-43-复制后立刻.png');
    await fitView(page, 1); await page.waitForTimeout(1600);
    const afterFit = { count: await N(), nodes: await nodeList(), dump: await dumpNodes() };
    // 决定性：刷新页面再数
    await page.reload({ waitUntil: 'domcontentloaded' }); await page.waitForTimeout(6500);
    await closePromos(page).catch(() => {}); await page.waitForTimeout(1500);
    await fitView(page, 1); await page.waitForTimeout(1500);
    const afterReload = { count: await N(), nodes: await nodeList(), drawer: await openDrawer().then(drawerRows) };
    await shot(page, 'M-44-复制后刷新.png');
    z1 = { beforeRows, immediate, afterFit, afterReload };
    await logStep(B, { id: 'Z1-copy-where', title: '「复制」出来的副本到底在哪：立刻查 / ⌘0 后查 / 刷新后查',
      target: '资产管理第 0 行 →「⋯ → 复制」，三个时点各数一次画布节点',
      evidence: z1,
      visible_text: `建 1 个节点时画布上有 ${start.count} 个（${JSON.stringify(start.nodes.map((n) => n.title))}）。` +
        `点「复制」后立刻数：**${immediate.count}** 个，抽屉 ${JSON.stringify(immediate.drawer.rows)}（${immediate.drawer.summary}）；` +
        `⌘0 适应画布后再数：**${afterFit.count}** 个；` +
        `**刷新页面后再数：${afterReload.count} 个**，抽屉 ${JSON.stringify(afterReload.drawer.rows)}（${afterReload.drawer.summary}）。` +
        `→ ${afterReload.count > start.count ? '副本真实存在，只是不在视口里，刷新/适应画布才看得到' : '副本没有落到画布上'}`,
      shot: 'M-44-复制后刷新.png' });
  } catch (e) { await logStep(B, { id: 'Z1-copy-where', title: '「复制」副本位置', failed: true, visible_text: String(e).slice(0, 300) }); console.log('Z1 失败', String(e).slice(0, 200)); }

  // ── Z2 删除：点完 200ms 内就查确认层
  try {
    if (!(await openDrawer())) throw new Error('抽屉打不开');
    const before = await N();
    const beforeDrawer = await drawerRows();
    await clickMenu('删除');
    // 不等！立刻查有没有确认层
    await page.waitForTimeout(200);
    const at200 = await overlayScan();
    await shot(page, 'M-45-删除后200毫秒.png');
    await page.waitForTimeout(2200);
    const at2400 = await overlayScan();
    const after = await N();
    const afterDrawer = await drawerRows();
    // 撤销能力
    await page.keyboard.press('Meta+z'); await page.waitForTimeout(2000);
    const afterUndo = { count: await N(), drawer: await drawerRows() };
    await shot(page, 'M-46-删除后撤销.png');
    const z2 = { before, beforeDrawer, at200, at2400, after, afterDrawer, afterUndo };
    await logStep(B, { id: 'Z2-delete-confirm', title: '「删除」有没有二次确认、能不能撤销',
      target: '点菜单里的「删除」后 200ms / 2400ms 各查一次浮层，再按 ⌘Z',
      evidence: z2,
      visible_text: `点之前：画布 ${before} 个节点，抽屉 ${JSON.stringify(beforeDrawer.rows)}。` +
        `点后 200 毫秒：浮层 ${JSON.stringify(at200.overlays)}（有无确认层：**${at200.overlays.length ? '有' : '没有'}**）；` +
        `点后 2400 毫秒：浮层 ${JSON.stringify(at2400.overlays)}，画布剩 **${after}** 个节点，抽屉 ${JSON.stringify(afterDrawer.rows)}（${afterDrawer.summary}）。` +
        `按 ⌘Z 撤销后：画布 ${afterUndo.count} 个，抽屉 ${JSON.stringify(afterUndo.drawer.rows)} → ` +
        `**${afterUndo.count > after ? '能撤销' : '撤不回来'}**`,
      shot: 'M-45-删除后200毫秒.png' });
    console.log('Z2:', JSON.stringify(z2.afterUndo));
  } catch (e) { await logStep(B, { id: 'Z2-delete-confirm', title: '「删除」二次确认', failed: true, visible_text: String(e).slice(0, 300) }); console.log('Z2 失败', String(e).slice(0, 200)); }

  console.log('收尾节点:', await N());
} finally {
  await browser.close();
}
