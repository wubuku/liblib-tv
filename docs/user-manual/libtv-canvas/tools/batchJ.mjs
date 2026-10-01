// Batch J —— 组操作条剩余元素 + 「创建新工具箱」弹窗交互。
//
// batchI 坐实了两件事，顺带推翻了一个旧假设：
//   · 「添加到工具箱」= 打开「创建新工具箱 / 更新工具箱」双标签弹窗（封面/名称/标签 0/5/备注/创建）
//   · 我一直叫它「⊞ 布局下拉」的那枚 20×20 元素，class 是 `size-5 rounded-full border-[…]`
//     —— **它是颜色圆点，不是布局下拉**。点开是 `grid grid-cols-5 gap-3` 的色板，
//     色块全是纯色 div 没有文字，所以 innerText 空，之前一直读不到内容。
//
// batchI 的 I2 之所以啥也没读到：I1 弹出的模态框带 `fixed inset-0` 遮罩，
// 那次点击全被遮罩吃掉了。**这轮先关弹窗再点圆点。**
//
// 这轮要拿到的：
//   J1 色板里到底几色、什么色（读 computed backgroundColor，色块无文字只能读样式）
//   J2 圆点与「整组执行」之间那两枚无文案按钮是什么（dump outerHTML 看图标）
//   J3 弹窗交互：更换封面 / 添加标签 / 创建 / 更新工具箱 标签页
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep, fingerprint, diffPanels } from './scenario.mjs';
import { nodeCount, fitView } from './canvas-ops.mjs';
import { openDropdown } from './canvas-dropdown.mjs';

const SPACE = '10354929';
const B = 'batchJ';
const { browser, page } = await launch();

const N = () => nodeCount(page);
const nodesOf = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => {
  const r = n.getBoundingClientRect();
  return { title: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 14),
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

/** 组操作条上的每一枚动作（叶子 div/span），按 x 排。顺带 dump outerHTML 认图标。 */
const toolbarLeaves = (withHtml = false) => page.evaluate((html) => {
  const g = [...document.querySelectorAll('.react-flow__node')].find((n) => /group/i.test(n.className || '') || /group/i.test(n.getAttribute('data-id') || ''));
  if (!g) return { present: false, why: '没有组节点' };
  const r = g.getBoundingClientRect();
  const leaves = [...g.querySelectorAll('div,span')].filter((e) => {
    const b = e.getBoundingClientRect();
    return b.width > 0 && b.height > 0 && b.y < r.y + 60 && b.y > r.y - 80 && b.width < 200 && !e.querySelector('div,span');
  }).map((e) => { const b = e.getBoundingClientRect();
    const svg = e.querySelector('svg');
    return { t: (e.getAttribute('aria-label') || e.title || e.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 14),
      x: Math.round(b.x + b.width / 2), y: Math.round(b.y + b.height / 2),
      w: Math.round(b.width), h: Math.round(b.height), op: +getComputedStyle(e).opacity,
      cls: (e.className || '').toString().slice(0, 46),
      icon: svg ? (svg.getAttribute('class') || '') + ' | ' + (svg.innerHTML || '').slice(0, 90) : null,
      html: html ? (e.outerHTML || '').slice(0, 260) : undefined }; })
    .sort((a, b) => a.x - b.x);
  return { present: true, groupSelected: g.classList.contains('selected'),
    groupRect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], leaves };
}, withHtml);

async function clickAndDiff(c) {
  const before = await fingerprint(page);
  await page.mouse.click(c.x, c.y);
  await page.waitForTimeout(2600);
  const fresh = diffPanels(before, await fingerprint(page));
  const pop = await page.evaluate(() => {
    const els = [...document.querySelectorAll('[role="menu"],[role="listbox"],[role="dialog"],[class*="Popover"],[class*="Dropdown"],[class*="Modal"],[class*="Drawer"]')]
      .filter((d) => { const r = d.getBoundingClientRect(); return r.width > 40 && r.height > 20; });
    return els.length ? els.map((e) => ({ cls: (e.className || '').toString().slice(0, 40), text: (e.innerText || '').replace(/\s+/g, ' ').slice(0, 200) })) : null;
  });
  return { fresh: fresh.map((f) => ({ sig: f.sig, all: f.all.slice(0, 200) })), pop };
}
const toasts = () => page.evaluate(() => [...document.querySelectorAll('[role="alert"],[class*="toast"],[class*="Toast"],[class*="toaster"]')]
  .filter((t) => t.getBoundingClientRect().width > 0).map((t) => (t.innerText || '').replace(/\s+/g, ' ').slice(0, 140)));
/** 当前有没有全屏模态遮罩挡路。 */
const overlayUp = () => page.evaluate(() => {
  const o = [...document.querySelectorAll('div')].find((d) => /fixed inset-0/.test(d.className || '') && +getComputedStyle(d).zIndex > 100);
  return o ? { z: getComputedStyle(o).zIndex, pe: getComputedStyle(o).pointerEvents } : null;
});
async function closeModal() {
  await page.keyboard.press('Escape').catch(() => {});
  await page.waitForTimeout(1200);
  if (await overlayUp()) {
    const x = await page.evaluate(() => {
      const b = [...document.querySelectorAll('div,button,svg')].filter((e) => {
        const r = e.getBoundingClientRect(); return r.width > 10 && r.width < 60 && r.height > 10 && r.height < 60;
      }).map((e) => ({ e, r: e.getBoundingClientRect() }))
        .filter((o) => o.r.x > 1100 && o.r.y < 200).pop();
      return b ? { x: Math.round(b.r.x + b.r.width / 2), y: Math.round(b.r.y + b.r.height / 2) } : null;
    });
    if (x) { await page.mouse.click(x.x, x.y); await page.waitForTimeout(1200); }
  }
}

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4000 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '先关弹窗再点颜色圆点；读色板样式 + 认图标 + 走一遍创建工具箱弹窗' });

  await openDropdown(page, 1000);
  await page.getByRole('button', { name: '新建画布', exact: true }).first().click();
  await page.waitForTimeout(4500);
  await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(1500);
  await addNodeAt(findEmptySpot([]).x, findEmptySpot([]).y, '文本');
  await addNodeAt(findEmptySpot(await nodesOf()).x, findEmptySpot(await nodesOf()).y, '音频');
  await fitView(page, 1); await page.keyboard.press('Meta+-'); await page.waitForTimeout(1400);

  // 框选 → ⌘G
  const plain = (await nodesOf()).filter((n) => !n.isGroup);
  const x0 = Math.min(...plain.map((n) => n.x)) - 14, y0 = Math.min(...plain.map((n) => n.y)) - 14;
  const x1 = Math.max(...plain.map((n) => n.x + n.w)) + 14, y1 = Math.max(...plain.map((n) => n.y + n.h)) + 14;
  await page.keyboard.down('Shift');
  await page.mouse.move(40, 200); await page.mouse.down(); await page.waitForTimeout(150);
  await page.mouse.move(x0, y0, { steps: 10 }); await page.mouse.move(x1, y1, { steps: 12 });
  await page.mouse.up(); await page.keyboard.up('Shift'); await page.waitForTimeout(1500);
  await page.keyboard.press('Meta+g'); await page.waitForTimeout(2600);

  const bar = await toolbarLeaves(true);
  console.log('组矩形:', JSON.stringify(bar.groupRect), 'selected:', bar.groupSelected);
  for (const l of bar.leaves) console.log(`  [${l.t || '·'}] x=${l.x} ${l.w}×${l.h} op=${l.op} cls=${l.cls} | ${(l.icon || '').slice(0, 70)}`);

  // ── J1 颜色圆点 → 色板
  try {
    const dot = bar.leaves.find((l) => /rounded-full/.test(l.cls));
    if (!dot) throw new Error('操作条里没有圆点元素');
    const r = await clickAndDiff(dot);
    const palette = await page.evaluate(() => {
      const root = [...document.querySelectorAll('div')].find((d) => /grid-cols-5/.test(d.className || ''));
      if (!root) return null;
      const rr = root.getBoundingClientRect();
      const sw = [...root.children].map((c) => { const b = c.getBoundingClientRect(); const s = getComputedStyle(c);
        return { bg: s.backgroundColor, w: Math.round(b.width), h: Math.round(b.height), cls: (c.className || '').toString().slice(0, 40),
          html: (c.outerHTML || '').slice(0, 120) }; });
      return { rect: [Math.round(rr.x), Math.round(rr.y), Math.round(rr.width), Math.round(rr.height)],
        inViewport: rr.y >= 0 && rr.bottom <= window.innerHeight, cols: 5, swatchCount: sw.length, swatches: sw };
    });
    await shot(page, 'M-09-组操作条-颜色色板.png');
    await logStep(B, { id: 'J1-color-dot', title: '组操作条颜色圆点 → 色板',
      target: `点 (${dot.x},${dot.y}) 的 20×20 圆点 (class ${dot.cls})`,
      evidence: { clicked: dot, newPanels: r.fresh, popups: r.pop, palette },
      visible_text: palette
        ? `色板容器 ${JSON.stringify(palette.rect)}，5 列 × ${palette.swatchCount} 个色块，是否在视口内 ${palette.inViewport}；色块 ${JSON.stringify(palette.swatches)}`
        : `点开没抓到 grid-cols-5；新面板 ${JSON.stringify(r.fresh)}；弹层 ${JSON.stringify(r.pop)}`,
      shot: 'M-09-组操作条-颜色色板.png' });
    await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(1000);
  } catch (e) { await logStep(B, { id: 'J1-color-dot', title: '组操作条颜色圆点 → 色板', failed: true, visible_text: String(e).slice(0, 300) }); }

  // ── J2 中间那两枚无文案按钮：逐个点开看是什么
  const runIdx = (await toolbarLeaves()).leaves.findIndex((l) => l.t === '整组执行');
  const mids = (await toolbarLeaves(true)).leaves.slice(0, runIdx).filter((l) => !l.t && l.y < 100 && l.w >= 14 && l.w <= 40);
  console.log('中间无文案按钮:', JSON.stringify(mids.map((m) => [m.x, m.w, m.cls, (m.icon || '').slice(0, 50)])));
  for (let i = 0; i < mids.length; i += 1) {
    try {
      const b = mids[i];
      const cur = (await toolbarLeaves()).leaves.find((l) => Math.abs(l.x - b.x) < 3);
      if (!cur) throw new Error(`x≈${b.x} 的按钮这一轮不见了`);
      const r = await clickAndDiff(cur);
      await shot(page, `M-10-组操作条-无名按钮${i + 1}.png`);
      await logStep(B, { id: `J2-unlabeled-btn-${i + 1}`, title: `组操作条第 ${i + 1} 枚无文案按钮 (x=${cur.x})`,
        target: `点 (${cur.x},${cur.y})，class ${cur.cls}，图标 ${(cur.icon || '无 svg').slice(0, 60)}`,
        evidence: { clicked: cur, newPanels: r.fresh, popups: r.pop, toast: await toasts() },
        visible_text: `弹出内容 ${JSON.stringify(r.pop)}；新面板 ${JSON.stringify(r.fresh.map((f) => f.all).filter(Boolean).slice(0, 6))}；提示 ${JSON.stringify(await toasts())}`,
        shot: `M-10-组操作条-无名按钮${i + 1}.png` });
      await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(1200);
    } catch (e) { await logStep(B, { id: `J2-unlabeled-btn-${i + 1}`, title: `组操作条第 ${i + 1} 枚无文案按钮 (x=${mids[i].x})`, failed: true, visible_text: String(e).slice(0, 250) }); }
  }

  // ── J3 「添加到工具箱」弹窗交互
  try {
    const bar3 = await toolbarLeaves();
    const btn = bar3.leaves.find((l) => l.t === '添加到工具箱');
    if (!btn) throw new Error('操作条里没有「添加到工具箱」');
    await page.mouse.click(btn.x, btn.y); await page.waitForTimeout(2600);
    const modalTitle = await page.evaluate(() => {
      const o = [...document.querySelectorAll('div')].find((d) => /fixed inset-0/.test(d.className || '') && +getComputedStyle(d).zIndex > 100);
      return o ? (o.innerText || '').replace(/\s+/g, ' ').slice(0, 300) : null;
    });
    // 标签页「更新工具箱」点一下看切过去是什么
    const tabs = await page.evaluate(() => {
      const o = [...document.querySelectorAll('div')].find((d) => /fixed inset-0/.test(d.className || '') && +getComputedStyle(d).zIndex > 100);
      if (!o) return [];
      return [...o.querySelectorAll('div,span,button')].filter((e) => { const b = e.getBoundingClientRect(); return b.width > 20 && b.height > 10 && b.height < 50; })
        .map((e) => { const b = e.getBoundingClientRect();
          return { t: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 12), x: Math.round(b.x + b.width / 2), y: Math.round(b.y + b.height / 2) }; })
        .filter((e) => e.t).slice(0, 14);
    });
    console.log('弹窗文案:', JSON.stringify(modalTitle));
    console.log('弹窗可点元素:', JSON.stringify(tabs));
    const upd = tabs.find((t) => t.t === '更新工具箱');
    if (upd) {
      await page.mouse.click(upd.x, upd.y); await page.waitForTimeout(2200);
      const after = await page.evaluate(() => {
        const o = [...document.querySelectorAll('div')].find((d) => /fixed inset-0/.test(d.className || '') && +getComputedStyle(d).zIndex > 100);
        return o ? (o.innerText || '').replace(/\s+/g, ' ').slice(0, 300) : null;
      });
      await shot(page, 'M-11-工具箱弹窗-更新工具箱页.png');
      await logStep(B, { id: 'J3b-update-tab', title: '工具箱弹窗「更新工具箱」标签页',
        target: `点弹窗里的「更新工具箱」(${upd.x},${upd.y})`,
        evidence: { createTabText: modalTitle, updateTabText: after },
        visible_text: `「创建新工具箱」页：${JSON.stringify(modalTitle)}；切到「更新工具箱」页：${JSON.stringify(after)}`,
        shot: 'M-11-工具箱弹窗-更新工具箱页.png' });
      await page.mouse.click(tabs[0].x, tabs[0].y).catch(() => {}); await page.waitForTimeout(1500);
    }
    // 填名称 + 点创建，看会发生什么
    const nameInput = page.locator('input[type="text"]').last();
    await nameInput.click({ timeout: 4000 }).catch(() => {});
    await nameInput.fill('手册取证测试箱').catch(() => {});
    await page.waitForTimeout(600);
    await shot(page, 'M-12-工具箱弹窗-填写名称.png');
    const createBtn = await page.evaluate(() => {
      const o = [...document.querySelectorAll('div')].find((d) => /fixed inset-0/.test(d.className || '') && +getComputedStyle(d).zIndex > 100);
      const b = o && [...o.querySelectorAll('button,div')].find((e) => (e.innerText || '').trim() === '创建');
      if (!b) return null; const r = b.getBoundingClientRect();
      return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) };
    });
    if (createBtn) {
      await page.mouse.click(createBtn.x, createBtn.y); await page.waitForTimeout(3200);
      await shot(page, 'M-13-工具箱弹窗-点创建之后.png');
      const still = await overlayUp();
      const bodyHas = await page.evaluate(() => (document.body.innerText || '').includes('手册取证测试箱'));
      await logStep(B, { id: 'J3c-create', title: '工具箱弹窗「创建」按钮',
        target: `名称填「手册取证测试箱」后点 (${createBtn.x},${createBtn.y}) 的「创建」`,
        evidence: { overlayStillUp: still, nameVisibleInPage: bodyHas, toast: await toasts() },
        visible_text: `点「创建」后遮罩是否还在 ${JSON.stringify(still)}；页面是否出现「手册取证测试箱」${bodyHas}；提示 ${JSON.stringify(await toasts())}`,
        shot: 'M-13-工具箱弹窗-点创建之后.png' });
    } else {
      await logStep(B, { id: 'J3c-create', title: '工具箱弹窗「创建」按钮', failed: true, visible_text: '弹窗里没找到「创建」按钮' });
    }
  } catch (e) { await logStep(B, { id: 'J3-toolbox-modal', title: '「添加到工具箱」弹窗交互', failed: true, visible_text: String(e).slice(0, 300) }); }

  console.log('节点:', await N());
} finally {
  await browser.close();
}
