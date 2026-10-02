// Batch BF —— 三块只读盘点，避开 BE 踩过的所有坑。
//
// BE 的教训直接写进了这个脚本的每一条判据：
//   · 可见文案**先排掉 SCRIPT/STYLE/NOSCRIPT/TEMPLATE**（Next.js 的 RSC payload）
//   · 每次读数都配一条「读到了几条」，空读数显式判失败
//   · 位置一律读**画布坐标**（transform translate），不读屏幕坐标
//   · 节点 id 从数组 `.slice()` 取，不用 `Object.keys()`
//   · 落点操作前验 `elementFromPoint` 归属
//
// 三个目标：
//
// 1. **缩放菜单的后三行**。AP 那批验过「顶部输入框」和三档预设（50/100/800%），
//    但菜单里那三行 `放大 ⌘+` / `缩小 ⌘-` / `适合屏幕 ⌘0` **作为菜单项点**会怎样，
//    一直没验过 —— 而且它们点下去后**菜单会不会自己关**也没人写过。
//    这次每一项点完都回读 scale **和菜单是否还开着**。
//    ⚠️ AP 已经踩过一次「点完第一档菜单自己关了，后两档在关着的菜单里找行」。
//    所以每一项之前**重新确认菜单开着**，关了就重新打开。
//
// 2. **顶栏「画布 N」下拉**：弹出的列表里到底有什么、当前画布怎么标。
//    只读打开→读→Esc。
//
// 3. **节点星级**：organize-canvas 的 not_verified 里明确挂着「节点星级在哪里打」📖。
//    这轮全量扫一遍看星级 UI 到底出现在哪 —— 节点卡片上？画布行菜单里？
//    资产管理列表里？（资产管理列表的「所有评级」筛子已坐实，说明数据存在，
//    但**入口**还没找到。）
//
// ⚠️ 只读：不生成、不上传、不创建、不删除、不付费、不提交任何表单。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';

const SPACE = '10354929';
const B = 'batchBF1';
const { browser, page } = await launch();

/** ⭐ 可见文案判据：先排掉 script/style/noscript/template。 */
const VIS = `(e) => !['SCRIPT','STYLE','NOSCRIPT','TEMPLATE'].includes(e.tagName)`;
const visText = (pg) => pg.evaluate(`(() => {
  const ok = ${VIS};
  return [...document.querySelectorAll('body *')].filter(ok)
    .map((e) => (e.innerText || '').replace(/\\s+/g, ' ').trim())
    .filter((t) => t && t.length < 120); })()`);

const snapScale = () => page.evaluate(() => {
  const v = document.querySelector('.react-flow__viewport');
  const m = v ? /scale\(([\d.]+)\)/.exec(v.style.transform || '') : null;
  return m ? +m[1] : null; });

/** 菜单开着没有？——「宽 > 120 且高 > 80 且可见」的面板数量。 */
const panelCount = () => page.evaluate(() => [...document.querySelectorAll('div,section,aside')]
  .filter((e) => {
    const t = e.tagName;
    if (['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE'].includes(t)) return false;
    const r = e.getBoundingClientRect();
    const cs = getComputedStyle(e);
    return r.width > 120 && r.height > 60 && cs.visibility !== 'hidden'
      && cs.display !== 'none' && +cs.opacity > 0.05 && r.x + r.width > 0 && r.x < 1440;
  }).length);

/** 点一个可见文本等于 target 的元素，返回点前信息。 */
const clickText = async (pg, target, exact = true) => pg.evaluate(([t, ex]) => {
  const ok = (e) => !['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE'].includes(e.tagName);
  const cands = [...document.querySelectorAll('button,[role="button"],li,div,span,a')]
    .filter(ok)
    .filter((e) => { const s = (e.innerText || '').replace(/\s+/g, ' ').trim();
      return ex ? s === t : s.includes(t); })
    .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; });
  if (!cands.length) return { err: '没找到「' + t + '」', n: 0 };
  // 取面积最小的（最内层、最可能就是那一行）
  cands.sort((a, b) => { const ra = a.getBoundingClientRect(), rb = b.getBoundingClientRect();
    return (ra.width * ra.height) - (rb.width * rb.height); });
  const e = cands[0];
  const r = e.getBoundingClientRect();
  const x = Math.round(r.x + r.width / 2), y = Math.round(r.y + r.height / 2);
  const at = document.elementFromPoint(x, y);
  return { x, y, n: cands.length,
    tag: e.tagName, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    ownerTag: at ? at.tagName : null,
    ownerIsTarget: !!(at && (at === e || e.contains(at))) };
}, [target, exact]);

const openZoomMenu = async () => {
  const p = await clickText(page, '100%', true);
  if (p.err) {
    // 兜底：找 aria=缩放选项
    const q = await page.evaluate(() => {
      const e = [...document.querySelectorAll('button,[role="button"]')]
        .find((x) => x.getAttribute('aria-label') === '缩放选项');
      if (!e) return { err: '没找到缩放按钮' };
      const r = e.getBoundingClientRect();
      return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) };
    });
    if (q.err) return q;
    await page.mouse.click(q.x, q.y);
  } else {
    await page.mouse.click(p.x, p.y);
  }
  await page.waitForTimeout(1800);
  return { ok: true };
};

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1500);
  await beginBatch(B, { note: '缩放菜单后三行 / 顶栏画布下拉 / 节点星级入口（三块只读）' });

  const out = {};
  await page.keyboard.press('Escape'); await page.waitForTimeout(1000);

  // ═══ 1. 缩放菜单的三行「动作项」
  console.log('--- BF-1 缩放菜单的动作项 ---');
  const scale0 = await snapScale();
  console.log('起始 scale =', scale0);
  out.zoom = { scale0, rows: [] };

  for (const label of ['放大', '缩小', '适合屏幕']) {
    // ⭐ 每一项之前**重新确认菜单开着**（AP 踩过：点完上一项菜单自己关了）
    let tries = 0;
    while ((await panelCount()) < 1 && tries < 3) { await openZoomMenu(); tries += 1; }
    const before = await snapScale();
    const panelsBefore = await panelCount();
    const hit = await clickText(page, label, false);
    if (hit.err) { console.log(`  ${label}: ${hit.err}`); out.zoom.rows.push({ label, err: hit.err }); continue; }
    const ownerOk = hit.ownerIsTarget;
    await page.mouse.click(hit.x, hit.y);
    await page.waitForTimeout(2200);
    const after = await snapScale();
    const panelsAfter = await panelCount();
    const row = { label, hit, ownerOk, scaleBefore: before, scaleAfter: after,
      scaleChanged: before !== after, panelsBefore, panelsAfter, menuClosed: panelsAfter < panelsBefore };
    out.zoom.rows.push(row);
    console.log(`  ${label}：命中 ${hit.n} 个候选；落点归属 ${ownerOk ? '✅' : '⚠️ 不是目标'}`);
    console.log(`    scale ${before} → ${after} ${before !== after ? '(变了 ✅)' : '(没变)'}`);
    console.log(`    可见面板 ${panelsBefore} → ${panelsAfter} ${panelsAfter < panelsBefore ? '(菜单关了)' : '(菜单还开着)'}`);
    await page.keyboard.press('Escape'); await page.waitForTimeout(900);
  }
  // 复原到 100%
  const restore = await openZoomMenu();
  if (!restore.err) {
    const inp = await page.evaluate(() => {
      const e = document.querySelector('input[aria-label="缩放比例"]');
      if (!e) return { err: '没找到缩放输入框' };
      e.focus();
      return { ok: true };
    });
    if (inp.ok) {
      await page.keyboard.press('Meta+a'); await page.keyboard.type('100');
      await page.keyboard.press('Enter');
      await page.waitForTimeout(2200);
      console.log('  已把缩放填回 100 →', await snapScale());
    }
    await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  }
  out.zoom.restored = await snapScale();
  await shot(page, 'M-191-缩放菜单-全貌.png');
  out.shot = 'M-191-缩放菜单-全貌.png';

  // ═══ 2. 顶栏「画布 N」下拉
  console.log('\n--- BF-2 顶栏画布下拉 ---');
  const cvBtn = await page.evaluate(() => {
    const cands = [...document.querySelectorAll('button,[role="button"]')]
      .filter((e) => /^画布\s*\d+$/.test((e.innerText || '').replace(/\s+/g, ' ').trim()))
      .filter((e) => e.getBoundingClientRect().width > 0);
    if (!cands.length) return { err: '没找到「画布 N」按钮' };
    const e = cands[0];
    const r = e.getBoundingClientRect();
    return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2),
      text: (e.innerText || '').trim(), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
  });
  if (cvBtn.err) { console.log(' ', cvBtn.err); out.canvasMenu = cvBtn; }
  else {
    console.log('  按钮：', JSON.stringify(cvBtn.rect), JSON.stringify(cvBtn.text));
    await page.mouse.move(cvBtn.x, cvBtn.y); await page.waitForTimeout(300);
    await page.mouse.click(cvBtn.x, cvBtn.y); await page.waitForTimeout(2400);
    const items = await page.evaluate(() => [...document.querySelectorAll('div,li,button,[role="menuitem"]')]
      .filter((e) => !['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE'].includes(e.tagName))
      .map((e) => { const r = e.getBoundingClientRect();
        return { text: (e.innerText || '').replace(/\s+/g, ' ').trim(),
          rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; })
      .filter((e) => e.rect[2] > 40 && e.rect[3] > 8 && e.rect[3] < 60
        && e.text && e.text.length < 40 && /画布|\d/.test(e.text))
      .sort((a, b) => a.rect[1] - b.rect[1] || a.rect[0] - b.rect[0]));
    console.log(`  下拉里读到 ${items.length} 行：`);
    items.forEach((i) => console.log(`    [${i.rect}] "${i.text}"`));
    out.canvasMenu = { btn: cvBtn, items };
    await shot(page, 'M-192-画布下拉-列表.png');
    out.shot2 = 'M-192-画布下拉-列表.png';
    await page.keyboard.press('Escape'); await page.waitForTimeout(1500);
  }

  // ═══ 3. 节点星级入口到底在哪
  console.log('\n--- BF-3 找节点星级的入口 ---');
  // 3a. 节点卡片上有没有星
  const starsOnCard = await page.evaluate(() => {
    const hits = [];
    for (const n of document.querySelectorAll('.react-flow__node')) {
      const els = [...n.querySelectorAll('*')].filter((e) => {
        const t = (e.innerText || e.textContent || '').trim();
        return /^[★☆]{1,5}$/.test(t) || /^[0-5]★$/.test(t);
      });
      if (els.length) hits.push({ id: n.getAttribute('data-id'),
        marks: els.map((e) => (e.innerText || e.textContent || '').trim()) });
    }
    return hits;
  });
  console.log(`  节点卡片上的星级元素：${starsOnCard.length} 个节点命中`, JSON.stringify(starsOnCard).slice(0, 300));
  out.stars = { onCard: starsOnCard };

  // 3b. 选中一个节点后，参数条/浮动层里有没有星级
  const sel = await page.evaluate(() => {
    const n = document.querySelector('.react-flow__node');
    if (!n) return { err: '没有节点' };
    const r = n.getBoundingClientRect();
    for (let fy = 0.2; fy <= 0.8; fy += 0.15) for (let fx = 0.06; fx <= 0.95; fx += 0.06) {
      const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
      const o = document.elementFromPoint(x, y);
      if (o && o.closest('.react-flow__node') === n) return { x, y, id: n.getAttribute('data-id') };
    }
    return { err: '没有独占点' };
  });
  if (sel.err) { console.log('  选中节点：', sel.err); out.stars.select = sel; }
  else {
    await page.mouse.click(sel.x, sel.y); await page.waitForTimeout(2400);
    // 选中后把整个页面里所有「看起来像星级」的元素全列出来
    const starish = await page.evaluate(() => {
      const ok = (e) => !['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE'].includes(e.tagName);
      return [...document.querySelectorAll('body *')].filter(ok)
        .filter((e) => { const r = e.getBoundingClientRect();
          return r.width > 0 && r.width < 30 && r.height > 0 && r.height < 30; })
        .map((e) => ({ tag: e.tagName, cls: (e.className || '').toString().slice(0, 40),
          text: (e.innerText || e.textContent || '').trim().slice(0, 12),
          aria: e.getAttribute('aria-label'), title: e.getAttribute('title'),
          rect: (() => { const r = e.getBoundingClientRect();
            return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; })(),
          parentText: (e.parentElement?.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30) }))
        .filter((e) => /★|星|rating|star/i.test(`${e.text}${e.aria || ''}${e.title || ''}${e.cls}`));
    });
    console.log(`  选中后页面上「像星级」的元素 ${starish.length} 个：`);
    starish.slice(0, 10).forEach((e) => console.log(`    [${e.rect}] tag=${e.tag} "${e.text}" aria=${e.aria} cls=${e.cls} 父="${e.parentText}"`));
    out.stars.afterSelect = starish;
    // 读参数条/浮动层里所有可交互元素的无障碍名，看有没有「评级」
    const barNames = await page.evaluate(() => {
      const n = document.querySelector('.react-flow__node.selected');
      if (!n) return { err: '没有选中' };
      return [...n.querySelectorAll('button,[role="button"]')]
        .map((b) => ({ aria: b.getAttribute('aria-label'), title: b.getAttribute('title'),
          text: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 16) }));
    });
    console.log('  选中节点内的按钮：', JSON.stringify(barNames).slice(0, 400));
    out.stars.selectedButtons = barNames;
    await shot(page, 'M-193-节点星级-入口探查.png');
    out.shot3 = 'M-193-节点星级-入口探查.png';
  }
  // 3c. 画布行菜单（资产管理列表里的「更多操作」）里有没有
  await page.keyboard.press('Escape'); await page.waitForTimeout(800);
  const dm = await page.evaluate(() => {
    const e = [...document.querySelectorAll('button,[role="button"]')]
      .find((x) => x.getAttribute('aria-label') === '资产管理');
    if (!e) return null;
    const r = e.getBoundingClientRect();
    return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) };
  });
  if (dm) {
    await page.mouse.click(dm.x, dm.y); await page.waitForTimeout(2400);
    const more = await page.evaluate(() => [...document.querySelectorAll('button,[role="button"]')]
      .filter((e) => { const r = e.getBoundingClientRect(); return r.x < 340 && r.width > 0 && r.height > 0; })
      .map((e) => { const r = e.getBoundingClientRect();
        return { aria: e.getAttribute('aria-label'), title: e.getAttribute('title'),
          text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 14),
          rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; })
      .filter((e) => /更多|操作|⋯|\.\.\./.test(`${e.aria || ''}${e.title || ''}${e.text}`)));
    console.log(`  抽屉里的「更多操作」按钮 ${more.length} 个`, JSON.stringify(more).slice(0, 200));
    if (more.length) {
      await page.mouse.click(more[0].rect[0] + more[0].rect[2] / 2, more[0].rect[1] + more[0].rect[3] / 2);
      await page.waitForTimeout(2000);
      const menu = await page.evaluate(() => [...document.querySelectorAll('body *')]
        .filter((e) => !['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE'].includes(e.tagName))
        .map((e) => { const r = e.getBoundingClientRect();
          return { text: (e.innerText || '').replace(/\s+/g, ' ').trim(),
            rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; })
        .filter((e) => e.rect[2] > 30 && e.rect[3] > 4 && e.rect[3] < 44 && e.text && e.text.length < 20)
        .slice(0, 20));
      console.log('  行菜单候选：', JSON.stringify(menu).slice(0, 400));
      out.stars.rowMenu = menu;
      await shot(page, 'M-193-节点星级-入口探查.png');
    }
    await page.keyboard.press('Escape'); await page.waitForTimeout(1000);
  }

  await logStep(B, {
    id: 'BF1-zoom-rows-canvas-menu-stars',
    title: '缩放菜单的三行动作 / 顶栏画布下拉 / 找节点星级入口',
    target: 'AP 验过缩放菜单的输入框与三档预设，但「放大/缩小/适合屏幕」三行当菜单项点会怎样、'
      + '以及点完菜单会不会自己关，一直没验（AP 恰恰踩过「点完第一档菜单关了，后两档在关着的菜单里找行」）。'
      + '另外两件只读盘点：顶栏「画布 N」下拉的完整列表、节点星级的入口到底在哪。',
    evidence: out,
    visible_text: JSON.stringify({ zoom: { scale0: out.zoom?.scale0, rows: out.zoom?.rows?.map((r) => ({ label: r.label, scaleChanged: r.scaleChanged, menuClosed: r.menuClosed })), restored: out.zoom?.restored },
      canvasMenu: { items: out.canvasMenu?.items?.length },
      stars: { onCard: out.stars?.onCard?.length, afterSelect: out.stars?.afterSelect?.length, rowMenu: out.stars?.rowMenu?.length } }).slice(0, 3000),
    shot: out.shot3 || out.shot2 || out.shot,
  });
  console.log('\nBF1 完成');
} finally {
  await browser.close();
}
