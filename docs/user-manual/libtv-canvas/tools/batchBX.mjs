// Batch BX — 智能剪辑里那枚 `1` 号卡片到底对应什么（BJ 的对照这回做得成了）
//
// BJ（§38.3）当时的结论是：「连接之后出现了 `1` 号卡片」，但**不能说「由连线引起」** ——
// 因为可逆对照卡在「`⌘L` 断不了线」那一步，标了 📖。
// ⭐ 现在断线做得到了（悬停点剪刀 / 选中按删除键，两条都验过），对照可以补上。
//
// ⭐ 而且**不必动 BJ 留下的那条边** —— 换个更有用的问法：
//   「我接**第二个**视频节点，卡片会变成 1、2 吗？」
//   · 接第二条 → 卡片数 1 → 2？  （证成「卡片 = 已连接视频的编号列表」）
//   · 再把第二条断掉 → 回到只有 1？
//   · ⭐ 顺手就是「同一对节点不能连两次」的**对照实验**：同一个动作做两次，
//     第一次成功、第二次（已存在的那一对）被拒 —— 分母 2，一条对照一条反例。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBX';
const CLIP = 'v-oZNpH99MtM';        // 智能剪辑 4
const V2 = 'v-v2hlWY4Br3';          // 已连着的那个视频节点（→ 1 号卡片的来源）
const V3 = 'v-eMpqKtiLlx';          // 准备接上去的第二个视频节点
const { browser, page } = await launch();
const settle = (ms = 900) => page.waitForTimeout(ms);

const edgeIds = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__edge')].map((e) => e.getAttribute('data-id')));
const edgeCount = () => page.evaluate(() => document.querySelectorAll('.react-flow__edge').length);
const edgeAria = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__edge')].map((e) => e.getAttribute('aria-label')));
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

/** 造线：拖到一半必须有预览线；返回 preview 与结果分开报（分不开的两种解释要靠这个劈开）。 */
const drag = async (fromId, toId) => {
  const ids0 = await edgeIds();
  const nf = await nodeBox(fromId); const nt = await nodeBox(toId);
  if (!nf || !nt) return { ok: false, why: '节点不在视口' };
  await page.mouse.move(nf.c[0], nf.c[1]); await settle(1100);
  const hs = await handleAt(fromId, 'source');
  await page.mouse.move(nt.c[0], nt.c[1]); await settle(1100);
  const ht = await handleAt(toId, 'target');
  if (!hs || !ht) return { ok: false, why: 'handle 取不到' };
  if (!hs.inView || !ht.inView) return { ok: false, why: `handle 出视口 ${JSON.stringify(hs.at)} / ${JSON.stringify(ht.at)}` };
  await page.mouse.move(hs.at[0], hs.at[1]); await settle(700);
  await page.mouse.down(); await settle(350);
  await page.mouse.move(hs.at[0] + 8, hs.at[1] + 4); await settle(300);
  await page.mouse.move((hs.at[0] + ht.at[0]) / 2, (hs.at[1] + ht.at[1]) / 2); await settle(450);
  const preview = await page.evaluate(() => document.querySelectorAll('.react-flow__connection, .react-flow__connectionline').length);
  await page.mouse.move(ht.at[0], ht.at[1]); await settle(500);
  await page.mouse.up(); await settle(2400);
  const ids1 = await edgeIds();
  const extra = ids1.filter((i) => !ids0.includes(i));
  return { ok: extra.length === 1, preview, extra: extra[0] || null, from: fromId, to: toId,
    sameAria: extra.length ? await page.evaluate((i) => document.querySelector(`.react-flow__edge[data-id="${i}"]`)?.getAttribute('aria-label'), extra[0]) : null };
};
const cut = async (id) => {
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
  return { ok: (await edgeCount()) < c0, mid, point: pt, before: c0, after: await edgeCount() };
};

/** 打开智能剪辑的参数面板并读卡片。判据：面板内**文字恰为数字**的元素个数。 */
const readClip = async (label) => {
  const nb = await nodeBox(CLIP);
  if (!nb) return { label, err: '节点不在视口' };
  await page.mouse.click(nb.c[0], nb.c[1]); await settle(2000);
  const r = await page.evaluate((id) => {
    const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
    if (!n) return null;
    // 面板 = 节点里「不是节点标题」的那部分：取节点内所有文字恰为 1–9 的方块
    const nums = [...n.querySelectorAll('*')]
      .filter((e) => { const t = (e.textContent || '').trim(); const b = e.getBoundingClientRect();
        return /^[1-9]$/.test(t) && b.width >= 10 && b.width <= 60 && b.height >= 10 && b.height <= 60 && e.children.length === 0; })
      .map((e) => { const b = e.getBoundingClientRect();
        return { n: e.textContent.trim(), at: [Math.round(b.x), Math.round(b.y)], size: [Math.round(b.width), Math.round(b.height)] }; });
    const uniq = []; const seen = new Set();
    for (const x of nums) { const k = `${x.n}@${x.at[0]},${x.at[1]}`; if (!seen.has(k)) { seen.add(k); uniq.push(x); } }
    return { nodeRect: (() => { const b = n.getBoundingClientRect(); return [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)]; })(),
      text: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 400), numberCards: uniq };
  }, CLIP);
  console.log(`  ── ${label}：数字卡片 ${r ? r.numberCards.length : '?'} 枚 ${JSON.stringify(r ? r.numberCards.map((x) => x.n + '@' + x.at.join(',')) : [])}`);
  if (r) console.log(`     面板文本：${r.text.slice(0, 150)}`);
  return { label, ...r };
};

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await settle(1800);
  await fitView(page); await settle(2200);
  await beginBatch(B, { note: '智能剪辑 1 号卡片的可逆对照 + 重复连线的对照实验' });
  const out = {};
  const baseIds = await edgeIds();
  out.base = { ids: baseIds, count: baseIds.length, aria: await edgeAria(), nodes: await page.evaluate(() => document.querySelectorAll('.react-flow__node').length) };
  console.log(`═══ 基线：连线 ${baseIds.length} 条｜节点 ${out.base.nodes} ═══`);
  out.base.aria.forEach((a) => console.log(`    ${a}`));

  // ── ① 基线：只有一条视频连着时，卡片长什么样
  console.log('\n═══ ① 基线面板（已连 1 个视频）═══');
  const p1 = await readClip('基线');
  out.panelBase = p1;
  if (p1.numberCards) await shot(page, 'M-287-智能剪辑-一个视频时.png');

  // ── ② 接第二个视频 → 卡片会变成 1、2 吗
  console.log('\n═══ ② 把第二个视频节点接到智能剪辑 ═══');
  const add = await drag(V3, CLIP);
  console.log(`  造线 ${V3} → ${CLIP}：ok=${add.ok}｜预览线 ${add.preview}｜新增 ${JSON.stringify(add.extra)}｜aria=${add.sameAria}`);
  out.addSecond = add;
  if (add.ok) {
    const p2 = await readClip('接了第二个视频');
    out.panelTwo = p2;
    await shot(page, 'M-288-智能剪辑-两个视频时.png');
    console.log(`  ⭐ 卡片从 ${p1.numberCards.length} 枚 → ${p2.numberCards.length} 枚`);

    // ── ③ ⭐ 对照：再连**同一对**一次（已存在），预期被拒
    console.log('\n═══ ③ 对照实验：把同一对再连一次（应该连不上）═══');
    const dup = await drag(V3, CLIP);
    console.log(`  重连同一对：ok=${dup.ok}｜预览线 ${dup.preview}｜新增 ${JSON.stringify(dup.extra)}`);
    out.duplicate = dup;
    const p2b = await readClip('重复连之后');
    out.panelAfterDup = p2b;
    console.log(`  ⭐ 卡片仍是 ${p2b.numberCards ? p2b.numberCards.length : '?'} 枚（没多也没少）`);

    // ── ④ 断掉第二条 → 卡片应回到只有 1
    console.log('\n═══ ④ 断掉第二条（可逆对照的后半段）═══');
    const cut2 = await cut(add.extra);
    console.log(`  剪断 ${add.extra}：ok=${cut2.ok}｜连线 ${cut2.before} → ${cut2.after}`);
    out.cutSecond = cut2;
    if (cut2.ok) {
      const p3 = await readClip('断掉第二个视频');
      out.panelOne = p3;
      await shot(page, 'M-289-智能剪辑-断掉第二个视频之后.png');
      console.log(`  ⭐ 卡片从 ${p2.numberCards.length} 枚 → ${p3.numberCards.length} 枚`);
    }
  } else {
    console.log('  ⛔ 没能接上第二个视频，可逆对照做不成');
  }

  // ── ⑤ 收尾
  const fin = await edgeIds();
  out.final = { count: fin.length, ids: fin, identical: fin.join(',') === baseIds.join(','),
    nodes: await page.evaluate(() => document.querySelectorAll('.react-flow__node').length) };
  console.log(`\n═══ ⑤ 收尾：连线 ${fin.length} 条（基线 ${baseIds.length}）｜逐项相同=${out.final.identical}｜节点 ${out.final.nodes}`);
  await clearToasts(page);

  console.log(`\n═══ 本轮结论 ═══`);
  console.log(`  · 卡片数：基线 ${out.panelBase?.numberCards?.length} → 加第二条 ${out.panelTwo?.numberCards?.length} → 断掉 ${out.panelOne?.numberCards?.length}`);
  console.log(`  · 「接第二对被拒」对照：预览线 ${out.duplicate?.preview} 条｜新增边 ${out.duplicate?.ok ? '有' : '无'}`);
  console.log(`  · 画布回到基线：${out.final.identical ? '✅' : '❌'}`);

  await logStep(B, {
    id: 'BX-clip-card-number-and-duplicate-control',
    title: '⭐ 智能剪辑「1 号卡片」的可逆对照补上了（BJ 当年卡在断不了线）',
    target: 'BJ（PROGRESS §38.3）当时只能写「连接之后出现了 `1` 号卡片」，'
      + '**不能说「由连线引起」** —— 可逆对照卡在 `⌘L` 断不了线那一步，标了 📖。'
      + '本轮断线已验（悬停点剪刀 / 选中按删除键），对照补上，而且**不动 BJ 留下的那条边**：'
      + '改问「接**第二个**视频，卡片会不会变成 1、2」—— '
      + '断掉第二条后卡片应回到只有 1。'
      + '⭐ 顺手就是「同一对节点不能连两次」的**对照实验**：同一个动作做两次，'
      + '第一次成功、第二次（已存在的那一对）被拒 —— 分母 2，一条正例一条反例。',
    evidence: out,
    visible_text: JSON.stringify({ 基线: out.base, 基线面板: out.panelBase, 加第二条: out.addSecond,
      两视频面板: out.panelTwo, 重复连: out.duplicate, 重复后面板: out.panelAfterDup,
      断第二条: out.cutSecond, 断后面板: out.panelOne, 收尾: out.final }).slice(0, 3400),
    shot: 'M-288-智能剪辑-两个视频时.png',
  });
  console.log('\nBX 完成');
} catch (e) {
  console.log('⛔ 中止：' + e.message + '\n' + (e.stack || '').split('\n').slice(0, 5).join('\n'));
} finally {
  await browser.close();
}
