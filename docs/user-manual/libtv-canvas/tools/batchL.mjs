// Batch L —— 收尾组操作条：颜色色板（要看见）+ 布局按钮（真身份）+ 工具箱弹窗交互。
//
// batchJ 查到的组操作条真实结构（按 x 排，全是叶子 div/span，组操作条不是 <button>）：
//   485  20×20  size-5 rounded-full border-[0.5px]  → 颜色圆点，当前色 rgb(184,184,184)
//   535  52×36  iconify iconify--libtv               → **这才是「布局」按钮**（batchJ 筛漏了）
//   567   1×24  mx-0.5 w-px                         → 分隔线
//   634        整组执行      745  添加到工具箱   856  转分镜组   941  解组
//   968   1×24  分隔线
//   993  36×36  iconify，opacity 0.45                → 批量下载（灰=不可用）
//
// batchJ 的两个老问题，这轮一起解：
//   1. 色板渲染在 y=-99（视口外）→ 成组后用 Space+拖 把组往视口中间平移，让弹层有地方展开。
//      注意：能平移的键只有 Space，⌘0 / ⌘- / Esc 都会丢选中态。
//   2. J3 找不到「添加到工具箱」→ 又是上一步结尾按了 Esc。这轮每步之间不按任何键，
//      实在要点就把「添加节点」面板用鼠标点空白关掉，不用 Esc。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep, fingerprint, diffPanels } from './scenario.mjs';
import { nodeCount, fitView } from './canvas-ops.mjs';
import { openDropdown } from './canvas-dropdown.mjs';

const SPACE = '10354929';
const B = 'batchL';
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
const toolbarLeaves = (withHtml = false) => page.evaluate((html) => {
  const g = [...document.querySelectorAll('.react-flow__node')].find((n) => /group/i.test(n.className || '') || /group/i.test(n.getAttribute('data-id') || ''));
  if (!g) return { present: false, why: '没有组节点' };
  const r = g.getBoundingClientRect();
  const leaves = [...g.querySelectorAll('div,span')].filter((e) => {
    const b = e.getBoundingClientRect();
    return b.width > 0 && b.height > 0 && b.y < r.y + 60 && b.y > r.y - 80 && b.width < 200 && !e.querySelector('div,span');
  }).map((e) => { const b = e.getBoundingClientRect(); const svg = e.querySelector('svg');
    return { t: (e.getAttribute('aria-label') || e.title || e.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 14),
      x: Math.round(b.x + b.width / 2), y: Math.round(b.y + b.height / 2),
      w: Math.round(b.width), h: Math.round(b.height), op: +getComputedStyle(e).opacity,
      cls: (e.className || '').toString().slice(0, 46),
      icon: svg ? (svg.getAttribute('class') || '') : null,
      svgHtml: svg ? (svg.innerHTML || '').slice(0, 500) : null,
      html: html ? (e.outerHTML || '').slice(0, 400) : undefined }; })
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
const overlayUp = () => page.evaluate(() => {
  const o = [...document.querySelectorAll('div')].find((d) => /fixed inset-0/.test(d.className || '') && +getComputedStyle(d).zIndex > 100);
  return o ? { z: getComputedStyle(o).zIndex, pe: getComputedStyle(o).pointerEvents } : null;
});

/**
 * 关掉点开的浮层，但**不能碰 Escape**（会丢组的选中态）。
 * batchK 在这里栽了：原来用「fixed inset-0 + z>100」找遮罩，
 * 可 Mantine 的空壳 .mantine-Modal-root 永远满足这个条件，
 * 于是每步都去点空白画布 → 组的选中态被清掉 → 后续全找不到按钮。
 * 正确做法：再点一次同一个触发按钮（toggle 关），模态框才用右上角 ×。
 */
async function dismissPopover(toggle) {
  if (!toggle) return;
  if (await page.evaluate(() => !!document.querySelector('div.grid.grid-cols-5'))) {
    await page.mouse.click(toggle.x, toggle.y);   // 再点一次 = 收起
    await page.waitForTimeout(1000);
  }
}
/** 组操作条万一没了，点组标题把它重新选中。 */
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
  await beginBatch(B, { note: 'K 的修正版：修 dismiss 误点空白取消选中、修正布局按钮认法' });

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

  // ── 平移：Space+拖 把组往下挪，给弹层留展开空间（Space 不会丢选中态，⌘0/⌘-/Esc 会）
  const rect0 = (await toolbarLeaves()).groupRect;
  await page.keyboard.down('Space');
  await page.mouse.move(1360, 400); await page.mouse.down(); await page.waitForTimeout(200);
  for (let i = 1; i <= 8; i += 1) { await page.mouse.move(1360, 400 + i * 22, { steps: 2 }); await page.waitForTimeout(40); }
  await page.mouse.up(); await page.keyboard.up('Space'); await page.waitForTimeout(1400);
  const bar0 = await toolbarLeaves();
  console.log('平移前组矩形:', JSON.stringify(rect0), '→ 平移后:', JSON.stringify(bar0.groupRect), 'selected:', bar0.groupSelected);
  for (const l of bar0.leaves) console.log(`  [${l.t || '·'}] x=${l.x} y=${l.y} ${l.w}×${l.h} op=${l.op} ${l.cls.slice(0, 40)}`);
  await shot(page, 'M-08-组操作条全景.png');

  // ── K1 布局按钮（52×36 iconify）真身：先认图标，再点开看
  let layout = null;
  try {
    // iconify 类名在内层 <svg> 上，div.className 里没有；按尺寸 + 有 svg 来认。
    layout = bar0.leaves.find((l) => l.t === '' && l.w >= 40 && l.w <= 60 && l.h >= 30 && l.icon);
    if (!layout) throw new Error('没找到 52×36 的 iconify 布局按钮');
    console.log('布局按钮 SVG:', (layout.svgHtml || '').slice(0, 300));
    const r = await clickAndDiff(layout);
    await shot(page, 'M-14-组操作条-布局按钮点开.png');
    await logStep(B, { id: 'K1-layout-btn', title: '组操作条上的 52×36 布局按钮',
      target: `点 (${layout.x},${layout.y})，${layout.w}×${layout.h}，class ${layout.cls}`,
      evidence: { clicked: layout, svgPathSnippet: (layout.svgHtml || '').slice(0, 240), newPanels: r.fresh, popups: r.pop,
        groupStillSelected: (await toolbarLeaves()).groupSelected, toast: await toasts() },
      visible_text: `SVG ${(layout.svgHtml || '').slice(0, 160)}；点开弹出 ${JSON.stringify(r.pop)}；新面板 ${JSON.stringify(r.fresh.map((f) => f.all).filter(Boolean).slice(0, 6))}；提示 ${JSON.stringify(await toasts())}`,
      shot: 'M-14-组操作条-布局按钮点开.png' });
  } catch (e) { await logStep(B, { id: 'K1-layout-btn', title: '组操作条上的 52×36 布局按钮', failed: true, visible_text: String(e).slice(0, 300) }); }
  await dismissPopover(layout);

  // ── K2 颜色圆点 → 色板（此时组已在视口中部，弹层应该能看见）
  try {
    const bar1 = await ensureToolbar();
    const dot = bar1.leaves.find((l) => /rounded-full/.test(l.cls));
    if (!dot) throw new Error('ensureToolbar 之后仍然没有颜色圆点；读到 ' + JSON.stringify(bar1.leaves.map((l) => [l.t, l.w, l.h])));
    if (!dot) throw new Error('没找到颜色圆点');
    const r = await clickAndDiff(dot);
    const palette = await page.evaluate(() => {
      const root = [...document.querySelectorAll('div')].find((d) => /grid-cols-5/.test(d.className || ''));
      if (!root) return null;
      const rr = root.getBoundingClientRect();
      const sw = [...root.children].map((c) => { const b = c.getBoundingClientRect();
        return { style: (c.getAttribute('style') || ''), x: Math.round(b.x), y: Math.round(b.y),
          w: Math.round(b.width), h: Math.round(b.height), cls: (c.className || '').toString().slice(0, 50) }; });
      return { rect: [Math.round(rr.x), Math.round(rr.y), Math.round(rr.width), Math.round(rr.height)],
        inViewport: rr.y >= 0 && rr.bottom <= window.innerHeight, swatchCount: sw.length, swatches: sw };
    });
    await shot(page, 'M-09-组操作条-颜色色板.png');
    await logStep(B, { id: 'K2-color-palette', title: '组操作条颜色圆点 → 10 色色板',
      target: `点 (${dot.x},${dot.y}) 的 20×20 圆点，style ${(dot.html || '').match(/background: [^;"]*/) || '?'}`,
      evidence: { groupRectBeforeClick: bar1.groupRect, clicked: dot, palette, newPanels: r.fresh.map((f) => f.sig), popups: r.pop },
      visible_text: palette
        ? `色板容器 ${JSON.stringify(palette.rect)}（宽 ${palette.rect[2]}、高 ${palette.rect[3]}），5 列共 ${palette.swatchCount} 个 ${palette.swatches[0]?.w}×${palette.swatches[0]?.h} 圆形色块，完整可见 ${palette.inViewport}；色块 style ${JSON.stringify(palette.swatches.map((s) => s.style))}`
        : `没抓到 grid-cols-5；新面板 ${JSON.stringify(r.fresh)}`,
      shot: 'M-09-组操作条-颜色色板.png' });
  } catch (e) { await logStep(B, { id: 'K2-color-palette', title: '组操作条颜色圆点 → 10 色色板', failed: true, visible_text: String(e).slice(0, 300) }); }
  await dismissPopover(dot);

  // ── K3 「添加到工具箱」弹窗：更新工具箱标签页 + 填名称 + 点创建
  try {
    const bar2 = await ensureToolbar();
    const btn = bar2.leaves.find((l) => l.t === '添加到工具箱');
    if (!btn) throw new Error('没找到「添加到工具箱」；实际读到 ' + JSON.stringify(bar2.leaves.map((l) => l.t)));
    await page.mouse.click(btn.x, btn.y); await page.waitForTimeout(2800);
    const readModal = () => page.evaluate(() => {
      const o = [...document.querySelectorAll('div')].find((d) => /fixed inset-0/.test(d.className || '') && +getComputedStyle(d).zIndex > 100);
      if (!o) return null;
      return { text: (o.innerText || '').replace(/\s+/g, ' ').slice(0, 320),
        clickable: [...o.querySelectorAll('div,span,button')].filter((e) => { const b = e.getBoundingClientRect(); return b.width > 16 && b.height > 8 && b.height < 60; })
          .map((e) => { const b = e.getBoundingClientRect();
            return { t: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 12), x: Math.round(b.x + b.width / 2), y: Math.round(b.y + b.height / 2) }; })
          .filter((e) => e.t).slice(0, 16) };
    });
    const create = await readModal();
    console.log('弹窗:', JSON.stringify(create));
    const upd = create?.clickable.find((c) => c.t === '更新工具箱');
    if (upd) {
      await page.mouse.click(upd.x, upd.y); await page.waitForTimeout(2400);
      const after = await readModal();
      await shot(page, 'M-11-工具箱弹窗-更新工具箱页.png');
      await logStep(B, { id: 'K3b-update-tab', title: '工具箱弹窗「更新工具箱」标签页',
        target: `点弹窗里的「更新工具箱」(${upd.x},${upd.y})`,
        evidence: { createTab: create, updateTab: after },
        visible_text: `「创建新工具箱」页 ${JSON.stringify(create?.text)}；切到「更新工具箱」页 ${JSON.stringify(after?.text)}`,
        shot: 'M-11-工具箱弹窗-更新工具箱页.png' });
      const back = after?.clickable.find((c) => c.t === '创建新工具箱');
      if (back) { await page.mouse.click(back.x, back.y); await page.waitForTimeout(2000); }
    }
    // 填名称再点创建
    const nameInput = page.locator('input[type="text"]').last();
    await nameInput.click({ timeout: 4000 }).catch(() => {});
    await nameInput.fill('手册取证测试箱').catch(() => {});
    await page.waitForTimeout(800);
    await shot(page, 'M-12-工具箱弹窗-填写名称.png');
    const now = await readModal();
    const cb = now?.clickable.find((c) => c.t === '创建');
    if (cb) {
      await page.mouse.click(cb.x, cb.y); await page.waitForTimeout(3600);
      await shot(page, 'M-13-工具箱弹窗-点创建之后.png');
      await logStep(B, { id: 'K3c-create', title: '工具箱弹窗「创建」按钮',
        target: `名称填「手册取证测试箱」后点 (${cb.x},${cb.y}) 的「创建」`,
        evidence: { overlayStillUp: await overlayUp(),
          nameVisibleInPage: await page.evaluate(() => (document.body.innerText || '').includes('手册取证测试箱')), toast: await toasts() },
        visible_text: `点「创建」后遮罩 ${JSON.stringify(await overlayUp())}；页面出现「手册取证测试箱」${await page.evaluate(() => (document.body.innerText || '').includes('手册取证测试箱'))}；提示 ${JSON.stringify(await toasts())}`,
        shot: 'M-13-工具箱弹窗-点创建之后.png' });
    } else { await logStep(B, { id: 'K3c-create', title: '工具箱弹窗「创建」按钮', failed: true, visible_text: '弹窗里没找到「创建」按钮；可点元素 ' + JSON.stringify(now?.clickable) }); }
  } catch (e) { await logStep(B, { id: 'K3-toolbox-modal', title: '「添加到工具箱」弹窗交互', failed: true, visible_text: String(e).slice(0, 300) }); }

  console.log('节点:', await N());
} finally {
  await browser.close();
}
