// Batch M —— 组操作条最后一轮，把剩下的问号全部坐实。
//
// batchL 拿到的：
//   · 色板容器 [470,77,228,84]，5 列 × 2 行 = 10 个 36×36 圆形色块，完整可见。
//     截图肉眼可数：上排 灰/红/橙/黄/绿，下排 青/蓝/紫/粉/白。
//     但每个色块 div 的 style 只有 `outline: none`，颜色挂在内层子元素上 —— 这轮挖进去。
//   · 52×36 那枚（⊞ + 小三角）点开 **DOM 零变化**：弹层 null、新面板 []、无提示。
//     截图里明明有下拉三角，所以这轮再用两个角度验：
//       ① 它会不会其实直接重排了节点？（比成员节点坐标前后）
//       ② 不按尺寸过滤，全量 DOM 差集 + body 文本差，看有没有任何变化
//
// M2 真正选一个色：点第 2 个色块（红），看组的框色/底色有没有跟着变。
// M3 「添加到工具箱」弹窗走完整交互：更新工具箱页 / 更换封面 / 添加标签 / 创建。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { nodeCount, fitView } from './canvas-ops.mjs';
import { openDropdown } from './canvas-dropdown.mjs';

const SPACE = '10354929';
const B = 'batchM';
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
/** 全量 DOM 指纹：不按尺寸过滤，什么都记，用来抓「悄悄变了」的东西。 */
const fullSnapshot = () => page.evaluate(() => ({
  els: document.querySelectorAll('*').length,
  bodyText: (document.body.innerText || '').replace(/\s+/g, ' '),
  sigs: [...document.querySelectorAll('div,span,button,svg,ul,li')].map((e) => {
    const b = e.getBoundingClientRect();
    return `${e.tagName}.${(e.className || '').toString().slice(0, 24)}@${Math.round(b.x)},${Math.round(b.y)}`;
  }),
}));
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
      .filter((e) => e.t).slice(0, 18) };
});
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

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4000 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '布局按钮全量 DOM 差集 + 节点坐标对照；真选一个色；工具箱弹窗完整交互' });

  await openDropdown(page, 1000);
  await page.getByRole('button', { name: '新建画布', exact: true }).first().click();
  await page.waitForTimeout(4500);
  await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(1500);
  await addNodeAt(findEmptySpot([]).x, findEmptySpot([]).y, '文本');
  await addNodeAt(findEmptySpot(await nodesOf()).x, findEmptySpot(await nodesOf()).y, '音频');
  await fitView(page, 1); await page.keyboard.press('Meta+-'); await page.waitForTimeout(1400);

  const plain = (await nodesOf()).filter((n) => !n.isGroup);
  const x0 = Math.min(...plain.map((n) => n.x)) - 14, y0 = Math.min(...plain.map((n) => n.y)) - 14;
  const x1 = Math.max(...plain.map((n) => n.x + n.w)) + 14, y1 = Math.max(...plain.map((n) => n.y + n.h)) + 14;
  await page.keyboard.down('Shift');
  await page.mouse.move(40, 200); await page.mouse.down(); await page.waitForTimeout(150);
  await page.mouse.move(x0, y0, { steps: 10 }); await page.mouse.move(x1, y1, { steps: 12 });
  await page.mouse.up(); await page.keyboard.up('Shift'); await page.waitForTimeout(1500);
  await page.keyboard.press('Meta+g'); await page.waitForTimeout(2600);
  // Space+拖 把组平移到视口中部，色板才展得开（Space 不丢选中态，⌘0/⌘-/Esc 会）
  await page.keyboard.down('Space');
  await page.mouse.move(1360, 400); await page.mouse.down(); await page.waitForTimeout(200);
  for (let i = 1; i <= 8; i += 1) { await page.mouse.move(1360, 400 + i * 22, { steps: 2 }); await page.waitForTimeout(40); }
  await page.mouse.up(); await page.keyboard.up('Space'); await page.waitForTimeout(1400);
  const bar = await toolbarLeaves();
  console.log('组矩形:', JSON.stringify(bar.groupRect), 'selected:', bar.groupSelected);

  // ── M1 布局按钮：全量差集 + 节点坐标，看它到底做了什么
  try {
    const layout = bar.leaves.find((l) => l.t === '' && l.w >= 40 && l.w <= 60 && l.h >= 30 && l.icon);
    if (!layout) throw new Error('没找到 52×36 布局按钮');
    const before = await fullSnapshot();
    const nodesBefore = await nodesOf();
    await page.mouse.click(layout.x, layout.y);
    await page.waitForTimeout(3000);
    const after = await fullSnapshot();
    const nodesAfter = await nodesOf();
    const added = after.sigs.filter((s) => !before.sigs.includes(s));
    const removed = before.sigs.filter((s) => !after.sigs.includes(s));
    const moved = nodesBefore.map((n, i) => {
      const m = nodesAfter[i]; if (!m) return null;
      const dx = m.x - n.x, dy = m.y - n.y;
      return (dx || dy) ? { title: n.title, dx, dy } : null;
    }).filter(Boolean);
    await shot(page, 'M-14-组操作条-布局按钮点开.png');
    await logStep(B, { id: 'M1-layout-btn', title: '组操作条 ⊞ 布局按钮：点开到底有没有菜单',
      target: `点 (${layout.x},${layout.y}) 的 52×36 按钮（⊞ 图标 + 小三角）`,
      evidence: { clicked: layout, domCountBefore: before.els, domCountAfter: after.els,
        newElements: added.slice(0, 20), removedElements: removed.slice(0, 20),
        bodyTextChanged: before.bodyText !== after.bodyText,
        nodesMoved: moved, toast: await toasts(),
        groupStillSelected: (await toolbarLeaves()).groupSelected },
      visible_text: `点前 DOM 元素 ${before.els} 个 → 点后 ${after.els} 个；新增元素 ${added.length} 个 ${JSON.stringify(added.slice(0, 8))}；` +
        `消失元素 ${removed.length} 个；body 文本是否变化 ${before.bodyText !== after.bodyText}；` +
        `成员节点位移 ${JSON.stringify(moved)}；提示 ${JSON.stringify(await toasts())}`,
      shot: 'M-14-组操作条-布局按钮点开.png' });
  } catch (e) { await logStep(B, { id: 'M1-layout-btn', title: '组操作条 ⊞ 布局按钮', failed: true, visible_text: String(e).slice(0, 300) }); }

  // ── M2 颜色圆点 → 10 色色板，挖出真实色值，并真的选一个色
  try {
    const bar1 = await ensureToolbar();
    const dot = bar1.leaves.find((l) => /rounded-full/.test(l.cls));
    if (!dot) throw new Error('没找到颜色圆点');
    const groupStyleBefore = await page.evaluate(() => {
      const g = [...document.querySelectorAll('.react-flow__node')].find((n) => /group/i.test(n.className || ''));
      if (!g) return null; const s = getComputedStyle(g);
      return { borderColor: s.borderColor, background: s.backgroundColor, cls: (g.className || '').toString().slice(0, 90) };
    });
    await page.mouse.click(dot.x, dot.y); await page.waitForTimeout(2600);
    const palette = await page.evaluate(() => {
      const root = [...document.querySelectorAll('div')].find((d) => /grid-cols-5/.test(d.className || ''));
      if (!root) return null;
      const rr = root.getBoundingClientRect();
      const sw = [...root.children].map((c) => {
        const inner = c.firstElementChild;
        return { x: Math.round(c.getBoundingClientRect().x + c.getBoundingClientRect().width / 2),
          y: Math.round(c.getBoundingClientRect().y + c.getBoundingClientRect().height / 2),
          size: [Math.round(c.getBoundingClientRect().width), Math.round(c.getBoundingClientRect().height)],
          ownBg: getComputedStyle(c).backgroundColor,
          innerBg: inner ? getComputedStyle(inner).backgroundColor : null,
          innerStyle: inner ? (inner.getAttribute('style') || '') : null };
      });
      return { rect: [Math.round(rr.x), Math.round(rr.y), Math.round(rr.width), Math.round(rr.height)], count: sw.length, swatches: sw };
    });
    console.log('色板:', JSON.stringify(palette?.swatches));
    await shot(page, 'M-09-组操作条-颜色色板.png');
    // 真的选第 2 个色块（红），看组的框色变不变
    const red = palette?.swatches[1];
    if (red) {
      await page.mouse.click(red.x, red.y); await page.waitForTimeout(2600);
      const groupStyleAfter = await page.evaluate(() => {
        const g = [...document.querySelectorAll('.react-flow__node')].find((n) => /group/i.test(n.className || ''));
        if (!g) return null; const s = getComputedStyle(g);
        return { borderColor: s.borderColor, background: s.backgroundColor, cls: (g.className || '').toString().slice(0, 90) };
      });
      const dotAfter = await toolbarLeaves();
      await shot(page, 'M-15-组操作条-选色之后.png');
      await logStep(B, { id: 'M2-pick-color', title: '组颜色色板：10 色与实际换色',
        target: `点颜色圆点 (${dot.x},${dot.y}) 展开色板，再点第 2 个色块 (${red.x},${red.y})`,
        evidence: { palette, groupStyleBefore, groupStyleAfter, toast: await toasts(),
          dotAfter: dotAfter.leaves.find((l) => /rounded-full/.test(l.cls)) },
        visible_text: `色板容器 ${JSON.stringify(palette?.rect)}，${palette?.count} 个色块；` +
          `色块尺寸 ${JSON.stringify(palette?.swatches[0]?.size)}，颜色 ${JSON.stringify((palette?.swatches || []).map((s) => s.innerBg || s.ownBg))}；` +
          `选色前组框 ${JSON.stringify(groupStyleBefore)}；点第 2 个色块后组框 ${JSON.stringify(groupStyleAfter)}；提示 ${JSON.stringify(await toasts())}`,
        shot: 'M-15-组操作条-选色之后.png' });
    } else {
      await logStep(B, { id: 'M2-pick-color', title: '组颜色色板', failed: true, visible_text: '色板没抓到，无法点色块' });
    }
  } catch (e) { await logStep(B, { id: 'M2-pick-color', title: '组颜色色板：10 色与实际换色', failed: true, visible_text: String(e).slice(0, 300) }); }

  // ── M3 「添加到工具箱」弹窗完整交互
  try {
    const bar2 = await ensureToolbar();
    const btn = bar2.leaves.find((l) => l.t === '添加到工具箱');
    if (!btn) throw new Error('没找到「添加到工具箱」；读到 ' + JSON.stringify(bar2.leaves.map((l) => l.t)));
    await page.mouse.click(btn.x, btn.y); await page.waitForTimeout(2800);
    const create = await modalText();
    console.log('创建页:', JSON.stringify(create));
    const upd = create?.clickable.find((c) => c.t === '更新工具箱');
    if (upd) {
      await page.mouse.click(upd.x, upd.y); await page.waitForTimeout(2400);
      const after = await modalText();
      await shot(page, 'M-11-工具箱弹窗-更新工具箱页.png');
      await logStep(B, { id: 'M3b-update-tab', title: '工具箱弹窗「更新工具箱」标签页',
        target: `点弹窗里的「更新工具箱」(${upd.x},${upd.y})`,
        evidence: { createTab: create, updateTab: after },
        visible_text: `「创建新工具箱」页 ${JSON.stringify(create?.text)}；切到「更新工具箱」页 ${JSON.stringify(after?.text)}`,
        shot: 'M-11-工具箱弹窗-更新工具箱页.png' });
      const back = after?.clickable.find((c) => c.t === '创建新工具箱');
      if (back) { await page.mouse.click(back.x, back.y); await page.waitForTimeout(2000); }
    } else {
      await logStep(B, { id: 'M3b-update-tab', title: '工具箱弹窗「更新工具箱」标签页', failed: true, visible_text: '弹窗里没找到「更新工具箱」标签' });
    }
    // 「添加标签」点开是什么
    const addTag = (await modalText())?.clickable.find((c) => c.t === '添加标签');
    if (addTag) {
      await page.mouse.click(addTag.x, addTag.y); await page.waitForTimeout(2000);
      const tagUi = await page.evaluate(() => {
        const inp = [...document.querySelectorAll('input')].map((i) => { const b = i.getBoundingClientRect();
          return { ph: i.placeholder, aria: i.getAttribute('aria-label'), v: i.value,
            rect: [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)], inModal: b.width > 0 }; })
          .filter((i) => i.inModal);
        return { inputs: inp, text: (document.body.innerText || '').match(/标签[^\n]{0,80}/g)?.slice(0, 6) };
      });
      console.log('添加标签 UI:', JSON.stringify(tagUi));
      await shot(page, 'M-16-工具箱弹窗-添加标签.png');
      await logStep(B, { id: 'M3c-tag', title: '工具箱弹窗「添加标签」',
        target: `点 (${addTag.x},${addTag.y}) 的「添加标签」`,
        evidence: { tagUi },
        visible_text: `点开后弹窗里的输入框 ${JSON.stringify(tagUi)}`,
        shot: 'M-16-工具箱弹窗-添加标签.png' });
    }
    // 填名称 → 点创建
    const nameInput = page.locator('input[type="text"]').last();
    await nameInput.click({ timeout: 4000 }).catch(() => {});
    await nameInput.fill('手册取证测试箱').catch(() => {});
    await page.waitForTimeout(800);
    await shot(page, 'M-12-工具箱弹窗-填写名称.png');
    const now = await modalText();
    const cb = now?.clickable.find((c) => c.t === '创建');
    if (cb) {
      await page.mouse.click(cb.x, cb.y); await page.waitForTimeout(4000);
      await shot(page, 'M-13-工具箱弹窗-点创建之后.png');
      const stillOpen = await modalText();
      const seen = await page.evaluate(() => (document.body.innerText || '').includes('手册取证测试箱'));
      await logStep(B, { id: 'M3d-create', title: '工具箱弹窗「创建」按钮',
        target: `名称填「手册取证测试箱」后点 (${cb.x},${cb.y}) 的「创建」`,
        evidence: { modalAfterClick: stillOpen, nameVisibleInPage: seen, toast: await toasts() },
        visible_text: `点「创建」后弹窗 ${stillOpen ? '仍然打开：' + JSON.stringify(stillOpen.text) : '已关闭'}；页面出现「手册取证测试箱」${seen}；提示 ${JSON.stringify(await toasts())}`,
        shot: 'M-13-工具箱弹窗-点创建之后.png' });
    } else { await logStep(B, { id: 'M3d-create', title: '工具箱弹窗「创建」按钮', failed: true, visible_text: '没找到「创建」按钮；可点元素 ' + JSON.stringify(now?.clickable) }); }
  } catch (e) { await logStep(B, { id: 'M3-toolbox-modal', title: '「添加到工具箱」弹窗交互', failed: true, visible_text: String(e).slice(0, 300) }); }

  console.log('节点:', await N());
} finally {
  await browser.close();
}
