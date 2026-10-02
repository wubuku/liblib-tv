// Batch BN3 — 广场卡片：走 **`详情`** 这条安全路径，而不是点卡片。
//
// BN2 已坐实的：每张卡有 `<button aria-label="收藏">`（右上 24×24 星标，`opacity:0` 悬停才现）
// 与 `<button aria-label="详情">`（下方 24×24），面板内共 **30 张**卡，
// 十个分类逐个点给出 **10 种不同的前三名** → 筛选确实生效。
//
// BN2 留下的坑：数字悬停时**像素变了但没弹浮层**。
//   → BN3 一算就通：那张裁剪区是 `num.rect ± [70,60,90,110]`，
//     而 `详情` 按钮恰好在 `[271,413]` —— **落在区内**。变的是它显形，不是 tooltip。
//
// ⭐ 本轮的关键设计：**点 `详情`，不点卡片**。
//   手册到现在挂着的「点一张会发生什么」，很可能 `详情` 就能回答，
//   而点卡片可能建节点、甚至扣积分。**先找只读的那条路。**
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';
import { resolve } from 'node:path';

const SPACE = '10354929';
const B = 'batchBN3';
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

/** 面板内一切，按 aria/坐标取。 */
const inPanel = (fn) => page.evaluate(fn);

const cardCount = () => page.evaluate(() => {
  const s = document.querySelector('button[aria-label="收藏"]');
  if (!s) return { err: '广场没开' };
  const pr = (() => { let e = s; for (let i = 0; i < 14 && e; i++) { const r = e.getBoundingClientRect();
    if (r.width > 900 && r.height > 400) return r; e = e.parentElement; } return null; })();
  if (!pr) return { err: '找不到面板' };
  const stars = [...document.querySelectorAll('button[aria-label="收藏"]')]
    .filter((b) => { const r = b.getBoundingClientRect();
      return r.x >= pr.x - 4 && r.y >= pr.y - 4 && r.x < pr.x + pr.width && r.y < pr.y + pr.height; });
  const first = stars[0];
  // 由星标反推卡片：星标所在预览图 + 同行的 详情 按钮
  const cards = new Set();
  for (const st of stars) {
    let e = st;
    for (let i = 0; i < 7 && e; i++) { const r = e.getBoundingClientRect();
      if (r.width > 130 && r.width < 400 && r.height > 150) { cards.add(e); break; }
      e = e.parentElement; }
  }
  const r0 = first ? first.getBoundingClientRect() : null;
  return { cards: stars.length, cardRoots: cards.size,
    star0: r0 ? [Math.round(r0.x), Math.round(r0.y), Math.round(r0.width), Math.round(r0.height)] : null,
    starOp0: first ? getComputedStyle(first).opacity : null,
    detail0: (() => { const c = [...cards][0]; if (!c) return null;
      const d = c.querySelector('button[aria-label="详情"]');
      if (!d) return null; const dr = d.getBoundingClientRect();
      return { rect: [Math.round(dr.x), Math.round(dr.y), Math.round(dr.width), Math.round(dr.height)],
        op: getComputedStyle(d).opacity, d: (d.querySelector('path')?.getAttribute('d') || '').slice(0, 40) }; })() };
});

/** 某张卡的完整可点件（传星标的 aria 序号）。 */
const cardParts = (idx = 0) => page.evaluate((i) => {
  const stars = [...document.querySelectorAll('button[aria-label="收藏"]')];
  const st = stars[i]; if (!st) return { err: '没有第 ' + i + ' 张' };
  let card = st;
  for (let k = 0; k < 7 && card; k++) { const r = card.getBoundingClientRect();
    if (r.width > 130 && r.width < 400 && r.height > 150) break; card = card.parentElement; }
  const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
  const out = [];
  for (const e of [card, ...card.querySelectorAll('button,[role="button"],[aria-label],[title]')]) {
    if (!e || skip.has(e.tagName)) continue;
    const r = e.getBoundingClientRect();
    if (r.width < 8 || r.width > 340 || r.height < 8) continue;
    out.push({ tag: e.tagName, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 60),
      aria: e.getAttribute('aria-label'), op: getComputedStyle(e).opacity,
      cur: getComputedStyle(e).cursor,
      d: (e.querySelector?.('path')?.getAttribute('d') || '').slice(0, 30) });
  }
  const cr = card.getBoundingClientRect();
  const texts = [...card.querySelectorAll('*')].filter((x) => !skip.has(x.tagName))
    .map((x) => ({ t: (x.innerText || '').replace(/\s+/g, ' ').trim(),
      r: (() => { const q = x.getBoundingClientRect(); return [Math.round(q.y - cr.y), Math.round(q.x - cr.x), Math.round(q.width)]; })() }))
    .filter((x) => x.t && x.t.length < 30 && x.r[0] >= 0 && x.r[0] < cr.height)
    .map((x) => x.t).filter((t, i, a) => a.indexOf(t) === i);
  return { cardRect: [Math.round(cr.x), Math.round(cr.y), Math.round(cr.width), Math.round(cr.height)], parts: out, texts };
}, idx);

/** 面板弹出的新层（遮罩 / 抽屉 / 浮层），按「比面板更靠上层且在视口中央」认。 */
const topLayer = () => page.evaluate(() => {
  const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
  const vw = innerWidth, vh = innerHeight;
  const cands = [...document.querySelectorAll('div')].filter((e) => {
    if (skip.has(e.tagName)) return false;
    const r = e.getBoundingClientRect();
    if (r.width < 200 || r.height < 150) return false;
    if (r.x > 60 || r.y > 60 || r.x + r.width < vw - 60 || r.y + r.height < vh - 60) return false;  // 要盖住中央
    const cs = getComputedStyle(e);
    if (cs.position !== 'fixed' && cs.position !== 'absolute') return false;
    if (parseInt(cs.zIndex || '0', 10) < 10) return false;
    return true; });
  return cands.map((e) => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    return { cls: (typeof e.className === 'string' ? e.className : '').slice(0, 60),
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      pos: cs.position, z: cs.zIndex,
      text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 700),
      buttons: [...e.querySelectorAll('button,[role="button"]')].filter((x) => !skip.has(x.tagName))
        .map((x) => ({ t: (x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20),
          aria: x.getAttribute('aria-label') })).filter((x) => x.t || x.aria).slice(0, 12) }; })
    .sort((a, b) => b.rect[2] * b.rect[3] - a.rect[2] * a.rect[3]).slice(0, 3);
});

const toasts = () => page.evaluate(() => {
  const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
  return [...document.querySelectorAll('div,li,span')].filter((e) => !skip.has(e.tagName))
    .map((e) => { const r = e.getBoundingClientRect();
      return { t: (e.innerText || '').replace(/\s+/g, ' ').trim(), r,
        cls: (typeof e.className === 'string' ? e.className : '').slice(0, 40) }; })
    .filter((x) => x.t && x.t.length < 40 && x.r.width > 60 && x.r.height > 18 && x.r.height < 70
      && x.r.y < 240 && /成功|失败|已|请|不能|收藏/.test(x.t))
    .map((x) => x.t).filter((t, i, a) => a.indexOf(t) === i);
});

const cardNames = (n = 3) => page.evaluate((cnt) => {
  const stars = [...document.querySelectorAll('button[aria-label="收藏"]')];
  const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
  return stars.slice(0, cnt).map((st) => {
    let c = st;
    for (let k = 0; k < 7 && c; k++) { const r = c.getBoundingClientRect();
      if (r.width > 130 && r.width < 400 && r.height > 150) break; c = c.parentElement; }
    const ts = [...c.querySelectorAll('*')].filter((x) => !skip.has(x.tagName))
      .map((x) => (x.innerText || '').replace(/\s+/g, ' ').trim())
      .filter((t) => t && t.length < 30).filter((t, i, a) => a.indexOf(t) === i);
    return ts.find((t) => !/^[\d.]+w?$/.test(t) && t !== '商用' && !/^•+$|^\.+$|^…+$/.test(t)) || ts[0] || '';
  });
}, n);

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1600);
  await fitView(page); await page.waitForTimeout(1600);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1000);
  await beginBatch(B, { note: '走「详情」这条只读路径看卡片；不点卡片' });
  const out = {};

  out.lib = await clickAria('素材库', 2400);
  out.style = await clickText('风格库', 3800);
  const cc = await cardCount();
  out.count = cc;
  console.log(`═══ 面板内 ${JSON.stringify(cc)} ═══`);
  if (cc.err) throw new Error('广场没开');
  const names0 = await cardNames(4);
  console.log(`  前几张：${JSON.stringify(names0)}`);

  // ── ① 悬停单卡，拍特写（收藏 + 详情 同时显形）
  console.log('\n═══ ① 悬停第 1 张卡，拍特写 ═══');
  const cp = await cardParts(0);
  out.card0 = cp;
  console.log(`  卡 1 ${JSON.stringify(cp.cardRect)}`);
  cp.parts.forEach((p) => console.log(`   · <${p.tag}> [${p.rect}] op=${p.op} cursor=${p.cur} aria=${p.aria} "${p.text}" d="${p.d}"`));
  console.log(`  文字段：${JSON.stringify(cp.texts)}`);
  const [cx, cy, cw, ch] = cp.cardRect;
  await page.mouse.move(cx + cw / 2, cy + ch / 2); await page.waitForTimeout(1800);
  const hov = await cardParts(0);
  const st = hov.parts.find((p) => p.aria === '收藏'); const dt = hov.parts.find((p) => p.aria === '详情');
  console.log(`  悬停后：收藏 op=${st?.op} @${JSON.stringify(st?.rect)}；详情 op=${dt?.op} @${JSON.stringify(dt?.rect)}`);
  out.hover = { star: st, detail: dt };
  const shotFile = 'M-231-风格卡片-悬停显形.png';
  await page.screenshot({ path: `${SHOTS}/${shotFile}`,
    clip: { x: cx - 6, y: cy - 6, width: Math.min(cw + 12, 1430 - cx + 6), height: Math.min(ch + 12, 800 - cy + 6) } });
  console.log(`  📸 ${shotFile}`);
  out.shotCard = shotFile;

  // ── ② 点 `详情`（只读路径）
  console.log('\n═══ ② 点「详情」═══');
  if (dt) {
    const layerBefore = await topLayer();
    const nodesBefore = await page.evaluate(() => document.querySelectorAll('.react-flow__node').length);
    await page.mouse.click(dt.rect[0] + dt.rect[2] / 2, dt.rect[1] + dt.rect[3] / 2);
    await page.waitForTimeout(2800);
    await page.mouse.move(700, 40); await page.waitForTimeout(1000);
    const layerAfter = await topLayer();
    const ts = await toasts();
    console.log(`  点前顶层 ${layerBefore.length} 个；点后 ${layerAfter.length} 个`);
    layerAfter.forEach((l) => console.log(`   ▸ [${l.rect}] pos=${l.pos} z=${l.z} cls="${l.cls}"\n      文字："${l.text}"\n      按钮：${JSON.stringify(l.buttons)}`));
    console.log(`  提示条：${JSON.stringify(ts)}`);
    out.detail = { before: layerBefore.length, after: layerAfter.length, layers: layerAfter, toasts: ts,
      nodesBefore, nodesAfter: await page.evaluate(() => document.querySelectorAll('.react-flow__node').length) };
    if (layerAfter.length > layerBefore.length) {
      await shot(page, 'M-232-风格详情面板.png'); out.shotDetail = 'M-232-风格详情面板.png';
    }
    // 关掉
    for (let i = 0; i < 3; i++) {
      const c = await clickAria('close', 1400);
      if (!c.executed) await page.keyboard.press('Escape');
      await page.waitForTimeout(1200);
      if ((await topLayer()).length <= layerBefore.length) { console.log(`  已关闭（第 ${i + 1} 次）`); break; }
    }
    out.detailClosed = (await topLayer()).length;
  } else out.detail = { err: '没认出详情按钮' };

  // ── ③ 收藏：点一下看发生什么，再点一下回退
  console.log('\n═══ ③ 收藏：能不能点、能不能回退 ═══');
  const cA = await cardCount();
  const favBefore = await page.evaluate(() => [...document.querySelectorAll('button[aria-label="收藏"]')]
    .map((b) => { const p = b.querySelector('path'); return p ? p.getAttribute('d').slice(0, 26) : null; })
    .filter((d, i, a) => a.indexOf(d) === i).length);
  console.log(`  点前：${cA.cards} 张卡；星标 path 形状种类 ${favBefore}`);
  if (st) {
    await page.mouse.move(cx + cw / 2, cy + ch / 2); await page.waitForTimeout(1200);
    const sRect = (await cardParts(0)).parts.find((p) => p.aria === '收藏').rect;
    await page.mouse.click(sRect[0] + sRect[2] / 2, sRect[1] + sRect[3] / 2);
    await page.waitForTimeout(2600);
    const t1 = await toasts();
    const shapes1 = await page.evaluate(() => [...document.querySelectorAll('button[aria-label="收藏"]')]
      .map((b) => (b.querySelector('path')?.getAttribute('d') || '').slice(0, 26))
      .filter((d, i, a) => a.indexOf(d) === i));
    console.log(`  点一下后：提示条 ${JSON.stringify(t1)}；星标形状种类 ${JSON.stringify(shapes1)}`);
    // 再点一下回退
    const s2 = (await cardParts(0)).parts.find((p) => p.aria === '收藏')?.rect;
    if (s2) { await page.mouse.click(s2[0] + s2[2] / 2, s2[1] + s2[3] / 2); await page.waitForTimeout(2400);
      console.log(`  再点一下（回退）后：提示条 ${JSON.stringify(await toasts())}；形状种类 ${JSON.stringify(await page.evaluate(() => [...document.querySelectorAll('button[aria-label="收藏"]')].map((b) => (b.querySelector('path')?.getAttribute('d') || '').slice(0, 26)).filter((d, i, a) => a.indexOf(d) === i)))}`); }
    out.fav = { toastsAfterFirst: t1, shapesAfterFirst: shapes1,
      toastsAfterSecond: await toasts(),
      shapesAfterSecond: await page.evaluate(() => [...document.querySelectorAll('button[aria-label="收藏"]')].map((b) => (b.querySelector('path')?.getAttribute('d') || '').slice(0, 26)).filter((d, i, a) => a.indexOf(d) === i)) };
    // 「我的收藏」标签现在有几张？
    const mine = await clickText('我的收藏', 2600, 40);
    const cnt = await cardCount();
    console.log(`  「我的收藏」标签：executed=${mine.executed} → ${JSON.stringify(cnt)}`);
    out.myFav = { executed: mine.executed, count: cnt };
    await shot(page, 'M-233-我的收藏.png'); out.shotMine = 'M-233-我的收藏.png';
    await clickText('风格广场', 2400, 40);
  }

  // ── ④ 排序下拉：换判据 —— 点开后数「面板内新增的按钮/文字」，且排除画布节点名
  console.log('\n═══ ④ 排序下拉（换判据：只看按钮与面板内元素）═══');
  const sb = await page.evaluate(() => {
    const p = document.querySelector('button[aria-label="收藏"]');
    if (!p) return null;
    let pan = p; for (let i = 0; i < 14 && pan; i++) { const r = pan.getBoundingClientRect();
      if (r.width > 900 && r.height > 400) break; pan = pan.parentElement; }
    const pr = pan.getBoundingClientRect();
    for (const e of pan.querySelectorAll('button')) {
      if ((e.innerText || '').replace(/\s+/g, ' ').trim() !== '全部') continue;
      const r = e.getBoundingClientRect();
      return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        at: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
        pr: [Math.round(pr.x), Math.round(pr.y), Math.round(pr.width), Math.round(pr.height)] };
    } return null; });
  console.log(`  排序按钮：${JSON.stringify(sb)}`);
  if (sb) {
    const inPanelNow = () => page.evaluate(() => {
      const p = document.querySelector('button[aria-label="收藏"]');
      let pan = p; for (let i = 0; i < 14 && pan; i++) { const r = pan.getBoundingClientRect();
        if (r.width > 900 && r.height > 400) break; pan = pan.parentElement; }
      if (!pan) return [];
      const pr = pan.getBoundingClientRect();
      return [...pan.querySelectorAll('button,[role="option"],[role="menuitem"],li,div')]
        .filter((e) => { const r = e.getBoundingClientRect();
          return r.x >= pr.x && r.y >= pr.y && r.x + r.width <= pr.x + pr.width + 2 && r.y + r.height <= pr.y + pr.height + 2; })
        .map((e) => ({ t: (e.innerText || '').replace(/\s+/g, ' ').trim(), kids: e.children.length }))
        .filter((x) => x.t && x.t.length < 12 && x.kids === 0);
    });
    const b0 = await inPanelNow();
    await page.mouse.click(sb.at[0], sb.at[1]); await page.waitForTimeout(2000);
    const b1 = await inPanelNow();
    const gained = b1.map((x) => x.t).filter((t) => !b0.some((y) => y.t === t));
    console.log(`  点前叶子 ${b0.length} 个；点后 ${b1.length} 个；新增：${JSON.stringify(gained)}`);
    out.sort = { button: sb.rect, before: b0.length, after: b1.length, gained };
    if (gained.length) { await shot(page, 'M-234-风格广场-排序下拉.png'); out.shotSort = 'M-234-风格广场-排序下拉.png'; }
    await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  }

  // ── 收尾：回 风格广场 / 推荐，关广场
  await clickText('风格广场', 2000, 40);
  await clickText('推荐', 2000, 40);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1500);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1500);
  out.finalNodes = await page.evaluate(() => document.querySelectorAll('.react-flow__node').length);
  out.finalGroups = await page.evaluate(() => document.querySelectorAll('.react-flow__node-group').length);
  console.log(`\n═══ 收尾：节点 ${out.finalNodes} 个 / 组 ${out.finalGroups} 个（开局 11 / 0）═══`);

  await logStep(B, {
    id: 'BN3-card-detail-panel',
    title: '走「详情」这条只读路径看广场卡片：详情面板里是什么、收藏能不能回退',
    target: '手册挂着「点一张会发生什么」。直接点卡片可能建节点甚至扣积分，'
      + '所以本轮改走每张卡都有的 `<button aria-label="详情">` —— **先找只读的那条路**。'
      + '收藏点两次回退，验它到底改了什么。⭐ 另解 BN2 的一个疑点：'
      + '数字悬停时像素变了却没有浮层 —— 算下来是 `详情` 按钮（`[271,413]`）'
      + '**恰好落在那张裁剪区里**，变的是它悬停显形，不是 tooltip。',
    evidence: out,
    visible_text: JSON.stringify({ 张数: out.count, 卡1: out.card0?.parts, 文字: out.card0?.texts,
      悬停: out.hover, 详情: out.detail, 收藏: out.fav, 我的收藏: out.myFav,
      排序: out.sort, 收尾: { 节点: out.finalNodes, 组: out.finalGroups } }).slice(0, 3000),
    shot: out.shotDetail || out.shotCard,
  });
  console.log('\nBN3 完成');
} catch (e) {
  console.log('⛔ 中止：' + e.message);
} finally {
  await browser.close();
}
