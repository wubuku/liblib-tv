// Batch AS4 —— 补 AS3 的两处缺口。
//
//   AS4a `LibTV Plugin` 在 AS3 里点得中、点完三路差集都空，判「等于没反应」。
//        但那一轮**没挂 popup 监听** —— 而「插件市场」这种东西最可能的形态就是
//        **开一个新窗口**（就像「在新窗口打开」那样）。空差集也可能是
//        「新窗口里发生了什么，我这边看不见」。
//        这次补上 `ctx.on('page')` + 原页 URL + 对话框，三路齐上。
//
//   AS4b 找底栏「+」失败：AS3 的条件是「最宽的、y>720、高 30~60 的 div 里
//        找无文字无 aria 的按钮」，这个 div 没筛到。
//        改用**直接几何**：M-125/M-126 的截图量过，那枚「+」在 `[789,757,32,32]`，
//        而它**整页只有一个**。不再猜容器，直接全页扫 button 按坐标取。
import { launch, open, ORIGIN } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { nodeCount } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchAS4';
const { browser, ctx, page } = await launch();

const floats = () => page.evaluate(() => [...document.querySelectorAll(
  '[class*="Menu-dropdown"],[class*="Popover-dropdown"],[class*="Dropdown-dropdown"],[class*="Modal-inner"],[role="dialog"]')]
  .map((e) => { const r = e.getBoundingClientRect();
    return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      cls: (e.className || '').toString().slice(0, 70),
      isModal: /Modal-inner/.test((e.className || '').toString()) || e.getAttribute('role') === 'dialog',
      text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 400),
      items: [...e.querySelectorAll('button,[role="button"],[role="menuitem"],li')].map((b) => {
        const q = b.getBoundingClientRect();
        return { t: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 50),
          aria: b.getAttribute('aria-label'),
          area: Math.round(q.width * q.height),
          cx: Math.round(q.x + q.width / 2), cy: Math.round(q.y + q.height / 2) };
      }).filter((x) => x.area > 0 && (x.t || x.aria)) }; })
  .filter((m) => m.rect[2] > 60 && m.rect[3] > 20));
const clickByAria = async (aria) => {
  const hit = await page.evaluate((a) => {
    const e = [...document.querySelectorAll('button,[role="button"],[aria-label]')]
      .filter((x) => (x.getAttribute('aria-label') || '').trim() === a)
      .map((x) => { const r = x.getBoundingClientRect();
        return { area: Math.round(r.width * r.height), visible: r.width > 2 && r.height > 2,
          cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; })
      .find((x) => x.visible);
    return e || { err: '找不到可见的 aria-label="' + a + '"' };
  }, aria);
  if (hit.err) return hit;
  await page.mouse.click(hit.cx, hit.cy); await page.waitForTimeout(2600);
  return hit;
};

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4000 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1200);
  await beginBatch(B, { note: 'Plugin 补 popup 监听 + 「+」改用直接几何' });

  // ── AS4a LibTV Plugin，三路齐上 ───────────────────────
  const as4a = {};
  const tv = await clickByAria('TV Director');
  as4a.drawerEntry = tv;
  if (!tv.err) {
    const popups = [];
    const onPopup = (p) => popups.push(p);
    ctx.on('page', onPopup);
    const dialogs = [];
    page.on('dialog', (d) => { dialogs.push({ type: d.type(), msg: d.message() }); d.dismiss().catch(() => {}); });
    const urlBefore = page.url(); const nodesBefore = await nodeCount(page);
    const f0 = await floats();
    const btn = await clickByAria('LibTV Plugin');
    await page.waitForTimeout(3200);
    const f1 = await floats();
    as4a.btn = btn;
    as4a.popups = popups.length;
    as4a.popupUrls = popups.map((p) => { try { return p.url(); } catch { return '?'; } });
    as4a.popupTitles = await Promise.all(popups.map(async (p) => { try { return await p.title(); } catch { return '?'; } }));
    as4a.pagesBefore = 1; as4a.pagesAfter = ctx.pages().length;
    as4a.urlChanged = page.url() !== urlBefore;
    as4a.currentUrl = page.url();
    as4a.nodesChanged = (await nodeCount(page)) !== nodesBefore;
    as4a.dialogs = dialogs;
    as4a.newFloats = f1.filter((n) => !f0.some((o) => o.rect.join() === n.rect.join() && o.text === n.text));
    as4a.consoleErrors = await page.evaluate(() => (window.__errs || []).slice(0, 5)).catch(() => null);
    ctx.off('page', onPopup);
    for (const p of popups) { await p.close().catch(() => {}); }
    await shot(page, 'M-126-LibTV-Plugin-点开之后.png');
    as4a.verdict = [
      `新开页签 ${as4a.popups} 个`, `原页 URL 变化 ${as4a.urlChanged}`,
      `节点数变化 ${as4a.nodesChanged}`, `对话框 ${dialogs.length} 个`,
      `新浮层 ${as4a.newFloats.length} 个`,
    ].join(' / ') + ' —— ' + (
      as4a.popups === 0 && !as4a.urlChanged && !as4a.nodesChanged && dialogs.length === 0 && as4a.newFloats.length === 0
        ? '**五路全空，点了确实没有任何可见变化**'
        : '有变化，见上面各字段');
    console.log('AS4a:', JSON.stringify(as4a).slice(0, 2000));
  }

  // ── AS4b 底栏「+」→ 素材库 → 打开工具箱 ─────────────
  await page.keyboard.press('Escape').catch(() => {});
  await page.waitForTimeout(900);
  const as4b = {};
  const plus = await page.evaluate(() => {
    const all = [...document.querySelectorAll('button,[role="button"]')].map((b) => {
      const r = b.getBoundingClientRect();
      return { t: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20),
        aria: b.getAttribute('aria-label'), title: b.getAttribute('title'),
        area: Math.round(r.width * r.height), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) };
    }).filter((b) => b.area > 300 && b.rect[1] > 700 && b.rect[0] > 600 && b.rect[0] < 1000);
    // 底栏那一排里**最靠左且没有文字**的那枚 = 「+」
    return all.find((b) => !b.t && !b.aria && !b.title) || null;
  });
  as4b.plus = plus;
  console.log('AS4b 「+」:', JSON.stringify(plus));
  if (plus) {
    const f0 = await floats();
    await page.mouse.click(plus.cx, plus.cy);
    await page.waitForTimeout(2400);
    const f1 = await floats();
    as4b.newFloats = f1.filter((n) => !f0.some((o) => o.rect.join() === n.rect.join() && o.text === n.text));
    as4b.panel = as4b.newFloats.find((n) => !n.isModal) || as4b.newFloats[0] || null;
    await shot(page, 'M-127-添加节点面板.png');
    console.log('AS4b 面板:', JSON.stringify(as4b.panel).slice(0, 1000));

    const lib = (as4b.panel?.items || []).find((i) => i.t === '素材库');
    as4b.libItem = lib || null;
    if (lib) {
      const f2 = await floats();
      for (const [dx, dy] of [[0, 0], [1, 0], [0, 1], [2, 0]]) {
        await page.mouse.move(lib.cx + dx, lib.cy + dy); await page.waitForTimeout(1400);
      }
      const f3 = await floats();
      as4b.submenu = f3.filter((n) => !f2.some((o) => o.rect.join() === n.rect.join() && o.text === n.text))
        .find((n) => !n.isModal) || null;
      await shot(page, 'M-128-素材库子菜单.png');
      console.log('AS4b 子菜单:', JSON.stringify(as4b.submenu).slice(0, 1000));

      const tb = (as4b.submenu?.items || []).find((i) => /工具箱/.test((i.t || '') + (i.aria || '')));
      as4b.toolboxBtn = tb || null;
      if (tb) {
        await page.mouse.click(tb.cx, tb.cy);
        await page.waitForTimeout(3200);
        await shot(page, 'M-129-工具箱弹窗.png');
        const f4 = await floats();
        as4b.dialog = f4.find((n) => n.isModal) || null;
        console.log('AS4b 工具箱弹窗:', JSON.stringify(as4b.dialog).slice(0, 1800));
        // 卡片上的「使用」按钮：**只读坐标与文案，不点**
        as4b.useButtons = (as4b.dialog?.items || []).filter((i) => /使用|应用|添加/.test(i.t || '') || /使用/.test(i.aria || ''));
        as4b.allButtons = (as4b.dialog?.items || []).map((i) => i.t || i.aria);
      } else {
        as4b.toolboxErr = '子菜单里没有工具箱项；items = ' + JSON.stringify((as4b.submenu?.items || []).map((i) => i.t || i.aria));
      }
    } else {
      as4b.libErr = '面板 items 里没有「素材库」；items = ' + JSON.stringify((as4b.panel?.items || []).map((i) => i.t || i.aria));
    }
  }
  console.log('AS4b:', JSON.stringify(as4b).slice(0, 2500));

  await logStep(B, {
    id: 'AS4-plugin-popup-and-toolbox', title: 'Plugin 补 popup 监听 + 「+」改直接几何 + 工具箱只读',
    target: 'Plugin 点完同时看：新页签 / 原页 URL / 节点数 / 对话框 / 新浮层（五路齐上）；工具箱卡片按钮**只读坐标不点**',
    evidence: { as4a, as4b },
    visible_text: `LibTV Plugin 五路监听：${JSON.stringify(as4a).slice(0, 800)}。`
      + `\n\n「+」→ 素材库 → 工具箱：${JSON.stringify(as4b).slice(0, 1200)}`,
    shot: 'M-129-工具箱弹窗.png',
  });
  console.log('AS4 完成');
} finally {
  await browser.close();
}
