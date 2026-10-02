// Batch BN2 — 风格广场重做。**BN1 的四处判据都是错的，本轮逐条修。**
//
// BN1 判了什么、错在哪（这是本轮的主要价值，不是广场本身）：
//
//  ① ⛔ **卡片根找错了**。BN1 从 `img` 本身开始往上走，而 `img` 自己就满足
//     `140<w<400 && 140<h<460`，所以「卡片」= 那张预览图，文字当然是空的、`⋯` 当然找不到。
//     → 本轮从 **`img.parentElement`** 起走，且要求 `innerText` **非空**才认作卡片。
//     ⭐ 一般教训：向上爬的循环**起点错了**，后面所有字段全空，而且**不报错**。
//  ② ⛔ **数字元素找的是顶栏的积分余额**。BN1 用 `^\d[\d.]*w?$` 全页扫，
//     第一个命中是右上角那个 `20`（`[1334,8,58,32]`）—— 余额，不是卡片数字。
//     → 本轮**所有查询都限定在广场面板内**（锚点：占位符 `搜索风格名称、作者`）。
//  ③ ⛔ **`masks()` 从没被阳性对照验过能不能用**。它全程读到 0 个浮层，
//     于是「悬停数字没 tooltip」这句话**没有证据**（可能压根没有浮层，也可能是选择器不对）。
//     → 本轮给两个对照：**① 合成一个 `role="tooltip"` 塞进去**（验选择器本身）；
//     **② 像素对照**（悬停前后裁同一块比 sha256）。
//  ④ ⛔ **分类筛选零分辨力**。BN1 十个分类全读到「12 张」—— 但广场是**滚动网格**，
//     12 只是**视口内渲染出来的张数**，与该分类有多少条无关。
//     → 本轮改读**前 3 张卡的名称/作者/数字**当判别式；并**明确报出「张数不可当判据」**。
//
// ⛔ 仍然**不点任何卡片**。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';
import { createHash } from 'node:crypto';
import { resolve } from 'node:path';

const SPACE = '10354929';
const B = 'batchBN2';
const SHOTS = resolve(import.meta.dirname, '../screenshots');
const { browser, page } = await launch();

const clickAria = async (label, wait = 2400) => {
  const p = await page.evaluate((l) => {
    const e = [...document.querySelectorAll('button,[role="button"],a,[aria-label]')].find((x) => x.getAttribute('aria-label') === l);
    if (!e) return null; const r = e.getBoundingClientRect();
    if (r.width < 4) return null;
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, label);
  if (!p) return { executed: false, note: `找不到 aria-label=${label}` };
  await page.mouse.click(p[0], p[1]); await page.waitForTimeout(wait);
  return { executed: true, at: p };
};
const clickText = async (txt, wait = 2400, minW = 0) => {
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

/** ⭐ 面板：以占位符 `搜索风格名称、作者` 的 input 为锚，向上找到那块深色面板。 */
const panel = () => page.evaluate(() => {
  const inp = [...document.querySelectorAll('input')].find((i) => (i.placeholder || '').includes('搜索风格'));
  if (!inp) return null;
  const ir = inp.getBoundingClientRect();
  let e = inp, best = null;
  for (let i = 0; i < 12 && e; i++) {
    const r = e.getBoundingClientRect();
    if (r.width > 900 && r.height > 400) { best = { e, r }; break; }
    e = e.parentElement;
  }
  if (!best) return { err: '从搜索框往上找不到面板' };
  return { rect: [Math.round(best.r.x), Math.round(best.r.y), Math.round(best.r.width), Math.round(best.r.height)],
    searchRect: [Math.round(ir.x), Math.round(ir.y), Math.round(ir.width), Math.round(ir.height)] };
});

/** 卡片：从 `img.parentElement` 起往上爬，要求 innerText 非空。 */
const cards = (n = 0) => page.evaluate((cnt) => {
  const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
  const pIn = [...document.querySelectorAll('input')].find((i) => (i.placeholder || '').includes('搜索风格'));
  if (!pIn) return { err: '广场没开' };
  let p = pIn;
  for (let i = 0; i < 12 && p; i++) { const r = p.getBoundingClientRect();
    if (r.width > 900 && r.height > 400) break; p = p.parentElement; }
  const pr = p.getBoundingClientRect();
  const inPanel = (r) => r.x >= pr.x - 4 && r.y >= pr.y - 4 && r.x + r.width <= pr.x + pr.width + 4 && r.y + r.height <= pr.y + pr.height + 4;
  const imgs = [...p.querySelectorAll('img')].filter((i) => { const r = i.getBoundingClientRect();
    return r.width > 80 && r.height > 80 && inPanel(r) && getComputedStyle(i).visibility !== 'hidden'; });
  const found = new Set();
  for (const im of imgs) {
    let e = im.parentElement;                       // ⭐ BN1 从 im 自己开始，错了
    for (let i = 0; i < 8 && e; i++) {
      const r = e.getBoundingClientRect();
      if (r.width > 130 && r.width < 400 && r.height > 150 && r.height < 500
          && (e.innerText || '').replace(/\s+/g, ' ').trim().length > 0) { found.add(e); break; }
      e = e.parentElement;
    }
  }
  const list = [...found].map((c) => {
    const r = c.getBoundingClientRect();
    const bits = [...c.querySelectorAll('*')].filter((x) => !skip.has(x.tagName)).map((x) => {
      const rr = x.getBoundingClientRect();
      return { t: (x.innerText || '').replace(/\s+/g, ' ').trim(),
        rect: [Math.round(rr.x), Math.round(rr.y), Math.round(rr.width), Math.round(rr.height)] };
    }).filter((b) => b.t && b.t.length < 26 && b.rect[2] > 0);
    return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      texts: bits.map((b) => b.t).filter((t, i, a) => a.indexOf(t) === i),
      // 卡片上「不悬停时就能看见」的收藏星
      starAlways: [...c.querySelectorAll('button[aria-label="收藏"]')]
        .map((b) => { const br = b.getBoundingClientRect();
          return { rect: [Math.round(br.x), Math.round(br.y), Math.round(br.width), Math.round(br.height)],
            visible: getComputedStyle(b).visibility !== 'hidden' && getComputedStyle(b).opacity !== '0',
            op: getComputedStyle(b).opacity }; })[0] || null };
  }).sort((a, b) => a.rect[1] - b.rect[1] || a.rect[0] - b.rect[0]);
  return { total: list.length, list: cnt ? list.slice(0, cnt) : list };
}, n);

/** 卡片上所有可点件：逐个报 tag/aria/title/cursor/位置，兼作「有没有 ⋯ / ☆ 在哪」的回答。 */
const clickables = () => page.evaluate(() => {
  const pIn = [...document.querySelectorAll('input')].find((i) => (i.placeholder || '').includes('搜索风格'));
  if (!pIn) return { err: '广场没开' };
  let p = pIn;
  for (let i = 0; i < 12 && p; i++) { const r = p.getBoundingClientRect();
    if (r.width > 900 && r.height > 400) break; p = p.parentElement; }
  const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
  const out = [];
  for (const e of p.querySelectorAll('button,[role="button"],[title],[aria-label],a')) {
    if (skip.has(e.tagName)) continue;
    const r = e.getBoundingClientRect();
    if (r.width < 10 || r.width > 60 || r.height < 10 || r.height > 60) continue;
    out.push({ tag: e.tagName, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20),
      aria: e.getAttribute('aria-label'), title: e.getAttribute('title'), role: e.getAttribute('role'),
      cursor: getComputedStyle(e).cursor,
      paths: (e.querySelector('svg') || e).querySelectorAll ? (e.querySelector('svg') || e).querySelectorAll('path').length : 0,
      d: ((e.querySelector('svg') || e).querySelector?.('path')?.getAttribute('d') || '').slice(0, 34) });
  }
  return out;
});

const masks = () => page.evaluate(() => {
  const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
  return [...document.querySelectorAll('[role="tooltip"],.mantine-Tooltip-tooltip,[class*="Tooltip"],[class*="tooltip"],[class*="Popover"],[class*="Dropdown"]')]
    .filter((e) => !skip.has(e.tagName))
    .map((e) => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
      return { t: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 120),
        rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        op: cs.opacity, vis: cs.visibility }; })
    .filter((x) => x.rect[2] > 0 && x.rect[3] > 0 && x.vis !== 'hidden' && x.op !== '0');
});

const sha = (buf) => createHash('sha256').update(buf).digest('hex').slice(0, 16);
const cropSha = async (rect, tag) => {
  const buf = await page.screenshot({ clip: { x: Math.round(rect[0]), y: Math.round(rect[1]), width: Math.round(rect[2]), height: Math.round(rect[3]) } });
  return { sha: sha(buf), bytes: buf.length };
};

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1600);
  await fitView(page); await page.waitForTimeout(1600);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1000);
  await beginBatch(B, { note: '风格广场重做：修 BN1 的四处判据' });
  const out = {};

  out.lib = await clickAria('素材库', 2400);
  out.style = await clickText('风格库', 3800);
  const pnl = await panel();
  out.panel = pnl;
  console.log(`面板：${JSON.stringify(pnl)}`);
  if (!pnl || pnl.err) throw new Error('广场没开');

  // ── ① 卡片解剖（修好的判据）
  const c0 = await cards(4);
  out.cards = c0;
  console.log(`\n═══ 面板内识别出 ${c0.total} 张卡 ═══`);
  for (const [i, c] of (c0.list || []).entries()) {
    console.log(`  ── 卡 ${i + 1} ${JSON.stringify(c.rect)}`);
    console.log(`     文字段：${JSON.stringify(c.texts)}`);
    console.log(`     不悬停时的收藏星：${JSON.stringify(c.starAlways)}`);
  }
  await shot(page, 'M-228-风格广场-卡片逐项读数.png');
  out.shotCards = 'M-228-风格广场-卡片逐项读数.png';

  const cks = await clickables();
  out.clickables = cks;
  console.log(`\n═══ 面板内 ${cks.length} 个可点件（前 24 个）═══`);
  cks.slice(0, 24).forEach((k) => console.log(`   <${k.tag}> [${k.rect}] cursor=${k.cursor} aria=${k.aria} title=${k.title} "${k.text}" path=${k.paths} d="${k.d}"`));
  const stars = cks.filter((k) => k.aria === '收藏');
  const dots = cks.filter((k) => k.text === '⋯' || k.text === '...' || (/^…+$/.test(k.text)));
  console.log(`  ⭐ 收藏星 ${stars.length} 个；⋯ 按钮 ${dots.length} 个`);
  out.stars = stars.length; out.dots = dots.length;

  // ── ② masks() 阳性对照：先证明这个工具能用
  console.log('\n═══ ② masks() 阳性对照（不悬停，先塞一个假的进去）═══');
  const synth = await page.evaluate(() => {
    const d = document.createElement('div');
    d.setAttribute('role', 'tooltip'); d.id = '__synth_tip';
    d.textContent = '合成阳性对照'; d.style.cssText = 'position:fixed;left:300px;top:300px;z-index:99999';
    document.body.appendChild(d); return true; });
  const withSynth = await masks();
  const sawSynth = withSynth.some((m) => m.t.includes('合成阳性对照'));
  await page.evaluate(() => document.getElementById('__synth_tip')?.remove());
  const without = await masks();
  console.log(`  塞进去后 masks() 读到 ${withSynth.length} 个：${JSON.stringify(withSynth.map((m) => m.t))}`);
  console.log(`  ⭐ 选择器认得自己造的吗？ ${sawSynth ? '✅ 认得 —— 之后「读到 0」才是有效读数' : '❌ 不认 —— 之前所有「没有浮层」的结论都作废'}`);
  console.log(`  拿掉后读到 ${without.length} 个：${JSON.stringify(without.map((m) => m.t))}`);
  out.maskControl = { synthSeen: sawSynth, withSynth: withSynth.map((m) => m.t), without: without.map((m) => m.t) };

  // ── ③ 数字悬停：tooltip + 像素双对照
  console.log('\n═══ ③ 卡片上那个数字：悬停有 tooltip 吗 ═══');
  const num = await page.evaluate(() => {
    const pIn = [...document.querySelectorAll('input')].find((i) => (i.placeholder || '').includes('搜索风格'));
    let p = pIn;
    for (let i = 0; i < 12 && p; i++) { const r = p.getBoundingClientRect();
      if (r.width > 900 && r.height > 400) break; p = p.parentElement; }
    for (const e of p.querySelectorAll('*')) {
      const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
      if (!/^\d[\d.]*w?$/.test(t)) continue;
      const r = e.getBoundingClientRect();
      if (r.width < 10 || r.height < 8) continue;
      return { t, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        at: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
        title: e.getAttribute('title'), aria: e.getAttribute('aria-label'),
        // 数字左边紧邻的那枚图标（手册说是「漏斗」，核一遍）
        iconAt: (() => { const sv = [...e.parentElement.querySelectorAll('svg,path')]
          .map((s) => { const rr = s.getBoundingClientRect();
            return { tag: s.tagName, rect: [Math.round(rr.x), Math.round(rr.y), Math.round(rr.width), Math.round(rr.height)],
              d: (s.getAttribute('d') || '').slice(0, 40) }; })
          .filter((s) => s.rect[2] > 4 && s.rect[2] < 30 && Math.abs((s.rect[0] + s.rect[2] / 2) - e.getBoundingClientRect().x) < 40);
          return sv; })() };
    } return null;
  });
  console.log(`  数字元素：${JSON.stringify(num)}`);
  if (num) {
    const zone = [num.rect[0] - 70, num.rect[1] - 60, num.rect[2] + 90, num.rect[3] + 110];
    await page.mouse.move(700, 60); await page.waitForTimeout(1000);
    const base = await masks(); const baseCrop = await cropSha(zone, 'before');
    await page.mouse.move(num.at[0], num.at[1]); await page.waitForTimeout(2000);
    const hov = await masks(); const hovCrop = await cropSha(zone, 'after');
    const gained = hov.filter((h) => !base.some((b) => b.t === h.t)).map((h) => h.t);
    console.log(`  悬停前浮层 ${base.length} 个；悬停后 ${hov.length} 个；新增 ${JSON.stringify(gained)}`);
    console.log(`  悬停前后同一块像素 sha：${baseCrop.sha}(${baseCrop.bytes}B) → ${hovCrop.sha}(${hovCrop.bytes}B)  ${baseCrop.sha === hovCrop.sha ? '**完全一样**' : '**不一样**'}`);
    out.numTip = { el: num, baseTooltips: base.map((b) => b.t), hoverTooltips: hov.map((h) => h.t),
      gained, cropBefore: baseCrop, cropAfter: hovCrop,
      cropIdentical: baseCrop.sha === hovCrop.sha };
  }

  // ── ④ 十个分类：用**前 3 张卡的名称**当判别式
  console.log('\n═══ ④ 十个分类逐个点（判别式 = 前 3 张卡名）═══');
  const cats = ['推荐', '摄影写真', '电商营销', '动漫游戏', '风格插画', '平面设计', '建筑及室内设计', '创意玩法', '文创周边', '小说推文'];
  const perCat = [];
  for (const c of cats) {
    const r = await clickText(c, 2600, 40);
    await page.mouse.move(700, 60); await page.waitForTimeout(800);
    const cc = await cards(3);
    const names = (cc.list || []).map((k) => k.texts.find((t) => !/商用|^\d[\d.]*w?$/.test(t)) || '').filter(Boolean);
    console.log(`  ${c}：executed=${r.executed} 面板内共 ${cc.total} 张 → 前三：${JSON.stringify(names)}`);
    perCat.push({ cat: c, executed: r.executed, total: cc.total, names });
  }
  out.perCat = perCat;
  const distinct = new Set(perCat.map((p) => JSON.stringify(p.names))).size;
  console.log(`  ⭐ ${perCat.length} 个分类给出了 ${distinct} 种不同的前三名 → 分类筛选${distinct > 1 ? '**确实生效**' : '**没测出差别**（判别式分辨力不足）'}`);
  out.catDistinct = distinct;

  // ── ⑤ `⋯` 菜单（点菜单 ≠ 点卡片，安全）
  console.log('\n═══ ⑤ 卡片上的 ⋯ 菜单里有什么 ═══');
  await clickText('推荐', 2400, 40);
  if (dots.length) {
    const d0 = dots[0];
    console.log(`  目标 ⋯ ${JSON.stringify(d0.rect)}`);
    const pBefore = await cropSha([d0.rect[0] - 220, d0.rect[1] - 10, 460, 300], 'pre');
    await page.mouse.click(d0.rect[0] + d0.rect[2] / 2, d0.rect[1] + d0.rect[3] / 2);
    await page.waitForTimeout(2000);
    const menu = await page.evaluate((at) => {
      const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
      return [...document.querySelectorAll('div')].filter((e) => {
        if (skip.has(e.tagName)) return false;
        const r = e.getBoundingClientRect();
        return r.width > 80 && r.width < 320 && r.height > 30 && r.height < 340
          && r.x > at[0] - 300 && r.x < at[0] + 300 && r.y >= at[1] - 20 && r.y < at[1] + 360
          && getComputedStyle(e).zIndex !== 'auto'; })
        .map((e) => { const r = e.getBoundingClientRect();
          return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
            text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 140),
            leaves: [...e.querySelectorAll('*')].filter((x) => !skip.has(x.tagName))
              .map((x) => (x.innerText || '').replace(/\s+/g, ' ').trim())
              .filter((t) => t && t.length < 16).filter((t, i, a) => a.indexOf(t) === i) }; })
        .filter((x) => x.text).sort((a, b) => a.rect[2] * a.rect[3] - b.rect[2] * b.rect[3]);
    }, [d0.rect[0], d0.rect[1]]);
    console.log(`  点完浮出 ${menu.length} 个候选浮层：`);
    menu.slice(0, 4).forEach((m) => console.log(`     [${m.rect}] "${m.text}"\n        叶子：${JSON.stringify(m.leaves)}`));
    const pAfter = await cropSha([d0.rect[0] - 220, d0.rect[1] - 10, 460, 300], 'post');
    console.log(`  点前/点后同一块像素 sha：${pBefore.sha} → ${pAfter.sha}  ${pBefore.sha === pAfter.sha ? '**没变**（菜单没开）' : '**变了**'}`);
    out.dotsMenu = { target: d0, layers: menu, cropBefore: pBefore, cropAfter: pAfter,
      changed: pBefore.sha !== pAfter.sha };
    if (out.dotsMenu.changed) { await shot(page, 'M-229-风格卡片-三点菜单.png'); out.shotMenu = 'M-229-风格卡片-三点菜单.png'; }
    await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  } else { out.dotsMenu = { err: '面板内没找到 ⋯ 按钮' }; }

  // ── ⑥ 排序下拉：按几何找（按钮下方的面板），不按文字猜
  console.log('\n═══ ⑥ 排序下拉里有什么（按几何找面板）═══');
  const sb = await page.evaluate(() => {
    for (const e of document.querySelectorAll('div,button,span')) {
      if ((e.innerText || '').replace(/\s+/g, ' ').trim() !== '全部') continue;
      const r = e.getBoundingClientRect();
      if (r.width < 40 || r.height < 14) continue;
      return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        at: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] };
    } return null; });
  console.log(`  按钮：${JSON.stringify(sb)}`);
  if (sb) {
    await page.mouse.click(sb.at[0], sb.at[1]); await page.waitForTimeout(1900);
    const opts = await page.evaluate((at) => {
      const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
      return [...document.querySelectorAll('div,li,span')].map((e) => {
        const r = e.getBoundingClientRect();
        return { t: (e.innerText || '').replace(/\s+/g, ' ').trim(), r,
          kids: e.children.length, cur: getComputedStyle(e).cursor }; })
        .filter((x) => x.t && x.t.length < 12 && x.r.width > 60 && x.r.height >= 16 && x.r.height < 48
          && x.r.x > at[0] - 260 && x.r.x < at[0] + 120 && x.r.y > at[1] - 10 && x.r.y < at[1] + 300)
        .filter((x) => x.kids === 0 || x.cur === 'pointer')
        .map((x) => ({ t: x.t, y: Math.round(x.r.y), x: Math.round(x.r.x) }))
        .filter((v, i, a) => a.findIndex((o) => o.t === v.t && Math.abs(o.y - v.y) < 6) === i);
    }, sb.at);
    console.log(`  浮出的选项：${JSON.stringify(opts.map((o) => o.t))}`);
    out.sort = { button: sb, options: opts };
    await shot(page, 'M-230-风格广场-排序下拉.png'); out.shotSort = 'M-230-风格广场-排序下拉.png';
    await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  }

  // ── 收尾
  await clickText('推荐', 2000, 40);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1500);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1500);
  out.finalNodes = await page.evaluate(() => document.querySelectorAll('.react-flow__node').length);
  console.log(`\n═══ 收尾：节点 ${out.finalNodes} 个（全程未点卡片，开局 11）═══`);

  await logStep(B, {
    id: 'BN2-style-plaza-card-anatomy',
    title: '风格广场卡片重做：修 BN1 的四处判据，再读 ⋯ 菜单 / 十个分类 / 排序下拉',
    target: 'BN1 判据四处皆错：① 向上爬的循环从 `img` 自己起步（img 就满足尺寸条件）→ 卡片根=预览图，'
      + '文字全空、⋯ 找不到；② 数字用全页正则扫，第一个命中是**顶栏积分余额 20**；'
      + '③ `masks()` 从没做阳性对照，「悬停没 tooltip」**没有证据**；'
      + '④ 分类筛选拿「12 张」当判据，而广场是滚动网格、**12 只是视口内渲染张数**，零分辨力。'
      + '本轮全修，并给 `masks()` 加合成阳性对照、给悬停加像素 sha256 对照。⛔ 仍不点任何卡片。',
    evidence: out,
    visible_text: JSON.stringify({ 面板: out.panel, 卡片: out.cards?.list?.map?.((c) => c.texts),
      收藏星: out.stars, 三点: out.dots, masks对照: out.maskControl, 数字: out.numTip,
      分类: out.perCat, 分类可分辨数: out.catDistinct, 三点菜单: out.dotsMenu,
      排序: out.sort, 收尾节点数: out.finalNodes }).slice(0, 3000),
    shot: out.shotCards,
  });
  console.log('\nBN2 完成');
} catch (e) {
  console.log('⛔ 中止：' + e.message);
} finally {
  await browser.close();
}
