// Batch BG2 — 连接口在**有连线 / 选中 / 悬停**三种状态下到底长什么样。
//
// BG1 把 11 个节点的连接口全盘出来了，但撞上一个必须解释的现象：
//   **所有连接口的 `getBoundingClientRect()` 都是 `0×0`** —— 它们当前不可见、不可点。
//
// 「这算不算数」有两种可能，必须分清：
//   (a) 连接口在**没有连线时就不渲染成可见的圆点**（那要连上才看得见）；
//   (b) 我的读法有问题（class 认对了但读的不是真正那个元素）。
//
// ✅ 画布上**本来就有 1 条连线**（早期批次用 `⌘L` 建的），那两个节点的连接口
//    必然是「已激活」状态 —— 直接对比「有连线的节点」与「无连线的节点」，
//    答案自己会冒出来，不用猜。
//
// 第二组对比：**选中**节点时连接口会不会变大/变色。
// 动手画一条新连线（从 source 拖到 target）再量一次 —— 连线可撤销，成本低。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBG2';
const { browser, page } = await launch();

/** ⭐ 连接口读数。**注意要同时读**元素本身**和**它所在节点的连线状态**。 */
const handles = () => page.evaluate(() => {
  const edges = [...document.querySelectorAll('.react-flow__edge')].map((e) => {
    const id = e.getAttribute('data-id') || '';
    return { id, source: e.getAttribute('data-source') || (/source-([\w-]+)/.exec(id) || [])[1] || null,
      target: e.getAttribute('data-target') || (/target-([\w-]+)/.exec(id) || [])[1] || null }; });
  const out = [];
  for (const n of document.querySelectorAll('.react-flow__node')) {
    const nid = n.getAttribute('data-id');
    const hs = [...n.querySelectorAll('[data-handleid]')].map((e) => {
      const r = e.getBoundingClientRect();
      const cs = getComputedStyle(e);
      return { handleId: e.getAttribute('data-handleid'),
        rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        cls: (e.className || '').toString().slice(0, 90),
        cursor: cs.cursor, opacity: cs.opacity, bg: cs.backgroundColor,
        border: cs.borderColor, w: cs.borderWidth, transform: cs.transform,
        display: cs.display, visibility: cs.visibility };
    });
    out.push({ id: nid, name: ((n.innerText || '').replace(/\s+/g, ' ').trim().split(' ')[0] || '').slice(0, 10),
      connectedAsSource: edges.some((e) => e.source === nid),
      connectedAsTarget: edges.some((e) => e.target === nid),
      selected: n.classList.contains('selected'),
      handles: hs });
  }
  return { edges, nodes: out };
});

const edgeCount = () => page.evaluate(() => document.querySelectorAll('.react-flow__edge').length);

async function exclusivePoint(pg, id) {
  return pg.evaluate((nid) => {
    const t = [...document.querySelectorAll('.react-flow__node')].find((n) => n.getAttribute('data-id') === nid);
    if (!t) return { err: 'no node' };
    const r = t.getBoundingClientRect();
    for (let fy = 0.2; fy <= 0.8; fy += 0.12) for (let fx = 0.06; fx <= 0.95; fx += 0.06) {
      const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
      const o = document.elementFromPoint(x, y);
      if (o && o.closest('.react-flow__node') === t) return { x, y };
    }
    return { err: 'no exclusive point' };
  }, id);
}

const fmt = (h) => `[${h.rect}] ${h.w}×${h.rect[2]}×${h.rect[3]} cur=${h.cursor} op=${h.opacity} bg=${h.bg} bd=${h.borderWidth}`;

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1600);
  await fitView(page); await page.waitForTimeout(1800);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '连接口在有连线 / 选中 / 悬停三种状态下的真实尺寸与样式' });

  const out = {};
  await page.mouse.move(720, 260); await page.waitForTimeout(800);

  // ═══ 1. 基线：哪些节点已经连着线？
  const h0 = await handles();
  console.log('--- BG2-1 基线 ---');
  console.log(`  画布上现有连线 ${h0.edges.length} 条：`, JSON.stringify(h0.edges));
  const conn = h0.nodes.filter((n) => n.connectedAsSource || n.connectedAsTarget);
  const free = h0.nodes.filter((n) => !n.connectedAsSource && !n.connectedAsTarget);
  console.log(`  已连线节点 ${conn.length} 个：${conn.map((n) => `${n.id}(${n.connectedAsSource ? 'S' : ''}${n.connectedAsTarget ? 'T' : ''})`).join(', ')}`);
  console.log(`  未连线节点 ${free.length} 个`);
  out.base = { edges: h0.edges, connected: conn.map((n) => n.id), free: free.map((n) => n.id) };
  console.log('  「已连线」节点的连接口：');
  for (const n of conn) n.handles.forEach((h) => console.log(`    ${n.name} ${h.handleId} → ${fmt(h)}`));
  console.log('  「未连线」节点的连接口：');
  for (const n of free.slice(0, 3)) n.handles.forEach((h) => console.log(`    ${n.name} ${h.handleId} → ${fmt(h)}`));
  out.baseDetail = { connected: conn, freeSample: free.slice(0, 3) };

  // ═══ 2. 选中一个未连线节点，看连接口会不会变大
  console.log('\n--- BG2-2 选中节点后的连接口 ---');
  const target = free.find((n) => n.id.startsWith('t-')) || free[0];
  if (!target) { console.log('  没有未连线节点'); out.select = { err: 'none' }; }
  else {
    const pt = await exclusivePoint(page, target.id);
    if (pt.err) { console.log('  ', pt.err); out.select = pt; }
    else {
      await page.mouse.click(pt.x, pt.y); await page.waitForTimeout(2400);
      const h1 = await handles();
      const sel = h1.nodes.find((n) => n.id === target.id);
      console.log(`  选中 ${target.id}（selected=${sel?.selected}）后：`);
      (sel?.handles || []).forEach((h) => console.log(`    ${h.handleId} → ${fmt(h)}`));
      out.select = { id: target.id, selected: sel?.selected, handles: sel?.handles };

      // ═══ 3. 从 source 口拖到另一个节点的 target 口，画一条新线
      console.log('\n--- BG2-3 试着连一条线 ---');
      const src = (sel?.handles || []).find((h) => h.handleId === 'source');
      const tgtNode = free.find((n) => n.id !== target.id);
      let newEdge = null;
      if (!src || !tgtNode) { console.log('  缺条件', { src: !!src, tgt: !!tgtNode }); out.connect = { err: 'no source or target node' }; }
      else {
        const before = await edgeCount();
        console.log(`  连线数 ${before} 条；准备把 ${target.id} 的 source 拖到 ${tgtNode.id} 的 target`);
        // 口是 0×0，点不到 —— 改用「节点边缘中点」落点（连接口就在那儿）
        const nrect = await page.evaluate((nid) => {
          const n = [...document.querySelectorAll('.react-flow__node')].find((x) => x.getAttribute('data-id') === nid);
          const r = n.getBoundingClientRect();
          return { x: r.x, y: r.y, w: r.width, h: r.height }; }, target.id);
        const mrect = await page.evaluate((nid) => {
          const n = [...document.querySelectorAll('.react-flow__node')].find((x) => x.getAttribute('data-id') === nid);
          const r = n.getBoundingClientRect();
          return { x: r.x, y: r.y, w: r.width, h: r.height }; }, tgtNode.id);
        const from = { x: Math.round(nrect.x + nrect.w - 2), y: Math.round(nrect.y + nrect.h / 2) };
        const to = { x: Math.round(mrect.x + 2), y: Math.round(mrect.y + mrect.h / 2) };
        await page.mouse.move(from.x, from.y); await page.mouse.down();
        for (let i = 1; i <= 12; i += 1) { await page.mouse.move(from.x + (to.x - from.x) * i / 12, from.y + (to.y - from.y) * i / 12); await page.waitForTimeout(70); }
        // 拖到一半时看有没有「正在连」的视觉
        const mid = await page.evaluate(() => [...document.querySelectorAll('.react-flow__connectionline,.react-flow__connection-path,.react-flow__handle')]
          .map((e) => { const r = e.getBoundingClientRect();
            return { cls: (e.className || '').toString().slice(0, 50), w: Math.round(r.width), h: Math.round(r.height) }; })
          .filter((x) => x.w > 0 || x.h > 0));
        console.log(`  拖动中可见的连线/连接口元素 ${mid.length} 个：`, JSON.stringify(mid).slice(0, 300));
        await page.mouse.up(); await page.waitForTimeout(2400);
        const after = await edgeCount();
        console.log(`  松手后连线数 ${before} → ${after} ${after > before ? '✅ 连上了' : '（没连上）'}`);
        newEdge = { before, after, created: after > before, midDrag: mid };
        await shot(page, 'M-195-连接口-拖拽中.png');
        out.shot = 'M-195-连接口-拖拽中.png';
        // 复原：⌘Z
        if (after > before) {
          await page.keyboard.press('Escape'); await page.waitForTimeout(500);
          await page.keyboard.press('Meta+z'); await page.waitForTimeout(2400);
          const back = await edgeCount();
          console.log(`  ⌘Z 撤销后连线数 ${back} 条 ${back === before ? '✅ 已复原' : '⚠️ 没复原'}`);
          out.connect = { ...newEdge, undoCount: back, restored: back === before };
        } else {
          out.connect = newEdge;
        }
      }
      // 画完线再量一次连接口
      if (newEdge?.created) {
        const h2 = await handles();
        const n2 = h2.nodes.find((n) => n.id === target.id);
        console.log('\n--- BG2-4 连上之后的连接口 ---');
        (n2?.handles || []).forEach((h) => console.log(`    ${h.handleId} → ${fmt(h)}`));
        out.afterConnect = { id: target.id, handles: n2?.handles };
      }
      await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
    }
  }

  await logStep(B, {
    id: 'BG2-handle-appearance',
    title: '连接口在有连线 / 选中 / 悬停状态下到底长什么样',
    target: 'BG1 发现 11 个节点的连接口 getBoundingClientRect 全是 0×0 —— 必须分清'
      + '「没有连线时就不渲染成可见圆点」和「我读的不是那个元素」。'
      + '画布上本来就有 1 条连线，直接对比已连线与未连线节点；'
      + '再从节点边缘拖一条新线看拖拽中与连上之后的口是什么样。',
    evidence: out,
    visible_text: JSON.stringify({ edges: out.base?.edges, connected: out.base?.connected,
      connectedHandles: out.baseDetail?.connected?.map((n) => `${n.name}:${n.handles.map((h) => `${h.handleId}=${h.rect[2]}×${h.rect[3]}`).join(',')}`),
      afterSelect: out.select?.handles?.map((h) => `${h.handleId}=${h.rect[2]}×${h.rect[3]}`),
      connect: out.connect, afterConnect: out.afterConnect?.handles?.map((h) => `${h.handleId}=${h.rect[2]}×${h.rect[3]}`) }).slice(0, 3000),
    shot: out.shot,
  });
  console.log('\nBG2 完成');
} finally {
  await browser.close();
}
