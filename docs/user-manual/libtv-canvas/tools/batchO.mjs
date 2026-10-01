// Batch O —— 排列菜单干净重测 + 工具箱创建验收。
//
// batchN 两个读数不可信，这轮修掉：
//
//  1. 排列菜单的陈旧坐标。batchN 用
//     `!!document.querySelector('div.nodrag.nopan.nowheel')` 判断「菜单还开着」，
//     但菜单收起后那个容器**还留在 DOM 里**，于是 probe 恒为 true，
//     后两次（水平/宫格）点的是上一轮的旧坐标 —— 宫格那一项的 x 从 527 变成了 210 就是证据。
//     结果「水平排列 (0,0) 没动」是**我点歪了**，不是产品没反应。
//     这轮每次都重新点开菜单、**重新读实时坐标**，并用「菜单里有没有三个已知文案」来确认开对了。
//
//  2. 工具箱创建没验成。batchN 名字确实填进去了（value = 手册取证测试箱），
//     点「创建」后弹窗关闭、无提示，但重开弹窗那步没读回内容。
//     这轮验收口径不变但读法更硬：**切到「更新工具箱」页，读它的完整正文**。
//     创建前 batchM 读到的是「暂无工具箱」，创建后如果这里出现工具箱名，就是成功。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { nodeCount, fitView } from './canvas-ops.mjs';
import { openDropdown } from './canvas-dropdown.mjs';

const SPACE = '10354929';
const B = 'batchO';
const { browser, page } = await launch();

const N = () => nodeCount(page);
const members = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')]
  .filter((n) => !/group/i.test(n.className || '') && !/group/i.test(n.getAttribute('data-id') || ''))
  .map((n) => { const r = n.getBoundingClientRect();
    return { title: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 8), x: Math.round(r.x), y: Math.round(r.y) }; })
  .sort((a, b) => a.x - b.x || a.y - b.y));
const groupRect = () => page.evaluate(() => {
  const g = [...document.querySelectorAll('.react-flow__node')].find((n) => /group/i.test(n.className || ''));
  if (!g) return null; const r = g.getBoundingClientRect();
  return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], selected: g.classList.contains('selected') };
});

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
  if (!g) return { present: false, leaves: [] };
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
  return { text: (o.innerText || '').replace(/\s+/g, ' ').slice(0, 400),
    clickable: [...o.querySelectorAll('div,span,button')].filter((e) => { const b = e.getBoundingClientRect(); return b.width > 16 && b.height > 8 && b.height < 60; })
      .map((e) => { const b = e.getBoundingClientRect();
        return { t: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 12), x: Math.round(b.x + b.width / 2), y: Math.round(b.y + b.height / 2) }; })
      .filter((e) => e.t).slice(0, 20) };
});
async function ensureToolbar() {
  const b = await toolbarLeaves();
  if (b.leaves.length > 3) return b;
  const g = await groupRect();
  if (g) { await page.mouse.click(Math.round(g.rect[0] + 30), Math.round(g.rect[1] - 16)); await page.waitForTimeout(1500); }
  return toolbarLeaves();
}
/** 点开排列菜单，**每次都重新读实时坐标**；用三个已知文案确认菜单真的开着。 */
async function openArrangeMenuFresh() {
  const b = await ensureToolbar();
  const btn = b.leaves.find((l) => l.t === '' && l.w >= 40 && l.w <= 60 && l.h >= 30 && l.icon);
  if (!btn) throw new Error('没找到排列按钮；操作条读到 ' + JSON.stringify(b.leaves.map((l) => [l.t, l.w, l.h])));
  await page.mouse.click(btn.x, btn.y);
  await page.waitForTimeout(2200);
  const items = await page.evaluate(() => {
    const pops = [...document.querySelectorAll('div.nodrag.nopan.nowheel')].filter((d) => d.getBoundingClientRect().width > 40);
    if (!pops.length) return [];
    const out = [];
    for (const pop of pops) for (const e of pop.querySelectorAll('div')) {
      const b = e.getBoundingClientRect(); const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
      if (t && b.width > 30 && b.height > 12 && b.height < 46 && !out.some((o) => o.t === t && Math.abs(o.y - Math.round(b.y + b.height / 2)) < 4)) {
        out.push({ t, x: Math.round(b.x + b.width / 2), y: Math.round(b.y + b.height / 2) });
      }
    }
    return out;
  });
  const known = ['宫格排列', '水平排列', '垂直排列'];
  if (!known.every((k) => items.some((i) => i.t === k))) throw new Error('菜单没开对，读到 ' + JSON.stringify(items));
  return { btn, items };
}

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4000 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '每次重开菜单重读坐标；工具箱创建后回「更新工具箱」页读完整正文验收' });

  await openDropdown(page, 1000);
  await page.getByRole('button', { name: '新建画布', exact: true }).first().click();
  await page.waitForTimeout(4500);
  await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(1500);
  await addNodeAt(findEmptySpot([]).x, findEmptySpot([]).y, '文本');
  await addNodeAt(findEmptySpot(await nodesOfSafe()).x, findEmptySpot(await nodesOfSafe()).y, '音频');
  await addNodeAt(findEmptySpot(await nodesOfSafe()).x, findEmptySpot(await nodesOfSafe()).y, '图片');
  await fitView(page, 1); await page.keyboard.press('Meta+-'); await page.waitForTimeout(1400);

  const plain = await nodesOfSafe();
  const x0 = Math.min(...plain.map((n) => n.x)) - 14, y0 = Math.min(...plain.map((n) => n.y)) - 14;
  const x1 = Math.max(...plain.map((n) => n.x + n.w)) + 14, y1 = Math.max(...plain.map((n) => n.y + n.h)) + 14;
  await page.keyboard.down('Shift');
  await page.mouse.move(40, 200); await page.mouse.down(); await page.waitForTimeout(150);
  await page.mouse.move(x0, y0, { steps: 10 }); await page.mouse.move(x1, y1, { steps: 12 });
  await page.mouse.up(); await page.keyboard.up('Shift'); await page.waitForTimeout(1500);
  await page.keyboard.press('Meta+g'); await page.waitForTimeout(2600);
  // 三个节点会被排到很高，组框顶边要留在视口内，菜单和色板才展得开
  const g0 = await groupRect();
  if (g0 && g0.rect[1] < 180) {
    const need = Math.min(180 - g0.rect[1], 150);
    await page.keyboard.down('Space');
    await page.mouse.move(1360, 400); await page.mouse.down(); await page.waitForTimeout(200);
    for (let i = 1; i <= 8; i += 1) { await page.mouse.move(1360, 400 + i * (need / 8), { steps: 2 }); await page.waitForTimeout(40); }
    await page.mouse.up(); await page.keyboard.up('Space'); await page.waitForTimeout(1400);
  }
  console.log('组矩形:', JSON.stringify(await groupRect()), '成员:', JSON.stringify(await members()));

  // ── O1 三种排列：每轮都重开菜单、重读坐标
  for (const want of ['水平排列', '垂直排列', '宫格排列']) {
    try {
      const m = await openArrangeMenuFresh();
      const it = m.items.find((i) => i.t === want);
      const before = await members();
      await page.mouse.click(it.x, it.y);
      await page.waitForTimeout(3200);
      const after = await members();
      const g = await groupRect();
      const delta = before.map((b) => { const a = after.find((x) => x.title === b.title);
        return a ? { title: b.title, dx: a.x - b.x, dy: a.y - b.y } : null; }).filter(Boolean);
      await shot(page, `M-17-排列-${want}.png`);
      await logStep(B, { id: `O1-arrange-${want}`, title: `排列：${want}`,
        target: `点开排列菜单后读到的实时坐标 (${it.x},${it.y})`,
        evidence: { menuItems: m.items, item: it, before, after, delta,
          groupRectAfter: g, toast: await toasts() },
        visible_text: `点「${want}」前成员 ${JSON.stringify(before)}；之后 ${JSON.stringify(after)}；` +
          `位移 ${JSON.stringify(delta)}；组框 ${JSON.stringify(g?.rect)}；提示 ${JSON.stringify(await toasts())}`,
        shot: `M-17-排列-${want}.png` });
      console.log(`  ${want}: ${JSON.stringify(before)} → ${JSON.stringify(after)}`);
    } catch (e) { await logStep(B, { id: `O1-arrange-${want}`, title: `排列：${want}`, failed: true, visible_text: String(e).slice(0, 300) }); }
  }

  // ── O2 工具箱创建验收
  try {
    const b = await ensureToolbar();
    const btn = b.leaves.find((l) => l.t === '添加到工具箱');
    if (!btn) throw new Error('没找到「添加到工具箱」；读到 ' + JSON.stringify(b.leaves.map((l) => l.t)));
    await page.mouse.click(btn.x, btn.y); await page.waitForTimeout(3000);
    const m = await modalText();
    // 先看看「更新工具箱」页现在长什么样（创建前的基线）
    const upd = m?.clickable.find((c) => c.t === '更新工具箱');
    let baseline = null;
    if (upd) {
      await page.mouse.click(upd.x, upd.y); await page.waitForTimeout(2600);
      baseline = await modalText();
      await shot(page, 'M-11-工具箱弹窗-更新工具箱页-创建前.png');
      const back = (await modalText())?.clickable.find((c) => c.t === '创建新工具箱');
      if (back) { await page.mouse.click(back.x, back.y); await page.waitForTimeout(2200); }
    }
    const nameBox = page.locator('input[placeholder="输入工具箱名称"]');
    await nameBox.first().click(); await page.keyboard.press('Meta+a');
    await page.keyboard.type('手册取证测试箱', { delay: 40 }); await page.waitForTimeout(1000);
    const typed = await page.evaluate(() => (document.querySelector('input[placeholder="输入工具箱名称"]') || {}).value);
    await shot(page, 'M-12-工具箱弹窗-填写名称.png');
    const now = await modalText();
    const cb = now?.clickable.find((c) => c.t === '创建');
    if (!cb) throw new Error('没找到「创建」按钮');
    await page.mouse.click(cb.x, cb.y); await page.waitForTimeout(4200);
    const afterCreate = { modal: await modalText(), toast: await toasts() };
    await shot(page, 'M-13-工具箱弹窗-点创建之后.png');
    // 验收：重开 → 切「更新工具箱」页
    const b2 = await ensureToolbar();
    const btn2 = b2.leaves.find((l) => l.t === '添加到工具箱');
    let updAfter = null;
    if (btn2) {
      await page.mouse.click(btn2.x, btn2.y); await page.waitForTimeout(3000);
      const m2 = await modalText();
      console.log('重开弹窗:', JSON.stringify(m2?.text));
      const u2 = m2?.clickable.find((c) => c.t === '更新工具箱');
      if (u2) { await page.mouse.click(u2.x, u2.y); await page.waitForTimeout(2800); updAfter = await modalText(); }
    }
    await shot(page, 'M-18-工具箱弹窗-创建后回查.png');
    await logStep(B, { id: 'O2-create-toolbox', title: '「添加到工具箱」创建前后对照',
      target: '点「添加到工具箱」→ 先读「更新工具箱」页基线 → 填名称「手册取证测试箱」→ 点「创建」→ 重开切回「更新工具箱」页',
      evidence: { updatePageBefore: baseline?.text, nameValueAfterTyping: typed,
        afterCreate, updatePageAfter: updAfter?.text, toast: await toasts() },
      visible_text: `创建前「更新工具箱」页 = ${JSON.stringify(baseline?.text)}；` +
        `打字后名称 = ${JSON.stringify(typed)}；点创建后弹窗 ${afterCreate.modal ? '仍开着' : '已关闭'}、提示 ${JSON.stringify(afterCreate.toast)}；` +
        `创建后「更新工具箱」页 = ${JSON.stringify(updAfter?.text)}`,
      shot: 'M-18-工具箱弹窗-创建后回查.png' });
  } catch (e) { await logStep(B, { id: 'O2-create-toolbox', title: '「添加到工具箱」创建验收', failed: true, visible_text: String(e).slice(0, 300) }); }

  console.log('节点:', await N());
} finally {
  await browser.close();
}

// 建点阶段也要用到的全量节点读数（含尺寸，用于算框选矩形）
async function nodesOfSafe() {
  return page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => {
    const r = n.getBoundingClientRect();
    return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) };
  }));
}
