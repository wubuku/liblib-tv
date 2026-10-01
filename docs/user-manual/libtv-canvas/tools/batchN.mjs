// Batch N —— 组操作条最后两块拼图：排列菜单真按 + 工具箱创建真验。
//
// batchM 拿到但还没验的两件事：
//   1. 布局菜单有 3 项：**宫格排列 / 水平排列 / 垂直排列**。
//      之前几轮一直读不到，是因为 scenario.mjs 的 fingerprint() 有 `width>120 && height>60`
//      的尺寸门槛，而这个竖排菜单整体比 120px 窄，被门槛整块挡掉了 ——
//      **「测不到」有时候只是探针太挑，不是产品没有**。这轮用全量差集读。
//   2. M3d 点「创建」后弹窗关了、页面也没有该名称，看起来像没生效。
//      但那一轮 nameInput.fill() 是 `.catch(() => {})` 吞着跑的，
//      站点又是 React 只设 property 的输入框，**填没填进去根本没验证**。
//      这轮：先读 input.value 确认写进去了再点创建，
//      然后走「更新工具箱」标签页回查 —— 那里会列出已建工具箱，是唯一可靠的验收口。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { nodeCount, fitView } from './canvas-ops.mjs';
import { openDropdown } from './canvas-dropdown.mjs';

const SPACE = '10354929';
const B = 'batchN';
const { browser, page } = await launch();

const N = () => nodeCount(page);
const nodesOf = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => {
  const r = n.getBoundingClientRect();
  return { title: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 12),
    isGroup: /group/i.test(n.className || '') || /group/i.test(n.getAttribute('data-id') || ''),
    x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) };
}));
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
const toolbarLeaves = () => page.evaluate(() => {
  const g = [...document.querySelectorAll('.react-flow__node')].find((n) => /group/i.test(n.className || '') || /group/i.test(n.getAttribute('data-id') || ''));
  if (!g) return { present: false };
  const r = g.getBoundingClientRect();
  const leaves = [...g.querySelectorAll('div,span')].filter((e) => {
    const b = e.getBoundingClientRect();
    return b.width > 0 && b.height > 0 && b.y < r.y + 60 && b.y > r.y - 80 && b.width < 200 && !e.querySelector('div,span');
  }).map((e) => { const b = e.getBoundingClientRect();
    return { t: (e.getAttribute('aria-label') || e.title || e.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 14),
      x: Math.round(b.x + b.width / 2), y: Math.round(b.y + b.height / 2),
      w: Math.round(b.width), h: Math.round(b.height), op: +getComputedStyle(e).opacity,
      cls: (e.className || '').toString().slice(0, 46), icon: e.querySelector('svg') ? 'svg' : null }; })
    .sort((a, b) => a.x - b.x);
  return { present: true, groupSelected: g.classList.contains('selected'),
    groupRect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], leaves };
});
const toasts = () => page.evaluate(() => [...document.querySelectorAll('[role="alert"],[class*="toast"],[class*="Toast"],[class*="toaster"]')]
  .filter((t) => t.getBoundingClientRect().width > 0).map((t) => (t.innerText || '').replace(/\s+/g, ' ').slice(0, 140)));
const modalText = () => page.evaluate(() => {
  const o = [...document.querySelectorAll('div')].find((d) => /fixed inset-0/.test(d.className || '')
    && +getComputedStyle(d).zIndex > 100 && (d.innerText || '').trim().length > 0);
  if (!o) return null;
  return { text: (o.innerText || '').replace(/\s+/g, ' ').slice(0, 320),
    clickable: [...o.querySelectorAll('div,span,button')].filter((e) => { const b = e.getBoundingClientRect(); return b.width > 16 && b.height > 8 && b.height < 60; })
      .map((e) => { const b = e.getBoundingClientRect();
        return { t: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 12), x: Math.round(b.x + b.width / 2), y: Math.round(b.y + b.height / 2) }; })
      .filter((e) => e.t).slice(0, 20) };
});
const modalInputs = () => page.evaluate(() => [...document.querySelectorAll('input,textarea')].map((i) => {
  const b = i.getBoundingClientRect();
  return { tag: i.tagName, ph: i.placeholder, aria: i.getAttribute('aria-label'), value: i.value,
    rect: [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)],
    inModal: b.width > 100 && b.height > 10 }; }).filter((i) => i.inModal));
async function ensureToolbar() {
  const b = await toolbarLeaves();
  if (b.leaves.length > 3) return b;
  const g = await page.evaluate(() => {
    const n = [...document.querySelectorAll('.react-flow__node')].find((x) => /group/i.test(x.className || ''));
    if (!n) return null; const r = n.getBoundingClientRect();
    return { x: Math.round(r.x + 30), y: Math.round(r.y - 16) };
  });
  if (g) { await page.mouse.click(g.x, g.y); await page.waitForTimeout(1500); }
  return toolbarLeaves();
}
/** 打开排列菜单，列出 3 个菜单项。 */
async function openArrangeMenu() {
  const b = await ensureToolbar();
  const btn = b.leaves.find((l) => l.t === '' && l.w >= 40 && l.w <= 60 && l.h >= 30 && l.icon);
  if (!btn) throw new Error('没找到排列按钮');
  await page.mouse.click(btn.x, btn.y); await page.waitForTimeout(2200);
  const items = await page.evaluate(() => {
    const pop = [...document.querySelectorAll('div.nodrag.nopan.nowheel')].filter((d) => d.getBoundingClientRect().width > 40);
    if (!pop.length) return null;
    const rows = [...pop[pop.length - 1].querySelectorAll('div')].filter((e) => {
      const b = e.getBoundingClientRect(); const s = getComputedStyle(e);
      return b.width > 30 && b.height > 12 && b.height < 46 && (e.innerText || '').trim();
    }).map((e) => { const b = e.getBoundingClientRect();
      return { t: (e.innerText || '').replace(/\s+/g, ' ').trim(), x: Math.round(b.x + b.width / 2), y: Math.round(b.y + b.height / 2) }; })
      .filter((e, i, a) => a.findIndex((o) => o.t === e.t && Math.abs(o.y - e.y) < 4) === i);
    return rows;
  });
  return { btn, items };
}

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4000 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '真按三种排列验证节点重排；工具箱创建先验 value 再点创建，再回「更新工具箱」页验收' });

  await openDropdown(page, 1000);
  await page.getByRole('button', { name: '新建画布', exact: true }).first().click();
  await page.waitForTimeout(4500);
  await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(1500);
  await addNodeAt(findEmptySpot([]).x, findEmptySpot([]).y, '文本');
  await addNodeAt(findEmptySpot(await nodesOf()).x, findEmptySpot(await nodesOf()).y, '音频');
  await addNodeAt(findEmptySpot(await nodesOf()).x, findEmptySpot(await nodesOf()).y, '图片');
  await fitView(page, 1); await page.keyboard.press('Meta+-'); await page.waitForTimeout(1400);

  const plain = (await nodesOf()).filter((n) => !n.isGroup);
  const x0 = Math.min(...plain.map((n) => n.x)) - 14, y0 = Math.min(...plain.map((n) => n.y)) - 14;
  const x1 = Math.max(...plain.map((n) => n.x + n.w)) + 14, y1 = Math.max(...plain.map((n) => n.y + n.h)) + 14;
  await page.keyboard.down('Shift');
  await page.mouse.move(40, 200); await page.mouse.down(); await page.waitForTimeout(150);
  await page.mouse.move(x0, y0, { steps: 10 }); await page.mouse.move(x1, y1, { steps: 12 });
  await page.mouse.up(); await page.keyboard.up('Shift'); await page.waitForTimeout(1500);
  await page.keyboard.press('Meta+g'); await page.waitForTimeout(2600);
  await page.keyboard.down('Space');
  await page.mouse.move(1360, 400); await page.mouse.down(); await page.waitForTimeout(200);
  for (let i = 1; i <= 8; i += 1) { await page.mouse.move(1360, 400 + i * 22, { steps: 2 }); await page.waitForTimeout(40); }
  await page.mouse.up(); await page.keyboard.up('Space'); await page.waitForTimeout(1400);
  const bar = await toolbarLeaves();
  console.log('组矩形:', JSON.stringify(bar.groupRect), '节点:', await N());

  // ── N1 排列菜单：列出 + 逐个真按，比对成员坐标
  let menu = null;
  try {
    menu = await openArrangeMenu();
    console.log('排列菜单:', JSON.stringify(menu.items));
    await shot(page, 'M-14-组操作条-排列菜单.png');
    await logStep(B, { id: 'N1a-menu-items', title: '组操作条排列菜单的 3 个动作',
      target: `点 (${menu.btn.x},${menu.btn.y}) 的 52×36 排列按钮`,
      evidence: { clicked: menu.btn, items: menu.items },
      visible_text: `排列菜单共 ${menu.items?.length} 项：${JSON.stringify(menu.items?.map((i) => i.t))}`,
      shot: 'M-14-组操作条-排列菜单.png' });
  } catch (e) { await logStep(B, { id: 'N1a-menu-items', title: '组操作条排列菜单', failed: true, visible_text: String(e).slice(0, 300) }); }

  for (const want of ['垂直排列', '水平排列', '宫格排列']) {
    try {
      if (!menu?.items) throw new Error('菜单没开成功');
      // 菜单可能被上一步关掉了，每次重开
      let items = menu.items;
      const probe = await page.evaluate(() => !!document.querySelector('div.nodrag.nopan.nowheel'));
      if (!probe) { const m2 = await openArrangeMenu(); items = m2.items; menu = m2; }
      const it = items.find((i) => i.t === want);
      if (!it) throw new Error(`菜单里没有「${want}」；现有 ${JSON.stringify(items.map((i) => i.t))}`);
      const before = (await nodesOf()).filter((n) => !n.isGroup);
      await page.mouse.click(it.x, it.y);
      await page.waitForTimeout(3000);
      const after = (await nodesOf()).filter((n) => !n.isGroup);
      const delta = before.map((b, i) => { const a = after[i]; return a ? { title: b.title, dx: a.x - b.x, dy: a.y - b.y } : null; }).filter(Boolean);
      await shot(page, `M-17-排列-${want}.png`);
      await logStep(B, { id: `N1-arrange-${want}`, title: `排列：${want}`,
        target: `点菜单里的「${want}」(${it.x},${it.y})`,
        evidence: { item: it, before, after, delta, toast: await toasts(), groupStillSelected: (await toolbarLeaves()).groupSelected },
        visible_text: `点「${want}」前成员坐标 ${JSON.stringify(before.map((b) => [b.title, b.x, b.y]))}；` +
          `之后 ${JSON.stringify(after.map((a) => [a.title, a.x, a.y]))}；位移 ${JSON.stringify(delta)}；提示 ${JSON.stringify(await toasts())}`,
        shot: `M-17-排列-${want}.png` });
    } catch (e) { await logStep(B, { id: `N1-arrange-${want}`, title: `排列：${want}`, failed: true, visible_text: String(e).slice(0, 300) }); }
  }

  // ── N2 工具箱创建：先验 value，再点创建，再回「更新工具箱」页验收
  try {
    const b = await ensureToolbar();
    const btn = b.leaves.find((l) => l.t === '添加到工具箱');
    if (!btn) throw new Error('没找到「添加到工具箱」');
    await page.mouse.click(btn.x, btn.y); await page.waitForTimeout(2800);
    const inputs0 = await modalInputs();
    console.log('创建页输入框:', JSON.stringify(inputs0));
    // 用 placeholder 精确定位（本轮记下：它没有 aria-label，只有 placeholder「输入工具箱名称」）
    const nameBox = page.locator('input[placeholder="输入工具箱名称"]');
    if (await nameBox.count()) {
      await nameBox.first().click(); await page.keyboard.press('Meta+a');
      await page.keyboard.type('手册取证测试箱', { delay: 40 });
    } else {
      await page.locator('input[type="text"]').last().fill('手册取证测试箱').catch(() => {});
    }
    await page.waitForTimeout(1000);
    const inputs1 = await modalInputs();
    const filled = inputs1.find((i) => i.ph === '输入工具箱名称')?.value;
    console.log('填完后的 name value =', JSON.stringify(filled));
    await shot(page, 'M-12-工具箱弹窗-填写名称.png');

    const m = await modalText();
    const cb = m?.clickable.find((c) => c.t === '创建');
    let afterCreate = null, updPage = null;
    if (cb) {
      await page.mouse.click(cb.x, cb.y); await page.waitForTimeout(4000);
      afterCreate = { modal: await modalText(), toast: await toasts() };
      // 验收：再开一次弹窗 → 切「更新工具箱」页，看建出来没有
      const b2 = await ensureToolbar();
      const btn2 = b2.leaves.find((l) => l.t === '添加到工具箱');
      if (btn2) {
        await page.mouse.click(btn2.x, btn2.y); await page.waitForTimeout(2800);
        const m2 = await modalText();
        const upd = m2?.clickable.find((c) => c.t === '更新工具箱');
        if (upd) {
          await page.mouse.click(upd.x, upd.y); await page.waitForTimeout(2600);
          updPage = await modalText();
          await shot(page, 'M-11-工具箱弹窗-更新工具箱页.png');
        }
      }
    }
    await logStep(B, { id: 'N2-create-toolbox', title: '「添加到工具箱」真的建出工具箱了吗',
      target: `点「添加到工具箱」→ 名称填「手册取证测试箱」→ 点「创建」→ 重开弹窗切「更新工具箱」页回查`,
      evidence: { inputsBefore: inputs0, nameValueAfterTyping: filled,
        afterCreate, updateTabPage: updPage, toast: await toasts() },
      visible_text: `创建页输入框 ${JSON.stringify(inputs0)}；打字后「输入工具箱名称」的值 = ${JSON.stringify(filled)}；` +
        `点创建后弹窗 ${afterCreate?.modal ? '仍开着' : '已关闭'}、提示 ${JSON.stringify(afterCreate?.toast)}；` +
        `「更新工具箱」页此时内容 = ${JSON.stringify(updPage?.text)}`,
      shot: 'M-11-工具箱弹窗-更新工具箱页.png' });
  } catch (e) { await logStep(B, { id: 'N2-create-toolbox', title: '「添加到工具箱」创建验证', failed: true, visible_text: String(e).slice(0, 300) }); }

  console.log('节点:', await N());
} finally {
  await browser.close();
}
