// 批次 123 · a 轮（只读）：画布上的节点**盖住顶栏**这回事，有多严重。
//
// 🔑 靶子来自批次 122 a 轮的顶栏普查，有一行当时没深究：
//   `<DIV> [12,10,871,40] tid="canvas-top-bar-left"`
//   「中心命中=DIV tid=flow-node-target-handle」**「命中落回自己=false」**
//   ⇒ 顶栏**左段**的中心点 (447,30) 上，命中的是**某个节点的连接把手**，
//     不是顶栏自己。也就是说**节点画到了顶栏上面**。
//   而批次 122 顺带读到：顶栏 `HEADER[canvas-top-bar]` 的 class 是
//   `pointer-events-none absolute left-3 top-[10px] z-canvas-chro…`，
//   **节点层 `.react-flow__renderer` 的 `z-index` 是 4**。
//   ⇒ 本轮要把「谁压谁」和「被盖住的范围」量出来。
//
// 本轮**纯只读**：不点任何按钮、不移动任何节点（那些节点是**别人的**）。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'a' };
const save = () => writeFileSync(new URL('./_tmp-b123a.json', import.meta.url), JSON.stringify(out, null, 1));

const zoom = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0]);

out.start = { zoom: await zoom(), credits: await credits(), status: await status() };
log('起点：', JSON.stringify(out.start));
await keyGuard(p);

// ============================================================
// ① 层序：顶栏 vs 节点层，逐个读 z-index 与 class
// ============================================================
out.layers = await p.evaluate(() => {
  const g = (sel) => { const e = document.querySelector(sel); if (!e) return { sel, __none: true };
    const cs = getComputedStyle(e); const q = e.getBoundingClientRect();
    return { sel, tag: e.tagName, z: cs.zIndex, pos: cs.position, pe: cs.pointerEvents, cls: (e.getAttribute('class') || '').toString().slice(0, 90), 矩形: [q.x, q.y, q.width, q.height].map(Math.round) }; };
  return {
    顶栏: g('[data-testid="canvas-top-bar"]'),
    顶栏左段: g('[data-testid="canvas-top-bar-left"]'),
    顶栏右段: g('[data-testid="canvas-top-bar-actions"]'),
    节点层: g('.react-flow__renderer'),
    节点容器: g('.react-flow__nodes'),
    pane: g('.react-flow__pane'),
    dock: g('[data-testid="canvas-navigation-dock"]'),
    左边栏: g('[data-testid="canvas-fixed-toolbar-left-rail"]'),
  };
});
log('\n=== ① 层序 ===');
for (const [k, v] of Object.entries(out.layers)) log(`   ${k.padEnd(8)} z=${String(v.z).padEnd(6)} pos=${String(v.pos).padEnd(8)} pe=${String(v.pe).padEnd(6)} ${JSON.stringify(v.矩形)}  ${JSON.stringify((v.cls || '').slice(0, 60))}`);

// ============================================================
// ② 顶栏被盖住的范围：逐列扫 elementFromPoint
// ============================================================
out.overlap = await p.evaluate(() => {
  const bar = document.querySelector('[data-testid="canvas-top-bar"]');
  if (!bar) return { __err: 'no-bar' };
  const r = bar.getBoundingClientRect();
  const cols = [];
  for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 4) {
    const y = Math.round(r.y + r.height / 2);
    const e = document.elementFromPoint(x, y);
    const inBar = bar.contains(e);
    const inNode = e ? !!e.closest('.react-flow__node') : false;
    cols.push({ x, 命中: e ? e.tagName + ' tid=' + e.getAttribute('data-testid') + ' aria=' + e.getAttribute('aria-label') : null, 在顶栏内: inBar, 在节点内: inNode });
  }
  const 被盖 = cols.filter((c) => !c.在顶栏内);
  // 归并成连续区间
  const runs = []; let cur = null;
  for (const c of cols) { if (!c.在顶栏内) { if (!cur) { cur = { 起: c.x, 止: c.x, 命中集合: new Set() }; runs.push(cur); } else cur.止 = c.x; cur.命中集合.add(c.命中); }
    else cur = null; }
  return { 顶栏矩形: [r.x, r.y, r.width, r.height].map(Math.round), 采样列数: cols.length, 被盖列数: 被盖.length,
    被盖比例: 被盖.length / cols.length, 区间: runs.map((x) => ({ x: [x.起, x.止], 宽: x.止 - x.起 + 4, 命中: [...x.命中集合] })),
    顶栏自身可点的点: cols.filter((c) => c.在顶栏内).length };
});
log('\n=== ② 顶栏被盖住的范围 ===');
log('  顶栏矩形：', JSON.stringify(out.overlap.顶栏矩形), '｜采样列', out.overlap.采样列数, '｜被盖', out.overlap.被盖列数, `（${(out.overlap.被盖比例 * 100).toFixed(1)}%）`);
out.overlap.区间.forEach((x) => log(`   x∈[${x.x[0]}, ${x.x[1]}] 宽 ${x.宽} → 命中 ${JSON.stringify(x.命中)}`));
save();

// ============================================================
// ③ 盖住顶栏的是哪个节点？它自己有多大、离顶栏多近
// ============================================================
out.who = await p.evaluate(() => {
  const r = (e) => { const q = e.getBoundingClientRect(); return [q.x, q.y, q.width, q.height].map(Math.round); };
  const list = [];
  for (const n of document.querySelectorAll('.react-flow__node[data-id]')) {
    const q = n.getBoundingClientRect();
    if (q.width === 0 || q.height === 0) continue;
    if (q.bottom <= 10 || q.top >= 50) continue;           // 与顶栏 y∈[10,50] 有交集
    list.push({ id: n.getAttribute('data-id'), 类型: (n.className || '').toString().split(' ').find((c) => c.startsWith('react-flow__node-')) || '?',
      标题: (n.innerText || '').split('\n')[0], 矩形: r(n), 与顶栏重叠高: Math.max(0, Math.min(q.bottom, 50) - Math.max(q.top, 10)),
      selected: n.classList.contains('selected'),
      canvas坐标: (() => { const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(n.style.transform || ''); return m ? [Number(m[1]), Number(m[2])] : null; })() });
  }
  return { 与顶栏相交的节点数: list.length, 节点: list.sort((a, b) => b.与顶栏重叠高 - a.与顶栏重叠高) };
});
log('\n=== ③ 盖住顶栏（或与之相交）的节点：' + out.who.与顶栏相交的节点数 + ' 个 ===');
out.who.节点.forEach((n) => log(`   ${n.id} ${n.类型} 「${n.标题}」 ${JSON.stringify(n.矩形)} 重叠高=${n.与顶栏重叠高} canvas=${JSON.stringify(n.canvas坐标)} selected=${n.selected}`));
save();

// ============================================================
// ④ 顶栏左段那几个可点元素，逐个测「点得到吗」
// ============================================================
out.reach = await p.evaluate(() => {
  const want = ['canvas-project-logo', 'canvas-project-title-trigger', 'canvas-project-trigger', 'canvas-node-summary-trigger', 'canvas-share-trigger', 'canvas-editor-menu', 'canvas-commerce-entry', 'canvas-user-menu-trigger'];
  const r = (e) => { const q = e.getBoundingClientRect(); return [q.x, q.y, q.width, q.height].map(Math.round); };
  const res = [];
  for (const t of want) {
    const e = document.querySelector(`[data-testid="${t}"]`);
    if (!e) { res.push({ tid: t, __none: true }); continue; }
    const q = e.getBoundingClientRect();
    // 在它自己的范围内扫，找有多少个点能命中它自己
    let 可命中点 = 0, 采样点 = 0, 首个被挡 = null;
    for (let y = Math.ceil(q.y) + 2; y <= q.y + q.height - 2; y += 3)
      for (let x = Math.ceil(q.x) + 2; x <= q.x + q.width - 2; x += 3) {
        采样点++;
        const h = document.elementFromPoint(x, y);
        if (h && (h === e || e.contains(h))) 可命中点++;
        else if (!首个被挡) 首个被挡 = { x, y, 挡住的: h ? h.tagName + ' tid=' + h.getAttribute('data-testid') : null };
      }
    const btn = e.tagName === 'BUTTON' || e.getAttribute('role') === 'button' ? e : e.querySelector('button,[role=button]');
    res.push({ tid: t, 矩形: [q.x, q.y, q.width, q.height].map(Math.round), 采样点, 可命中点, 全可命中: 可命中点 === 采样点, 首个被挡,
      实际可点的那个元素: btn ? btn.tagName + ' aria=' + btn.getAttribute('aria-label') + ' tid=' + btn.getAttribute('data-testid') : '（本元素就是）' });
  }
  return res;
});
log('\n=== ④ 顶栏各按钮「点得到吗」（在自己矩形内逐点 elementFromPoint）===');
out.reach.forEach((d) => log(`   ${d.__none ? d.tid + ' 不存在' : `${d.tid.padEnd(28)} ${JSON.stringify(d.矩形)} 可命中 ${d.可命中点}/${d.采样点} ${d.全可命中 ? '✅全可命中' : '⛔有被挡：' + JSON.stringify(d.首个被挡)}\n        实际可点元素：${d.实际可点的那个元素}`}`));
save();

out.end = { zoom: await zoom(), status: await status() };
save();
log('\n终点：', JSON.stringify(out.end));
log('\nDONE a');
process.exit(0);
