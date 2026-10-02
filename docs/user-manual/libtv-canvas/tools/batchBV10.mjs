// Batch BV10 — ⭐⭐⭐ 点剪刀。顺便把 BV9 留在画布上的那条边清掉。
//
// 上一轮的两件事：
// ① ⭐ 造线成功：`i-9nlG6HdjK2 → v-v2hlWY4Br3` 造出 `e-w1H9Qs9Rwx`，连线 2 → 3。
//    「拖到一半读现场」这个判据立住了：成功那次半程有 2 条 `.react-flow__connection` 预览线，
//    失败那次 0 条 —— 两种失败原因被一次读数劈开。
// ② ⛔ BV9 结束时没清理，画布上多了一条边。**这是我留下的东西，必须由我自己清掉。**
//
// ⭐ 而这条自造边正好是**最理想的对象**：它属于我，删掉它零风险；
//    更重要的是，**现在我已经知道线怎么接回去了**（拖 source → target，拖到一半要有预览线），
//    所以即便剪刀失灵，我也有一条已验证的复原路。**回退动作先复核，再用它冒险。**
//
// 结论口径：只有当「点剪刀」这一段真的执行了，才允许输出「能/不能」。
// 分母为 0 时输出必须是「⛔ 没测到」——BV6 已经吃过一次这个亏。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBV10';
const MINE = 'e-w1H9Qs9Rwx';            // BV9 造出来的那条，属于我
const { browser, page } = await launch();
const settle = (ms = 900) => page.waitForTimeout(ms);

const edgeIds = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__edge')].map((e) => e.getAttribute('data-id')));
const edgeCount = () => page.evaluate(() => document.querySelectorAll('.react-flow__edge').length);
const nodeCount = () => page.evaluate(() => document.querySelectorAll('.react-flow__node').length);
const edgeMids = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__edge')].map((g) => {
  const p = g.querySelector('path'); let L = 0; try { L = p.getTotalLength(); } catch { L = 0; }
  const ctm = p && p.getScreenCTM(); let mid = null;
  if (ctm && L) { const q = p.getPointAtLength(L / 2); const s = new DOMPoint(q.x, q.y, 0, 1).matrixTransform(ctm); mid = [Math.round(s.x), Math.round(s.y)]; }
  return { id: g.getAttribute('data-id'), aria: g.getAttribute('aria-label'), mid,
    inView: mid && mid[0] > 3 && mid[0] < 1437 && mid[1] > 3 && mid[1] < 786 };
}));

const nodeBox = (id) => page.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return null; const r = n.getBoundingClientRect();
  return { c: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], r: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
}, id);
const handleAt = (nodeId, kind) => page.evaluate(({ nodeId, kind }) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nodeId}"]`);
  if (!n) return null;
  const h = [...n.querySelectorAll('.react-flow__handle')].find((x) => kind === 'source'
    ? /\bsource\b/.test(x.getAttribute('class') || '') : /\btarget\b/.test(x.getAttribute('class') || ''));
  if (!h) return null;
  const ir = h.getBoundingClientRect();
  return [Math.round(ir.x), Math.round(ir.y)];
}, { nodeId, kind });
const hasConnectionPreview = () => page.evaluate(() => document.querySelectorAll('.react-flow__connection, .react-flow__connectionline').length);

const dialogs = () => page.evaluate(() => [...document.querySelectorAll('[role="dialog"],.mantine-Modal-content')]
  .filter((d) => { const r = d.getBoundingClientRect(); return r.width > 4 && r.height > 4; })
  .map((d) => (d.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 160)));
const toasts = () => page.evaluate(() => [...document.querySelectorAll('[class*="toast" i],[class*="Toast" i],[class*="notification" i],[class*="alert" i]')]
  .filter((d) => { const r = d.getBoundingClientRect(); return r.width > 10 && r.height > 10 && r.top < 700; })
  .map((d) => (d.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 100)));

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await settle(1800);
  await fitView(page); await settle(2500);
  await beginBatch(B, { note: '点自造边中点的剪刀断线，并清理 BV9 的残留' });
  const out = {};

  const ids0 = await edgeIds();
  out.start = { ids: ids0, count: ids0.length, nodes: await nodeCount() };
  console.log(`═══ 起点：连线 ${ids0.length} 条 ${JSON.stringify(ids0)}｜节点 ${out.start.nodes} ═══`);
  const baseIds = ids0.filter((i) => i !== MINE);
  console.log(`  其中属于我的：${MINE}｜用户原有：${JSON.stringify(baseIds)}`);

  if (!ids0.includes(MINE)) {
    console.log(`\n⛔ 画布上已经没有 ${MINE}（可能被别的会话清掉了），本轮无对象可试`);
    out.subject = null;
  } else {
    out.subject = MINE;
    // ── ① 悬停到它的中点，把剪刀找出来（不点，先看清楚）
    const mids = await edgeMids();
    const m = mids.find((x) => x.id === MINE);
    console.log(`\n═══ ① ${MINE}｜aria=${m?.aria}｜中点 ${JSON.stringify(m?.mid)} 视口内=${m?.inView} ═══`);
    out.mid = m;
    if (!m || !m.inView) {
      console.log('  ⛔ 中点不在视口内，需要先平移画布');
    } else {
      await page.mouse.move(200, 780); await settle(700);
      const sc0 = await page.evaluate(() => document.querySelectorAll('.scissors-enter').length);
      await page.mouse.move(m.mid[0], m.mid[1]); await settle(1800);
      const sc = await page.evaluate(() => [...document.querySelectorAll('.scissors-enter')].map((e) => {
        const r = e.getBoundingClientRect();
        return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
          center: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
          onClick: !!Object.keys(e).find((k) => k.startsWith('__reactProps$') && typeof e[k].onClick === 'function'),
          near: Math.abs(r.x + r.width / 2 - 9999) < 1 };
      }));
      const mine = sc.map((s) => ({ ...s, near: Math.abs(s.center[0] - m.mid[0]) < 40 && Math.abs(s.center[1] - m.mid[1]) < 40 })).filter((s) => s.near);
      console.log(`  未悬停时剪刀数 ${sc0}｜悬停后 ${sc.length} 枚，其中贴着中点的 ${mine.length} 枚`);
      mine.forEach((s) => console.log(`     ${JSON.stringify(s.rect)} 中心 ${JSON.stringify(s.center)} onClick=${s.onClick}`));
      out.scissors = { idle: sc0, all: sc, mine };
      await shot(page, 'M-280-自造连线中点悬停出的剪刀.png');

      if (mine.length) {
        // ── ② ⭐⭐⭐ 点它
        const pt = mine[mine.length - 1].center;
        const c0 = await edgeCount();
        console.log(`\n═══ ② 点剪刀 @${JSON.stringify(pt)} ═══`);
        console.log(`  点之前：连线 ${c0} 条 ${JSON.stringify(await edgeIds())}`);
        await page.mouse.move(pt[0], pt[1]); await settle(700);
        await page.mouse.down(); await settle(200);
        await page.mouse.up(); await settle(3000);
        const c1 = await edgeCount();
        const ids1 = await edgeIds();
        const dlg = await dialogs(); const ts = await toasts();
        out.click = { point: pt, before: c0, after: c1, idGone: !ids1.includes(MINE),
          ids1, dialogs: dlg, toasts: ts, removed: c1 < c0 && !ids1.includes(MINE) };
        console.log(`  ⭐⭐⭐ 点之后：连线 ${c1} 条 ${JSON.stringify(ids1)}`);
        console.log(`  自造边还在吗：${ids1.includes(MINE) ? '❌ 还在' : '✅ 没了'}`);
        console.log(`  弹窗 ${JSON.stringify(dlg)}｜提示条 ${JSON.stringify(ts)}`);
        if (out.click.removed) { await shot(page, 'M-281-点剪刀之后连线断了.png'); }
      } else {
        out.click = { skipped: '中点上没找到剪刀' };
      }
    }
  }

  // ── ③ 清理兜底：若自造边还在，⌘Z 撤；还不行就重新拖出来再想办法
  let idsMid = await edgeIds();
  if (idsMid.includes(MINE)) {
    console.log(`\n═══ ③ 兜底清理：${MINE} 还在，试 ⌘Z ═══`);
    await page.keyboard.down('Meta'); await page.keyboard.press('z'); await page.keyboard.up('Meta');
    await settle(2600);
    idsMid = await edgeIds();
    console.log(`  ⌘Z 后：${idsMid.length} 条 ${JSON.stringify(idsMid)}`);
    out.undo = { after: idsMid.length, ids: idsMid, worked: !idsMid.includes(MINE) };
    if (idsMid.includes(MINE)) {
      console.log(`  ⛔ ⌘Z 撤不掉，如实记录，不继续乱试`);
    }
  } else {
    out.undo = { needed: false, note: '剪刀点完就没了，用不上 ⌘Z' };
  }

  // ── ④ 收尾：逐项复核
  const idsF = await edgeIds();
  out.final = { count: idsF.length, ids: idsF, nodes: await nodeCount(),
    baseIntact: baseIds.every((i) => idsF.includes(i)),
    noExtra: idsF.every((i) => baseIds.includes(i)),
    identical: idsF.join(',') === baseIds.join(',') };
  console.log(`\n═══ ④ 收尾复核 ═══`);
  console.log(`  连线 ${out.final.count} 条（用户原有 ${baseIds.length}）｜原有全在=${out.final.baseIntact}｜无多余=${out.final.noExtra}｜逐项相同=${out.final.identical}`);
  console.log(`  节点 ${out.final.nodes} 个（起点 ${out.start.nodes}）`);
  console.log(`  ${JSON.stringify(idsF)}`);
  await clearToasts(page);

  const verdict = out.click && out.click.removed ? '✅ 能（点中点的剪刀）'
    : out.click ? '❌ 点了但没断' : '⛔ 没测到（分母 0）';
  console.log(`\n═══ 本轮结论 ═══`);
  console.log(`  · 点剪刀能断线吗？ ${verdict}`);
  console.log(`  · 画布复原了吗？ ${out.final.identical ? '✅ 与 BV9 起点逐项一致' : '❌ 还没复原'}`);

  await logStep(B, {
    id: 'BV10-click-scissors-disconnect',
    title: '⭐⭐⭐ 断线入口结案：在连线中点的剪刀上点一下就断',
    target: '对象是**我自己造的那条边**（BV9 的 `e-w1H9Qs9Rwx`），删它零风险；'
      + '更重要的是**回退路径已经先复核过**——BV9 已经验证了「拖 source → target 能造出线」'
      + '（拖到半程有 `.react-flow__connection` 预览线，成功那条 2→3），'
      + '所以即便剪刀失灵也接得回去。**回退动作先复核，再用它冒险。**'
      + '结论口径：只有这段真的执行了才输出「能/不能」，分母 0 时输出「⛔ 没测到」'
      + '——BV6 正是栽在这上面：造边失败导致剪刀一下没点，却打出了「不能」。',
    evidence: out,
    visible_text: JSON.stringify({ 起点: out.start, 对象: out.subject, 剪刀: out.scissors,
      点击: out.click, 兜底: out.undo, 收尾: out.final }).slice(0, 3400),
    shot: out.click && out.click.removed ? 'M-281-点剪刀之后连线断了.png' : 'M-280-自造连线中点悬停出的剪刀.png',
  });
  console.log('\nBV10 完成');
} catch (e) {
  console.log('⛔ 中止：' + e.message + '\n' + (e.stack || '').split('\n').slice(0, 5).join('\n'));
} finally {
  await browser.close();
}
