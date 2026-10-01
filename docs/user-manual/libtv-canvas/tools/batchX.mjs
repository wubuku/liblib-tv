// Batch X —— 终于点开「更多操作」。前面四轮全在用 innerText 找它，而它是纯图标按钮。
//
// batchW 的决定性读数：两枚按钮**一直都在**行里，只是 innerText 为空：
//   <BUTTON aria-label="更多操作"             rect=[253,200,24,24]>
//   <BUTTON aria-label="定位到节点 图片节点 1"  rect=[279,200,24,24]>
//
// 我 batchV/batchU 用的判据全是 `/更多操作/.test(innerText)` 和 `txt(e) === '更多操作'`，
// **纯图标按钮的 innerText 是空字符串**，所以永远匹配不上。
// 正确判据是 `getAttribute('aria-label')`。
//
// 这轮：按 aria-label 精确定位 → 点开 → 读菜单内容。
// 同时验一下节点名按钮 —— 它的 aria-label 也叫「定位到节点 {名}」，
// 也就是说**点节点名本身就是定位到节点**，右侧那枚同名按钮可能是历史遗留。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep, fingerprint, diffPanels } from './scenario.mjs';
import { nodeCount } from './canvas-ops.mjs';
import { openDropdown } from './canvas-dropdown.mjs';

const SPACE = '10354929';
const B = 'batchX';
const { browser, page } = await launch();

/** 行内所有 **aria-label 非空** 的按钮 —— 这才是找动作按钮的正确判据。 */
const rowAriaButtons = () => page.evaluate(() => {
  const row = document.querySelector('div.group\\/node');
  if (!row) return null;
  const rb = row.getBoundingClientRect();
  const bs = [...row.querySelectorAll('button')].map((e) => { const b = e.getBoundingClientRect();
    return { aria: e.getAttribute('aria-label'), text: (e.innerText || '').trim().slice(0, 16),
      rect: [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)],
      cx: Math.round(b.x + b.width / 2), cy: Math.round(b.y + b.height / 2),
      opacity: +getComputedStyle(e).opacity, vis: getComputedStyle(e).visibility }; });
  return { rowRect: [Math.round(rb.x), Math.round(rb.y), Math.round(rb.width), Math.round(rb.height)], buttons: bs };
});
async function clickAndRead(fn, wait = 2400) {
  const before = await fingerprint(page);
  await fn(); await page.waitForTimeout(wait);
  const fresh = diffPanels(before, await fingerprint(page));
  const pop = await page.evaluate(() => {
    const els = [...document.querySelectorAll('[role="menu"],[role="listbox"],[role="dialog"],[class*="Popover"],[class*="Dropdown"],[class*="Modal"]')]
      .filter((d) => { const r = d.getBoundingClientRect(); return r.width > 40 && r.height > 20; });
    return els.length ? els.map((e) => ({ cls: (e.className || '').toString().slice(0, 40),
      text: (e.innerText || '').replace(/\s+/g, ' ').slice(0, 400) })) : null;
  });
  return { fresh: fresh.map((f) => ({ sig: f.sig, all: f.all.slice(0, 400) })), pop };
}

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4000 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '按 aria-label 定位动作按钮（不是 innerText），点开读菜单' });

  await openDropdown(page, 1000);
  await page.getByRole('button', { name: '新建画布', exact: true }).first().click();
  await page.waitForTimeout(4500);
  await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(1500);
  await page.mouse.dblclick(500, 300); await page.waitForTimeout(1200);
  await page.locator('[data-guide-lockable-portal="true"], [data-canvas-menu-portal="true"]').first()
    .getByText('图片', { exact: false }).first().click({ timeout: 8000 });
  await page.waitForTimeout(2600);
  console.log('节点:', await nodeCount(page));

  const opener = page.locator('[data-academy-guide-anchor="workspace-asset-management"]');
  await opener.first().click({ timeout: 6000 });
  await page.waitForTimeout(2800);
  const rows = await rowAriaButtons();
  console.log('\n行内按钮（按 aria-label）:', JSON.stringify(rows.buttons, null, 1));
  await shot(page, 'M-34-资产管理-行内动作按钮.png');

  // ── X1 点「更多操作」
  const more = rows.buttons.find((b) => b.aria === '更多操作');
  if (!more) throw new Error('行里没有 aria-label="更多操作" 的按钮；实际 ' + JSON.stringify(rows.buttons.map((b) => b.aria)));
  const r1 = await clickAndRead(async () => { await page.mouse.move(more.cx, more.cy); await page.waitForTimeout(400); await page.mouse.click(more.cx, more.cy); });
  await shot(page, 'M-35-更多操作菜单.png');
  console.log('\n点「更多操作」弹层:', JSON.stringify(r1.pop, null, 1));
  await logStep(B, { id: 'X1-more-actions', title: '资产管理：「更多操作」菜单里到底有什么',
    target: `点行内 aria-label="更多操作" 的图标按钮 (${more.cx},${more.cy})，尺寸 ${more.rect[2]}×${more.rect[3]}`,
    evidence: { rowButtons: rows.buttons, fresh: r1.fresh, popups: r1.pop },
    visible_text: `菜单弹层 ${JSON.stringify(r1.pop)}；新面板 ${JSON.stringify(r1.fresh.map((f) => f.all).filter(Boolean).slice(0, 8))}`,
    shot: 'M-35-更多操作菜单.png' });
  await page.mouse.click(1250, 780); await page.waitForTimeout(1200);

  // ── X2 节点名按钮的 aria-label 也叫「定位到节点」：点它会怎样（只读观察视口变化）
  try {
    const rows2 = await rowAriaButtons();
    const nameBtn = rows2.buttons.find((b) => b.aria && b.aria.startsWith('定位到节点') && b.rect[2] > 60);
    if (!nameBtn) throw new Error('没找到节点名按钮');
    // 先把画布平移到离节点很远的位置，点一下看它会不会把视口拉回去
    const nodePos = await page.evaluate(() => {
      const n = document.querySelector('.react-flow__node'); if (!n) return null;
      const b = n.getBoundingClientRect(); return [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)]; });
    await page.keyboard.down('Space');
    await page.mouse.move(700, 400); await page.mouse.down(); await page.waitForTimeout(180);
    for (let i = 1; i <= 6; i += 1) { await page.mouse.move(700 - i * 60, 400, { steps: 2 }); await page.waitForTimeout(50); }
    await page.mouse.up(); await page.keyboard.up('Space'); await page.waitForTimeout(1600);
    const far = await page.evaluate(() => {
      const n = document.querySelector('.react-flow__node');
      return n ? Math.round(n.getBoundingClientRect().x) : null; });
    await page.locator('button[aria-label="定位到节点"]').first().click({ timeout: 6000 }).catch(async () => {
      await page.mouse.click(nameBtn.cx, nameBtn.cy);
    });
    await page.waitForTimeout(2200);
    const near = await page.evaluate(() => {
      const n = document.querySelector('.react-flow__node');
      return n ? Math.round(n.getBoundingClientRect().x) : null; });
    await shot(page, 'M-37-定位到节点之后.png');
    await logStep(B, { id: 'X2-locate', title: '「定位到节点」按钮：真的会把视口拉回去吗',
      target: `先把画布平移 -360px 让节点跑到左边，再点 aria-label="定位到节点 {名}" 的按钮 (${nameBtn.cx},${nameBtn.cy})`,
      evidence: { nodePosBefore: nodePos, nodeXAfterPanAway: far, nodeXAfterClick: near, buttonAria: nameBtn.aria },
      visible_text: `节点名按钮的 aria-label = ${JSON.stringify(nameBtn.aria)}；` +
        `平移后节点 x = ${far}，点按钮后节点 x = ${near}（差 ${far !== null && near !== null ? near - far : '?'}px）→ ` +
        `${far !== null && near !== null && Math.abs(near - far) > 20 ? '**视口确实被拉回去了，定位生效**' : '**视口没变化**'}`,
      shot: 'M-37-定位到节点之后.png' });
  } catch (e) { await logStep(B, { id: 'X2-locate', title: '「定位到节点」按钮', failed: true, visible_text: String(e).slice(0, 250) }); }

  console.log('最终节点:', await nodeCount(page));
} finally {
  await browser.close();
}
