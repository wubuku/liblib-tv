// Batch BV5 — ⭐⭐ 把那枚剪刀找出来。
//
// BV4 的截图揭穿了 BV2 的盲点：**选中的连线中点有一枚剪刀图标**（截图里就在
// `[405,428]`，和仪器自证的点击点分毫不差）。而 BV2 在中点悬停时数到「0 个按钮」——
// ⭐⭐ **因为剪刀不是 `<button>`**。我拿「数 button」当探针，探针问错了地方。
//
// 本轮三件事：
// ① ⭐⭐⭐ **元素链解剖**：在中点取 `elementFromPoint`，沿 `parentElement` 一路往上，
//    每一层都记 tag / class / aria / role / cursor / 背景色 / 尺寸。
//    同一件事在**三个状态**各做一次（未选 / 悬停 / 选中），差出来的就是「选中才出现的东西」。
//    —— 这一招把「有没有按钮」这种问法，换成「这里到底站着什么」。
// ② 修 BV4 的时序污染：基线连采两次 + **往返差分**（选中→取消选中→再比一次），
//    并且给差分结果**标注是否在视口内**（BV4 报出来的那几枚 x=1498/1578 根本不在屏幕上）。
// ③ 断线实验依然在**自造连线**上做，不碰用户已有的两条边。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBV5';
const VW = 1440; const VH = 810;
const { browser, page } = await launch();

const settle = (ms = 900) => page.waitForTimeout(ms);
const esc = async () => { await page.keyboard.press('Escape'); await settle(900); };

/** ⭐ 每条连线：沿 path 采样，找「在视口内 + elementFromPoint 确认落在自己身上」的点击点。 */
const edgePts = () => page.evaluate((vw) => {
  const out = [];
  for (const g of document.querySelectorAll('.react-flow__edge')) {
    const p = g.querySelector('path');
    const rec = { id: g.getAttribute('data-id'), aria: g.getAttribute('aria-label'),
      selected: g.classList.contains('selected'), len: null, hit: null, hitOn: null, mid: null };
    if (!p) { out.push(rec); continue; }
    let L = 0; try { L = p.getTotalLength(); } catch { L = 0; }
    rec.len = Math.round(L);
    const ctm = p.getScreenCTM();
    if (!ctm || !L) { out.push(rec); continue; }
    for (let i = 0; i <= 20; i += 1) {
      const q = p.getPointAtLength((L * i) / 20);
      const s = new DOMPoint(q.x, q.y, 0, 1).matrixTransform(ctm);
      if (s.x < 4 || s.y < 4 || s.x > vw - 4 || s.y > 786) continue;
      const el = document.elementFromPoint(s.x, s.y);
      const owner = el && el.closest && el.closest('.react-flow__edge');
      if (owner && owner.getAttribute('data-id') === rec.id) {
        rec.hit = [Math.round(s.x), Math.round(s.y)];
        rec.hitOn = `${el.tagName}.${(el.getAttribute('class') || '').toString().split(' ')[0]}`;
        break;
      }
    }
    // ⭐ 中点单独再取一次（截图里剪刀所在的位置），不依赖「命中的那个点恰好是中点」
    const q = p.getPointAtLength(L / 2);
    const s = new DOMPoint(q.x, q.y, 0, 1).matrixTransform(ctm);
    rec.mid = [Math.round(s.x), Math.round(s.y)];
    rec.midEl = (() => { const e = document.elementFromPoint(s.x, s.y);
      return e ? `${e.tagName}.${(e.getAttribute('class') || '').toString().split(' ').slice(0, 2).join('.')}` : null; })();
    out.push(rec);
  }
  return out;
}, VW);

/** ⭐⭐⭐ 元素链解剖：从 (x,y) 命中元素起，逐层往上报身份。 */
const chainAt = (x, y) => page.evaluate(({ x, y }) => {
  const el = document.elementFromPoint(x, y);
  if (!el) return null;
  const out = [];
  let cur = el; let depth = 0;
  while (cur && depth < 9) {
    const r = cur.getBoundingClientRect();
    const s = getComputedStyle(cur);
    out.push({
      depth, tag: cur.tagName,
      cls: (cur.getAttribute('class') || '').toString().slice(0, 80),
      id: cur.id || null, aria: cur.getAttribute('aria-label'),
      role: cur.getAttribute('role'), title: cur.getAttribute('title'),
      text: (cur.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 24),
      cursor: s.cursor, pointerEvents: s.pointerEvents, opacity: s.opacity,
      bg: s.backgroundColor, zIndex: s.zIndex,
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      svgs: cur.querySelectorAll ? cur.querySelectorAll('svg').length : 0,
      paths: cur.querySelectorAll ? cur.querySelectorAll('svg path,svg circle,svg line,svg polyline').length : 0,
    });
    cur = cur.parentElement; depth += 1;
  }
  return out;
}, { x, y });

/** 全页按钮清单（含无字图标按钮），并标注是否在视口内。 */
const buttonSet = () => page.evaluate(({ vw, vh }) => {
  const list = [];
  for (const b of document.querySelectorAll('button,[role="button"],[role="menuitem"],[role="menuitemcheckbox"],[role="tab"]')) {
    const r = b.getBoundingClientRect();
    if (r.width < 2 || r.height < 2) continue;
    const s = getComputedStyle(b);
    if (s.visibility === 'hidden' || s.display === 'none' || +s.opacity < 0.05) continue;
    const label = (b.getAttribute('aria-label') || b.getAttribute('title')
      || (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 24));
    const icons = b.querySelectorAll('svg *').length;
    const inView = r.x >= 0 && r.y >= 0 && r.x + r.width <= vw && r.y + r.height <= vh;
    list.push({ key: `${label || '(无字)'}|${icons}|${Math.round(r.x)},${Math.round(r.y)}|${(b.getAttribute('class') || '').slice(0, 40)}`,
      label, icons, inView, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] });
  }
  return list;
}, { vw: VW, vh: VH });

const diffKeys = (before, after) => { const seen = new Set(before.map((b) => b.key)); return after.filter((a) => !seen.has(b.key)); };
const edgeCount = () => page.evaluate(() => document.querySelectorAll('.react-flow__edge').length);
const selState = () => page.evaluate(() => ({
  edges: [...document.querySelectorAll('.react-flow__edge')].filter((e) => e.classList.contains('selected')).map((e) => e.getAttribute('data-id')),
  nodes: [...document.querySelectorAll('.react-flow__node')].filter((e) => e.classList.contains('selected')).map((e) => e.getAttribute('data-id')),
}));

const handleAt = (nodeId, kind) => page.evaluate(({ nodeId, kind }) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nodeId}"]`);
  if (!n) return null;
  const h = [...n.querySelectorAll('.react-flow__handle')].find((x) => kind === 'source' ? /source/.test(x.getAttribute('class') || '') : /target/.test(x.getAttribute('class') || ''));
  if (!h) return null;
  const r = h.getBoundingClientRect();
  if (r.width < 2 && r.height < 2) return null;
  return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
}, { nodeId, kind });

const nodeBox = (nodeId) => page.evaluate((id) => {
  const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
  if (!n) return null; const r = n.getBoundingClientRect();
  return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
}, nodeId);

const dragTo = async (from, to, steps = 10) => {
  await page.mouse.move(from[0], from[1]); await settle(450);
  await page.mouse.down(); await settle(350);
  for (let s = 1; s <= steps; s += 1) {
    await page.mouse.move(from[0] + (to[0] - from[0]) * (s / steps), from[1] + (to[1] - from[1]) * (s / steps));
    await settle(140);
  }
  await page.mouse.up(); await settle(2000);
};

const selectEdgeById = async (id) => {
  await page.mouse.move(700, 730); await page.waitForTimeout(300);
  await page.keyboard.press('Escape'); await settle(800);
  const pts = await edgePts();
  const e = pts.find((x) => x.id === id);
  if (!e || !e.hit) return { ok: false, why: '没有自证过的可点位置' };
  await page.mouse.move(e.hit[0], e.hit[1]); await settle(500);
  await page.mouse.click(e.hit[0], e.hit[1]); await settle(1500);
  const sel = await selState();
  return { ok: sel.edges.includes(id), at: e.hit, sel };
};

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await settle(1800);
  await fitView(page); await settle(2500);
  await beginBatch(B, { note: '中点元素链三态解剖 + 修时序污染的往返差分 + 自造连线上试剪刀' });
  const out = {};

  const before = await edgePts();
  out.before = before;
  const target = before.find((e) => e.hit);
  console.log('═══ ① 中点元素链：未选 / 悬停 / 选中 ═══');
  if (!target) { console.log('⛔ 没有可操作连线'); }
  const probe = {};
  if (target) {
    console.log(`  连线 ${target.id}｜自证点 ${JSON.stringify(target.hit)}｜几何中点 ${JSON.stringify(target.mid)}`);
    const at = (p) => p && p[0] > 3 && p[0] < VW - 3 && p[1] > 3 && p[1] < 786 ? p : target.hit;
    const midPt = at(target.mid);

    // 状态 A：未选
    await page.mouse.move(200, 780); await settle(900);
    probe.unselected = await chainAt(midPt[0], midPt[1]);
    // 状态 B：悬停（鼠标停在中点）
    await page.mouse.move(midPt[0], midPt[1]); await settle(1400);
    probe.hovered = await chainAt(midPt[0], midPt[1]);
    // 状态 C：选中
    const s = await selectEdgeById(target.id);
    probe.select = { sel: s, chain: await chainAt(midPt[0], midPt[1]) };
    console.log(`  选中：ok=${s.ok}｜${JSON.stringify(s.sel)}`);
    await shot(page, 'M-279-选中连线之后画布什么样.png');

    const show = (k) => {
      const c = probe[k];
      console.log(`  ── ${k} ──`);
      (c || []).slice(0, 5).forEach((n) => console.log(`     ${'·'.repeat(n.depth)} ${n.tag} cls=${n.cls || '(无)'} aria=${n.aria || '-'} role=${n.role || '-'} cursor=${n.cursor} op=${n.opacity} rect=${JSON.stringify(n.rect)} svg=${n.svgs}/${n.paths} text="${n.text}"`));
    };
    show('unselected'); show('hovered'); show('select');

    // ⭐ 差分：哪些层是「选中才有」的
    const key = (n) => `${n.tag}|${n.cls}|${n.rect.join(',')}`;
    const setA = new Set((probe.unselected || []).map(key));
    const setB = new Set((probe.hovered || []).map(key));
    const chainC = (probe.select?.chain) || [];
    const onlyC = chainC.filter((n) => !setA.has(key(n)) && !setB.has(key(n)));
    probe.onlyInSelected = onlyC;
    console.log(`  ⭐⭐ 只在选中态出现的层：${onlyC.length} 层`);
    onlyC.forEach((n) => console.log(`     ${'·'.repeat(n.depth)} ${n.tag} cls=${n.cls} aria=${n.aria || '-'} role=${n.role || '-'} cursor=${n.cursor} rect=${JSON.stringify(n.rect)} svgpath=${n.paths}`));
    out.probe = probe;
  }

  // ── ② 修时序污染的按钮差分：基线稳定性 + 往返
  console.log('\n═══ ② 按钮差分：基线稳定性 + 往返 ═══');
  await page.mouse.move(200, 780); await page.keyboard.press('Escape'); await settle(1200);
  const idle1 = await buttonSet();
  await settle(3500);
  const idle2 = await buttonSet();
  const drift = diffKeys(idle1, idle2);
  console.log(`  空闲基线两次采样：${idle1.length} / ${idle2.length} 枚｜自发漂移 ${drift.length} 枚：${JSON.stringify(drift.map((d) => d.label))}`);
  if (target) {
    const s = await selectEdgeById(target.id);
    const onEdge = await buttonSet();
    const newOnEdge = diffKeys(idle2, onEdge);
    await esc();
    const offEdge = await buttonSet();
    const persisted = diffKeys(idle2, offEdge);
    console.log(`  选中：ok=${s.ok}｜新增 ${newOnEdge.length} 枚 ${JSON.stringify(newOnEdge.map((b) => ({ label: b.label, inView: b.inView, rect: b.rect })))}`);
    console.log(`  ⭐ 取消选中后仍然残留：${persisted.length} 枚 ${JSON.stringify(persisted.map((b) => ({ label: b.label, inView: b.inView })))}`);
    out.buttons = { idle1: idle1.length, idle2: idle2.length, drift, newOnEdge, persisted };
  }

  // ── ③ 右键连线
  console.log('\n═══ ③ 右键连线 ═══');
  let rt = {};
  if (target) {
    await page.mouse.move(target.hit[0], target.hit[1]); await settle(500);
    const bMenu = await buttonSet();
    await page.mouse.click(target.hit[0], target.hit[1], { button: 'right' }); await settle(1800);
    const aMenu = await buttonSet();
    const menuProbe = await page.evaluate(() => [...document.querySelectorAll('[role="menu"],[role="listbox"],.mantine-Menu-content,[class*="context"],[class*="ContextMenu"],[class*="popover"],[class*="Popover"]')]
      .filter((d) => { const r = d.getBoundingClientRect(); return r.width > 4 && r.height > 4 && getComputedStyle(d).display !== 'none'; })
      .map((d) => ({ cls: (d.getAttribute('class') || '').slice(0, 60), text: (d.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 200) })));
    rt = { hit: target.hit, newButtons: diffKeys(bMenu, aMenu), menuProbe };
    console.log(`  右键后新增按钮 ${rt.newButtons.length} 枚 ${JSON.stringify(rt.newButtons.map((b) => b.label))}`);
    console.log(`  菜单类节点 ${menuProbe.length} 个：${JSON.stringify(menuProbe)}`);
    const chainAfterRight = await chainAt(target.hit[0], target.hit[1]);
    rt.chain = chainAfterRight;
    if (menuProbe.length) { await shot(page, 'M-283-右键连线之后.png'); }
    await esc();
  }
  out.rightClick = rt;

  // ── ④ ⭐ 断线实验：在自造连线上做
  console.log('\n═══ ④ 自造一条连线，在它身上找剪刀 ═══');
  const n0 = await edgeCount();
  const pairs = [['t-UtVx3lZmrV', 'b-mfkcQNULC3'], ['a-CUfJfmKzUJ', 't-xVGmDWNLaZ'], ['t-UtVx3lZmrV', 'a-THmbuJXQj4']];
  let made = null;
  for (const [a, b] of pairs) {
    // 先把源节点 hover 一下（handle 常常要 hover 才现身）
    const nb = await nodeBox(a);
    if (!nb) { console.log(`  ${a} 不在视口里`); continue; }
    await page.mouse.move(nb[0], nb[1]); await settle(900);
    const hs = await handleAt(a, 'source');
    const hbx = await nodeBox(b);
    if (hbx) await page.mouse.move(hbx[0], hbx[1]);
    await settle(800);
    const ht = await handleAt(b, 'target');
    if (!hs || !ht) { console.log(`  ${a}→${b}：handle 取不到（${JSON.stringify(hs)} / ${JSON.stringify(ht)}）`); continue; }
    await dragTo(hs, ht);
    const n1 = await edgeCount();
    console.log(`  ${a} → ${b}：连线 ${n0} → ${n1}（handle ${JSON.stringify(hs)} → ${JSON.stringify(ht)}）`);
    if (n1 > n0) { made = { from: a, to: b, fromHandle: hs, toHandle: ht, count: n1 }; break; }
  }
  out.makeEdge = made;

  const del = {};
  if (made) {
    const pts = await edgePts();
    const extra = pts.map((e) => e.id).filter((i) => !before.some((b) => b.id === i));
    const mine = pts.find((e) => extra.includes(e.id) && e.hit);
    console.log(`  自造边 ${JSON.stringify(extra)}｜连线数 ${made.count}｜可点 ${JSON.stringify(mine?.hit)}｜中点 ${JSON.stringify(mine?.mid)}`);
    if (mine) {
      // 选中它，然后解剖中点
      const s = await selectEdgeById(mine.id);
      console.log(`  选中自造边：ok=${s.ok}｜${JSON.stringify(s.sel)}`);
      const mp = mine.mid && mine.mid[0] > 3 && mine.mid[0] < VW - 3 && mine.mid[1] > 3 && mine.mid[1] < 786 ? mine.mid : mine.hit;
      const chain = await chainAt(mp[0], mp[1]);
      const key = (n) => `${n.tag}|${n.cls}|${n.rect.join(',')}`;
      const pre = new Set([...((await chainAt(mp[0], mp[1])) || []).map(key)]);
      // 上面那行是选中后的自身，单独找「不像 path 本身」的层
      const suspects = (chain || []).filter((n) => n.depth < 4
        && !/react-flow__edge/.test(n.cls) && n.rect[2] < 120 && n.rect[3] < 120 && n.rect[2] > 2);
      console.log(`  ⭐ 自造边中点 ${JSON.stringify(mp)} 上的可疑层：${suspects.length}`);
      (chain || []).slice(0, 6).forEach((n) => console.log(`     ${'·'.repeat(n.depth)} ${n.tag} cls=${n.cls || '(无)'} aria=${n.aria || '-'} role=${n.role || '-'} cursor=${n.cursor} rect=${JSON.stringify(n.rect)} svg=${n.svgs}/${n.paths} text="${n.text}"`));
      del.select = s; del.chain = chain; del.mid = mp;
      await shot(page, 'M-282-自造连线选中之后.png');

      // 优先点「剪刀」：非 path、面积小、在连线组内或紧邻、看起来可点
      const scissor = (chain || []).find((n) => n.depth >= 1 && n.depth <= 4
        && n.svgs > 0 && n.rect[2] > 6 && n.rect[2] < 80 && /react-flow__edges|react-flow__edgelabel|react-flow__node/i.test(
          (chain || []).find((m) => m.depth === n.depth + 1)?.cls || ''));
      const cands = (chain || []).filter((n) => n.depth >= 1 && n.depth <= 5 && n.rect[2] > 6 && n.rect[2] < 100
        && n.rect[3] > 6 && n.rect[3] < 100 && !/react-flow__edge\b/.test(n.cls));
      console.log(`  候选可点小元素：${JSON.stringify(cands.map((c) => ({ d: c.depth, tag: c.tag, cls: c.cls, cursor: c.cursor, rect: c.rect })))}`);

      // 依次尝试：剪刀候选 → 删除键
      const tries = [];
      for (const c of cands.reverse()) {
        const cx = c.rect[0] + c.rect[2] / 2; const cy = c.rect[1] + c.rect[3] / 2;
        if (cx < 2 || cx > VW - 2 || cy < 2 || cy > VH - 2) continue;
        const before2 = await edgeCount();
        await page.mouse.move(cx, cy); await settle(600);
        await page.mouse.click(cx, cy); await settle(2200);
        const after2 = await edgeCount();
        const dlg = await page.evaluate(() => [...document.querySelectorAll('[role="dialog"],.mantine-Modal-content')]
          .filter((d) => { const r = d.getBoundingClientRect(); return r.width > 4 && r.height > 4; })
          .map((d) => (d.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 140)));
        tries.push({ what: `点 ${c.tag}.${c.cls}`, at: [Math.round(cx), Math.round(cy)], before: before2, after: after2, dialogs: dlg });
        console.log(`  点 ${c.tag}.${(c.cls || '').slice(0, 40)} @${Math.round(cx)},${Math.round(cy)}：连线 ${before2} → ${after2}${after2 < before2 ? ' ⭐⭐ 断掉了！' : ''}｜弹窗 ${JSON.stringify(dlg)}`);
        if (after2 < before2) { await shot(page, 'M-281-点中点上的剪刀之后.png'); break; }
      }
      for (const k of ['Delete', 'Backspace']) {
        if (tries.some((t) => t.after < t.before)) break;
        const c0 = await edgeCount();
        await page.keyboard.press(k); await settle(2200);
        const c1 = await edgeCount();
        const dlg = await page.evaluate(() => [...document.querySelectorAll('[role="dialog"],.mantine-Modal-content')]
          .filter((d) => { const r = d.getBoundingClientRect(); return r.width > 4 && r.height > 4; })
          .map((d) => (d.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 140)));
        tries.push({ what: `按 ${k}`, before: c0, after: c1, dialogs: dlg });
        console.log(`  选中后按 ${k}：连线 ${c0} → ${c1}${c1 < c0 ? ' ⭐⭐ 断掉了！' : ''}｜弹窗 ${JSON.stringify(dlg)}`);
        if (c1 < c0) { await shot(page, 'M-281-选中连线后按删除.png'); break; }
      }
      del.tries = tries;
      del.removed = tries.some((t) => t.after < t.before);
    }
  }
  out.delete = del;

  // ── ⑤ 收尾：账户复原复核
  const fin = await edgePts();
  const finIds = fin.map((e) => e.id);
  out.final = { count: fin.length, ids: finIds,
    originalIntact: before.every((b) => finIds.includes(b.id)),
    noExtra: finIds.every((i) => before.some((b) => b.id === i)) };
  console.log(`\n═══ ⑤ 收尾：连线 ${fin.length} 条｜原有两条都在=${out.final.originalIntact}｜无多余=${out.final.noExtra}`);
  console.log(`  id：${JSON.stringify(finIds)}`);

  console.log(`\n═══ 本轮结论 ═══`);
  console.log(`  · 只在选中态出现的层：${(probe.onlyInSelected || []).length} 层 ${JSON.stringify((probe.onlyInSelected || []).map((n) => n.tag + '.' + n.cls))}`);
  console.log(`  · 空闲基线自发漂移：${(out.buttons?.drift || []).length} 枚`);
  console.log(`  · 选中连线新增按钮：${(out.buttons?.newOnEdge || []).length} 枚`);
  console.log(`  · 取消选中后残留：${(out.buttons?.persisted || []).length} 枚`);
  console.log(`  · 断线成功了吗？ ${del.removed ? '✅ ' + JSON.stringify(del.tries?.find((t) => t.after < t.before)?.what) : '❌'}`);

  await logStep(B, {
    id: 'BV5-scissors-at-edge-midpoint',
    title: '⭐⭐⭐ 把连线中点那枚「剪刀」找出来——探针问错了地方',
    target: 'BV4 的截图揭穿 BV2 的盲点：**选中的连线中点浮着一枚剪刀**（就在仪器自证的点击点'
      + '`[405,428]` 上），而 BV2 在中点数到「0 个按钮」—— ⭐⭐ **因为剪刀不是 `<button>`**。'
      + '本轮 ① 在中点做**元素链三态解剖**（未选/悬停/选中），把「有没有按钮」换成「这里到底站着什么」；'
      + '② 修 BV4 的时序污染：空闲基线连采两次看漂移 + **往返差分** + 标注差分项**是否在视口内**；'
      + '③ 断线实验在**自造连线**上做，不碰用户已有的两条边。',
    evidence: out,
    visible_text: JSON.stringify({ 未选: probe.unselected, 悬停: probe.hovered, 选中: probe.select,
      只在选中出现: probe.onlyInSelected, 按钮: out.buttons, 删除: out.delete, 收尾: out.final }).slice(0, 3400),
    shot: 'M-282-自造连线选中之后.png',
  });
  console.log('\nBV5 完成');
} catch (e) {
  console.log('⛔ 中止：' + e.message + '\n' + (e.stack || '').split('\n').slice(0, 5).join('\n'));
} finally {
  await browser.close();
}
