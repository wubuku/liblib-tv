// Batch AP —— 两处「有截图但从没逐项实点」的地方：
//
//   ① **缩放菜单**（左下角百分比 / 「缩放选项」）：`A6-zoom-menu.png` 是 Batch A 时代拍的，
//      菜单里写了几档「缩放至50%/100%/800%」——但**一档都没点过**，
//      也没有验证过「直接输入百分比」这个顶部输入框能不能用。
//   ② **画布下拉里的行菜单**：Batch A 拍过 `A9c-delete-confirm-btn.png` 等，
//      每一行的「⋯」菜单内容**从没读过**（那是「切换画布」的行操作，和资产管理的行菜单不是一回事）。
//
// 判据沿用 §17 的教训：
//   · **用 locator，不手搓遍历**；
//   · 弹层坐标**每次重读**，不复用；
//   · 断言「点了没变化」之前，先确认「变化该长什么样」。
//
// ⚠️ 缩放会改变整个画布的坐标系 —— 每次读节点坐标前都要先读缩放值，
//    否则前后两轮的坐标根本不可比（这一条以前栽过：见 PROGRESS §5）。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { nodeCount, fitView } from './canvas-ops.mjs';
import { openDropdown } from './canvas-dropdown.mjs';

const SPACE = '10354929';
const B = 'batchAP';
const { browser, page } = await launch();

const N = () => nodeCount(page);
const nodeList = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => {
  const r = n.getBoundingClientRect();
  return { title: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 8),
    rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
}));
/** 当前缩放比：读 viewport 的 transform，别用别处的百分比文本。 */
const zoom = () => page.evaluate(() => {
  const v = document.querySelector('.react-flow__viewport');
  if (!v) return null;
  const m = /scale\(([\d.]+)\)/.exec(v.style.transform || '');
  const pct = [...document.querySelectorAll('*')].find((e) => /^\d+%$/.test((e.innerText || '').trim())
    && e.getBoundingClientRect().width < 60 && e.getBoundingClientRect().y > 700);
  return { scale: m ? Number(m[1]) : null, label: pct ? pct.innerText.trim() : null,
    pctRect: pct ? [Math.round(pct.getBoundingClientRect().x), Math.round(pct.getBoundingClientRect().y),
      Math.round(pct.getBoundingClientRect().width), Math.round(pct.getBoundingClientRect().height)] : null };
});
const floating = () => page.evaluate(() => [...document.querySelectorAll('[class*="Menu-dropdown"],[class*="Popover-dropdown"],[class*="Dropdown-dropdown"]')]
  .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 40 && r.height > 12; })
  .map((e) => { const r = e.getBoundingClientRect();
    return { cls: (e.className || '').toString().slice(0, 36), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 260),
      inputs: [...e.querySelectorAll('input')].map((i) => { const ir = i.getBoundingClientRect();
        return { v: i.value, aria: i.getAttribute('aria-label'), ph: i.placeholder, type: i.type,
          rect: [Math.round(ir.x), Math.round(ir.y), Math.round(ir.width), Math.round(ir.height)] }; }),
      items: [...e.querySelectorAll('[role="menuitem"],button,li,label,div')].filter((c) => {
        const cr = c.getBoundingClientRect();
        return cr.width > 24 && cr.height > 8 && cr.height < 46 && (c.innerText || '').trim().length <= 26 && !c.querySelector('div[style]');
      }).map((c) => { const cr = c.getBoundingClientRect();
        return { t: (c.innerText || '').trim(), cx: Math.round(cr.x + cr.width / 2), cy: Math.round(cr.y + cr.height / 2) }; })
        .filter((x, i, a) => a.findIndex((y) => y.t === x.t && y.cy === x.cy) === i) }; }));

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4000 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '缩放菜单逐档实按 + 输入框 + 画布下拉行菜单' });

  // 建两个节点，缩放才有东西可看
  await openDropdown(page, 1000);
  await page.getByRole('button', { name: '新建画布', exact: true }).first().click();
  await page.waitForTimeout(4500);
  await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(1500);
  for (const item of ['图片', '文本']) {
    for (const [x, y] of [[600, 300], [600, 500], [900, 300], [900, 500]]) {
      await page.mouse.dblclick(x, y); await page.waitForTimeout(1100);
      const it = page.locator('[data-guide-lockable-portal="true"], [data-canvas-menu-portal="true"]').first()
        .getByText(item, { exact: false }).first();
      if (await it.count().catch(() => 0)) {
        const b = await N();
        await it.click({ timeout: 4000 }).catch(() => {}); await page.waitForTimeout(2300);
        if (await N() > b) break;
      }
      await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(700);
    }
  }
  await fitView(page, 1); await page.waitForTimeout(1200);
  const z0 = await zoom();
  console.log('起点缩放:', JSON.stringify(z0));

  // ── AP1 缩放菜单：读全貌，再逐档实按
  const openZoomMenu = async () => {
    const loc = page.getByText(/^\d+%$/, { exact: true });
    const n = await loc.count().catch(() => 0);
    if (!n) throw new Error('左下角找不到百分比文本');
    const info = await loc.first().evaluate((e) => { const r = e.getBoundingClientRect();
      return { t: e.innerText.trim(), cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2),
        rect: [Math.round(r.width), Math.round(r.height)],
        clickable: (e.closest('button,[role="button"]') || e).tagName }; });
    await page.mouse.click(info.cx, info.cy); await page.waitForTimeout(1600);
    return info;
  };
  const probe = { start: z0 };
  try {
    probe.opener = await openZoomMenu();
    probe.menu = await floating();
    await shot(page, 'M-111-缩放菜单-全貌.png');
    console.log('AP1 menu:', JSON.stringify(probe.menu).slice(0, 1200));
  } catch (e) { probe.err = String(e).slice(0, 250); console.log('AP1 失败', probe.err); }

  // 逐档点：每一档都重开菜单、重读坐标
  const PRESETS = ['缩放至50%', '缩放至100%', '缩放至800%'];
  const results = [];
  for (const label of PRESETS) {
    try {
      const before = await zoom();
      const opener2 = await openZoomMenu().catch(() => null);
      const pop = await floating();
      const it = pop?.[0]?.items?.find((i) => i.t === label);
      if (!it) { results.push({ label, err: '菜单里没有这一项；菜单=' + JSON.stringify(pop?.[0]?.items?.map((i) => i.t)) }); continue; }
      await page.mouse.click(it.cx, it.cy); await page.waitForTimeout(1800);
      const after = await zoom();
      await shot(page, `M-112-缩放-${label}.png`);
      results.push({ label, before, after, matched: before && after && before.scale !== null && after.scale !== null
        ? Math.abs(before.scale / after.scale - (parseInt(label.replace(/\D/g, ''), 10) / 100)) < 0.02
        : null });
    } catch (e) { results.push({ label, err: String(e).slice(0, 200) }); }
    console.log(`AP1 ${label}:`, JSON.stringify(results[results.length - 1]));
  }
  probe.presets = results;

  // 顶部那个百分比输入框能不能直接输
  try {
    await openZoomMenu();
    const pop = await floating();
    const inp = pop?.[0]?.inputs?.[0];
    if (!inp) { probe.inputBox = { err: '菜单里没有输入框' }; }
    else {
      const before = await zoom();
      await page.mouse.click(inp.rect[0] + inp.rect[2] / 2, inp.rect[1] + inp.rect[3] / 2);
      await page.keyboard.press('Meta+a');
      await page.keyboard.type('200', { delay: 60 });
      await page.waitForTimeout(600);
      await shot(page, 'M-113-缩放-输入200.png');
      const typed = { value: await page.evaluate((r) => {
        const e = [...document.querySelectorAll('input')].find((x) => { const b = x.getBoundingClientRect();
          return Math.abs(b.x - r[0]) < 12 && Math.abs(b.y - r[1]) < 12; });
        return e ? e.value : null; }, inp.rect) };
      await page.keyboard.press('Enter'); await page.waitForTimeout(1800);
      const after = await zoom();
      await shot(page, 'M-114-缩放-输入后.png');
      probe.inputBox = { inp, before, typed, after };
      console.log('AP1 输入框:', JSON.stringify(probe.inputBox));
    }
    await page.keyboard.press('Escape').catch(() => {});
    await page.waitForTimeout(800);
  } catch (e) { probe.inputBox = { err: String(e).slice(0, 200) }; }

  // ── AP2 画布下拉里每一行的「⋯」
  try {
    await openDropdown(page, 1400);
    await shot(page, 'M-115-画布下拉-行列表.png');
    const rows = await page.evaluate(() => {
      const pop = [...document.querySelectorAll('[class*="Menu-dropdown"],[class*="Popover-dropdown"],[class*="Dropdown-dropdown"]')]
        .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 120 && r.height > 60; })
        .sort((a, b) => (b.getBoundingClientRect().width * b.getBoundingClientRect().height)
          - (a.getBoundingClientRect().width * a.getBoundingClientRect().height))[0];
      if (!pop) return { err: '下拉没打开' };
      const btns = [...pop.querySelectorAll('button,[role="button"]')].map((e) => { const r = e.getBoundingClientRect();
        return { t: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 16), aria: e.getAttribute('aria-label'),
          rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
          cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; });
      return { popText: (pop.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 300), btns };
    });
    console.log('AP2 rows:', JSON.stringify(rows).slice(0, 1600));
    // 逐行找「⋯」：x 靠右、尺寸小的无名按钮
    const moreBtns = (rows.btns || []).filter((b) => !b.t && !b.aria && b.rect[2] <= 32 && b.rect[2] >= 12);
    const menus = [];
    for (let i = 0; i < Math.min(moreBtns.length, 4); i += 1) {
      await openDropdown(page, 1200);
      const rr = await page.evaluate(() => {
        const pop = [...document.querySelectorAll('[class*="Menu-dropdown"],[class*="Popover-dropdown"],[class*="Dropdown-dropdown"]')]
          .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 120 && r.height > 60; })
          .sort((a, b) => (b.getBoundingClientRect().width * b.getBoundingClientRect().height)
            - (a.getBoundingClientRect().width * a.getBoundingClientRect().height))[0];
        if (!pop) return null;
        const hit = [...pop.querySelectorAll('button,[role="button"]')].filter((e) => {
          const r = e.getBoundingClientRect();
          return !(e.innerText || '').trim() && !(e.getAttribute('aria-label') || '').trim() && r.width >= 12 && r.width <= 32;
        })[0];
        if (!hit) return null;
        const r = hit.getBoundingClientRect();
        return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) };
      });
      if (!rr) { menus.push({ i: i + 1, err: '这一行没有无名小按钮' }); break; }
      await page.mouse.click(rr.cx, rr.cy); await page.waitForTimeout(1700);
      const pop = await floating();
      menus.push({ i: i + 1, at: [rr.cx, rr.cy],
        text: pop?.[0]?.text, items: pop?.[0]?.items?.map((x) => x.t) });
      await shot(page, `M-116-画布下拉-行菜单${i + 1}.png`);
    }
    probe.rows = rows; probe.rowMenus = menus;
    await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(800);
  } catch (e) { probe.rows = { err: String(e).slice(0, 250) }; }

  await shot(page, 'M-117-缩放与画布下拉-收尾.png');
  await logStep(B, { id: 'AP1-zoom-and-rowmenu', title: '缩放菜单逐档实按 + 画布下拉的行菜单',
    target: '把缩放菜单每档都点一遍并读 `viewport` 的 scale；再逐行点画布下拉里的无名小按钮',
    evidence: probe,
    visible_text: `起点缩放 ${JSON.stringify(z0)}（节点 ${JSON.stringify((await nodeList()).map((n) => n.title))}）。` +
      `打开缩放菜单的触发点 ${JSON.stringify(probe.opener)}；菜单 ${JSON.stringify(probe.menu)}。` +
      `\n**三档预设逐个实按**：${JSON.stringify(results)}。` +
      `\n**顶部输入框**：${JSON.stringify(probe.inputBox)}。` +
      `\n**画布下拉**：${JSON.stringify(probe.rows)}；逐行菜单 ${JSON.stringify(probe.rowMenus)}。`,
    shot: 'M-111-缩放菜单-全貌.png' });
  console.log('AP:', JSON.stringify(probe).slice(0, 3000));

  console.log('收尾节点:', await N());
} finally {
  await browser.close();
}
