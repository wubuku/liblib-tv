// Batch BN1 — 风格广场：把「卡片」这件东西彻底解剖清楚，**全程不点任何卡片**。
//
// 手册里关于风格/特效广场还挂着的 📖：
//   ① 卡片上那个数字（`532.0w` / `1.1w` / `279` / `5900`）**是什么单位**；
//   ② 卡片上的 `⋯` 菜单**里有什么**（正文只写了「只读没点」）；
//   ③ 十个分类标签**各筛出什么**；
//   ④ 悬停浮出的那枚 ☆ **是什么**。
//
// ⛔ 本轮**一张卡片都不点**，理由是安全边界：特效广场那个数字量级像价格，
//    点了可能扣积分（余额 20），而手册自己都写着「是不是积分价格没点过」。
//    所以先只读，把「点它会发生什么」留给下一批 —— 前提是这轮读数能告诉我们值不值得点。
//
// 读数纪律（BM3 之后）：
//   · 每个交互都带 `executed`/`hit` 自证字段，**没执行就报未执行，不许报成「无反应」**；
//   · 每个「悬停读 tooltip」都先读**基线**（没悬停时的浮层数），点完再读，**只认增量**；
//   · 分类逐个点完**必须回到 `推荐`** 收尾，否则下一轮起点就变了。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBN1';
const { browser, page } = await launch();

const masks = () => page.evaluate(() => {
  const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
  return [...document.querySelectorAll('[role="tooltip"],.mantine-Tooltip-tooltip,[class*="Tooltip"],[class*="tooltip"]')]
    .filter((e) => !skip.has(e.tagName))
    .map((e) => { const r = e.getBoundingClientRect();
      return { t: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 120),
        rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        vis: getComputedStyle(e).visibility, op: getComputedStyle(e).opacity }; })
    .filter((x) => x.rect[2] > 0 && x.rect[3] > 0 && x.vis !== 'hidden' && x.op !== '0');
});

const clickAria = async (label, wait = 2200) => {
  const p = await page.evaluate((l) => {
    const e = [...document.querySelectorAll('button,[role="button"],a,[aria-label]')].find((x) => x.getAttribute('aria-label') === l);
    if (!e) return null; const r = e.getBoundingClientRect();
    if (r.width < 4) return null;
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, label);
  if (!p) return { executed: false, note: `找不到 aria-label=${label}` };
  await page.mouse.click(p[0], p[1]); await page.waitForTimeout(wait);
  return { executed: true, at: p };
};

const clickText = async (txt, wait = 2600, minW = 0) => {
  const p = await page.evaluate(([t, mw]) => {
    const seen = new Set();
    for (const e of document.querySelectorAll('div,button,span,li,a')) {
      if ((e.innerText || '').replace(/\s+/g, ' ').trim() !== t) continue;
      const r = e.getBoundingClientRect();
      if (r.width < 4 || r.height < 4 || r.width < mw) continue;
      const k = `${Math.round(r.x)}@${Math.round(r.y)}`; if (seen.has(k)) continue; seen.add(k);
      return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
    } return null; }, [txt, minW]);
  if (!p) return { executed: false, note: `找不到文字「${txt}」` };
  await page.mouse.click(p[0], p[1]); await page.waitForTimeout(wait);
  return { executed: true, at: p };
};

/** 广场的整体骨架：顶部标签 / 搜索框 / 分类标签 / 商用勾选 / 排序 / 卡片网格。 */
const skeleton = () => page.evaluate(() => {
  const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
  const vis = (e) => { const r = e.getBoundingClientRect();
    return r.width >= 4 && r.height >= 4 && getComputedStyle(e).visibility !== 'hidden'; };
  const box = [...document.querySelectorAll('div')].filter((e) => {
    const r = e.getBoundingClientRect();
    return r.width > 900 && r.height > 500 && vis(e); })
    .sort((a, b) => a.getBoundingClientRect().height * a.getBoundingClientRect().width
      - b.getBoundingClientRect().height * b.getBoundingClientRect().width)[0];
  if (!box) return { err: '找不到广场容器' };
  const r0 = box.getBoundingClientRect();
  const kids = [...box.querySelectorAll('*')].filter((e) => !skip.has(e.tagName) && vis(e));
  const uniq = [];
  for (const e of kids) {
    const r = e.getBoundingClientRect(); const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
    if (!t || t.length > 24) continue;
    if (kids.some((o) => o !== e && o.contains(e))) continue;      // 只留叶子
    const k = `${t}@${Math.round(r.y)}`;
    if (uniq.some((u) => u.k === k)) continue;
    uniq.push({ k, t, x: Math.round(r.x - r0.x), y: Math.round(r.y - r0.y),
      w: Math.round(r.width), h: Math.round(r.height), tag: e.tagName,
      cursor: getComputedStyle(e).cursor,
      role: e.getAttribute('role'), aria: e.getAttribute('aria-label') });
  }
  return { rect: [Math.round(r0.x), Math.round(r0.y), Math.round(r0.width), Math.round(r0.height)], leaves: uniq };
});

/** 卡片解剖：对前 3 张，逐个列出所有「可点」的子孙。 */
const cardAnatomy = (n = 3) => page.evaluate((cnt) => {
  const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
  // 卡片 = 含预览图、且自身或其祖先有 cursor:pointer 的最小单元
  const imgs = [...document.querySelectorAll('img')].filter((i) => { const r = i.getBoundingClientRect();
    return r.width > 80 && r.height > 80 && getComputedStyle(i).visibility !== 'hidden'; });
  const cards = [];
  for (const im of imgs) {
    let e = im;
    for (let i = 0; i < 8 && e; i++) {
      const r = e.getBoundingClientRect();
      if (r.width > 140 && r.width < 400 && r.height > 140 && r.height < 460) { cards.push(e); break; }
      e = e.parentElement;
    }
  }
  // 去重（同一个卡被 img 和兄弟 img 各推出一次）
  const uniq = [...new Set(cards)].slice(0, cnt);
  return uniq.map((c) => {
    const r = c.getBoundingClientRect();
    const clickables = [...c.querySelectorAll('*'), c].filter((e) => !skip.has(e.tagName)).map((e) => {
      const rr = e.getBoundingClientRect(); const cs = getComputedStyle(e);
      return { tag: e.tagName, rect: [Math.round(rr.x), Math.round(rr.y), Math.round(rr.width), Math.round(rr.height)],
        text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 40), cursor: cs.cursor,
        role: e.getAttribute('role'), aria: e.getAttribute('aria-label'), title: e.getAttribute('title'),
        hasSvg: !!e.querySelector('svg'), paths: e.querySelectorAll('path').length,
        isBtn: e.tagName === 'BUTTON', cls: (typeof e.className === 'string' ? e.className : '').slice(0, 70) };
    }).filter((x) => x.cursor === 'pointer' || x.role === 'button' || x.isBtn || x.aria || x.title);
    return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      cls: (typeof c.className === 'string' ? c.className : '').slice(0, 110),
      text: (c.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 120),
      clickables };
  });
}, n);

/** 数卡片：取解剖里认定的卡片根，再数一遍有多少个。 */
const countCards = () => page.evaluate(() => {
  const imgs = [...document.querySelectorAll('img')].filter((i) => { const r = i.getBoundingClientRect();
    return r.width > 80 && r.height > 80 && getComputedStyle(i).visibility !== 'hidden'; });
  const set = new Set();
  for (const im of imgs) { let e = im;
    for (let i = 0; i < 8 && e; i++) { const r = e.getBoundingClientRect();
      if (r.width > 140 && r.width < 400 && r.height > 140 && r.height < 460) { set.add(e); break; }
      e = e.parentElement; } }
  return { cards: set.size, imgs: imgs.length };
});

const at = (x, y, w, h) => page.evaluate(([a, b, c, d]) => {
  const e = document.elementFromPoint(a, b);
  return e ? { tag: e.tagName, text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 40),
    cls: (typeof e.className === 'string' ? e.className : '').slice(0, 60),
    aria: e.getAttribute('aria-label'), title: e.getAttribute('title') } : null; }, [x, y, w, h]);

/** 「仅看可商用」那个勾选框的当前 checked —— 单独抽出来，免得内联 find 写串。 */
const cbChecked = () => page.evaluate(() => {
  const e = [...document.querySelectorAll('input[type="checkbox"],[role="checkbox"]')]
    .find((x) => { const r = x.getBoundingClientRect(); return r.width > 4 && r.height > 4; });
  return e ? (e.checked !== undefined ? e.checked : e.getAttribute('aria-checked')) : null;
});

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1600);
  await fitView(page); await page.waitForTimeout(1600);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1000);
  await beginBatch(B, { note: '风格广场只读解剖：不点任何卡片' });
  const out = {};

  // ── 打开
  out.lib = await clickAria('素材库', 2400);
  out.style = await clickText('风格库', 3600);
  console.log(`打开：素材库 ${JSON.stringify(out.lib)} / 风格库 ${JSON.stringify(out.style)}`);
  const sk = await skeleton();
  out.skeleton = sk;
  if (sk.err) { console.log('⛔ ' + sk.err); throw new Error('no plaza'); }
  console.log(`\n═══ 广场容器 ${JSON.stringify(sk.rect)}，叶子元素 ${sk.leaves.length} 个 ═══`);
  sk.leaves.slice(0, 40).forEach((l) => console.log(`   ${l.tag} [${l.x},${l.y},${l.w}×${l.h}] cursor=${l.cursor} "${l.t}"${l.aria ? ' aria=' + l.aria : ''}`));

  // ── 卡片解剖
  const an = await cardAnatomy(3);
  out.cards = an;
  console.log(`\n═══ 卡片解剖（前 ${an.length} 张）═══`);
  for (const [i, c] of an.entries()) {
    console.log(`  ── 卡 ${i + 1} ${JSON.stringify(c.rect)} cls="${c.cls}"`);
    console.log(`     文字："${c.text}"`);
    c.clickables.forEach((k) => console.log(`     · <${k.tag}> [${k.rect}] cursor=${k.cursor}${k.role ? ' role=' + k.role : ''}${k.aria ? ' aria=' + k.aria : ''}${k.title ? ' title=' + k.title : ''} svg=${k.hasSvg}/${k.paths} "${k.text}"`));
  }
  const n0 = await countCards();
  console.log(`  卡片总数（起手）：${JSON.stringify(n0)}`);
  out.count0 = n0;
  await shot(page, 'M-224-风格广场-卡片解剖.png');
  out.shot0 = 'M-224-风格广场-卡片解剖.png';

  // ── ① 数字的 tooltip：先读基线，再悬停
  console.log('\n═══ ① 卡片上那个数字，悬停会说什么 ═══');
  const numEl = await page.evaluate(() => {
    const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
    for (const e of document.querySelectorAll('body *')) {
      if (skip.has(e.tagName)) continue;
      const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
      if (!/^\d[\d.]*w?$/.test(t)) continue;
      const r = e.getBoundingClientRect();
      if (r.width < 12 || r.height < 8) continue;
      return { t, at: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
        rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        title: e.getAttribute('title'), aria: e.getAttribute('aria-label'), cursor: getComputedStyle(e).cursor };
    } return null;
  });
  console.log(`  数字元素：${JSON.stringify(numEl)}`);
  if (!numEl) { out.numTip = { err: '没找到纯数字元素' }; }
  else {
    await page.mouse.move(700, 60); await page.waitForTimeout(900);
    const base = await masks();
    console.log(`  基线浮层数：${base.length} ${JSON.stringify(base.map((b) => b.t))}`);
    await page.mouse.move(numEl.at[0], numEl.at[1]); await page.waitForTimeout(1800);
    const hov = await masks();
    const gained = hov.filter((h) => !base.some((b) => b.t === h.t));
    console.log(`  悬停后浮层数：${hov.length}；新增：${JSON.stringify(gained.map((g) => g.t))}`);
    console.log(`  元素自身 title=${JSON.stringify(numEl.title)} aria=${JSON.stringify(numEl.aria)} cursor=${numEl.cursor}`);
    out.numTip = { el: numEl, baseline: base, hover: hov, gained: gained.map((g) => g.t) };
  }

  // ── ② 悬停浮出的 ☆
  console.log('\n═══ ② 悬停卡片右上角那枚 ☆ ═══');
  if (an[0]) {
    const [cx, cy, cw] = an[0].rect;
    await page.mouse.move(700, 60); await page.waitForTimeout(800);
    const starBefore = await page.evaluate(() => [...document.querySelectorAll('svg,path')]
      .map((e) => { const r = e.getBoundingClientRect();
        return { d: (e.getAttribute && (e.getAttribute('d') || '')).slice(0, 30), r,
          op: getComputedStyle(e.parentElement || e).opacity }; })
      .filter((x) => x.r.width >= 8 && x.r.width <= 26 && x.r.height >= 8 && x.r.height <= 26).length);
    await page.mouse.move(cx + cw / 2, cy + 60); await page.waitForTimeout(1600);
    const starInfo = await page.evaluate(([bx, by, bw]) => {
      const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
      return [...document.querySelectorAll('body *')].filter((e) => !skip.has(e.tagName)).map((e) => {
        const r = e.getBoundingClientRect();
        if (r.x < bx - 4 || r.x + r.width > bx + bw + 4 || r.y < by - 10 || r.y > by + 140) return null;
        const op = getComputedStyle(e).opacity;
        if (parseFloat(op) < 0.9) return null;
        const svg = e.querySelector('svg') || (e.tagName === 'svg' ? e : null);
        if (!svg) return null;
        return { tag: e.tagName, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
          aria: e.getAttribute('aria-label'), title: e.getAttribute('title'), cursor: getComputedStyle(e).cursor,
          paths: svg.querySelectorAll('path').length,
          d: (svg.querySelector('path')?.getAttribute('d') || '').slice(0, 44) };
      }).filter(Boolean).slice(0, 12);
    }, [cx, cy, cw]);
    console.log(`  未悬停时卡内可见 svg：${starBefore} 个`);
    console.log(`  悬停后卡内可见 svg 元素：`);
    starInfo.forEach((s) => console.log(`     <${s.tag}> [${s.rect}] cursor=${s.cursor}${s.aria ? ' aria=' + s.aria : ''}${s.title ? ' title=' + s.title : ''} path=${s.paths} d="${s.d}"`));
    const hv2 = await masks();
    console.log(`  悬停后浮层：${JSON.stringify(hv2.map((m) => m.t))}`);
    out.star = { before: starBefore, after: starInfo, tooltips: hv2.map((m) => m.t) };
    await shot(page, 'M-225-风格卡片-悬停浮出星标.png');
    out.shot1 = 'M-225-风格卡片-悬停浮出星标.png';
  }

  // ── ③ `⋯` 菜单（点菜单是安全的，不等于点卡片）
  console.log('\n═══ ③ `⋯` 菜单里有什么 ═══');
  if (an[0] && an[0].clickables.length) {
    const dots = an[0].clickables.filter((k) => /…|\.\.\./.test(k.text) || (k.hasSvg && k.w <= 32 && k.h <= 32 && !k.text));
    const target = dots[0] || an[0].clickables.find((k) => k.w <= 32 && k.h <= 32);
    console.log(`  选中目标：${JSON.stringify(target && { rect: target.rect, text: target.text, aria: target.aria })}`);
    out.dotsCand = dots.length;
    if (target) {
      const b4 = (await masks()).length;
      await page.mouse.click(Math.round(target.rect[0] + target.rect[2] / 2), Math.round(target.rect[1] + target.rect[3] / 2));
      await page.waitForTimeout(1800);
      const menu = await page.evaluate(() => {
        const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
        return [...document.querySelectorAll('[role="menu"],[class*="Menu"],[class*="Dropdown"],[class*="Popover"]')]
          .filter((e) => !skip.has(e.tagName))
          .map((e) => { const r = e.getBoundingClientRect();
            return { cls: (typeof e.className === 'string' ? e.className : '').slice(0, 50),
              rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
              text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 160),
              items: [...e.querySelectorAll('*')].filter((x) => !skip.has(x.tagName))
                .map((x) => (x.innerText || '').replace(/\s+/g, ' ').trim())
                .filter((t) => t && t.length < 14).filter((t, i, a) => a.indexOf(t) === i) }; })
          .filter((x) => x.rect[2] > 40 && x.rect[3] > 20 && x.text);
      });
      console.log(`  点完浮出 ${menu.length} 个浮层：`);
      menu.forEach((m) => console.log(`     [${m.rect}] cls="${m.cls}"\n        文字："${m.text}"\n        叶子项：${JSON.stringify(m.items)}`));
      out.dotsMenu = { baselineTooltips: b4, layers: menu };
      await shot(page, 'M-226-风格卡片-三点菜单.png');
      out.shot2 = 'M-226-风格卡片-三点菜单.png';
      await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
    }
  }

  // ── ④ 十个分类逐个筛
  console.log('\n═══ ④ 十个分类标签逐个点，看各筛出什么 ═══');
  const cats = ['推荐', '摄影写真', '电商营销', '动漫游戏', '风格插画', '平面设计', '建筑及室内设计', '创意玩法', '文创周边', '小说推文'];
  const perCat = [];
  for (const c of cats) {
    const before = await countCards();
    const r = await clickText(c, 2200, 40);
    const after = await countCards();
    const first = await page.evaluate(() => {
      const imgs = [...document.querySelectorAll('img')].filter((i) => { const r = i.getBoundingClientRect();
        return r.width > 80 && r.height > 80 && getComputedStyle(i).visibility !== 'hidden'; });
      if (!imgs.length) return null;
      const r = imgs[0].getBoundingClientRect();
      let e = imgs[0];
      for (let i = 0; i < 8 && e; i++) { const rr = e.getBoundingClientRect();
        if (rr.width > 140 && rr.width < 400 && rr.height > 140 && rr.height < 460) break; e = e.parentElement; }
      return (e ? (e.innerText || '') : (imgs[0].alt || '')).replace(/\s+/g, ' ').trim().slice(0, 60);
    });
    console.log(`  ${c}：点前 ${before.cards} → 点后 ${after.cards} 张（executed=${r.executed}）首张："${first}"`);
    perCat.push({ cat: c, before: before.cards, after: after.cards, first, executed: r.executed });
  }
  out.perCat = perCat;

  // ── ⑤ 仅看可商用
  console.log('\n═══ ⑤ 「仅看可商用」勾选 ═══');
  await clickText('推荐', 2200, 40);
  const cb0 = await countCards();
  const cbP = await page.evaluate(() => {
    const e = [...document.querySelectorAll('input[type="checkbox"],[role="checkbox"]')]
      .find((x) => { const r = x.getBoundingClientRect(); return r.width > 4 && r.height > 4; });
    if (!e) return null; const r = e.getBoundingClientRect();
    return { at: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
      checked: e.checked, aria: e.getAttribute('aria-label'),
      cls: (typeof e.className === 'string' ? e.className : '').slice(0, 60) }; });
  console.log(`  勾选框：${JSON.stringify(cbP)}（点前 ${cb0.cards} 张）`);
  if (cbP) {
    await page.mouse.click(cbP.at[0], cbP.at[1]); await page.waitForTimeout(2400);
    const cb1 = await countCards();
    const now = await cbChecked();
    console.log(`  点后 ${cb1.cards} 张；checked=${now}（点前 ${cbP.checked}）`);
    out.commercial = { before: cb0.cards, after: cb1.cards, checkedBefore: cbP.checked, checkedAfter: now, box: cbP };
    if (now !== cbP.checked) {
      await page.mouse.click(cbP.at[0], cbP.at[1]); await page.waitForTimeout(2000);
      console.log(`  已改回：checked=${await cbChecked()}`);
    }
  }

  // ── ⑥ 排序下拉
  console.log('\n═══ ⑥ 排序下拉里有什么 ═══');
  const srt = await page.evaluate(() => {
    for (const e of document.querySelectorAll('div,button,span')) {
      const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
      if (!/^(全部|最新|最热|价格).*[▾▼⌄]?$/.test(t) && t !== '全部') continue;
      const r = e.getBoundingClientRect();
      if (r.width < 40 || r.height < 12) continue;
      return { t, at: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
        rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
    } return null; });
  console.log(`  排序按钮：${JSON.stringify(srt)}`);
  if (srt) {
    await page.mouse.click(srt.at[0], srt.at[1]); await page.waitForTimeout(1800);
    const opts = await page.evaluate(() => [...document.querySelectorAll('div,li,span')]
      .map((e) => { const r = e.getBoundingClientRect();
        return { t: (e.innerText || '').replace(/\s+/g, ' ').trim(), r }; })
      .filter((x) => x.t && x.t.length < 12 && x.r.width > 60 && x.r.height > 14 && x.r.height < 50 && x.r.width < 400)
      .filter((x) => /^(全部|最新|最热|价格|最多使用|综合|人气)/.test(x.t))
      .map((x) => x.t).filter((t, i, a) => a.indexOf(t) === i));
    console.log(`  浮出的选项：${JSON.stringify(opts)}`);
    out.sort = { button: srt, options: opts };
    await shot(page, 'M-227-风格广场-排序下拉.png');
    out.shot3 = 'M-227-风格广场-排序下拉.png';
    await page.keyboard.press('Escape'); await page.waitForTimeout(1000);
  }

  // ── ⑦ 收尾：回推荐 + 关广场
  await clickText('推荐', 1800, 40);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1600);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1600);
  const nodeN = await page.evaluate(() => document.querySelectorAll('.react-flow__node').length);
  console.log(`\n═══ 收尾：节点 ${nodeN} 个（全程未点卡片，应与开局 11 一致）═══`);
  out.finalNodes = nodeN;

  await logStep(B, {
    id: 'BN1-style-plaza-anatomy',
    title: '风格广场卡片解剖 + 数字悬停 + ⋯ 菜单 + 十个分类各筛出什么',
    target: '⛔ **全程不点任何卡片** —— 特效广场那个数字量级像价格，点了可能扣积分（余额 20），'
      + '而手册自己写着「是不是积分价格没点过」。本轮先把卡片这件东西读清楚，值不值得点留给下一批。'
      + '悬停读 tooltip 一律先读基线、只认增量；十个分类点完必须回 `推荐` 收尾。',
    evidence: out,
    visible_text: JSON.stringify({ 卡片: out.cards?.map?.((c) => c.text), 张数: out.count0,
      数字: out.numTip, 星标: out.star, 三点菜单: out.dotsMenu?.layers, 分类: out.perCat,
      商用: out.commercial, 排序: out.sort, 收尾节点数: out.finalNodes }).slice(0, 3000),
    shot: out.shot0,
  });
  console.log('\nBN1 完成');
} catch (e) {
  console.log('⛔ 中止：' + e.message);
} finally {
  await browser.close();
}
