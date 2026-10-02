// Batch BO — 把 BN 的「详情」这条路在**特效广场**上再走一遍。
//
// 为什么要复验一遍：BN 在风格广场查到 ⤢「详情」+ 只读详情浮层 +「首选推荐模型」。
// 但那**可能只是风格广场有**。⭐ 同一个发现，在**第二个对象**上成立才叫规律；
// 只在一个对象上成立，那只是「风格广场有」—— 而这恰好是手册早期栽过的坑
// （「漏斗图标是特效广场特有」/「模型徽标是风格名」都是只在一处看过就下结论）。
//
// ⭐ 本轮真正想拿的东西：**特效广场那个数字到底是不是价格。**
// 手册里它已经挂了很久的 📖，理由是「量级像价格，不敢点」。
// 而 `详情` 是**只读**的 —— 如果详情面板里写着这个数字的单位，📖 就掉了。
//
// ⛔ 全程不点 `使用`、不点卡面。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';
import { resolve } from 'node:path';

const SPACE = '10354929';
const B = 'batchBO1';
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
const clickText = async (txt, wait = 3000, minW = 0) => {
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

/** 面板：以搜索框占位符为锚（风格/特效两处都是 `搜索XX名称、作者`）。 */
const panel = () => page.evaluate(() => {
  const inp = [...document.querySelectorAll('input')].find((i) => /搜索(风格|特效)/.test(i.placeholder || ''));
  if (!inp) return { err: '广场没开' };
  let e = inp;
  for (let i = 0; i < 14 && e; i++) { const r = e.getBoundingClientRect();
    if (r.width > 900 && r.height > 400) return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      placeholder: inp.placeholder };
    e = e.parentElement; }
  return { err: '从搜索框往上找不到面板' };
});

/** 卡片按钮盘点：⭐ 这次**按图形**找那个 `•••`（一个 svg 里三个 circle）。 */
const buttons = () => page.evaluate(() => {
  const inp = [...document.querySelectorAll('input')].find((i) => /搜索(风格|特效)/.test(i.placeholder || ''));
  if (!inp) return { err: '广场没开' };
  let pnl = inp;
  for (let i = 0; i < 14 && pnl; i++) { const r = pnl.getBoundingClientRect();
    if (r.width > 900 && r.height > 400) break; pnl = pnl.parentElement; }
  const pr = pnl.getBoundingClientRect();
  const inside = (e) => { const r = e.getBoundingClientRect();
    return r.x >= pr.x - 4 && r.y >= pr.y - 4 && r.x < pr.x + pr.width && r.y < pr.y + pr.height; };
  const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
  const all = [...pnl.querySelectorAll('button,[role="button"]')].filter((e) => !skip.has(e.tagName) && inside(e));
  const shape = (e) => {
    const sv = e.querySelector('svg') || e;
    const circles = sv.querySelectorAll('circle').length;
    const paths = sv.querySelectorAll('path').length;
    const r = e.getBoundingClientRect();
    return { aria: e.getAttribute('aria-label'), text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 24),
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      op: getComputedStyle(e).opacity, circles, paths,
      d: (sv.querySelector('path')?.getAttribute('d') || '').slice(0, 36) };
  };
  const list = all.map(shape);
  return { total: list.length,
    byAria: list.reduce((a, x) => { const k = x.aria || `(${x.text || '空'})`; a[k] = (a[k] || 0) + 1; return a; }, {}),
    dotsLike: list.filter((x) => x.circles >= 2 || /^[•·…\.]{2,}$/.test(x.text) || (x.circles >= 1 && x.rect[2] <= 30 && !x.aria && x.paths === 0)),
    sample: list.slice(0, 10) };
});

/** 顶层浮层集合（身份 = cls|rect|z），用来做差分。 */
const topLayers = () => page.evaluate(() => {
  const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
  const vw = innerWidth, vh = innerHeight;
  return [...document.querySelectorAll('div')].filter((e) => {
    if (skip.has(e.tagName)) return false;
    const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    if (r.width < 200 || r.height < 120) return false;
    if (r.x > 60 || r.y > 60 || r.x + r.width < vw - 60 || r.y + r.height < vh - 60) return false;
    if (cs.position !== 'fixed' && cs.position !== 'absolute') return false;
    return parseInt(cs.zIndex || '0', 10) >= 10; })
    .map((e) => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
      return { id: `${(typeof e.className === 'string' ? e.className : '').slice(0, 36)}|${Math.round(r.x)},${Math.round(r.y)},${Math.round(r.width)}x${Math.round(r.height)}|z${cs.zIndex}`,
        cls: (typeof e.className === 'string' ? e.className : '').slice(0, 50),
        rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], z: cs.zIndex,
        text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 1000),
        buttons: [...e.querySelectorAll('button,[role="button"],[aria-label]')].filter((x) => !skip.has(x.tagName))
          .map((x) => ({ t: (x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 24), aria: x.getAttribute('aria-label') }))
          .filter((x) => x.t || x.aria).slice(0, 18) }; });
});

const toasts = () => page.evaluate(() => [...document.querySelectorAll('div,li,span')]
  .filter((e) => !['SCRIPT','STYLE','NOSCRIPT','TEMPLATE'].includes(e.tagName))
  .map((e) => { const r = e.getBoundingClientRect();
    return { t: (e.innerText || '').replace(/\s+/g, ' ').trim(), r }; })
  .filter((x) => x.t && x.t.length < 30 && x.r.width > 50 && x.r.height > 16 && x.r.height < 70
    && x.r.y < 260 && /(成功|失败|已|请|不能|收藏|积分|价格)/.test(x.t))
  .map((x) => x.t).filter((t, i, a) => a.indexOf(t) === i));

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1600);
  await fitView(page); await page.waitForTimeout(1600);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1000);
  await beginBatch(B, { note: '把「详情」这条路在特效广场上再走一遍' });
  const out = {};

  await clickAria('素材库', 2400);
  out.fx = await clickText('特效库', 4000);
  const pnl = await panel();
  out.panel = pnl;
  console.log(`═══ 特效广场：${JSON.stringify(out.fx)} / 面板 ${JSON.stringify(pnl)} ═══`);
  if (!pnl || pnl.err) throw new Error('特效广场没开');

  // ── ① 按钮盘点：BN 的机制在这儿也成立吗
  const bs = await buttons();
  out.buttons = bs;
  console.log(`\n═══ ① 面板内 ${bs.total} 个按钮，按无障碍名归类 ═══`);
  console.log(`  ${JSON.stringify(bs.byAria)}`);
  console.log(`  ⭐ 长得像「•••」的候选（svg 里 ≥2 个 circle / 文字是点号）：${bs.dotsLike.length} 个`);
  bs.dotsLike.slice(0, 6).forEach((d) => console.log(`     ${JSON.stringify(d)}`));
  console.log(`  前 10 个样本：`);
  bs.sample.forEach((s) => console.log(`     <${s.aria || '空'}> ${JSON.stringify(s.rect)} op=${s.op} circle=${s.circles} path=${s.paths} d="${s.d}"`));

  // ── ② 悬停显形：收藏 / 详情两枚
  console.log(`\n═══ ② 悬停显形复验 ═══`);
  const dPos = await page.evaluate(() => {
    const inp = [...document.querySelectorAll('input')].find((i) => /搜索(风格|特效)/.test(i.placeholder || ''));
    let pnl = inp; for (let i = 0; i < 14 && pnl; i++) { const r = pnl.getBoundingClientRect();
      if (r.width > 900 && r.height > 400) break; pnl = pnl.parentElement; }
    const pr = pnl.getBoundingClientRect();
    const d = [...pnl.querySelectorAll('button[aria-label="详情"]')].find((b) => { const r = b.getBoundingClientRect();
      return r.x >= pr.x - 4 && r.y >= pr.y - 4 && r.x < pr.x + pr.width && r.y < pr.y + pr.height; });
    if (!d) return null;
    const r = d.getBoundingClientRect();
    return { at: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
  });
  const fPos = await page.evaluate(() => {
    const inp = [...document.querySelectorAll('input')].find((i) => /搜索(风格|特效)/.test(i.placeholder || ''));
    let pnl = inp; for (let i = 0; i < 14 && pnl; i++) { const r = pnl.getBoundingClientRect();
      if (r.width > 900 && r.height > 400) break; pnl = pnl.parentElement; }
    const pr = pnl.getBoundingClientRect();
    const f = [...pnl.querySelectorAll('button[aria-label="收藏"]')].find((b) => { const r = b.getBoundingClientRect();
      return r.x >= pr.x - 4 && r.y >= pr.y - 4 && r.x < pr.x + pr.width && r.y < pr.y + pr.height; });
    if (!f) return null;
    const r = f.getBoundingClientRect();
    return { at: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], op: getComputedStyle(f).opacity };
  });
  console.log(`  悬停前：详情 @${JSON.stringify(dPos?.rect)}；收藏 @${JSON.stringify(fPos)}`);
  if (dPos) {
    await page.mouse.move(dPos.at[0] - 90, dPos.at[1] - 70); await page.waitForTimeout(800);
    await page.mouse.move(dPos.at[0], dPos.at[1]); await page.waitForTimeout(1600);
    const after = await page.evaluate((at) => [...document.querySelectorAll('button[aria-label="收藏"],button[aria-label="详情"]')]
      .map((b) => ({ aria: b.getAttribute('aria-label'), op: getComputedStyle(b).opacity,
        d: Math.round(Math.hypot(b.getBoundingClientRect().x - at[0], b.getBoundingClientRect().y - at[1])) }))
      .filter((x) => x.d < 400), dPos.at);
    console.log(`  悬停后：${JSON.stringify(after)}`);
    out.hover = { before: { detail: dPos.rect, fav: fPos }, after };
    // 卡片特写（含下方文字行）
    const card = await page.evaluate((at) => {
      const inp = [...document.querySelectorAll('input')].find((i) => /搜索(风格|特效)/.test(i.placeholder || ''));
      let pnl = inp; for (let i = 0; i < 14 && pnl; i++) { const r = pnl.getBoundingClientRect();
        if (r.width > 900 && r.height > 400) break; pnl = pnl.parentElement; }
      const d = [...pnl.querySelectorAll('button[aria-label="详情"]')]
        .find((b) => { const r = b.getBoundingClientRect();
          return r.x >= pnl.getBoundingClientRect().x - 4 && r.x < pnl.getBoundingClientRect().x + pnl.getBoundingClientRect().width; });
      let c = d;
      for (let k = 0; k < 9 && c; k++) { const r = c.getBoundingClientRect();
        if (r.width > 130 && r.width < 400 && r.height > 150) break; c = c.parentElement; }
      const r = c.getBoundingClientRect();
      return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)];
    }, dPos.at);
    console.log(`  卡片 ${JSON.stringify(card)}`);
    if (card) {
      const w = Math.min(card[2] + 16, 1436 - card[0]);
      const h = Math.min(card[3] + 80, 800 - card[1]);
      await page.screenshot({ path: `${SHOTS}/M-241-特效卡片-悬停显形.png`,
        clip: { x: card[0] - 8, y: card[1] - 8, width: w, height: h + 8 } });
      out.shotCard = 'M-241-特效卡片-悬停显形.png';
      console.log(`  📸 ${out.shotCard}`);
    }
  }

  // ── ③ 点「详情」：⭐ 那个数字的单位就在这里
  console.log(`\n═══ ③ 点「详情」，找那个数字的单位 ═══`);
  if (dPos) {
    const L0 = await topLayers();
    await page.mouse.move(dPos.at[0] - 90, dPos.at[1] - 70); await page.waitForTimeout(700);
    await page.mouse.move(dPos.at[0], dPos.at[1]); await page.waitForTimeout(1300);
    await page.mouse.click(dPos.at[0], dPos.at[1]); await page.waitForTimeout(3200);
    await page.mouse.move(700, 40); await page.waitForTimeout(1000);
    const L1 = await topLayers();
    const gained = L1.filter((x) => !L0.some((y) => y.id === x.id));
    console.log(`  点前 ${L0.length} 层、点后 ${L1.length} 层；新增 ${gained.length} 层`);
    gained.forEach((l) => console.log(`   ▸ [${l.rect}] z=${l.z} cls="${l.cls}"\n      文字：「${l.text}」\n      按钮：${JSON.stringify(l.buttons)}`));
    console.log(`  提示条：${JSON.stringify(await toasts())}`);
    out.detail = { before: L0.length, after: L1.length, gained, toasts: await toasts() };
    if (gained.length) {
      const full = await page.evaluate(() => {
        const zs = [...document.querySelectorAll('div')].map((e) => ({ e, z: parseInt(getComputedStyle(e).zIndex || '0', 10), r: e.getBoundingClientRect() }))
          .filter((x) => x.z >= 800 && x.r.width > 200 && x.r.height > 120).sort((a, b) => b.z - a.z);
        if (!zs.length) return null;
        // ⭐ 把**每一个**可见文字块逐个读出来，别只读容器的合成 innerText
        const top = zs[0].e;
        const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
        const texts = [...top.querySelectorAll('*')].filter((x) => !skip.has(x.tagName))
          .map((x) => { const r = x.getBoundingClientRect();
            return { t: (x.innerText || '').replace(/\s+/g, ' ').trim(), kids: x.children.length,
              rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; })
          .filter((x) => x.t && x.t.length < 40 && x.kids === 0 && x.rect[2] > 0)
          .map((x) => x.t).filter((t, i, a) => a.indexOf(t) === i);
        return { all: (top.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 1200), leaves: texts };
      });
      console.log(`  ⭐ 详情面板全文：${JSON.stringify(full).slice(0, 2400)}`);
      out.detail.full = full;
      await shot(page, 'M-242-特效详情面板.png'); out.shotDetail = 'M-242-特效详情面板.png';
    }
    for (let i = 0; i < 3; i++) {
      const c = await clickAria('close', 1400);
      if (!c.executed) await page.keyboard.press('Escape');
      await page.waitForTimeout(1200);
      if ((await topLayers()).length <= L0.length) { console.log(`  已关闭（第 ${i + 1} 次）`); break; }
    }
  }

  await page.keyboard.press('Escape'); await page.waitForTimeout(1500);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1500);
  out.finalNodes = await page.evaluate(() => document.querySelectorAll('.react-flow__node').length);
  out.finalGroups = await page.evaluate(() => document.querySelectorAll('.react-flow__node-group').length);
  console.log(`\n═══ 收尾：节点 ${out.finalNodes} / 组 ${out.finalGroups} ═══`);

  await logStep(B, {
    id: 'BO1-fx-plaza-detail-panel',
    title: '把「详情」这条路在特效广场上再走一遍 —— 顺便找那个数字的单位',
    target: 'BN 在风格广场查到 ⤢「详情」+ 只读详情浮层 +「首选推荐模型」。'
      + '⭐ 但那**可能只是风格广场有** —— 同一个发现在**第二个对象**上成立才叫规律。'
      + '本轮正想拿的是**特效广场那个数字到底是不是价格**（挂了最久的 📖，'
      + '理由是「量级像价格、不敢点」）；而 `详情` 是只读的，单位如果写在面板里，📖 就掉了。'
      + '⛔ 不点 `使用`、不点卡面。',
    evidence: out,
    visible_text: JSON.stringify({ 面板: out.panel, 按钮归类: out.buttons?.byAria,
      三点候选: out.buttons?.dotsLike, 悬停: out.hover, 详情: out.detail,
      收尾: { 节点: out.finalNodes, 组: out.finalGroups } }).slice(0, 3000),
    shot: out.shotDetail || out.shotCard,
  });
  console.log('\nBO1 完成');
} catch (e) {
  console.log('⛔ 中止：' + e.message);
} finally {
  await browser.close();
}
