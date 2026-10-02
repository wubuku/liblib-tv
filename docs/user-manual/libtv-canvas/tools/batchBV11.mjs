// Batch BV11 — 结案取景：干净的「断线前 / 断线后」两张图，并把断线**独立复现一次**。
//
// 为什么重拍：
// ① BV7/BV10 的截图右侧都开着「新对话」面板（TV Director 助手），遮掉半张画布；
// ② ⭐ `M-281-点剪刀之后连线断了.png` 里，图片节点 2 与视频节点 3 之间**还看得见一条灰线**，
//    和「已断开」在画面上打架。DOM 说 3→2、id 确实没了，但图上说不清楚就不能用。
//    —— 截图必须能**自己讲完这个故事**，不能靠正文去解释。
//
// 为什么复现：断线是**破坏性**结论，只跑一遍就写进手册是不负责的。本轮造**两条**自造边，
//    各点一次剪刀，两次都要「id 消失 + 画布回到基线」。
//
// ⭐ 顺带把 TV Director 面板关掉并**自证它关了**（否则又拍出一张遮半边的图）。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBV11';
const { browser, page } = await launch();
const settle = (ms = 900) => page.waitForTimeout(ms);

const edgeIds = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__edge')].map((e) => e.getAttribute('data-id')));
const edgeCount = () => page.evaluate(() => document.querySelectorAll('.react-flow__edge').length);
const nodeCount = () => page.evaluate(() => document.querySelectorAll('.react-flow__node').length);
const edgeInfo = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__edge')].map((g) => {
  const p = g.querySelector('path'); let L = 0; try { L = p.getTotalLength(); } catch { L = 0; }
  const ctm = p && p.getScreenCTM(); let mid = null;
  if (ctm && L) { const q = p.getPointAtLength(L / 2); const s = new DOMPoint(q.x, q.y, 0, 1).matrixTransform(ctm); mid = [Math.round(s.x), Math.round(s.y)]; }
  return { id: g.getAttribute('data-id'), aria: g.getAttribute('aria-label'), mid,
    inView: mid && mid[0] > 3 && mid[0] < 1437 && mid[1] > 3 && mid[1] < 786 };
}));

/** 关掉 TV Director「新对话」侧栏，并自证它真的关了。 */
const closeDirector = async () => {
  const probe = () => page.evaluate(() => [...document.querySelectorAll('div,section,aside')]
    .filter((d) => { const r = d.getBoundingClientRect(); const t = (d.innerText || '').replace(/\s+/g, ' ');
      return r.width > 300 && r.height > 400 && t.includes('让 TV Director 辅助你的无限创意'); })
    .map((d) => { const r = d.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; }));
  for (let round = 0; round < 4; round += 1) {
    const p = await probe();
    if (!p.length) return { closed: true, rounds: round };
    // 找面板内的关闭/最小化按钮：标题栏右端那排小图标
    const hit = await page.evaluate((box) => {
      const [x, y, w, h] = box;
      const cands = [...document.querySelectorAll('button,[role="button"],[class*="close" i],[class*="Close"]')]
        .map((b) => { const r = b.getBoundingClientRect();
          return { el: b, r, label: b.getAttribute('aria-label') || b.getAttribute('title') || (b.className || '').toString().slice(0, 40) }; })
        .filter((c) => c.r.x > x + w - 260 && c.r.y > y && c.r.y < y + 60 && c.r.width > 8 && c.r.width < 60)
        .sort((a, b) => b.r.x - a.r.x);
      if (!cands.length) return null;
      const t = cands[cands.length - 1];
      return { label: t.label, at: [Math.round(t.r.x + t.r.width / 2), Math.round(t.r.y + t.r.height / 2)] };
    }, p[0]);
    if (!hit) { await page.mouse.click(p[0][0] + p[0][2] / 2, p[0][1] + 20); }
    else { await page.mouse.click(hit.at[0], hit.at[1]); }
    await settle(1400);
  }
  const left = await probe();
  return { closed: !left.length, stillThere: left };
};

const nodeBox = (id) => page.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return null; const r = n.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
}, id);
const handleAt = (nodeId, kind) => page.evaluate(({ nodeId, kind }) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nodeId}"]`);
  if (!n) return null;
  const h = [...n.querySelectorAll('.react-flow__handle')].find((x) => kind === 'source'
    ? /\bsource\b/.test(x.getAttribute('class') || '') : /\btarget\b/.test(x.getAttribute('class') || ''));
  if (!h) return null;
  const r = h.getBoundingClientRect();
  return { at: [Math.round(r.x), Math.round(r.y)], hit: (() => {
    const e = document.elementFromPoint(Math.round(r.x), Math.round(r.y));
    return e ? `${e.tagName}.${(e.getAttribute('class') || '').toString().split(' ').slice(0, 2).join('.')}` : null; })() };
}, { nodeId, kind });

/** 造一条边：拖到一半必须有连接预览线，否则报失败。 */
const makeEdge = async (a, b) => {
  const n0 = await edgeCount();
  const ids0 = await edgeIds();
  const na = await nodeBox(a); const nb = await nodeBox(b);
  if (!na || !nb) return { ok: false, why: '节点不在视口' };
  await page.mouse.move(na[0], na[1]); await settle(1100);
  const hs = await handleAt(a, 'source');
  await page.mouse.move(nb[0], nb[1]); await settle(1100);
  const ht = await handleAt(b, 'target');
  if (!hs || !ht) return { ok: false, why: 'handle 取不到' };
  await page.mouse.move(hs.at[0], hs.at[1]); await settle(700);
  await page.mouse.down(); await settle(350);
  await page.mouse.move(hs.at[0] + 8, hs.at[1] + 4); await settle(300);
  await page.mouse.move((hs.at[0] + ht.at[0]) / 2, (hs.at[1] + ht.at[1]) / 2); await settle(450);
  const preview = await page.evaluate(() => document.querySelectorAll('.react-flow__connection, .react-flow__connectionline').length);
  await page.mouse.move(ht.at[0], ht.at[1]); await settle(450);
  await page.mouse.up(); await settle(2400);
  const n1 = await edgeCount();
  const extra = (await edgeIds()).filter((i) => !ids0.includes(i));
  return { ok: n1 > n0 && extra.length === 1, preview, from: a, to: b, hs, ht, n0, n1, extra };
};

/** 悬停某条边中点，把剪刀点出来。 */
const scissorsOn = async (id) => {
  const info = await edgeInfo();
  const m = info.find((x) => x.id === id);
  if (!m || !m.inView) return { ok: false, why: '中点不在视口内', m };
  await page.mouse.move(200, 780); await settle(600);
  await page.mouse.move(m.mid[0], m.mid[1]); await settle(1700);
  const list = await page.evaluate(([mx, my]) => [...document.querySelectorAll('.scissors-enter')].map((e) => {
    const r = e.getBoundingClientRect(); const c = [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
    return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], center: c,
      near: Math.abs(c[0] - mx) < 40 && Math.abs(c[1] - my) < 40,
      onClick: !!Object.keys(e).find((k) => k.startsWith('__reactProps$') && typeof e[k].onClick === 'function') };
  }), m.mid);
  const mine = list.filter((s) => s.near);
  return { ok: mine.length > 0, mid: m.mid, mine, all: list.length };
};

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await settle(1600);
  await fitView(page); await settle(2200);
  await beginBatch(B, { note: '干净取景 + 断线独立复现两次' });
  const out = {};

  // ── ① 关掉 TV Director 侧栏并自证
  const closed = await closeDirector();
  out.director = closed;
  console.log(`═══ ① TV Director 侧栏：${closed.closed ? '✅ 已关掉' : '❌ 还在 ' + JSON.stringify(closed.stillThere)} ═══`);
  if (!closed.closed) { await page.keyboard.press('Escape'); await settle(1200); console.log(`   再按 Esc 后：${JSON.stringify(await closeDirector())}`); }
  await clearToasts(page); await settle(800);

  const base = await edgeInfo();
  const baseIds = base.map((e) => e.id);
  out.base = { ids: baseIds, count: base.length, nodes: await nodeCount(), map: base.map((e) => ({ id: e.id, aria: e.aria, mid: e.mid })) };
  console.log(`  基线：连线 ${base.length} 条 ${JSON.stringify(baseIds)}｜节点 ${out.base.nodes}`);
  base.forEach((e) => console.log(`    ${e.id}｜${e.aria}｜中点 ${JSON.stringify(e.mid)}`));

  // ── ② M-279：悬停已有连线 → 剪刀（干净画面）
  const exist = base.find((e) => e.inView);
  let sc = null;
  if (exist) {
    sc = await scissorsOn(exist.id);
    console.log(`\n═══ ② 悬停 ${exist.id}：剪刀 ${sc.mine ? sc.mine.length : 0} 枚 ${JSON.stringify(sc.mine || sc.why)}`);
    if (sc.ok) { await shot(page, 'M-279-连线中点悬停出的剪刀.png'); console.log('  📸 M-279 已拍'); }
  }
  out.hover = sc;
  await page.mouse.move(200, 780); await settle(700);

  // ── ③④ 造边 → 点剪刀，做两遍
  const runs = [];
  const plan = [['i-9nlG6HdjK2', 'v-v2hlWY4Br3'], ['i-9nlG6HdjK2', 'v-eMpqKtiLlx', '换一对不同目标']];
  for (let i = 0; i < 2; i += 1) {
    const pair = plan[i];
    console.log(`\n═══ ${i === 0 ? '③' : '④'} 第 ${i + 1} 次复现：造边 ${pair[0]} → ${pair[1]} ═══`);
    const made = await makeEdge(pair[0], pair[1]);
    console.log(`  造边：ok=${made.ok}｜拖到一半预览线 ${made.preview} 条｜连线 ${made.n0} → ${made.n1}｜新增 ${JSON.stringify(made.extra || [])}`);
    if (!made.ok) { runs.push({ i, made, click: null, note: '没造出边，本轮不点' }); continue; }
    const mineId = made.extra[0];
    const scs = await scissorsOn(mineId);
    console.log(`  自造边中点 ${JSON.stringify(scs.mid)}：剪刀 ${scs.mine ? scs.mine.length : 0} 枚`);
    if (i === 0) { await shot(page, 'M-280-自造连线中点的剪刀.png'); console.log('  📸 M-280 已拍'); }
    if (!scs.ok) { runs.push({ i, made, click: null, note: '中点没剪刀' }); continue; }
    const pt = scs.mine[scs.mine.length - 1].center;
    const c0 = await edgeCount(); const ids0 = await edgeIds();
    await page.mouse.move(pt[0], pt[1]); await settle(700);
    await page.mouse.down(); await settle(180);
    await page.mouse.up(); await settle(3200);
    const c1 = await edgeCount(); const ids1 = await edgeIds();
    const gone = !ids1.includes(mineId);
    console.log(`  ⭐ 点剪刀 @${JSON.stringify(pt)}：连线 ${c0} → ${c1}｜自造边消失=${gone ? '✅' : '❌'}`);
    console.log(`     ${JSON.stringify(ids0)} → ${JSON.stringify(ids1)}`);
    if (i === 0) {
      await page.mouse.move(200, 780); await settle(900);
      await shot(page, 'M-281-点剪刀之后连线断了.png'); console.log('  📸 M-281 已拍');
    }
    runs.push({ i, made, click: { point: pt, before: c0, after: c1, gone, ids0, ids1 } });
  }
  out.runs = runs;

  // ── ⑤ 收尾：必须回到基线
  const fin = await edgeInfo();
  const finIds = fin.map((e) => e.id);
  out.final = { count: fin.length, ids: finIds, nodes: await nodeCount(),
    identical: finIds.join(',') === baseIds.join(','),
    baseIntact: baseIds.every((i) => finIds.includes(i)) };
  console.log(`\n═══ ⑤ 收尾复核 ═══`);
  console.log(`  连线 ${out.final.count} 条（基线 ${baseIds.length}）｜逐项相同=${out.final.identical}｜原有全在=${out.final.baseIntact}｜节点 ${out.final.nodes}`);
  await clearToasts(page);

  const ok = runs.filter((r) => r.click && r.click.gone).length;
  const total = runs.filter((r) => r.click).length;
  console.log(`\n═══ 本轮结论 ═══`);
  console.log(`  · 断线复现：${total === 0 ? '⛔ 没测到（分母 0）' : `${ok}/${total} 次点剪刀后自造边消失`}`);
  console.log(`  · 画布回到基线：${out.final.identical ? '✅' : '❌'}`);

  await logStep(B, {
    id: 'BV11-clean-shots-and-replication',
    title: '断线结论独立复现 + 干净取景（关掉 TV Director 侧栏）',
    target: '断线是**破坏性**结论，只跑一遍就写进手册不负责 —— 本轮造**两条**自造边各点一次剪刀，'
      + '两次都要「id 消失 + 画布回到基线」。'
      + '⛔ 上一轮的截图右侧开着 TV Director「新对话」侧栏遮掉半张画布，'
      + '且 `M-281` 里两节点间**还看得见一条灰线**和「已断开」打架 —— '
      + 'DOM 说 3→2 但图上说不清楚就不能用：**截图必须能自己讲完这个故事**。',
    evidence: out,
    visible_text: JSON.stringify({ 侧栏: out.director, 基线: out.base, 悬停: out.hover, 复现: out.runs, 收尾: out.final }).slice(0, 3400),
    shot: 'M-281-点剪刀之后连线断了.png',
  });
  console.log('\nBV11 完成');
} catch (e) {
  console.log('⛔ 中止：' + e.message + '\n' + (e.stack || '').split('\n').slice(0, 5).join('\n'));
} finally {
  await browser.close();
}
