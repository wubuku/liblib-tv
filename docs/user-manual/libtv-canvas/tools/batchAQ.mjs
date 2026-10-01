// Batch AQ —— 补救 batchAP 的两处漏测，两处都是**同一个老坑**：
//
//   · `缩放至50%` / `缩放至800%` 报「菜单里没有这一项」
//   · 画布下拉的行菜单一项没读到
//
// 根因：`openZoomMenu()` 无条件点一下百分比。而它是个 **toggle** ——
// 第二轮点下去不是「打开菜单」而是「把菜单关掉」，于是紧接着的 `floating()` 返回 `undefined`。
// §15.6 已经为这个坑写过一版修法（先探当前状态再决定点不点），**AP 又犯了一遍**。
//
// 而行菜单筛不出东西，是因为我按「无名小按钮」筛 ——
// 画布下拉每一行那枚按钮其实**有 aria**：`aria-label="更多操作"`（24×24）。
//
// 所以这一轮的判据定死成一条：
//   **toggle 类控件（菜单/下拉/抽屉）一律先读状态，再决定点不点；**
//   **找控件先按 aria-label 兜一遍，不按「无名」筛。**
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { nodeCount, fitView } from './canvas-ops.mjs';
import { openDropdown } from './canvas-dropdown.mjs';

const SPACE = '10354929';
const B = 'batchAQ';
const { browser, page } = await launch();

const N = () => nodeCount(page);
const zoom = () => page.evaluate(() => {
  const v = document.querySelector('.react-flow__viewport');
  const m = v && /scale\(([\d.]+)\)/.exec(v.style.transform || '');
  const pct = [...document.querySelectorAll('*')].find((e) => /^\d+%$/.test((e.innerText || '').trim())
    && e.getBoundingClientRect().width < 60 && e.getBoundingClientRect().y > 700);
  return { scale: m ? Number(m[1]) : null, label: pct ? pct.innerText.trim() : null };
});
const menuOpen = () => page.evaluate(() => [...document.querySelectorAll('[class*="Menu-dropdown"],[class*="Popover-dropdown"],[class*="Dropdown-dropdown"]')]
  .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 40 && r.height > 12; }).length > 0);
const readMenu = () => page.evaluate(() => [...document.querySelectorAll('[class*="Menu-dropdown"],[class*="Popover-dropdown"],[class*="Dropdown-dropdown"]')]
  .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 40 && r.height > 12; })
  .map((e) => { const r = e.getBoundingClientRect();
    return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 260),
      inputs: [...e.querySelectorAll('input')].map((i) => ({ v: i.value, aria: i.getAttribute('aria-label'), type: i.type })),
      items: [...e.querySelectorAll('[role="menuitem"],button,li,label,div')].filter((c) => {
        const cr = c.getBoundingClientRect();
        return cr.width > 24 && cr.height > 8 && cr.height < 46 && (c.innerText || '').trim().length <= 26 && !c.querySelector('div[style]');
      }).map((c) => { const cr = c.getBoundingClientRect();
        return { t: (c.innerText || '').replace(/\s+/g, ' ').trim(), cx: Math.round(cr.x + cr.width / 2), cy: Math.round(cr.y + cr.height / 2) }; })
        .filter((x, i, a) => a.findIndex((y) => y.t === x.t && y.cy === x.cy) === i) }; }));

/** toggle 安全版：先探状态，开着就点一下关掉，再点才是打开。 */
async function ensureMenuOpen(trigger) {
  if (await menuOpen()) { await page.mouse.click(trigger.cx, trigger.cy); await page.waitForTimeout(1100); }
  if (!(await menuOpen())) { await page.mouse.click(trigger.cx, trigger.cy); await page.waitForTimeout(1600); }
  return readMenu();
}
const zoomTrigger = () => page.evaluate(() => {
  const e = [...document.querySelectorAll('*')].find((x) => /^\d+%$/.test((x.innerText || '').trim())
    && x.getBoundingClientRect().width < 60 && x.getBoundingClientRect().y > 700);
  if (!e) return null;
  const b = (e.closest('button,[role="button"]') || e).getBoundingClientRect();
  return { label: e.innerText.trim(), cx: Math.round(b.x + b.width / 2), cy: Math.round(b.y + b.height / 2) };
});

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4000 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '补救 AP：toggle 安全 + 按 aria 找行菜单' });

  await openDropdown(page, 1000);
  await page.getByRole('button', { name: '新建画布', exact: true }).first().click();
  await page.waitForTimeout(4500);
  await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(1500);
  for (const [x, y] of [[600, 300], [600, 500]]) {
    await page.mouse.dblclick(x, y); await page.waitForTimeout(1100);
    const it = page.locator('[data-guide-lockable-portal="true"], [data-canvas-menu-portal="true"]').first()
      .getByText('图片', { exact: false }).first();
    if (await it.count().catch(() => 0)) {
      const b = await N(); await it.click({ timeout: 4000 }).catch(() => {}); await page.waitForTimeout(2300);
      if (await N() > b) break;
    }
    await page.keyboard.press('Escape').catch(() => {});
  }
  await fitView(page, 1); await page.waitForTimeout(1200);
  const z0 = await zoom();

  // ── AQ1 三档预设逐个实按（toggle 安全版）
  const results = [];
  for (const label of ['缩放至50%', '缩放至100%', '缩放至800%']) {
    try {
      const trig = await zoomTrigger();
      if (!trig) throw new Error('找不到百分比触发点');
      const before = await zoom();
      const menu = await ensureMenuOpen(trig);
      const it = menu[0]?.items.find((i) => i.t === label);
      if (!it) { results.push({ label, err: '菜单里没有；读到 ' + JSON.stringify(menu[0]?.items.map((i) => i.t)) }); continue; }
      await page.mouse.click(it.cx, it.cy); await page.waitForTimeout(1900);
      const after = await zoom();
      await shot(page, `M-118-缩放-${label}.png`);
      const want = parseInt(label.replace(/\D/g, ''), 10) / 100;
      results.push({ label, before, after, want,
        hit: before.scale !== null && after.scale !== null && Math.abs(after.scale - want) < 0.01 });
    } catch (e) { results.push({ label, err: String(e).slice(0, 200) }); }
    console.log(`AQ1 ${label}:`, JSON.stringify(results[results.length - 1]));
  }

  // ── AQ2 画布下拉每行那枚 `aria-label="更多操作"` 的菜单内容
  const rowMenus = [];
  for (let i = 0; i < 3; i += 1) {
    await page.keyboard.press('Escape').catch(() => {});
    await page.waitForTimeout(700);
    await openDropdown(page, 1400);
    const hit = await page.evaluate((idx) => {
      const pop = [...document.querySelectorAll('[class*="Menu-dropdown"],[class*="Popover-dropdown"],[class*="Dropdown-dropdown"]')]
        .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 120 && r.height > 60; })[0];
      if (!pop) return { err: '下拉没打开' };
      const all = [...pop.querySelectorAll('button,[role="button"]')]
        .filter((b) => b.getAttribute('aria-label') === '更多操作');
      const el = all[idx];
      if (!el) return { err: `只有 ${all.length} 枚「更多操作」`, total: all.length };
      const name = (el.previousElementSibling?.innerText || '').trim()
        || (el.parentElement?.innerText || '').replace(/\s+/g, ' ').trim();
      const r = el.getBoundingClientRect();
      return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2), row: name, total: all.length };
    }, i);
    if (hit.err) { rowMenus.push({ i: i + 1, err: hit.err }); if (hit.total) break; else break; }
    await page.mouse.click(hit.cx, hit.cy); await page.waitForTimeout(1700);
    const menu = await readMenu();
    rowMenus.push({ i: i + 1, row: hit.row, at: [hit.cx, hit.cy],
      menuText: menu.map((m) => m.text), items: menu.map((m) => m.items.map((x) => x.t)) });
    await shot(page, `M-119-画布下拉-行${i + 1}菜单.png`);
    console.log(`AQ2 第${i + 1}行:`, JSON.stringify(rowMenus[rowMenus.length - 1]).slice(0, 500));
  }
  await page.keyboard.press('Escape').catch(() => {});
  await page.waitForTimeout(800);
  await shot(page, 'M-120-收尾.png');

  await logStep(B, { id: 'AQ1-fix', title: '缩放三档预设 + 画布下拉行菜单（toggle 安全版 + 按 aria 定位）',
    target: '每个菜单先读状态再决定点不点；行菜单按 `aria-label="更多操作"` 定位，不再按「无名按钮」筛',
    evidence: { z0, results, rowMenus },
    visible_text: `起点缩放 ${JSON.stringify(z0)}。` +
      `**三档预设**：${JSON.stringify(results)}。` +
      `**画布下拉行菜单**（共探 ${rowMenus.length} 行）：${JSON.stringify(rowMenus)}。` +
      `\n每行那枚按钮是 \`aria-label="更多操作"\`（24×24），**有 aria**，不是无名按钮。`,
    shot: 'M-118-缩放-缩放至50.png' });
  console.log('AQ:', JSON.stringify({ z0, results, rowMenus }).slice(0, 2500));

  console.log('收尾节点:', await N());
} finally {
  await browser.close();
}
