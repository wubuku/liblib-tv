// 批次 50：给「组工具条是否出现『下载』」做控制变量。
//
// 背景：批次 15 断定组工具条只有三项（无「下载」），批次 35 在
// 「视频×2 + 时间线 + 主体 + 文本×4」的组上测到第四项「下载」——两次冲突，
// 且都没做控制变量。本批只改一个变量：组里有没有媒体节点。
//   A 组 = 3 个文本节点
//   B 组 = 2 个文本 + 1 个空视频节点
//
// 本轮探针（jimeng-b50-probe.mjs）校准到的三条硬事实：
//  1) 抓手工具拖 (dx,dy) → 视口 translate **同向** +（dx,dy)，画布数据不动；
//  2) 新建节点固定落在**视口正中**（屏幕框 192×192，中心恰为 640,360→视口中心）；
//  3) 抓手拖拽不改缩放。
// 因此策略是「先平移、再建节点」：把视口中心挪到远离他人节点的空白画布区，
// 新节点就会直接生在那片空白里，框选矩形与他人节点区完全分离。
//
// 共享画布安全设计（吸取批次 35/39/48 的教训）：
//  1) 平移量按探针校准的方向算，并且**每拖一步都回读 translate** 验证确实动了；
//  2) 框选**前后都断言** id 集合必须**恰好等于**我建的那几个，不等就放弃、
//     绝不点「编组」（批次 35 的事故正是跳过了这一步）；
//  3) 额外断言框选矩形与他人 6 个节点的矩形**零相交**；
//  4) 编组/解除编组**前后都断言**编组数与节点数；
//  5) 全程不点任何生成类按钮；临时节点先记账，收尾按 id 全删。
import { chromium } from 'playwright';
import { readFileSync } from 'node:fs';
import { keyGuard, canvasBaseline, diffNodePositions, pinViewport } from './jimeng-safe-keys.mjs';

const BASELINE = JSON.parse(readFileSync(new URL('./jimeng-baseline-nodes.json', import.meta.url), 'utf8'));
const OTHERS = Object.keys(BASELINE.nodes);

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
if (!p) { console.error('canvas page not found'); process.exit(1); }
await pinViewport(p);

const reset = async () => { for (let i = 0; i < 3; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(320); } };
// ⚠️ 批次 50 实测：选中一个组时，`.react-flow__node-group` 会匹配到 **2 个**元素 ——
//    组节点本身 + `__group-resize-chrome__<组id>`（缩放把手，只在选中时渲染）。
//    不排除这个伪节点，编组后的「组数 +1 / 节点数 +1」断言会全部误判。
const real = (list) => list.filter((x) => !String(x).startsWith('__group-resize-chrome__'));
const ids = async () => real(await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id'))));
const selIds = async () => real(await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((e) => e.getAttribute('data-id'))));
const groupIds = async () => real(await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node-group')).map((e) => e.getAttribute('data-id'))));
const vp = () => p.evaluate(() => {
  const v = document.querySelector('.react-flow__viewport');
  if (!v) return null;
  const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)\s*scale\(([-\d.]+)\)/.exec(v.style.transform);
  return m ? { tx: +m[1], ty: +m[2], scale: +m[3] } : null;
});
const boxes = (list) => p.evaluate((I) => I.map((id) => {
  const e = document.querySelector(`.react-flow__node[data-id="${id}"]`);
  if (!e) return null; const r = e.getBoundingClientRect();
  return { id, x: r.x, y: r.y, w: r.width, h: r.height };
}), list);
const isEmpty = (x, y) => p.evaluate(([x, y]) => {
  const el = document.elementFromPoint(x, y);
  if (!el) return true;
  if (el.closest('.react-flow__node')) return false;
  if (el.closest('button,[role="button"],input,textarea,[role="menu"],[role="listbox"],[data-testid="node-toolbar"],[data-testid="workspace-bottom-dock-frame"],[data-testid="canvas-fixed-toolbar-left-rail"],[data-testid="canvas-top-bar-actions"],[data-testid="canvas-panel-launcher"]')) return false;
  return true;
}, [x, y]);
const findEmpty = async () => {
  for (let y = 110; y <= 630; y += 20) for (let x = 80; x <= 1250; x += 20) {
    if (x > 1150 && y > 600) continue;
    if (await isEmpty(x, y)) return { x, y };
  }
  return null;
};
const setTool = async (want) => {
  const cur = await p.evaluate(() => (document.querySelector('[data-testid="canvas-pointer-tool-toggle"]') || {}).getAttribute?.('aria-label'));
  if (cur !== want) { await p.evaluate(() => document.querySelector('[data-testid="canvas-pointer-tool-toggle"]').click()); await p.waitForTimeout(600); }
  return await p.evaluate(() => (document.querySelector('[data-testid="canvas-pointer-tool-toggle"]') || {}).getAttribute?.('aria-label'));
};
// 正确抓手拖拽（探针校准：内容与鼠标同向移动）
const drag = async (from, tdx, tdy) => {
  const steps = Math.max(1, Math.ceil(Math.max(Math.abs(tdx), Math.abs(tdy)) / 130));
  await p.mouse.move(from.x, from.y);
  await p.mouse.down();
  await p.waitForTimeout(120);
  for (let i = 1; i <= steps; i++) { await p.mouse.move(from.x + (tdx * i) / steps, from.y + (tdy * i) / steps); await p.waitForTimeout(45); }
  await p.mouse.up();
  await p.waitForTimeout(650);
};
// 把视口平移到「视口中心 = 画布 (CX,CY)」；每步回读验证
const panTo = async (CX, CY) => {
  let ok = true;
  for (let round = 0; round < 20; round++) {
    const v = await vp();
    if (!v) return false;
    // 探针实测：新节点屏幕框 (544,384) 192×192 → 落点中心 = (640,480)
    const tx = 640 - CX * v.scale, ty = 480 - CY * v.scale;
    const dx = tx - v.tx, dy = ty - v.ty;
    if (Math.abs(dx) < 4 && Math.abs(dy) < 4) { console.log(`  平移到位 ${round} 步: ${JSON.stringify(v)}`); return true; }
    const s = await findEmpty();
    if (!s) { console.log('  ⛔ 找不到空白起点，平移中止'); return false; }
    const sx = Math.max(-130, Math.min(130, dx)), sy = Math.max(-90, Math.min(90, dy));
    await drag(s, sx, sy);
    const v2 = await vp();
    const moved = Math.abs(v2.tx - v.tx) > 1 || Math.abs(v2.ty - v.ty) > 1;
    if (!moved) { console.log(`  ⛔ 第 ${round} 步拖拽没生效（起点 ${JSON.stringify(s)}，期望 ${sx},${sy}）`); return false; }
    if (v2.scale !== v.scale) { console.log('  ⛔ 缩放被改变，放弃'); return false; }
  }
  console.log('  ⛔ 20 步仍未到位');
  ok = false;
  return ok;
};
const toolbarItems = () => p.evaluate(() => Array.from(document.querySelectorAll('[data-testid="node-toolbar"]'))
  .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 1 && r.height > 1; })
  .map((bar) => {
    const r = bar.getBoundingClientRect();
    return {
      bar: `${Math.round(r.width)}x${Math.round(r.height)}`,
      inner: Array.from(bar.querySelectorAll('div[aria-label]')).map((e) => e.getAttribute('aria-label')).slice(0, 4),
      items: Array.from(bar.querySelectorAll('button,[role="button"]')).map((e) => {
        const rr = e.getBoundingClientRect();
        return { name: e.getAttribute('aria-label') || (e.innerText || '').trim().slice(0, 8),
          w: Math.round(rr.width), h: Math.round(rr.height),
          disabled: e.getAttribute('aria-disabled'),
          title: e.getAttribute('title'),
          txt: (e.innerText || '').replace(/\n/g, ' ⏎ ').trim().slice(0, 60),
          data: Array.from(e.attributes).filter((a) => a.name.startsWith('data-')).map((a) => `${a.name}=${a.value}`).join(' '),
          cx: Math.round(rr.x + rr.width / 2), cy: Math.round(rr.y + rr.height / 2) };
      }) };
  }));
// 深挖「下载」项的真实 DOM 与「原因副文案」是否存在
// （手册旧结论写的是「禁用 + 附『没有可用的就绪资源』」，必须用 outerHTML 核实）
const deepDownload = () => p.evaluate(() => {
  const bars = Array.from(document.querySelectorAll('[data-testid="node-toolbar"]')).filter((e) => e.getBoundingClientRect().width > 1);
  const out = bars.map((bar) => {
    const dl = Array.from(bar.querySelectorAll('button,[role="button"]')).find((e) => e.getAttribute('aria-label') === '下载');
    return { barText: (bar.innerText || '').replace(/\n/g, ' ⏎ ').trim().slice(0, 120),
      html: dl ? dl.outerHTML.slice(0, 420) : '(无下载项)',
      parentText: dl ? (dl.parentElement ? (dl.parentElement.innerText || '').replace(/\n/g, ' ⏎ ').trim().slice(0, 80) : '') : '' };
  });
  const hits = [];
  for (const e of document.querySelectorAll('div,span,p,button,li,label')) {
    if (e.children.length) continue;
    const t = (e.textContent || '').trim();
    if (t && /就绪资源|没有可用/.test(t)) hits.push(t.slice(0, 40));
    if (hits.length >= 4) break;
  }
  return { out, hits };
});

const createByRail = async (aria) => {
  const before = await ids();
  await p.evaluate((a) => { const t = Array.from(document.querySelectorAll('button,[role="button"]')).find((e) => e.getAttribute('aria-label') === a); if (t) t.click(); }, aria);
  await p.waitForTimeout(1700);
  const fresh = (await ids()).filter((x) => !before.includes(x));
  if (fresh.length !== 1) { console.error(`  ABORT: 建「${aria}」新增 ${fresh.length} 个`); return null; }
  return fresh[0];
};
const deleteById = async (id) => {
  if (!(await ids()).includes(id)) return 'absent';
  const pt = await p.evaluate((v) => { const e = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!e) return null; const r = e.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + 16) }; }, id);
  if (!pt) return 'nobox';
  await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(650);
  let s = await p.evaluate(() => { const e = document.querySelector('.react-flow__node.selected'); return e ? e.getAttribute('data-id') : null; });
  if (s !== id) {
    await p.evaluate((v) => { const e = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!e) return; const r = e.getBoundingClientRect(); const cx = Math.round(r.x + r.width / 2), cy = Math.round(r.y + 16);
      for (const t of ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click']) e.dispatchEvent(new MouseEvent(t, { bubbles: true, cancelable: true, clientX: cx, clientY: cy })); }, id);
    await p.waitForTimeout(650);
    s = await p.evaluate(() => { const e = document.querySelector('.react-flow__node.selected'); return e ? e.getAttribute('data-id') : null; });
  }
  if (s !== id) return 'notselected';
  await p.evaluate((v) => { const e = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!e) return; const r = e.getBoundingClientRect(); e.dispatchEvent(new MouseEvent('contextmenu', { bubbles: true, cancelable: true, clientX: Math.round(r.x + r.width / 2), clientY: Math.round(r.y + 12) })); }, id);
  await p.waitForTimeout(650);
  const clicked = await p.evaluate(() => { const m = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"],[role="menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop(); if (!m) return false;
    const it = Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => /删除/.test(x.innerText || '')); if (!it) return false; it.click(); return true; });
  await p.waitForTimeout(1200);
  return clicked ? 'deleted' : 'noclick';
};
// 框选 + 三重断言：矩形与他人零相交 / 选中集合恰好等于目标 / 前后都报数
const rubberBand = async (myIds, label) => {
  const mine = (await boxes(myIds)).filter(Boolean);
  if (mine.length !== myIds.length) { console.log(`  ❌ ${label}: 有节点不在视口内`); return false; }
  const others = (await boxes(OTHERS)).filter(Boolean);
  const minX = Math.min(...mine.map((v) => v.x)), maxX = Math.max(...mine.map((v) => v.x + v.w));
  const minY = Math.min(...mine.map((v) => v.y)), maxY = Math.max(...mine.map((v) => v.y + v.h));
  const sx = Math.round(minX - 28), sy = Math.round(minY - 28);
  const ex = Math.round(maxX + 24), ey = Math.round(maxY + 24);
  // 底栏 dock 的真实上沿（不写死 640，实测拿 DOM）
  const dockTop = await p.evaluate(() => { const d = document.querySelector('[data-testid="workspace-bottom-dock-frame"]'); return d ? Math.round(d.getBoundingClientRect().top) : 640; });
  if (sx < 80 || ex > 1265 || sy < 110 || ey > Math.min(dockTop, 705) - 6) { console.log(`  ❌ ${label}: 框选矩形出安全区 (${sx},${sy})-(${ex},${ey})，dock 上沿 ${dockTop}`); return false; }
  if (!(await isEmpty(sx, sy))) { console.log(`  ❌ ${label}: 起点(${sx},${sy})不空`); return false; }
  const hit = others.filter((o) => o.x < ex && o.x + o.w > sx && o.y < ey && o.y + o.h > sy);
  console.log(`  框选矩形 (${sx},${sy})-(${ex},${ey})，我的 ${myIds.length} 个节点全在矩形内`);
  console.log(`  与他人节点相交: ${hit.length} 个 ${hit.map((o) => o.id).join(',') || '✅ 0'}`);
  if (hit.length) return false;
  if ((await selIds()).length) { console.log(`  ❌ ${label}: 框选前已有选中`); return false; }
  await p.mouse.move(sx, sy);
  await p.mouse.down();
  for (let i = 1; i <= 10; i++) { await p.mouse.move(sx + ((ex - sx) * i) / 10, sy + ((ey - sy) * i) / 10); await p.waitForTimeout(55); }
  await p.mouse.up();
  await p.waitForTimeout(750);
  const post = (await selIds()).sort(), want = [...myIds].sort();
  const ok = post.length === want.length && post.every((v, i) => v === want[i]);
  console.log(`    选中 ${post.length} 个: ${post.join(', ')}`);
  console.log(`    ${ok ? '✅ 与目标完全一致' : `❌ 不一致（目标 ${want.join(',')}）`}`);
  return ok;
};

// 把「我的节点」的屏幕包围盒中心拖到视口中心 (640,480)。
// ⚠️ 不能用节点左上角 transform 的中点当中心——那是**锚点**，不是包围盒中心，
//    320×320 的节点会让中心偏 160px，框选矩形直接掉出安全区（批次 50 实测踩过）。
const centerMine = async (myIds) => {
  for (let round = 0; round < 8; round++) {
    const u = await p.evaluate((I) => {
      const rs = I.map((id) => { const e = document.querySelector(`.react-flow__node[data-id="${id}"]`); return e ? e.getBoundingClientRect() : null; }).filter(Boolean);
      if (rs.length !== I.length) return null;
      const x0 = Math.min(...rs.map((r) => r.x)), x1 = Math.max(...rs.map((r) => r.right));
      const y0 = Math.min(...rs.map((r) => r.y)), y1 = Math.max(...rs.map((r) => r.bottom));
      return { x0, y0, x1, y1, cx: (x0 + x1) / 2, cy: (y0 + y1) / 2 };
    }, myIds);
    if (!u) { console.log('  ⛔ 有节点不在视口内，无法居中'); return false; }
    const dx = 640 - u.cx, dy = 480 - u.cy;
    if (Math.abs(dx) < 6 && Math.abs(dy) < 6) { console.log(`  我的节点并集屏幕框 (${Math.round(u.x0)},${Math.round(u.y0)})-(${Math.round(u.x1)},${Math.round(u.y1)})，已居中`); return true; }
    const s = await findEmpty();
    if (!s) { console.log('  ⛔ 找不到空白起点，居中失败'); return false; }
    await drag(s, Math.max(-130, Math.min(130, dx)), Math.max(-130, Math.min(130, dy)));
  }
  console.log('  ⛔ 8 步仍未居中');
  return false;
};

// ---- 起点 ----
await reset();
const bad0 = await diffNodePositions(p, BASELINE.nodes, 1.5);
if (bad0.length || (await ids()).length !== 6) { console.error('ABORT: 起点与基线不一致', JSON.stringify({ bad: bad0 })); await b.close(); process.exit(2); }
console.log('起点与基线一致 ✅  6 个节点、canvas 位置逐项对齐');
console.log('焦点守卫:', (await keyGuard(p)).where);

const CREATED = [];
const CX = 1700, CY = 400;   // 视口中心要挪到的画布坐标（远离他人节点 x≤960）
const ROUNDS = [
  { label: 'A 组：3 个文本节点', want: ['文本', '文本', '文本'] },
  { label: 'B 组：2 个文本 + 1 个空视频节点', want: ['文本', '文本', '视频'] },
];
const RESULTS = [];

for (const round of ROUNDS) {
  console.log(`\n########## ${round.label} ##########`);
  await reset();
  // ① 先平移到空白区（探针实测：建节点固定落在视口中心，所以必须先挪视口再建）
  await setTool('抓手工具');
  const panned0 = await panTo(CX, CY);
  await setTool('选择工具');
  if (!panned0) { console.log('  ⛔ 起点平移失败，本轮放弃'); continue; }
  const vBefore = await vp();
  // ② 再建节点
  const myIds = [];
  for (const aria of round.want) { const id = await createByRail(aria); if (!id) break; myIds.push(id); CREATED.push(id); }
  const vAfter = await vp();
  console.log(`  建节点前后视口: ${JSON.stringify(vBefore)} → ${JSON.stringify(vAfter)}`,
    vBefore && vAfter && vBefore.scale !== vAfter.scale ? `🔴 建节点把缩放 ${vBefore.scale} → ${vAfter.scale}（自动适配）` : '缩放未变');
  if (myIds.length !== 3) { console.log('  建节点未达 3 个'); for (const id of myIds) await deleteById(id); while (CREATED.length) await deleteById(CREATED.pop()); continue; }
  const titles = await p.evaluate((I) => I.map((id) => { const e = document.querySelector(`.react-flow__node[data-id="${id}"]`); return e ? (e.innerText || '').split('\n').filter(Boolean).pop().trim().slice(0, 20) : null; }), myIds);
  console.log('  我建的三个:', JSON.stringify(myIds), '末行文字', JSON.stringify(titles));
  // ③ 新建节点会自动选中 → 框选前必须先清选中
  console.log('  建完自动选中:', JSON.stringify(await selIds()));
  await reset();
  console.log('  清选中后:', (await selIds()).length, '个');
  // ④ 视口对齐「我的节点并集包围盒」，保证框选矩形落在安全区
  const myPos = await p.evaluate((I) => I.map((id) => { const e = document.querySelector(`.react-flow__node[data-id="${id}"]`); const m = e && /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(e.style.transform); return m ? [+m[1], +m[2]] : null; }), myIds);
  console.log('  我的节点 canvas 坐标:', JSON.stringify(myPos));
  await setTool('抓手工具');
  const centered = await centerMine(myIds);
  await setTool('选择工具');
  if (!centered) { console.log('  本轮放弃'); for (const id of myIds) await deleteById(id); while (CREATED.length) await deleteById(CREATED.pop()); continue; }
  const othersNow = (await boxes(OTHERS)).filter(Boolean).filter((o) => o.x < 1280 && o.x + o.w > 0 && o.y < 720 && o.y + o.h > 0);
  console.log('  对齐后视口内可见的他人节点:', othersNow.length, '个', othersNow.map((o) => `${o.id}@${Math.round(o.x)},${Math.round(o.y)}`).join(' '));

  const g0 = (await groupIds()).length, n0 = (await ids()).length;
  if (!await rubberBand(myIds, '框选')) { await reset(); for (const id of myIds) await deleteById(id); while (CREATED.length) await deleteById(CREATED.pop()); continue; }
  const tbMulti = await toolbarItems();
  console.log('  多选工具条:', JSON.stringify(tbMulti.map((t) => ({ bar: t.bar, items: t.items.map((i) => i.name) }))));
  const mdl = tbMulti.flatMap((t) => t.items).find((i) => i.name === '下载');
  if (mdl) console.log(`  多选态下载项: aria-disabled=${JSON.stringify(mdl.disabled)} 文案=${JSON.stringify(mdl.txt)} ${mdl.w}×${mdl.h}`);
  console.log('  多选态深挖:', JSON.stringify(await deepDownload(), null, 1));
  const gb = tbMulti.flatMap((t) => t.items).find((i) => i.name === '编组');
  if (!gb) { console.log('  ❌ 没有「编组」项'); await reset(); for (const id of myIds) await deleteById(id); while (CREATED.length) await deleteById(CREATED.pop()); continue; }
  await p.mouse.click(gb.cx, gb.cy); await p.waitForTimeout(1100);
  const g1 = (await groupIds()).length, n1 = (await ids()).length;
  console.log(`  编组后：真组数 ${g0} → ${g1}，节点总数 ${n0} → ${n1}`);
  if (g1 !== g0 + 1) { console.log('  ❌ 编组没发生'); await reset(); }
  else {
    const gid = (await groupIds())[0];
    const gmeta = await p.evaluate((v) => {
      const g = document.querySelector(`.react-flow__node-group[data-id="${v}"]`);
      if (!g) return null; const r = g.getBoundingClientRect();
      return { aria: g.getAttribute('aria-label'), text: (g.innerText || '').split('\n').filter(Boolean),
        nested: Array.from(g.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')),
        rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
    }, gid);
    console.log('  组节点:', JSON.stringify(gmeta));
    // 选中组：点组卡片标题「编组 N」那几个字本身（实测只有标题那一小块收得到点击）
    await reset();
    const gsel = await p.evaluate((v) => {
      const g = document.querySelector(`.react-flow__node-group[data-id="${v}"]`);
      if (!g) return null;
      const r = g.getBoundingClientRect();
      const cx = Math.round(r.x + r.width / 2);
      for (let y = Math.round(r.y + 2); y <= Math.round(r.y + 40) && y < r.y + r.height; y += 2) {
        const el = document.elementFromPoint(cx, y);
        if (el && el.closest(`.react-flow__node-group[data-id="${v}"]`)) return { x: cx, y, tag: el.tagName, txt: (el.innerText || '').trim().slice(0, 10) };
      }
      return null;
    }, gid);
    console.log('  组标题可点位置:', JSON.stringify(gsel));
    if (gsel) {
      await p.mouse.click(gsel.x, gsel.y); await p.waitForTimeout(900);
      const selNow = await selIds();
      console.log('  点后选中:', JSON.stringify(selNow), selNow.includes(gid) ? '✅ 含组本身' : '⚠️ 不含组');
    }
    const tbG = await toolbarItems();
    console.log('  🔑 组工具条:', JSON.stringify(tbG, null, 1));
    const gItems = tbG.flatMap((t) => t.items);
    const names = gItems.map((i) => i.name);
    const dl = gItems.find((i) => i.name === '下载');
    console.log('  逐项:', names.join(' ｜ '));
    console.log(`  ⇒ 含「下载」？ ${names.includes('下载') ? '🔴 是' : '❌ 否'}`);
    if (dl) console.log(`  下载项细节: aria-disabled=${JSON.stringify(dl.disabled)} title=${JSON.stringify(dl.title)} 文案=${JSON.stringify(dl.txt)} data=${JSON.stringify(dl.data)} ${dl.w}×${dl.h}`);
    console.log('  组态深挖:', JSON.stringify(await deepDownload(), null, 1));
    // 布局下拉（只读：开菜单看逐字，不点任何条目）
    const lay = gItems.find((i) => i.name === '布局');
    if (lay) {
      await p.mouse.click(lay.cx, lay.cy); await p.waitForTimeout(800);
      const menu = await p.evaluate(() => { const m = Array.from(document.querySelectorAll('[role="menu"],[data-testid="canvas-zoom-menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop();
        return m ? { w: Math.round(m.getBoundingClientRect().width), h: Math.round(m.getBoundingClientRect().height), items: Array.from(m.querySelectorAll('[role="menuitem"],button')).map((e) => (e.getAttribute('aria-label') || e.innerText || '').trim().split('\n')[0]) } : null; });
      console.log('  布局下拉:', JSON.stringify(menu));
      await p.keyboard.press('Escape'); await p.waitForTimeout(500);
    }
    RESULTS.push({ label: round.label, bar: tbG.map((t) => t.bar), names, hasDownload: names.includes('下载'), dl: dl && { disabled: dl.disabled, title: dl.title, txt: dl.txt } });
    // 解除编组
    const un = tbG.flatMap((t) => t.items).find((i) => i.name === '解除编组');
    if (un) { await p.mouse.click(un.cx, un.cy); await p.waitForTimeout(1100); }
    else { console.log('  ❌ 找不到「解除编组」，改用 ⌘⇧G'); await reset(); await p.keyboard.press('Meta+Shift+G'); await p.waitForTimeout(1000); }
    console.log(`  解除编组后：真组数 ${g1} → ${(await groupIds()).length}，节点总数 ${n1} → ${(await ids()).length}`);
  }
  await reset();
  // 本轮收尾：先确保没有残留编组（有就 ⌘⇧G 解除），再按 id 删我自己的节点
  let gleft = await groupIds();
  if (gleft.length) {
    console.log('  ⚠️ 残留编组', JSON.stringify(gleft), '→ 逐个选中后 ⌘⇧G');
    for (const g of gleft) {
      const gmeta = await p.evaluate((v) => { const e = document.querySelector(`.react-flow__node-group[data-id="${v}"]`); if (!e) return null; const r = e.getBoundingClientRect();
        return { nested: Array.from(e.querySelectorAll('.react-flow__node')).map((x) => x.getAttribute('data-id')), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; }, g);
      if (!gmeta) { console.log('   ', g, '不在画布上'); continue; }
      if (gmeta.nested.some((x) => OTHERS.includes(x))) { console.error('  ⛔⛔ 组内含他人节点', g, JSON.stringify(gmeta.nested), '—— 停止，不自动解除'); await b.close(); process.exit(9); }
      const pt = await p.evaluate((v) => { const e = document.querySelector(`.react-flow__node-group[data-id="${v}"]`); const r = e.getBoundingClientRect(); const cx = Math.round(r.x + r.width / 2);
        for (let y = Math.round(r.y + 2); y <= Math.round(r.y + 40) && y < r.y + r.height; y += 2) { const el = document.elementFromPoint(cx, y); if (el && el.closest(`.react-flow__node-group[data-id="${v}"]`)) return { x: cx, y }; } return null; }, g);
      if (!pt) { console.log('   ', g, '标题点不中'); continue; }
      await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(800);
      await p.keyboard.press('Meta+Shift+G'); await p.waitForTimeout(1100);
      console.log('    ⌘⇧G 后真组数', (await groupIds()).length);
      await reset();
    }
    gleft = await groupIds();
    if (gleft.length) console.error('  ⛔ 仍有残留编组', JSON.stringify(gleft));
  }
  for (const id of myIds) console.log('  删', id, '→', await deleteById(id));
  while (CREATED.length) await deleteById(CREATED.pop());
  const nEnd = (await ids()).length, gEnd = (await groupIds()).length;
  console.log(`  本轮结束，节点数 ${nEnd}（期望 6）${nEnd === 6 ? '✅' : '❌'}，真组数 ${gEnd}${gEnd === 0 ? ' ✅' : ' ❌'}`);
  if (nEnd !== 6 || gEnd !== 0) { console.error('  ⚠️ 本轮未回到基线节点集，后续轮次可能受影响'); }
}

console.log('\n########## A/B 对照 ##########');
for (const r of RESULTS) console.log(`  ${r.label}：${r.bar.join(' / ')} ｜ ${r.names.join(' ｜ ')} ｜ 含下载 ${r.hasDownload ? '是' : '否'}`);
if (RESULTS.length === 2) {
  const [a, bb] = RESULTS;
  console.log(`  ⇒ 唯一变量=组内有无媒体节点：A ${a.hasDownload ? '有' : '无'}「下载」，B ${bb.hasDownload ? '有' : '无'}「下载」 → ${a.hasDownload !== bb.hasDownload ? '🔴 媒体节点就是开关' : (a.hasDownload ? '两者都有' : '两者都没有')}`);
}

// ---- 收尾归位 ----
await reset();
await setTool('选择工具');
await p.keyboard.press('Escape'); await p.waitForTimeout(400);
await p.mouse.click(700, 150); await p.waitForTimeout(600);
await p.keyboard.press('Escape'); await p.waitForTimeout(400);
await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(600);
const zsel = 'input[data-testid="canvas-zoom-percent-input"]';
if (await p.$(zsel)) { await p.fill(zsel, '60'); await p.keyboard.press('Enter'); await p.waitForTimeout(900); }
await p.keyboard.press('Escape'); await p.waitForTimeout(400);
await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(600);
await p.evaluate(() => { const m = document.querySelector('[data-testid="canvas-zoom-menu"]');
  const it = m && Array.from(m.querySelectorAll('button,[role="menuitem"]')).find((e) => /适配画布/.test(e.innerText || '')); if (it) it.click(); });
await p.waitForTimeout(1300);
await p.keyboard.press('Escape'); await p.waitForTimeout(400);
await p.mouse.click(700, 150); await p.waitForTimeout(700);

const fin = await canvasBaseline(p);
const badFin = await diffNodePositions(p, BASELINE.nodes, 1.5);
const g = await keyGuard(p);
console.log('\n=== 收尾核对 ===');
console.log('  焦点守卫:', g.safe ? '✅ 可按' : `⛔ ${g.where}`);
console.log('  节点数:', fin.nodes.length, '(基线 6)');
console.log('  状态行:', fin.status);
console.log('  积分:', fin.credit, '(基线', BASELINE.credit + ')');
console.log('  缩放:', fin.zoom, '| 编组数', (await groupIds()).length);
console.log('  位置偏离:', badFin.length, badFin.length ? badFin.join(', ') : '✅ 0');
console.log('  剩余待删:', JSON.stringify(CREATED));
await b.close();
