// Batch BV4 — 断线入口，第三条路，并且**先修仪器**。
//
// ⛔ BV3 落了空，但**不是产品的结论，是我的仪器坏了**：
//    `Object.values(path.getPointAtLength(0))` 对 DOMPoint 取不到任何属性（属性都在原型上，
//    是访问器不是自有属性），于是点坐标恒为 (0,0)，再经 CTM 换算成同一个屏幕点
//    `[916,-90]`（两条连线读数一模一样就是证据）。脚本拿屏幕外的坐标去点，点了空气。
//    ✅ 好消息：安全网是对的 —— `inView:false` 拒绝写入，连线数 2 → 2 没动过。
//
// 本轮三条新东西：
// ① ⭐ 换一种读法取连线的屏幕坐标：沿 path **采样 21 个点**，逐个换算到屏幕，
//    再用 `elementFromPoint` 反查「这个点是不是真的落在这条连线上」。
//    **点自己证明自己站得住**，不再相信任何坐标公式。
// ② ⭐⭐ 全页按钮集合的**三向差分**：什么都不选 / 选中连线 / 选中节点，三份按钮清单做差。
//    思路来自一句话：找不到入口时，**别只盯着你已知的地方**——
//    很多产品把「删除」做成「选中后才出现」的那枚按钮，它根本不在这时之前存在过。
// ③ 断线实验**改成在一枚我自己造的连线上做**，前提是**先验 ⌘Z 能撤销边**
//    （回退动作必须独立复核，而且要在依赖它之前复核）。⌘Z 撤不掉边，才退回去动已有连线。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBV4';
const VW = 1440; const VH = 810;
const { browser, page } = await launch();

const settle = (ms = 900) => page.waitForTimeout(ms);
const esc = async () => { await page.keyboard.press('Escape'); await settle(900); };

/** ⭐ 每条连线：沿 path 采样，找出「在视口内 + elementFromPoint 确认落在自己身上」的点击点。 */
const edgePts = () => page.evaluate((vw) => {
  const out = [];
  for (const g of document.querySelectorAll('.react-flow__edge')) {
    const p = g.querySelector('path');
    const rec = { id: g.getAttribute('data-id'), aria: g.getAttribute('aria-label'),
      cls: (g.getAttribute('class') || ''), selected: g.classList.contains('selected'),
      len: null, hit: null, tries: 0 };
    if (!p) { out.push({ ...rec, err: '没有 path' }); continue; }
    let L = 0; try { L = p.getTotalLength(); } catch { L = 0; }
    rec.len = Math.round(L);
    const ctm = p.getScreenCTM();
    if (!ctm || !L) { out.push({ ...rec, err: '没有 CTM 或长度' }); continue; }
    for (let i = 0; i <= 20; i += 1) {
      const d = (L * i) / 20;
      const q = p.getPointAtLength(d);
      const s = new DOMPoint(q.x, q.y, 0, 1).matrixTransform(ctm);
      rec.tries += 1;
      if (s.x < 4 || s.y < 4 || s.x > vw - 4 || s.y > vw * 0 + 786) continue; // 786 = 画布区底（底栏上方）
      const el = document.elementFromPoint(s.x, s.y);
      if (!el) continue;
      const owner = el.closest && el.closest('.react-flow__edge');
      if (owner && owner.getAttribute('data-id') === rec.id) {
        rec.hit = [Math.round(s.x), Math.round(s.y)];
        rec.hitOn = `${el.tagName}.${(el.getAttribute('class') || '').toString().split(' ')[0]}`;
        rec.at = `${Math.round(d)}/${Math.round(L)}`;
        break;
      }
    }
    out.push(rec);
  }
  return out;
}, VW);

/** ⭐ 全页按钮清单 —— 含**没有文字的图标按钮**（只看 key 的差集，新出现的按钮一定在里面）。 */
const buttonSet = () => page.evaluate(() => {
  const list = [];
  for (const b of document.querySelectorAll('button,[role="button"],[role="menuitem"],[role="menuitemcheckbox"],[role="tab"]')) {
    const r = b.getBoundingClientRect();
    if (r.width < 2 || r.height < 2) continue;
    const s = getComputedStyle(b);
    if (s.visibility === 'hidden' || s.display === 'none' || +s.opacity < 0.05) continue;
    const label = (b.getAttribute('aria-label') || b.getAttribute('title')
      || (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 24));
    const icons = b.querySelectorAll('svg *').length;
    list.push({ key: `${label || '(无字)'}|${icons}|${Math.round(r.x)},${Math.round(r.y)}|${(b.getAttribute('class') || '').slice(0, 40)}`,
      label, icons, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] });
  }
  return list;
});

const diffKeys = (before, after) => {
  const seen = new Set(before.map((b) => b.key));
  return after.filter((a) => !seen.has(a.key));
};

const edgeCount = () => page.evaluate(() => document.querySelectorAll('.react-flow__edge').length);
const selectedEdges = () => page.evaluate(() => ({
  edges: [...document.querySelectorAll('.react-flow__edge')].filter((e) => e.classList.contains('selected'))
    .map((e) => e.getAttribute('data-id')),
  nodes: [...document.querySelectorAll('.react-flow__node')].filter((e) => e.classList.contains('selected'))
    .map((e) => e.getAttribute('data-id')),
}));

/** 节点上的连接点（handle）屏幕坐标，用来造线 / 接回线。 */
const handleAt = (nodeId, kind) => page.evaluate(({ nodeId, kind }) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nodeId}"]`);
  if (!n) return null;
  const hs = [...n.querySelectorAll('.react-flow__handle')].filter((h) => {
    const c = h.getAttribute('class') || '';
    return kind === 'source' ? /source/.test(c) : /target/.test(c);
  });
  const h = hs[0]; if (!h) return null;
  const r = h.getBoundingClientRect();
  return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
}, { nodeId, kind });

/** 分步拖拽：从 A 拖到 B。React Flow 一次性拖常常不触发连接逻辑。 */
const dragTo = async (from, to, steps = 10) => {
  await page.mouse.move(from[0], from[1]); await settle(500);
  await page.mouse.down(); await settle(400);
  for (let s = 1; s <= steps; s += 1) {
    await page.mouse.move(from[0] + (to[0] - from[0]) * (s / steps),
      from[1] + (to[1] - from[1]) * (s / steps));
    await settle(150);
  }
  await page.mouse.up(); await settle(2000);
};

/** 选中某条连线：先点空白解选，再点它自证过的那个点。 */
const selectEdgeById = async (id) => {
  await page.mouse.move(700, 700); await page.waitForTimeout(400);
  await page.keyboard.press('Escape'); await settle(800);
  const pts = await edgePts();
  const e = pts.find((x) => x.id === id);
  if (!e || !e.hit) return { ok: false, why: `${id} 没有自证过的可点位置`, got: e };
  await page.mouse.move(e.hit[0], e.hit[1]); await settle(600);
  await page.mouse.click(e.hit[0], e.hit[1]); await settle(1500);
  const sel = await selectedEdges();
  return { ok: sel.edges.includes(id), point: e.hit, hitOn: e.hitOn, at: e.at, sel };
};

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await settle(1600);
  await fitView(page); await settle(2200);
  await beginBatch(B, { note: '修好连线坐标仪器 + 全页按钮三向差分 + 选中后按删除键（在自造连线上做）' });
  const out = {};

  // ── ① 修好仪器：连线坐标现在自证
  const before = await edgePts();
  out.before = before;
  console.log('═══ ① 连线坐标（自证过的可点位置）═══');
  before.forEach((e, i) => console.log(`  ${i + 1}. ${e.id}｜${e.aria}\n     长度=${e.len}｜可点=${JSON.stringify(e.hit)} 命中=${e.hitOn} 位置=${e.at}${e.err ? ' ❌' + e.err : ''}`));
  console.log(`  ⭐ 仪器自检：${before.filter((e) => e.hit).length}/${before.length} 条连线拿到了自证点击点`);

  // ── ② ⭐⭐ 三向差分：什么都不选 / 选中连线 / 选中节点
  console.log('\n═══ ② 全页按钮集合三向差分 ═══');
  const btnIdle = await buttonSet();
  console.log(`  空闲基线：${btnIdle.length} 枚按钮`);

  const selTarget = before.find((e) => e.hit);
  let selEdge = null;
  if (selTarget) selEdge = await selectEdgeById(selTarget.id);
  console.log(`  选中连线 ${selTarget?.id}：ok=${selEdge?.ok}｜${JSON.stringify(selEdge?.sel || selEdge?.why)}`);
  const btnEdge = await buttonSet();
  const newOnEdge = diffKeys(btnIdle, btnEdge);
  console.log(`  选中后多出 ${newOnEdge.length} 枚：` + JSON.stringify(newOnEdge.map((b) => ({ label: b.label, rect: b.rect }))));
  await shot(page, 'M-279-选中连线之后画布什么样.png');

  // 换一条连线再差一次（第一条在 BV2 里点中过一次就失手过）
  const other = before.filter((e) => e.hit && e.id !== selTarget?.id)[0];
  let selEdge2 = null;
  if (other) {
    selEdge2 = await selectEdgeById(other.id);
    const btn2 = await buttonSet();
    const newOnEdge2 = diffKeys(btnIdle, btn2);
    console.log(`  换选 ${other.id}：ok=${selEdge2?.ok}｜多出 ${newOnEdge2.length} 枚 ` + JSON.stringify(newOnEdge2.map((b) => ({ label: b.label, rect: b.rect }))));
    out.select2 = selEdge2; out.newOnEdge2 = newOnEdge2;
  }

  // 选中一个节点，再差一次
  let selNode = null;
  const nodeId = 't-UtVx3lZmrV';
  await page.mouse.move(700, 700); await settle(400);
  await page.keyboard.press('Escape'); await settle(800);
  const nb = await page.evaluate((id) => { const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
    if (!n) return null; const r = n.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, nodeId);
  if (nb) {
    await page.mouse.click(nb[0], nb[1]); await settle(1500);
    const sel = await selectedEdges();
    selNode = { nodeId, at: nb, sel };
    const btnN = await buttonSet();
    const newOnNode = diffKeys(btnIdle, btnN);
    console.log(`  选中节点 ${nodeId}：selected=${JSON.stringify(sel.nodes)}｜多出 ${newOnNode.length} 枚 ` + JSON.stringify(newOnNode.map((b) => ({ label: b.label, rect: b.rect }))));
    out.newOnNode = newOnNode;
  }
  out.buttons = { idle: btnIdle.length, newOnEdge, select: selEdge, selNode };
  await esc();

  // ── ③ 右键连线：有没有自定义菜单
  console.log('\n═══ ③ 右键连线 ═══');
  const rt = {};
  if (selTarget) {
    await page.mouse.move(selTarget.hit[0], selTarget.hit[1]); await settle(500);
    const bMenu = await buttonSet();
    await page.mouse.click(selTarget.hit[0], selTarget.hit[1], { button: 'right' }); await settle(1800);
    const aMenu = await buttonSet();
    const menuProbe = await page.evaluate(() => [...document.querySelectorAll('[role="menu"],[role="listbox"],.mantine-Menu-content,[class*="context"],[class*="ContextMenu"]')]
      .filter((d) => { const r = d.getBoundingClientRect(); return r.width > 4 && r.height > 4; })
      .map((d) => ({ cls: (d.getAttribute('class') || '').slice(0, 60), text: (d.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 200) })));
    rt = { hit: selTarget.hit, newButtons: diffKeys(bMenu, aMenu), menuProbe };
    console.log(`  右键后多出 ${rt.newButtons.length} 枚按钮；菜单节点 ${rt.menuProbe.length} 个：${JSON.stringify(rt.menuProbe)}`);
    if (rt.newButtons.length) console.log(`  ⭐ ${JSON.stringify(rt.newButtons.map((b) => ({ label: b.label, rect: b.rect })))}`);
    await esc();
  }
  out.rightClick = rt;

  // ── ④ ⭐ 回退能力先验：造一条边，⌘Z 撤得掉吗？
  console.log('\n═══ ④ 先验回退：造一条自己的连线，再用 ⌘Z 撤掉 ═══');
  const pairs = [['t-UtVx3lZmrV', 't-xVGmDWNLaZ'], ['b-mfkcQNULC3', 'a-CUfJfmKzUJ'], ['t-UtVx3lZmrV', 'b-mfkcQNULC3']];
  const n0 = await edgeCount();
  let made = null;
  for (const [a, b] of pairs) {
    const hs = await handleAt(a, 'source'); const ht = await handleAt(b, 'target');
    if (!hs || !ht) { console.log(`  ${a}→${b}：handle 不在视口内（${JSON.stringify(hs)} / ${JSON.stringify(ht)}）`); continue; }
    await dragTo(hs, ht);
    const n1 = await edgeCount();
    console.log(`  ${a} → ${b}：连线 ${n0} → ${n1}`);
    if (n1 > n0) { made = { from: a, to: b, fromHandle: hs, toHandle: ht, count: n1 }; break; }
  }
  out.makeEdge = made;
  let undoWorks = false;
  if (made) {
    const ids = (await edgePts()).map((e) => e.id);
    const extra = ids.filter((i) => !before.some((b) => b.id === i));
    out.makeEdge.ids = extra;
    console.log(`  造出来的边：${JSON.stringify(extra)}`);
    await page.keyboard.down('Meta'); await page.keyboard.press('z'); await page.keyboard.up('Meta');
    await settle(2400);
    const n2 = await edgeCount();
    const ids2 = (await edgePts()).map((e) => e.id);
    undoWorks = n2 === n0 && extra.every((i) => !ids2.includes(i));
    out.undo = { after: n2, ids: ids2, works: undoWorks, baseline: n0 };
    console.log(`  ⭐ ⌘Z 后连线 ${made.count} → ${n2}｜基线 ${n0}｜撤得掉=${undoWorks ? '✅' : '❌'}`);
    if (!undoWorks) {
      // 撤不掉就手动拖掉（这时候这条边是我自己造的，删它没有副作用）
      const p = await page.mouse; // noop
      const pts = await edgePts();
      const mine = pts.find((e) => extra.includes(e.id) && e.hit);
      if (mine) { await dragTo(await handleAt(made.from, 'source'), await handleAt(made.to, 'target')); }
      const n3 = await edgeCount();
      console.log(`  ⛔ ⌘Z 撤不掉（${n2} 条）；手动再拖一次回到 ${n3} 条`);
      out.undo.manual = n3;
    }
    await clearToasts(page);
  }
  out.undoWorks = undoWorks;

  // ── ⑤ 断线实验：在**自己造的**连线上按删除键
  console.log('\n═══ ⑤ 在自造连线上按删除键 ═══');
  const del = { tried: [] };
  if (undoWorks) {
    // 再造一条，这次不去碰它，只为试删除键
    const hs = await handleAt(made.from, 'source'); const ht = await handleAt(made.to, 'target');
    await dragTo(hs, ht);
    const pts = await edgePts();
    const extra2 = pts.map((e) => e.id).filter((i) => !before.some((b) => b.id === i));
    const base = await edgeCount();
    const mine = pts.find((e) => extra2.includes(e.id) && e.hit);
    console.log(`  新边 ${JSON.stringify(extra2)}｜连线数 ${base}｜可点 ${JSON.stringify(mine?.hit)}`);
    del.edgeId = extra2[0];
    if (mine) {
      const s = await selectEdgeById(mine.id);
      console.log(`  选中它：ok=${s.ok}｜${JSON.stringify(s.sel || s.why)}`);
      del.select = s;
      if (s.ok) {
        for (const k of ['Delete', 'Backspace']) {
          const c0 = await edgeCount();
          await page.keyboard.press(k); await settle(2200);
          const c1 = await edgeCount();
          const dialogs = await page.evaluate(() => [...document.querySelectorAll('[role="dialog"],.mantine-Modal-content')]
            .filter((d) => { const r = d.getBoundingClientRect(); return r.width > 4 && r.height > 4; })
            .map((d) => (d.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 140)));
          del.tried.push({ key: k, before: c0, after: c1, delta: c1 - c0, dialogs });
          console.log(`  按 ${k}：${c0} → ${c1}（${c1 - c0 >= 0 ? '+' : ''}${c1 - c0}）｜弹窗 ${JSON.stringify(dialogs)}`);
          if (c1 < c0) { del.removedBy = k; await shot(page, 'M-281-选中连线后按删除.png'); break; }
          if (c1 > c0) { // 多出线了（不可能），也记下来
          }
        }
      }
      // 不管删没删掉，用**已验证过的** ⌘Z 收尾
      const c0 = await edgeCount();
      await page.keyboard.down('Meta'); await page.keyboard.press('z'); await page.keyboard.up('Meta'); await settle(2400);
      const c1 = await edgeCount();
      del.undoTail = { before: c0, after: c1 };
      console.log(`  收尾 ⌘Z：${c0} → ${c1}`);
    }
  } else {
    // 回退能力没有保障 —— 只在**已有**连线上试，并提前记下两端 handle 坐标好接回去
    const target = before.find((e) => e.hit);
    const m = target && /from (\S+) to (\S+)/.exec(target.aria || '');
    console.log(`  没有回退保障，改在已有连线 ${target?.id} 上试；两端 ${m ? m[1] + ' → ' + m[2] : '读不出'}`);
    if (target && m) {
      const hs = await handleAt(m[1], 'source'); const ht = await handleAt(m[2], 'target');
      out.restoreHandles = { from: hs, to: ht, fromNode: m[1], toNode: m[2] };
      console.log(`  handle 坐标：${JSON.stringify(hs)} / ${JSON.stringify(ht)}`);
      const s = await selectEdgeById(target.id);
      console.log(`  选中：ok=${s.ok}`);
      del.select = s;
      if (s.ok) {
        for (const k of ['Delete', 'Backspace']) {
          const c0 = await edgeCount();
          await page.keyboard.press(k); await settle(2200);
          const c1 = await edgeCount();
          del.tried.push({ key: k, before: c0, after: c1, delta: c1 - c0 });
          console.log(`  按 ${k}：${c0} → ${c1}`);
          if (c1 < c0) { del.removedBy = k; break; }
        }
      }
      const c2 = await edgeCount();
      if (c2 < before.length) {
        console.log(`  ⭐ 接回去：从 ${JSON.stringify(ht)} 拖到 ${JSON.stringify(hs)}`);
        await dragTo(ht, hs, 12);
        del.restoredByDrag = (await edgeCount()) >= before.length;
        console.log(`  拖回后连线数 ${await edgeCount()}｜id 列表 ${JSON.stringify((await edgePts()).map((e) => e.id))}`);
      }
    }
  }
  out.delete = del;

  // ── ⑥ 收尾：账户复原复核
  const fin = await edgePts();
  const finIds = fin.map((e) => e.id);
  out.final = { count: fin.length, ids: finIds,
    originalIntact: before.every((b) => finIds.includes(b.id)),
    noExtra: finIds.every((i) => before.some((b) => b.id === i)) };
  console.log(`\n═══ ⑥ 收尾复核：连线 ${fin.length} 条｜原有两条都在=${out.final.originalIntact}｜没有多出来的=${out.final.noExtra}`);
  console.log(`  id：${JSON.stringify(finIds)}`);
  await shot(page, 'M-282-连线实验之后画布什么样.png');

  console.log(`\n═══ 本轮结论 ═══`);
  console.log(`  · 仪器修好了吗？ ${before.filter((e) => e.hit).length}/${before.length} 条连线拿到自证点击点`);
  console.log(`  · 选中连线后多出按钮？ ${out.buttons.newOnEdge.length} 枚 ${JSON.stringify(out.buttons.newOnEdge.map((b) => b.label))}`);
  console.log(`  · 选中节点后多出按钮？ ${(out.newOnNode || []).length} 枚 ${JSON.stringify((out.newOnNode || []).map((b) => b.label))}`);
  console.log(`  · 右键连线有菜单？ ${(rt.menuProbe || []).length} 个菜单节点`);
  console.log(`  · ⌘Z 能撤销连线吗？ ${undoWorks ? '✅ 能' : '❌ 不能'}`);
  console.log(`  · 选中后按删除键能断线吗？ ${del.removedBy ? '✅ 能（' + del.removedBy + '）' : '❌ 不能'}`);

  await logStep(B, {
    id: 'BV4-edge-click-fix-and-button-diff',
    title: '⭐⭐ 修好连线坐标仪器 + 「选中前后全页按钮差分」：断线入口第三路',
    target: '⛔ BV3 落空是**仪器坏了**不是产品坏了：`Object.values(DOMPoint)` 取不到属性，'
      + '点坐标恒为 (0,0)，两条连线读出同一个屏幕点 `[916,-90]`，脚本拿屏幕外的坐标去点。'
      + '✅ 安全网是对的：`inView:false` 拒绝写入，连线数 2→2 未动。'
      + '本轮 ① 沿 path 采样 21 点并用 `elementFromPoint` **让点自证**；'
      + '② **什么都不选/选中连线/选中节点**三份全页按钮清单做差（很多产品的「删除」是选中后才出现的那枚）；'
      + '③ 断线实验在**自造连线**上做，**前提是先验 ⌘Z 撤得掉边**（回退动作必须先独立复核）。',
    evidence: out,
    visible_text: JSON.stringify(out).slice(0, 3400),
    shot: 'M-282-连线实验之后画布什么样.png',
  });
  console.log('\nBV4 完成');
} catch (e) {
  console.log('⛔ 中止：' + e.message + '\n' + (e.stack || '').split('\n').slice(0, 5).join('\n'));
} finally {
  await browser.close();
}
