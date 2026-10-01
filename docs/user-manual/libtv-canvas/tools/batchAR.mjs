// Batch AR —— 补两处「只有一句结论、没有控件级证据」的地方：
//
//   AR1  行菜单「在新窗口打开」到底开在哪
//        手册里只把它列成四项之一，从没点过。**开新窗口是不可逆的对外动作吗？不是** ——
//        同一张画布、同一份登录态，地址栏不变。唯一要防的是它开成新标签页之后
//        我们跑去操作那个新页面、或者留下野标签，所以**全程用 context 拦截 popup**，
//        读完 URL 立刻关掉，一个字都不点。
//
//   AR2  「发布与分享」面板里到底有几个控件
//        A5 那张截图是 Batch 时代的，只读到两段说明文案。
//        这次把面板里**每一个** button / input / switch / tab 逐个读出来：
//        文案、aria、坐标、disabled 态、hover title。
//        **发布按钮和分享链接按钮一个都不点** —— 前者让作品对外可见，后者生成可访问的 URL。
//        只读。
//
// 判据：
//   · 「在新窗口打开」可能是 `target=_blank`（真 popup）也可能是 `window.open`，
//     **两者都能被 context 的 page 事件捕获**；如果一个都没捕获到，
//     说明它可能是「当前页跳转」或者「压根没反应」—— 这三种要分得开，
//     所以同时监听 popup / 原页 URL 变化 / 页面数变化三件事。
//   · 面板是懒挂载的，**每次读之前重新定位**，不复用上一次坐标。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { openDropdown } from './canvas-dropdown.mjs';

const SPACE = '10354929';
const B = 'batchAR';
const { browser, ctx, page } = await launch();

/** 面板/浮层的通用读法：只认「真的有面积」的容器。 */
const panels = () => page.evaluate(() => [...document.querySelectorAll('div,section,aside')]
  .filter((e) => {
    const r = e.getBoundingClientRect();
    if (r.width < 160 || r.height < 80) return false;
    const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
    return /发布|分享|链接|画布/.test(t.slice(0, 400)) && t.length < 900;
  })
  .map((e) => {
    const r = e.getBoundingClientRect();
    const cs = getComputedStyle(e);
    return {
      cls: (e.className || '').toString().slice(0, 90),
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      pos: cs.position, z: cs.zIndex,
      text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 400),
      depth: (() => { let d = 0, n = e; while ((n = n.parentElement)) d += 1; return d; })(),
    };
  })
  .sort((a, b) => a.depth - b.depth));

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4000 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '「在新窗口打开」实按（拦截 popup）+ 发布与分享面板逐控件只读' });

  // ─────────────────────────────────────────────────────────
  // AR1 「在新窗口打开」
  // ─────────────────────────────────────────────────────────
  const urlBefore = page.url();
  const pagesBefore = ctx.pages().length;

  // 三路同时监听，才能区分「真开新窗」/「当前页跳转」/「压根没反应」
  const popups = [];
  const onPopup = (p) => popups.push(p);
  ctx.on('page', onPopup);
  const dialogs = [];
  page.on('dialog', (d) => { dialogs.push({ type: d.type(), msg: d.message() }); d.dismiss().catch(() => {}); });

  await openDropdown(page, 1400);
  const hit = await page.evaluate(() => {
    const pop = [...document.querySelectorAll('[class*="Menu-dropdown"],[class*="Popover-dropdown"],[class*="Dropdown-dropdown"]')]
      .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 120 && r.height > 60; })[0];
    if (!pop) return { err: '画布下拉没打开' };
    const more = [...pop.querySelectorAll('button,[role="button"]')]
      .filter((b) => b.getAttribute('aria-label') === '更多操作')[0];
    if (!more) return { err: '没有 aria-label="更多操作" 的按钮' };
    const r = more.getBoundingClientRect();
    return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2),
      row: (more.previousElementSibling?.innerText || '').trim() };
  });
  if (hit.err) throw new Error('AR1 前置失败: ' + hit.err);
  await page.mouse.click(hit.cx, hit.cy); await page.waitForTimeout(1600);

  const openInNew = await page.evaluate(() => {
    // 「在新窗口打开」在行菜单浮层里。**按文案找，不按坐标** —— 浮层坐标每帧都在变。
    const all = [...document.querySelectorAll('div,li,button,span,a')];
    const el = all.filter((e) => (e.innerText || '').trim() === '在新窗口打开')
      .sort((a, b) => {
        const ra = a.getBoundingClientRect(), rb = b.getBoundingClientRect();
        return (ra.width * ra.height) - (rb.width * rb.height);   // 取最小的那个，通常就是行本身
      })[0];
    if (!el) return { err: '菜单里找不到「在新窗口打开」' };
    const r = el.getBoundingClientRect();
    const covered = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2);
    return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2),
      tag: el.tagName, tagOf: el.closest('a') ? 'A' : (el.closest('button') ? 'BUTTON' : 'div'),
      href: el.closest('a')?.getAttribute('href') || null,
      target: el.closest('a')?.getAttribute('target') || null,
      onClick: el.closest('a')?.getAttribute('onclick') || null,
      coveredBy: covered ? (covered.tagName + '.' + (covered.className || '').toString().slice(0, 40)) : null,
      coveredIsSelf: covered ? el.contains(covered) || covered.contains(el) : false };
  });
  console.log('AR1 菜单项:', JSON.stringify(openInNew));

  let afterClick = { err: '没点到' };
  if (!openInNew.err) {
    await shot(page, 'M-121-画布下拉-在新窗口打开项.png');
    await page.mouse.click(openInNew.cx, openInNew.cy);
    await page.waitForTimeout(3500);
    const pagesAfter = ctx.pages().length;
    afterClick = {
      popupsCaught: popups.length,
      popupUrls: popups.map((p) => { try { return p.url(); } catch { return '?'; } }),
      popupTitles: await Promise.all(popups.map(async (p) => { try { return await p.title(); } catch { return '?'; } })),
      pagesBefore, pagesAfter,
      currentUrl: page.url(),
      currentUrlChanged: page.url() !== urlBefore,
      dialogs,
    };
    // 读完立刻关掉新开的页签，绝不去操作它
    for (const p of popups) { await p.close().catch(() => {}); }
  }
  ctx.off('page', onPopup);
  console.log('AR1 点完:', JSON.stringify(afterClick));

  // ─────────────────────────────────────────────────────────
  // AR2 发布与分享面板：逐控件只读，**一个危险按钮都不点**
  // ─────────────────────────────────────────────────────────
  await page.keyboard.press('Escape').catch(() => {});
  await page.waitForTimeout(900);

  const trigger = await page.evaluate(() => {
    const b = [...document.querySelectorAll('button,[role="button"]')]
      .find((e) => /发布与分享|发布\s*与\s*分享/.test((e.innerText || e.getAttribute('aria-label') || '').trim()));
    if (!b) return null;
    const r = b.getBoundingClientRect();
    return { t: (b.innerText || b.getAttribute('aria-label') || '').trim(),
      aria: b.getAttribute('aria-label'),
      cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
  });
  console.log('AR2 触发点:', JSON.stringify(trigger));

  let share = { err: '没找到「发布与分享」触发点' };
  if (trigger) {
    await page.mouse.click(trigger.cx, trigger.cy);
    await page.waitForTimeout(2600);
    await shot(page, 'M-122-发布与分享-面板全貌.png');

    const before = await panels();
    share = await page.evaluate(() => {
      // 选**最外层**那个（深度最小）匹配面板 —— 之前 §14 记过「取最小的锚点会爬过头」
      const cands = [...document.querySelectorAll('div,section,aside')].filter((e) => {
        const r = e.getBoundingClientRect();
        if (r.width < 200 || r.height < 120) return false;
        const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
        return /发布你的作品|分享链接/.test(t) && t.length < 900;
      });
      if (!cands.length) return { err: '面板没打开' };
      let best = cands[0], bd = 1e9;
      for (const e of cands) {
        let d = 0, n = e; while ((n = n.parentElement)) d += 1;
        if (d < bd) { bd = d; best = e; }
      }
      const r = best.getBoundingClientRect();
      const inRect = (el) => { const q = el.getBoundingClientRect();
        return q.width > 0 && q.height > 0 && q.x >= r.x - 2 && q.y >= r.y - 2
          && q.x + q.width <= r.x + r.width + 2 && q.y + q.height <= r.y + r.height + 2; };
      const rd = (el) => { const q = el.getBoundingClientRect();
        return [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)]; };
      const safe = (el) => { const q = el.getBoundingClientRect();
        if (!inRect(el)) return '不在面板内';
        const hitEl = document.elementFromPoint(q.x + q.width / 2, q.y + q.height / 2);
        return hitEl && (el.contains(hitEl) || hitEl.contains(el)) ? null : `被 ${hitEl ? hitEl.tagName : 'null'} 挡住`; };
      return {
        rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        cls: (best.className || '').toString().slice(0, 100),
        text: (best.innerText || '').replace(/\s+/g, ' ').trim(),
        // 只读：这只是枚举，不是点击
        buttons: [...best.querySelectorAll('button,[role="button"],[role="switch"]')].filter(inRect).map((b) => ({
          t: (b.innerText || '').replace(/\s+/g, ' ').trim(),
          aria: b.getAttribute('aria-label'),
          title: b.getAttribute('title'),
          role: b.getAttribute('role'),
          disabled: b.disabled === true || b.getAttribute('aria-disabled') === 'true'
            || getComputedStyle(b).opacity === '0.4',
          opacity: getComputedStyle(b).opacity,
          rect: rd(b),
          covered: safe(b),
        })),
        inputs: [...best.querySelectorAll('input,textarea')].filter(inRect).map((i) => ({
          type: i.type, aria: i.getAttribute('aria-label'), ph: i.placeholder, v: i.value,
          readOnly: i.readOnly, rect: rd(i), covered: safe(i),
        })),
        links: [...best.querySelectorAll('a')].filter(inRect).map((a) => ({
          t: (a.innerText || '').trim(), href: a.getAttribute('href'), target: a.getAttribute('target'),
        })),
        // 有没有 tab / 分段控件 / 开关
        tabs: [...best.querySelectorAll('[role="tab"],[role="tablist"]')].filter(inRect).map((t) => ({
          role: t.getAttribute('role'), t: (t.innerText || '').replace(/\s+/g, ' ').trim(), rect: rd(t),
        })),
        checkboxLike: [...best.querySelectorAll('input[type="checkbox"],[role="checkbox"],[role="switch"]')].filter(inRect)
          .map((c) => ({ type: c.type, checked: c.checked, rect: rd(c) })),
      };
    });
    share.outerCandidates = before.map((p) => ({ rect: p.rect, depth: p.depth, text: p.text.slice(0, 90) }));
  }
  console.log('AR2 面板:', JSON.stringify(share).slice(0, 2600));

  // 悬停读 title（**hover 不是点击**，安全）
  const hovers = [];
  for (const b of (share.buttons || []).slice(0, 6)) {
    if (b.covered) continue;
    await page.mouse.move(b.rect[0] + b.rect[2] / 2, b.rect[1] + b.rect[3] / 2);
    await page.waitForTimeout(900);
    const tip = await page.evaluate(() => {
      const t = [...document.querySelectorAll('[role="tooltip"],[class*="Tooltip-tooltip"],[class*="Tooltip-body"]')]
        .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 4 && r.height > 4; });
      return t.length ? t.map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim()).join(' | ') : null;
    });
    hovers.push({ btn: b.t || b.aria, tip });
    console.log('AR2 hover:', JSON.stringify(hovers[hovers.length - 1]));
  }
  share.hoverTitles = hovers;

  // **关面板：不按 Esc**（§15 的规矩，Esc 会连带改别的东西），点同一个触发按钮
  if (trigger) {
    await page.mouse.click(trigger.cx, trigger.cy);
    await page.waitForTimeout(1600);
    share.closedByReclick = !(await panels()).some((p) => /发布你的作品|分享链接/.test(p.text));
  }
  await page.waitForTimeout(600);
  await shot(page, 'M-123-发布与分享-收尾.png');

  await logStep(B, {
    id: 'AR1-new-window', title: '「在新窗口打开」实按（拦截 popup）+ 发布与分享面板逐控件只读',
    target: '实按行菜单第一项并三路监听（原页 URL / popup / 对话框）；把发布面板里每个控件的文案、aria、disabled、遮挡情况读出来，**但不点发布、不点分享链接**',
    evidence: { row: hit.row, menuItem: openInNew, urlBefore, afterClick, trigger, share },
    visible_text: `行菜单项「在新窗口打开」读数：${JSON.stringify(openInNew)}。`
      + `点完三路监听：${JSON.stringify(afterClick)}。`
      + `\n\n发布与分享面板：${JSON.stringify(share).slice(0, 1200)}`,
    shot: 'M-122-发布与分享-面板全貌.png',
  });
  console.log('AR 完成');
} finally {
  await browser.close();
}
