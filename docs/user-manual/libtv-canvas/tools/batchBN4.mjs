// Batch BN4 — ① **先查账号有没有被 BN3 弄脏**；② 详情面板内容这回真读出来；③ 排序下拉换锚点。
//
// BN3 的两笔糊涂账：
//   ⚠️ **收藏到底回退没有**。点第一下弹「收藏成功」且浮层里出现「取消收藏」；
//      但点第二下之后读到的提示条仍是 `["收藏成功","取消收藏"]` —— 那是**没清掉的残留**，
//      所以「回退成功」**没验成**。而「我的收藏」那一读又报 `广场没开`
//      （我的判据以 `button[aria-label="收藏"]` 为锚点，收藏页为空时锚点就没了）。
//      → **给用户账号留脏状态是不能留到下一轮的。** 本轮第一件事就是查清楚并清掉。
//   ⚠️ **详情面板内容没读到**。BN3 用「顶层浮层**数目**」判变化，结果点前 3 个、点后 3 个 ——
//      **数目一样，但多了一枚 `z=800`**。⭐ 又是「条数判据不够，得看属性」。
//      本轮改成**集合差分**（按 `class|rect|z` 当身份），直接把新出现的那层读出来。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBN4';
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

/** ⭐ 面板锚点用**搜索框**（不是收藏星标）—— 收藏页为空时星标会消失，锚点就断了。 */
const panelEl = () => page.evaluate(() => {
  const inp = [...document.querySelectorAll('input')].find((i) => (i.placeholder || '').includes('搜索风格'));
  if (!inp) return null;
  let e = inp;
  for (let i = 0; i < 14 && e; i++) { const r = e.getBoundingClientRect();
    if (r.width > 900 && r.height > 400) { const rr = e.getBoundingClientRect();
      return { rect: [Math.round(rr.x), Math.round(rr.y), Math.round(rr.width), Math.round(rr.height)] }; }
    e = e.parentElement; }
  return null; });

/** 面板内卡片数：⭐ 数 `button[aria-label="详情"]`（收藏页为空时详情也没了 → 报 0 而不是「没开」）。 */
const cardsIn = () => page.evaluate(() => {
  const pnl = (() => { const inp = [...document.querySelectorAll('input')].find((i) => (i.placeholder || '').includes('搜索风格'));
    if (!inp) return null; let e = inp;
    for (let i = 0; i < 14 && e; i++) { const r = e.getBoundingClientRect(); if (r.width > 900 && r.height > 400) return e; e = e.parentElement; }
    return null; })();
  if (!pnl) return { err: '广场没开' };
  const pr = pnl.getBoundingClientRect();
  const inside = (e) => { const r = e.getBoundingClientRect();
    return r.x >= pr.x - 4 && r.y >= pr.y - 4 && r.x < pr.x + pr.width && r.y < pr.y + pr.height; };
  const det = [...pnl.querySelectorAll('button[aria-label="详情"]')].filter(inside);
  const fav = [...pnl.querySelectorAll('button[aria-label="收藏"]')].filter(inside);
  const empty = [...pnl.querySelectorAll('*')].filter((e) => !['SCRIPT','STYLE','NOSCRIPT','TEMPLATE'].includes(e.tagName))
    .map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim())
    .filter((t) => /暂无|没有|空空|无收藏|还没有/.test(t) && t.length < 30)
    .filter((t, i, a) => a.indexOf(t) === i);
  return { detailBtns: det.length, favBtns: fav.length, emptyHints: empty,
    first: det[0] ? (() => { let c = det[0];
      for (let k = 0; k < 7 && c; k++) { const r = c.getBoundingClientRect();
        if (r.width > 130 && r.width < 400 && r.height > 150) break; c = c.parentElement; }
      return (c.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 80); })() : null };
});

const toasts = () => page.evaluate(() => [...document.querySelectorAll('div,li,span')]
  .filter((e) => !['SCRIPT','STYLE','NOSCRIPT','TEMPLATE'].includes(e.tagName))
  .map((e) => { const r = e.getBoundingClientRect();
    return { t: (e.innerText || '').replace(/\s+/g, ' ').trim(), r,
      cls: (typeof e.className === 'string' ? e.className : '').slice(0, 40) }; })
  .filter((x) => x.t && x.t.length < 30 && x.r.width > 50 && x.r.height > 16 && x.r.height < 70
    && x.r.y < 260 && /(成功|失败|已|请|不能|收藏|取消)/.test(x.t))
  .map((x) => x.t).filter((t, i, a) => a.indexOf(t) === i));

/** ⭐ 顶层浮层「集合」：身份 = cls|rect|z。用来做差分，而不是数数目。 */
const topLayers = () => page.evaluate(() => {
  const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
  const vw = innerWidth, vh = innerHeight;
  return [...document.querySelectorAll('div')].filter((e) => {
    if (skip.has(e.tagName)) return false;
    const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    if (r.width < 200 || r.height < 120) return false;
    if (r.x > 60 || r.y > 60 || r.x + r.width < vw - 60 || r.y + r.height < vh - 60) return false;
    if (cs.position !== 'fixed' && cs.position !== 'absolute') return false;
    if (parseInt(cs.zIndex || '0', 10) < 10) return false;
    return true; })
    .map((e) => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
      return { id: `${(typeof e.className === 'string' ? e.className : '').slice(0, 40)}|${Math.round(r.x)},${Math.round(r.y)},${Math.round(r.width)}x${Math.round(r.height)}|z${cs.zIndex}`,
        cls: (typeof e.className === 'string' ? e.className : '').slice(0, 55),
        rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        z: cs.zIndex,
        text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 900),
        buttons: [...e.querySelectorAll('button,[role="button"],[aria-label]')].filter((x) => !skip.has(x.tagName))
          .map((x) => ({ t: (x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 24), aria: x.getAttribute('aria-label') }))
          .filter((x) => x.t || x.aria).slice(0, 16) }; });
});

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1600);
  await fitView(page); await page.waitForTimeout(1600);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1000);
  await beginBatch(B, { note: '查账号是否被 BN3 弄脏 + 详情面板集合差分 + 排序换锚点' });
  const out = {};

  await clickAria('素材库', 2400);
  await clickText('风格库', 3800);
  console.log(`面板：${JSON.stringify(await panelEl())}`);

  // ── ① 账号脏没脏
  console.log('\n═══ ① 先查「我的收藏」 ═══');
  const mine = await clickText('我的收藏', 3000, 40);
  await clearToasts(page);
  const inMine = await cardsIn();
  console.log(`  点「我的收藏」executed=${mine.executed} → ${JSON.stringify(inMine)}`);
  out.myFavBefore = inMine;
  if (inMine.detailBtns > 0) {
    console.log(`  ⚠️ 账号里留了 ${inMine.detailBtns} 张收藏 → 本轮清掉`);
    for (let i = 0; i < inMine.detailBtns; i++) {
      const cur = await cardsIn();
      if (cur.detailBtns === 0) break;
      // 悬停第 i 张卡再点收藏
      const pos = await page.evaluate((k) => {
        const inp = [...document.querySelectorAll('input')].find((i) => (i.placeholder || '').includes('搜索风格'));
        let pnl = inp; for (let i = 0; i < 14 && pnl; i++) { const r = pnl.getBoundingClientRect();
          if (r.width > 900 && r.height > 400) break; pnl = pnl.parentElement; }
        const pr = pnl.getBoundingClientRect();
        const det = [...pnl.querySelectorAll('button[aria-label="详情"]')]
          .filter((b) => { const r = b.getBoundingClientRect();
            return r.x >= pr.x - 4 && r.y >= pr.y - 4 && r.x < pr.x + pr.width && r.y < pr.y + pr.height; });
        const d = det[k]; if (!d) return null;
        const fav = d.parentElement?.querySelector('button[aria-label="收藏"]')
          || pnl.querySelectorAll('button[aria-label="收藏"]')[k];
        if (!fav) return null;
        const fr = fav.getBoundingClientRect();
        return [Math.round(fr.x + fr.width / 2), Math.round(fr.y + fr.height / 2)];
      }, i);
      if (!pos) { console.log(`  第 ${i + 1} 张没找到收藏按钮`); break; }
      await page.mouse.move(pos[0] - 60, pos[1] + 60); await page.waitForTimeout(700);
      await page.mouse.move(pos[0], pos[1]); await page.waitForTimeout(1300);
      await page.mouse.click(pos[0], pos[1]); await page.waitForTimeout(2400);
      const t = await toasts();
      const after = await cardsIn();
      console.log(`  取消第 ${i + 1} 张：提示=${JSON.stringify(t)} → 收藏页剩 ${after.detailBtns} 张`);
      out.cancelLog = out.cancelLog || []; out.cancelLog.push({ i, toasts: t, left: after.detailBtns });
      await clearToasts(page);
    }
    const fin = await cardsIn();
    console.log(`  ⭐ 清完：${JSON.stringify(fin)}`);
    out.myFavAfter = fin;
  } else {
    console.log(`  ✅ 账号是干净的：收藏页 0 张（BN3 那个「再点一下」回退**确实生效了**，只是读数没验成）`);
    out.myFavAfter = inMine;
  }

  // ── ② 详情面板：集合差分
  console.log('\n═══ ② 详情面板（集合差分，不是数数目）═══');
  await clickText('风格广场', 2800, 40);
  await clearToasts(page);
  const L0 = await topLayers();
  console.log(`  点前顶层 ${L0.length} 个：${JSON.stringify(L0.map((l) => l.id))}`);
  const dPos = await page.evaluate(() => {
    const inp = [...document.querySelectorAll('input')].find((i) => (i.placeholder || '').includes('搜索风格'));
    let pnl = inp; for (let i = 0; i < 14 && pnl; i++) { const r = pnl.getBoundingClientRect();
      if (r.width > 900 && r.height > 400) break; pnl = pnl.parentElement; }
    const pr = pnl.getBoundingClientRect();
    const d = [...pnl.querySelectorAll('button[aria-label="详情"]')].find((b) => { const r = b.getBoundingClientRect();
      return r.x >= pr.x - 4 && r.y >= pr.y - 4 && r.x < pr.x + pr.width && r.y < pr.y + pr.height; });
    if (!d) return null;
    const r = d.getBoundingClientRect();
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
  });
  console.log(`  「详情」按钮位置：${JSON.stringify(dPos)}`);
  if (dPos) {
    await page.mouse.move(dPos[0] - 80, dPos[1] - 60); await page.waitForTimeout(800);
    await page.mouse.move(dPos[0], dPos[1]); await page.waitForTimeout(1300);
    await page.mouse.click(dPos[0], dPos[1]); await page.waitForTimeout(3200);
    await page.mouse.move(700, 40); await page.waitForTimeout(1000);
    const L1 = await topLayers();
    const gained = L1.filter((x) => !L0.some((y) => y.id === x.id));
    const lost = L0.filter((x) => !L1.some((y) => y.id === x.id));
    console.log(`  点后顶层 ${L1.length} 个；新增 ${gained.length} 个、消失 ${lost.length} 个`);
    gained.forEach((l) => console.log(`   ▸新增 [${l.rect}] z=${l.z} cls="${l.cls}"\n      文字："${l.text}"\n      按钮：${JSON.stringify(l.buttons)}`));
    lost.forEach((l) => console.log(`   ▸消失 [${l.rect}] z=${l.z} cls="${l.cls}"`));
    console.log(`  提示条：${JSON.stringify(await toasts())}`);
    out.detail = { before: L0.map((l) => l.id), after: L1.map((l) => l.id), gained, lost,
      toasts: await toasts() };
    if (gained.length) {
      // 把新层的文字完整读一遍（上面截了 900 字）
      const full = await page.evaluate(() => {
        const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
        const zs = [...document.querySelectorAll('div')].map((e) => ({ e, z: parseInt(getComputedStyle(e).zIndex || '0', 10), r: e.getBoundingClientRect() }))
          .filter((x) => x.z >= 800 && x.r.width > 200 && x.r.height > 120)
          .sort((a, b) => b.z - a.z);
        if (!zs.length) return null;
        // 找 z 最高那一层的**兄弟**（真正装内容的）
        const top = zs[0].e;
        const sibs = [top, ...(top.parentElement ? top.parentElement.children : [])];
        return sibs.map((s) => ({ z: getComputedStyle(s).zIndex, cls: (typeof s.className === 'string' ? s.className : '').slice(0, 50),
          text: (s.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 1200),
          buttons: [...s.querySelectorAll('button,[role="button"]')].filter((x) => !skip.has(x.tagName))
            .map((x) => ({ t: (x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 24), aria: x.getAttribute('aria-label') }))
            .filter((x) => x.t || x.aria).slice(0, 20) }));
      });
      console.log(`  ⭐ 新层全文：${JSON.stringify(full).slice(0, 2200)}`);
      out.detail.full = full;
      await shot(page, 'M-235-风格详情.png'); out.shotDetail = 'M-235-风格详情.png';
    }
    // 关
    for (let i = 0; i < 3; i++) {
      const c = await clickAria('close', 1400);
      if (!c.executed) await page.keyboard.press('Escape');
      await page.waitForTimeout(1200);
      const now = await topLayers();
      if (now.length <= L0.length) { console.log(`  已关闭（第 ${i + 1} 次，回到 ${now.length} 个）`); break; }
    }
    out.detailClosed = (await topLayers()).length;
  }

  // ── ③ 排序下拉：锚点换成搜索框所在的**面板**，按钮用「面板内、叶子、文字=全部」
  console.log('\n═══ ③ 排序下拉（锚点 = 面板）═══');
  const sb = await page.evaluate(() => {
    const inp = [...document.querySelectorAll('input')].find((i) => (i.placeholder || '').includes('搜索风格'));
    if (!inp) return { err: '广场没开' };
    let pnl = inp; for (let i = 0; i < 14 && pnl; i++) { const r = pnl.getBoundingClientRect();
      if (r.width > 900 && r.height > 400) break; pnl = pnl.parentElement; }
    const pr = pnl.getBoundingClientRect();
    for (const e of pnl.querySelectorAll('button')) {
      if ((e.innerText || '').replace(/\s+/g, ' ').trim() !== '全部') continue;
      const r = e.getBoundingClientRect();
      if (r.x < pr.x || r.y < pr.y) continue;
      return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        at: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] };
    } return { err: '面板里没有文字为「全部」的按钮' };
  });
  console.log(`  排序按钮：${JSON.stringify(sb)}`);
  if (sb.at) {
    const zone = { x: sb.rect[0] - 220, y: sb.rect[1] - 10, width: 300, height: 320 };
    const before = await page.screenshot({ clip: zone });
    await page.mouse.click(sb.at[0], sb.at[1]); await page.waitForTimeout(2200);
    await page.mouse.move(500, 300); await page.waitForTimeout(900);
    const after = await page.screenshot({ clip: zone });
    const same = Buffer.compare(before, after) === 0;
    const opts = await page.evaluate((z) => {
      const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
      return [...document.querySelectorAll('div,li,span,button')].map((e) => { const r = e.getBoundingClientRect();
        return { t: (e.innerText || '').replace(/\s+/g, ' ').trim(), r, kids: e.children.length }; })
        .filter((x) => x.t && x.t.length < 10 && x.r.x >= z.x && x.r.x < z.x + z.width
          && x.r.y >= z.y && x.r.y < z.y + z.height && x.r.width > 40 && x.r.height >= 14 && x.r.height < 44)
        .filter((x) => x.kids === 0)
        .map((x) => ({ t: x.t, y: Math.round(x.r.y) }))
        .filter((v, i, a) => a.findIndex((o) => o.t === v.t && Math.abs(o.y - v.y) < 6) === i);
    }, zone);
    console.log(`  点前/点后同一块像素：${same ? '**完全一样**（没开）' : '**变了**'}`);
    console.log(`  区内叶子：${JSON.stringify(opts)}`);
    out.sort = { button: sb.rect, pixelChanged: !same, leaves: opts };
    if (!same) { await shot(page, 'M-236-排序下拉.png'); out.shotSort = 'M-236-排序下拉.png'; }
    await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  } else out.sort = sb;

  await clickText('风格广场', 2000, 40);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1400);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1400);
  out.finalNodes = await page.evaluate(() => document.querySelectorAll('.react-flow__node').length);
  console.log(`\n═══ 收尾：节点 ${out.finalNodes} ═══`);

  await logStep(B, {
    id: 'BN4-account-cleanup-and-detail-panel',
    title: '查账号有没有被 BN3 弄脏 + 详情面板用集合差分读出来 + 排序换锚点',
    target: 'BN3 留了两笔糊涂账：① 收藏「再点一下回退」之后读到的提示条是**残留 toast**，'
      + '回退是否成功没验成，而「我的收藏」那一读又因锚点消失报 `广场没开`；'
      + '② 详情面板用「顶层浮层**数目**」判变化，结果 3→3 —— 数目一样但多了一枚 `z=800`。'
      + '⭐ 给用户账号留脏状态不能留到下一轮，本轮第一件事就是查清并清掉；'
      + '⭐ 浮层变化改用**集合差分**（身份 = class|rect|z），不再数数目。',
    evidence: out,
    visible_text: JSON.stringify({ 我的收藏_查: out.myFavBefore, 我的收藏_清后: out.myFavAfter,
      取消记录: out.cancelLog, 详情: out.detail, 排序: out.sort, 收尾节点数: out.finalNodes }).slice(0, 3000),
    shot: out.shotDetail || out.shotSort,
  });
  console.log('\nBN4 完成');
} catch (e) {
  console.log('⛔ 中止：' + e.message);
} finally {
  await browser.close();
}
