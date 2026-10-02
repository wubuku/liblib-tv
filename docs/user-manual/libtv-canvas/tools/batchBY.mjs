// Batch BY — 智能剪辑卡片：先修测量，再做 BJ 当年做不成的可逆对照。
//
// BX 的两条教训：
// ① **读数自相矛盾就不能用**：BX 报「智能剪辑里有 1 枚数字卡片」，但那张 `1` 的坐标是
//    `[750,282]`，而智能剪辑节点自身的矩形是 `[979,55,169,169]` —— **卡片落在了节点外面**。
//    一个 169×169 的盒子也装不下「参考 + 提示词 + 默认模式 + 16:9·720P·30s」。
//    ⭐ 治法：**按节点逐个点名**，每张卡片报「属于哪个节点」，归属由结构决定，不由猜决定。
// ② 接第二个视频那次 `preview: 0` —— 拖拽**根本没启动**，不是「连不上」。
//    而画布上只有两个视频节点，其中一个已经连着智能剪辑，所以「接第二个」这条路没有素材。
//
// ⭐ 于是改做 BJ 当年想做的那个对照（§38.3 卡在「`⌘L` 断不了线」）：
//    断开「视频 → 智能剪辑」→ 卡片应消失 → 再接回来 → 卡片应恢复。
//    断线（悬停点剪刀）与接回（拖 source → target）都已各自验过，才敢动这条边。
//    ⚠️ 代价：接回来的边 **id 会变**（`e-ptEDqoajM7` → 新 id），两端与方向不变。
//    如实记录，不假装 id 一样。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBY';
const CLIP = 'v-oZNpH99MtM';
const V2 = 'v-v2hlWY4Br3';
const OLD_EDGE = 'e-ptEDqoajM7';
const { browser, page } = await launch();
const settle = (ms = 900) => page.waitForTimeout(ms);

const edgeIds = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__edge')].map((e) => e.getAttribute('data-id')));
const edgeAria = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__edge')].map((e) => e.getAttribute('aria-label')));
const edgeCount = () => page.evaluate(() => document.querySelectorAll('.react-flow__edge').length);
const nodeBox = (id) => page.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return null; const r = n.getBoundingClientRect();
  return { c: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], r: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; }, id);
const handleAt = (nodeId, kind) => page.evaluate(({ nodeId, kind }) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nodeId}"]`);
  if (!n) return null;
  const h = [...n.querySelectorAll('.react-flow__handle')].find((x) => kind === 'source' ? /\bsource\b/.test(x.getAttribute('class') || '') : /\btarget\b/.test(x.getAttribute('class') || ''));
  if (!h) return null; const r = h.getBoundingClientRect();
  return { at: [Math.round(r.x), Math.round(r.y)], inView: r.x > 2 && r.x < 1438 && r.y > 2 && r.y < 808 };
}, { nodeId, kind });

/** ⭐ 逐节点点名：每个节点里有几张「文字恰为数字」的小卡片，并报告卡片是否落在节点矩形内。 */
const cardCensus = async (label) => {
  const r = await page.evaluate(() => {
    const out = [];
    for (const n of document.querySelectorAll('.react-flow__node')) {
      const nr = n.getBoundingClientRect();
      const cards = [...n.querySelectorAll('*')]
        .filter((e) => { const t = (e.textContent || '').trim(); const b = e.getBoundingClientRect();
          return /^[1-9]$/.test(t) && b.width >= 8 && b.width <= 60 && b.height >= 8 && b.height <= 60 && e.children.length === 0; })
        .map((e) => { const b = e.getBoundingClientRect();
          return { n: e.textContent.trim(), at: [Math.round(b.x), Math.round(b.y)], size: [Math.round(b.width), Math.round(b.height)],
            inside: b.x >= nr.x - 1 && b.x + b.width <= nr.x + nr.width + 1 }; });
      const uniq = []; const seen = new Set();
      for (const c of cards) { const k = `${c.n}@${c.at[0]},${c.at[1]}`; if (!seen.has(k)) { seen.add(k); uniq.push(c); } }
      if (uniq.length) out.push({ id: n.getAttribute('data-id'),
        title: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 24),
        rect: [Math.round(nr.x), Math.round(nr.y), Math.round(nr.width), Math.round(nr.height)], cards: uniq });
    }
    return out;
  });
  console.log(`  ── ${label}：${r.length} 个节点带数字卡片`);
  r.forEach((n) => console.log(`     ${n.id}（${n.title}）矩形 ${JSON.stringify(n.rect)} → 卡片 ${JSON.stringify(n.cards)}`));
  return { label, nodes: r };
};

const readClipText = async () => {
  const nb = await nodeBox(CLIP);
  await page.mouse.click(nb.c[0], nb.c[1]); await settle(2000);
  return page.evaluate((id) => {
    const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
    const r = n.getBoundingClientRect();
    return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      text: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 300) };
  }, CLIP);
};

const cutEdge = async (id) => {
  const mid = await page.evaluate((i) => { const g = document.querySelector(`.react-flow__edge[data-id="${i}"]`);
    const p = g && g.querySelector('path'); if (!p) return null;
    let L = 0; try { L = p.getTotalLength(); } catch { L = 0; }
    const ctm = p.getScreenCTM(); if (!ctm || !L) return null;
    const q = p.getPointAtLength(L / 2); const s = new DOMPoint(q.x, q.y, 0, 1).matrixTransform(ctm);
    return [Math.round(s.x), Math.round(s.y)]; }, id);
  if (!mid) return { ok: false, why: '取不到中点' };
  await page.mouse.move(200, 780); await settle(600);
  await page.mouse.move(mid[0], mid[1]); await settle(1700);
  const sc = await page.evaluate(([mx, my]) => [...document.querySelectorAll('.scissors-enter')]
    .map((e) => { const r = e.getBoundingClientRect(); const c = [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
      return { c, near: Math.abs(c[0] - mx) < 40 && Math.abs(c[1] - my) < 40 }; }).filter((s) => s.near), mid);
  if (!sc.length) return { ok: false, why: '中点没剪刀' };
  const pt = sc[sc.length - 1].c;
  const c0 = await edgeCount();
  await page.mouse.move(pt[0], pt[1]); await settle(600);
  await page.mouse.down(); await settle(180); await page.mouse.up(); await settle(3000);
  return { ok: (await edgeCount()) < c0, point: pt, before: c0, after: await edgeCount() };
};
const dragEdge = async (fromId, toId) => {
  const ids0 = await edgeIds();
  const nf = await nodeBox(fromId); const nt = await nodeBox(toId);
  if (!nf || !nt) return { ok: false, why: '节点不在视口' };
  await page.mouse.move(nf.c[0], nf.c[1]); await settle(1100);
  const hs = await handleAt(fromId, 'source');
  await page.mouse.move(nt.c[0], nt.c[1]); await settle(1100);
  const ht = await handleAt(toId, 'target');
  if (!hs || !ht) return { ok: false, why: 'handle 取不到' };
  if (!hs.inView || !ht.inView) return { ok: false, why: 'handle 出视口' };
  await page.mouse.move(hs.at[0], hs.at[1]); await settle(700);
  await page.mouse.down(); await settle(350);
  await page.mouse.move(hs.at[0] + 8, hs.at[1] + 4); await settle(300);
  await page.mouse.move((hs.at[0] + ht.at[0]) / 2, (hs.at[1] + ht.at[1]) / 2); await settle(450);
  const preview = await page.evaluate(() => document.querySelectorAll('.react-flow__connection, .react-flow__connectionline').length);
  await page.mouse.move(ht.at[0], ht.at[1]); await settle(500);
  await page.mouse.up(); await settle(2400);
  const extra = (await edgeIds()).filter((i) => !ids0.includes(i));
  return { ok: extra.length === 1, preview, extra: extra[0] || null,
    aria: extra.length ? await page.evaluate((i) => document.querySelector(`.react-flow__edge[data-id="${i}"]`)?.getAttribute('aria-label'), extra[0]) : null };
};

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await settle(1800);
  await fitView(page); await settle(2200);
  await beginBatch(B, { note: '修卡片测量 + 断开/接回做可逆对照' });
  const out = {};
  const baseIds = await edgeIds();
  const baseAria = await edgeAria();
  out.base = { ids: baseIds, aria: baseAria, nodes: await page.evaluate(() => document.querySelectorAll('.react-flow__node').length) };
  console.log(`═══ 基线：连线 ${baseIds.length} 条｜节点 ${out.base.nodes} ═══`);
  baseAria.forEach((a) => console.log(`    ${a}`));

  // ── ① 卡片归属普查（修 BX 的测量）
  console.log('\n═══ ① 卡片归属普查 ═══');
  const c1 = await cardCensus('基线（已连 1 个视频）');
  out.censusBase = c1;
  const clip0 = await readClipText();
  out.clipTextBase = clip0;
  console.log(`  智能剪辑矩形 ${JSON.stringify(clip0.rect)}｜文本「${clip0.text.slice(0, 120)}」`);
  await shot(page, 'M-287-智能剪辑-已连一个视频.png');

  // ── ② 断开「视频 → 智能剪辑」
  console.log(`\n═══ ② 断开 ${OLD_EDGE}（视频 → 智能剪辑）═══`);
  const cut = await cutEdge(OLD_EDGE);
  console.log(`  剪断：ok=${cut.ok}｜连线 ${cut.before} → ${cut.after}`);
  out.cut = cut;
  if (!cut.ok) { console.log('  ⛔ 没断开，本轮到此为止'); }
  else {
    const c2 = await cardCensus('断开之后');
    out.censusCut = c2;
    const clip1 = await readClipText();
    out.clipTextCut = clip1;
    console.log(`  智能剪辑文本「${clip1.text.slice(0, 120)}」`);
    await shot(page, 'M-288-智能剪辑-断开视频之后.png');

    // ── ③ 接回来
    console.log('\n═══ ③ 接回来 ═══');
    const back = await dragEdge(V2, CLIP);
    console.log(`  拖 ${V2} → ${CLIP}：ok=${back.ok}｜预览线 ${back.preview}｜新 id ${JSON.stringify(back.extra)}｜aria=${back.aria}`);
    out.reconnect = back;
    if (back.ok) {
      const c3 = await cardCensus('接回来之后');
      out.censusBack = c3;
      const clip2 = await readClipText();
      out.clipTextBack = clip2;
      console.log(`  智能剪辑文本「${clip2.text.slice(0, 120)}」`);
      await shot(page, 'M-289-智能剪辑-接回视频之后.png');
      const cards = (x) => (x.nodes || []).reduce((s, n) => s + n.cards.filter((c) => c.inside).length, 0);
      console.log(`  ⭐ 节点内卡片数（只算落在矩形内的）：基线 ${cards(c1)} → 断开 ${cards(c2)} → 接回 ${cards(c3)}`);
      out.cardCounts = { base: cards(c1), cut: cards(c2), back: cards(c3) };
    }
  }

  // ── ④ 收尾：语义复原（id 可能变，如实记）
  const fin = await edgeIds(); const finAria = await edgeAria();
  out.final = { count: fin.length, ids: fin, aria: finAria, nodes: await page.evaluate(() => document.querySelectorAll('.react-flow__node').length),
    sameIds: fin.join(',') === baseIds.join(','),
    sameAria: finAria.slice().sort().join(' | ') === baseAria.slice().sort().join(' | ') };
  console.log(`\n═══ ④ 收尾 ═══`);
  console.log(`  连线 ${fin.length} 条｜节点 ${out.final.nodes}`);
  console.log(`  id 与基线逐项相同：${out.final.sameIds}｜两端与方向相同：${out.final.sameAria}`);
  finAria.forEach((a) => console.log(`    ${a}`));
  if (!out.final.sameIds) console.log(`  ⚠️ 被剪断再接回的边 id 变了（${OLD_EDGE} → ${fin.filter((i) => !baseIds.includes(i)).join(',') || '无'}），两端与方向不变`);
  await clearToasts(page);

  console.log(`\n═══ 本轮结论 ═══`);
  const ownerSummary = (out.censusBase.nodes || []).map((n) => `${n.id}: ${n.cards.map((c) => c.n + (c.inside ? '' : '(出框)')).join('/')}`);
  console.log(`  · 卡片归属：${JSON.stringify(ownerSummary)}`);
  console.log(`  · 断开 → 卡片：${out.cardCounts ? `${out.cardCounts.base} → ${out.cardCounts.cut}` : '⛔ 没做成'}`);
  console.log(`  · 接回 → 卡片：${out.cardCounts ? `${out.cardCounts.cut} → ${out.cardCounts.back}` : '⛔ 没做成'}`);

  await logStep(B, {
    id: 'BY-clip-card-reversible-control',
    title: '智能剪辑卡片：先修测量，再把 BJ 当年做不成的可逆对照补上',
    target: 'BX 读到的「1 号卡片」**自相矛盾**（卡片坐标 `[750,282]` 落在节点矩形 `[979,55,169,169]` 之外），'
      + '所以本轮先**按节点逐个点名**修测量，只认「落在节点矩形内」的卡片。'
      + '⭐ 然后做 BJ（§38.3）当年卡在「`⌘L` 断不了线」的那个对照：'
      + '断开「视频 → 智能剪辑」→ 卡片应消失 → 再接回来 → 卡片应恢复。'
      + '⚠️ 代价：接回来的边 **id 会变**（两端与方向不变），如实记录。',
    evidence: out,
    visible_text: JSON.stringify({ 基线: out.base, 普查: out.censusBase, 剪断: out.cut,
      断后普查: out.censusCut, 接回: out.reconnect, 回后普查: out.censusBack,
      卡片数: out.cardCounts, 收尾: out.final }).slice(0, 3400),
    shot: 'M-287-智能剪辑-已连一个视频.png',
  });
  console.log('\nBY 完成');
} catch (e) {
  console.log('⛔ 中止：' + e.message + '\n' + (e.stack || '').split('\n').slice(0, 5).join('\n'));
} finally {
  await browser.close();
}
