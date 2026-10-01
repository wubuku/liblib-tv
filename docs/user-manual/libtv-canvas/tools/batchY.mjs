// Batch Y —— 把「更多操作」菜单里的四项真按一遍。
//
// batchX 打开了菜单但四项一个都没点。这轮在**一次性测试画布**上点三个安全的：
//   重命名 / 复制 / 删除  —— 全部只改这张测试画布，删完再建，不碰用户真实项目。
//   添加到Agent —— 名字听起来会触发 Agent 动作，这轮**只点开看它变成什么**，
//                  一旦出现「发送 / 提交 / 派发」字样就立刻停手。
//
// 判据沿用 batchX 的教训：**找控件读 `aria-label`，不读 `innerText`**。
// 菜单项是 Mantine Menu，应该有文字，但仍然两个都查一遍。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep, fingerprint, diffPanels } from './scenario.mjs';
import { nodeCount, fitView } from './canvas-ops.mjs';
import { openDropdown } from './canvas-dropdown.mjs';

const SPACE = '10354929';
const B = 'batchY';
const { browser, page } = await launch();

const N = () => nodeCount(page);
const nodeList = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n, i) => {
  const r = n.getBoundingClientRect();
  return { i, title: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 16),
    x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) };
}));
async function addNodeAt(x, y, item) {
  for (const [dx, dy] of [[0, 0], [0, 90], [0, -90], [90, 0], [-90, 0]]) {
    const ns = await nodeList();
    if (ns.some((n) => x + dx > n.x - 20 && x + dx < n.x + n.w + 20 && y + dy > n.y - 20 && y + dy < n.y + n.h + 20)) continue;
    await page.mouse.dblclick(x + dx, y + dy); await page.waitForTimeout(1000);
    const it = page.locator('[data-guide-lockable-portal="true"], [data-canvas-menu-portal="true"]').first()
      .getByText(item, { exact: false }).first();
    if (await it.count().catch(() => 0)) {
      const b = await N(); await it.click({ timeout: 4000 }).catch(() => {}); await page.waitForTimeout(2200);
      if (await N() > b) return true;
    }
    await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(600);
  }
  return false;
}
/** 打开抽屉里第 idx 行的「⋯」菜单，返回菜单项（含 aria-label 与坐标）。 */
const openRowMenu = (idx = 0) => page.evaluate((i) => {
  const rows = [...document.querySelectorAll('div.group\\/node')];
  const row = rows[i];
  if (!row) return { err: '没有第 ' + i + ' 行' };
  const btn = [...row.querySelectorAll('button')].find((b) => b.getAttribute('aria-label') === '更多操作');
  if (!btn) return { err: '该行没有「更多操作」按钮' };
  const b = btn.getBoundingClientRect();
  return { cx: Math.round(b.x + b.width / 2), cy: Math.round(b.y + b.height / 2), rowText: (row.innerText || '').trim() };
}, idx);
const readMenu = () => page.evaluate(() => {
  const m = document.querySelector('[class*="mantine-Menu-dropdown"]');
  if (!m) return null;
  const b = m.getBoundingClientRect();
  return { rect: [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)],
    text: (m.innerText || '').replace(/\s+/g, ' ').trim(),
    items: [...m.querySelectorAll('button,[role="menuitem"],li,div')].filter((e) => {
      const r = e.getBoundingClientRect();
      return r.width > 40 && r.height > 16 && r.height < 46 && (e.innerText || '').trim().length <= 12 && !e.querySelector('div[style]');
    }).map((e) => { const r = e.getBoundingClientRect();
      return { t: (e.innerText || '').trim(), aria: e.getAttribute('aria-label'),
        cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2),
        color: getComputedStyle(e).color, disabled: getComputedStyle(e).opacity < 0.6 }; })
      .filter((x, i, a) => a.findIndex((y) => y.t === x.t && y.cy === x.cy) === i) };
});
const toasts = () => page.evaluate(() => [...document.querySelectorAll('[role="alert"],[class*="toast"],[class*="Toast"]')]
  .filter((t) => t.getBoundingClientRect().width > 0).map((t) => (t.innerText || '').replace(/\s+/g, ' ').slice(0, 140)));

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4000 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '真按 重命名/复制/删除；添加到Agent 只点开观察' });

  await openDropdown(page, 1000);
  await page.getByRole('button', { name: '新建画布', exact: true }).first().click();
  await page.waitForTimeout(4500);
  await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(1500);
  console.log('建 图片:', await addNodeAt(500, 300, '图片'));
  await fitView(page, 1); await page.waitForTimeout(1400);
  console.log('初始节点:', await N());

  const opener = page.locator('[data-academy-guide-anchor="workspace-asset-management"]');
  const openDrawer = async () => {
    if (await page.evaluate(() => !!document.querySelector('div.group\\/node'))) return true;
    await opener.first().click({ timeout: 6000 }); await page.waitForTimeout(2600);
    return await page.evaluate(() => !!document.querySelector('div.group\\/node'));
  };
  if (!(await openDrawer())) throw new Error('抽屉打不开');

  // ── Y1 重命名
  try {
    const m0 = await openRowMenu(0);
    if (m0.err) throw new Error(m0.err);
    await page.mouse.click(m0.cx, m0.cy); await page.waitForTimeout(2000);
    const menu = await readMenu();
    console.log('\n菜单项:', JSON.stringify(menu?.items));
    const item = menu?.items.find((i) => i.t === '重命名');
    if (!item) throw new Error('菜单里没有「重命名」；读到 ' + JSON.stringify(menu?.items.map((i) => i.t)));
    const before = (await nodeList()).map((n) => n.title);
    await page.mouse.click(item.cx, item.cy);
    await page.waitForTimeout(1800);
    // 菜单里直接改？还是弹输入框？两种都看一眼
    const editing = await page.evaluate(() => {
      const inputs = [...document.querySelectorAll('input,textarea')].map((e) => { const b = e.getBoundingClientRect();
        return { tag: e.tagName, v: e.value, ph: e.placeholder, aria: e.getAttribute('aria-label'),
          focused: document.activeElement === e, rect: [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)] }; })
        .filter((e) => e.rect[2] > 40 && e.rect[3] > 8);
      return { inputs, bodyText: (document.body.innerText || '').replace(/\s+/g, ' ').slice(0, 200) };
    });
    await shot(page, 'M-38-重命名-点完之后.png');
    // 若是输入框：清空 → 打字 → Enter
    let after = (await nodeList()).map((n) => n.title);
    if (editing.inputs.length) {
      const inp = editing.inputs[editing.inputs.length - 1];
      await page.mouse.click(inp.rect[0] + inp.rect[2] / 2, inp.rect[1] + inp.rect[3] / 2);
      await page.keyboard.press('Meta+a');
      await page.keyboard.type('取证重命名', { delay: 40 });
      await page.waitForTimeout(700);
      await shot(page, 'M-38-重命名-输入中.png');
      await page.keyboard.press('Enter');
      await page.waitForTimeout(2200);
      after = (await nodeList()).map((n) => n.title);
    }
    await shot(page, 'M-39-重命名-完成.png');
    const drawerText = await page.evaluate(() => {
      const d = document.querySelector('div.group\\/node');
      return d ? (d.innerText || '').trim() : null; });
    await logStep(B, { id: 'Y1-rename', title: '资产管理「更多操作 → 重命名」：节点名真的会改吗',
      target: `点菜单里的「重命名」(${item.cx},${item.cy})`,
      evidence: { before, editingInputs: editing.inputs, after, drawerRowText: drawerText, toast: await toasts() },
      visible_text: `重命名前节点名 ${JSON.stringify(before)}；点「重命名」后页面出现的输入框 ${JSON.stringify(editing.inputs)}；` +
        `输入「取证重命名」并回车后节点名 ${JSON.stringify(after)}；` +
        `抽屉那一行的文案 ${JSON.stringify(drawerText)} → **${after.join() !== before.join() ? '改名生效' : '没变'}**；提示 ${JSON.stringify(await toasts())}`,
      shot: 'M-39-重命名-完成.png' });
  } catch (e) { await logStep(B, { id: 'Y1-rename', title: '「重命名」', failed: true, visible_text: String(e).slice(0, 300) }); }

  // ── Y2 复制
  try {
    await page.mouse.click(1250, 780); await page.waitForTimeout(1000);
    if (!(await openDrawer())) throw new Error('抽屉打不开');
    const m0 = await openRowMenu(0);
    await page.mouse.click(m0.cx, m0.cy); await page.waitForTimeout(2000);
    const menu = await readMenu();
    const item = menu?.items.find((i) => i.t === '复制');
    if (!item) throw new Error('菜单里没有「复制」');
    const before = await N();
    await page.mouse.click(item.cx, item.cy);
    await page.waitForTimeout(2600);
    const after = await N();
    const list = await nodeList();
    await shot(page, 'M-40-复制之后.png');
    await logStep(B, { id: 'Y2-duplicate', title: '资产管理「更多操作 → 复制」：节点数会 +1 吗',
      target: `点菜单里的「复制」(${item.cx},${item.cy})`,
      evidence: { before, after, nodes: list, toast: await toasts() },
      visible_text: `点「复制」前节点数 ${before} → 点后 ${after}（${after > before ? '**+1 复制成功**' : '**没变**'}）；` +
        `节点列表 ${JSON.stringify(list.map((n) => n.title))}；提示 ${JSON.stringify(await toasts())}`,
      shot: 'M-40-复制之后.png' });
  } catch (e) { await logStep(B, { id: 'Y2-duplicate', title: '「复制」', failed: true, visible_text: String(e).slice(0, 300) }); }

  // ── Y3 添加到Agent：只点开看它变成什么
  try {
    await page.mouse.click(1250, 780); await page.waitForTimeout(1000);
    if (!(await openDrawer())) throw new Error('抽屉打不开');
    const m0 = await openRowMenu(0);
    await page.mouse.click(m0.cx, m0.cy); await page.waitForTimeout(2000);
    const menu = await readMenu();
    const item = menu?.items.find((i) => i.t === '添加到Agent');
    if (!item) throw new Error('菜单里没有「添加到Agent」');
    const before = await fingerprint(page);
    const beforeN = await N();
    await page.mouse.click(item.cx, item.cy);
    await page.waitForTimeout(2600);
    const after = await fingerprint(page);
    const fresh = diffPanels(before, after).map((f) => ({ sig: f.sig, all: f.all.slice(0, 300) }));
    const pop = await page.evaluate(() => {
      const els = [...document.querySelectorAll('[role="dialog"],[class*="Modal"],[class*="Popover"],[class*="Drawer"],[class*="Dropdown"]')]
        .filter((d) => { const r = d.getBoundingClientRect(); return r.width > 60 && r.height > 30; });
      return els.length ? els.map((e) => ({ cls: (e.className || '').toString().slice(0, 34), text: (e.innerText || '').replace(/\s+/g, ' ').slice(0, 300) })) : null;
    });
    const danger = (pop || []).some((p) => /发送|提交|派发|运行|开始生成|消耗/.test(p.text));
    await shot(page, 'M-41-添加到Agent-点开之后.png');
    await logStep(B, { id: 'Y3-add-to-agent', title: '资产管理「更多操作 → 添加到Agent」点开是什么',
      target: `点菜单里的「添加到Agent」(${item.cx},${item.cy})`,
      evidence: { nodeCountBefore: beforeN, nodeCountAfter: await N(), fresh, popups: pop, toast: await toasts() },
      visible_text: `点前节点数 ${beforeN} → 点后 ${await N()}；新出现面板 ${JSON.stringify(fresh.map((f) => f.all).filter(Boolean).slice(0, 6))}；` +
        `弹层 ${JSON.stringify(pop)}；提示 ${JSON.stringify(await toasts())}；` +
        `**是否出现「发送/提交/派发」类危险字样：${danger ? '有，已停手未继续' : '无'}**`,
      shot: 'M-41-添加到Agent-点开之后.png' });
    if (danger) console.log('⚠️ 出现危险字样，就此停手：', JSON.stringify(pop));
  } catch (e) { await logStep(B, { id: 'Y3-add-to-agent', title: '「添加到Agent」', failed: true, visible_text: String(e).slice(0, 300) }); }

  // ── Y4 删除（测试画布，删光正好收尾）
  try {
    await page.mouse.click(1250, 780); await page.waitForTimeout(1000);
    if (!(await openDrawer())) throw new Error('抽屉打不开');
    const before = await N();
    // 反复删到空
    const steps = [];
    for (let k = 0; k < 8; k += 1) {
      if (!(await openDrawer())) break;
      const rowCount = await page.evaluate(() => document.querySelectorAll('div.group\\/node').length);
      if (!rowCount) break;
      const m0 = await openRowMenu(0);
      if (m0.err) { steps.push({ k, err: m0.err }); break; }
      await page.mouse.click(m0.cx, m0.cy); await page.waitForTimeout(1700);
      const menu = await readMenu();
      const item = menu?.items.find((i) => i.t === '删除');
      if (!item) { steps.push({ k, err: '菜单里没有「删除」', items: menu?.items.map((i) => i.t) }); break; }
      const n0 = await N();
      await page.mouse.click(item.cx, item.cy);
      await page.waitForTimeout(2400);
      const n1 = await N();
      steps.push({ k, rowText: m0.rowText, before: n0, after: n1 });
      if (n1 >= n0) { steps.push({ k, stuck: true }); break; }
    }
    await shot(page, 'M-42-删除之后.png');
    await logStep(B, { id: 'Y4-delete', title: '资产管理「更多操作 → 删除」：逐个删到空',
      target: '对每一行点「⋯ → 删除」，直到画布空',
      evidence: { nodesBefore: before, nodesAfter: await N(), steps },
      visible_text: `删之前节点数 ${before}；逐次删除 ${JSON.stringify(steps)}；最终节点数 ${await N()}`,
      shot: 'M-42-删除之后.png' });
  } catch (e) { await logStep(B, { id: 'Y4-delete', title: '「删除」', failed: true, visible_text: String(e).slice(0, 300) }); }

  console.log('最终节点:', await N());
} finally {
  await browser.close();
}
