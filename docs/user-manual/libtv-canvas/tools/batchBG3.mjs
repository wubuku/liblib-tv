// Batch BG3 — 连接口「什么时候才看得见」。
//
// BG1/BG2 的读数组合起来是个谜：
//   · 11 个节点每个 2 个口，class 里明写 `target connectable` / `source connectable`
//   · `getBoundingClientRect()` **全是 0×0**，但 `display: block` / `visibility: visible` / `opacity: 1`
//   · 位置**是对的**（target 贴节点左边界、source 贴右边界）
//
// 「0×0 但可见」有三种可能，必须分开：
//   (a) 可见圆点是用**伪元素/背景**画的，盒子本身没尺寸；
//   (b) 要**悬停**节点才展开（最常见的设计）；
//   (c) 只有在**能连线的状态**（比如正在拖一条线、或节点被选中）才显示。
//
// ✅ 这一轮做一个**状态梯度实验**，一次分清三种可能：
//   ① 什么都不做 → ② 悬停节点（不点）→ ③ 点选节点 → ④ 悬停连接口位置 → ⑤ 从口的位置按下拖动
//   每一步都读**同一个**连接口元素（按 `data-handleid` 锚定，不重新查找），
//   记录它的 rect/宽高/伪元素尺寸/可见性。
//
// ⚠️ 附带：BG2 想从 `.react-flow__edge` 读 source/target 失败 ——
//    `data-source` / `data-target` **不存在**，id 也是随机串（`e-5U2jB82fuL`）。
//    ✅ 改从**几何**反推：连线 path 的 `d` 里有两端坐标，
//    拿它去匹配 11 个节点的 source/target 口坐标（口位置在 BG1 已经量准了）。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBG3';
const { browser, page } = await launch();

/** ⭐ 按 `data-handleid` 锚定读一个连接口 —— 包含**伪元素**尺寸。 */
const readHandle = (pg, nodeId, handleId) => pg.evaluate(([nid, hid]) => {
  const n = [...document.querySelectorAll('.react-flow__node')]
    .find((x) => x.getAttribute('data-id') === nid);
  if (!n) return { err: 'no node' };
  const e = [...n.querySelectorAll('[data-handleid]')]
    .find((x) => x.getAttribute('data-handleid') === hid);
  if (!e) return { err: 'no handle' };
  const r = e.getBoundingClientRect();
  const cs = getComputedStyle(e);
  const pe = getComputedStyle(e, '::before');
  const pe2 = getComputedStyle(e, '::after');
  return {
    rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    w: cs.width, h: cs.height, minW: cs.minWidth, minH: cs.minHeight,
    display: cs.display, visibility: cs.visibility, opacity: cs.opacity,
    cursor: cs.cursor, bg: cs.backgroundColor, borderW: cs.borderWidth, radius: cs.borderRadius,
    overflow: cs.overflow,
    before: { content: pe.content, w: pe.width, h: pe.height, bg: pe.backgroundColor, display: pe.display },
    after: { content: pe2.content, w: pe2.width, h: pe2.height, bg: pe2.backgroundColor, display: pe2.display },
    childCount: e.children.length,
    html: e.innerHTML.slice(0, 160),
  };
}, [nodeId, handleId]);

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

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1600);
  await fitView(page); await page.waitForTimeout(1800);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '连接口在五种状态下的尺寸梯度 + 从连线几何反推两端节点' });

  const out = {};
  await page.mouse.move(720, 260); await page.waitForTimeout(800);

  const NODE = 't-UtVx3lZmrV';
  const gradient = {};

  // ═══ 状态梯度：① 基线
  console.log('--- BG3-1 连接口的状态梯度 ---');
  const s1 = await readHandle(page, NODE, 'source');
  console.log(`① 基线（什么都不做）source：rect=${JSON.stringify(s1.rect)} w=${s1.w} h=${s1.h} display=${s1.display} vis=${s1.visibility}`);
  console.log(`   ::before content=${s1.before.content} w=${s1.before.w} h=${s1.before.h} bg=${s1.before.bg}`);
  console.log(`   ::after  content=${s1.after.content} w=${s1.after.w} h=${s1.after.h} bg=${s1.after.bg}`);
  console.log(`   子元素 ${s1.childCount} 个；innerHTML: ${s1.html}`);
  gradient.baseline = s1;

  // ② 悬停节点（不点）
  const pt = await exclusivePoint(page, NODE);
  if (pt.err) { console.log('  没有独占点', pt.err); out.gradient = { err: pt.err }; }
  else {
    await page.mouse.move(pt.x, pt.y); await page.waitForTimeout(1600);
    const s2 = await readHandle(page, NODE, 'source');
    console.log(`② 悬停节点（不点）：rect=${JSON.stringify(s2.rect)} w=${s2.w} h=${s2.h} cursor=${s2.cursor}`);
    gradient.hover = s2;
    out.expandedOnHover = s2.rect[2] > s1.rect[2] || s2.rect[3] > s1.rect[3];

    // ③ 点选
    await page.mouse.click(pt.x, pt.y); await page.waitForTimeout(2400);
    const s3 = await readHandle(page, NODE, 'source');
    console.log(`③ 点选节点：rect=${JSON.stringify(s3.rect)} w=${s3.w} h=${s3.h} cursor=${s3.cursor}`);
    gradient.selected = s3;
    out.expandedOnSelect = s3.rect[2] > s1.rect[2] || s3.rect[3] > s1.rect[3];

    // ④ 悬停到连接口位置
    const hp = { x: s3.rect[0] + s3.rect[2] / 2, y: s3.rect[1] + s3.rect[3] / 2 };
    await page.mouse.move(hp.x, hp.y); await page.waitForTimeout(1600);
    const s4 = await readHandle(page, NODE, 'source');
    const owner = await page.evaluate(([x, y]) => {
      const o = document.elementFromPoint(x, y);
      if (!o) return { err: 'null' };
      const h = o.closest('[data-handleid]');
      return { tag: o.tagName, handleId: h ? h.getAttribute('data-handleid') : null,
        isHandle: !!h, inNode: !!o.closest('.react-flow__node') };
    }, [hp.x, hp.y]);
    console.log(`④ 悬停到口的位置：rect=${JSON.stringify(s4.rect)}；落点归属 ${JSON.stringify(owner)}`);
    gradient.hoverHandle = s4; gradient.owner = owner;
    out.handleReachable = owner.isHandle && owner.handleId === 'source';

    // ⑤ 从口的位置按下，看会不会拉出一条「正在连」的线
    const before = await page.evaluate(() => document.querySelectorAll('.react-flow__edge').length);
    await page.mouse.move(hp.x, hp.y); await page.mouse.down();
    await page.mouse.move(hp.x + 120, hp.y + 60); await page.waitForTimeout(400);
    await page.mouse.move(hp.x + 220, hp.y + 110); await page.waitForTimeout(600);
    const dragging = await page.evaluate(() => ({
      connLines: document.querySelectorAll('.react-flow__connectionline,.react-flow__connection-path').length,
      connHtml: [...document.querySelectorAll('[class*="connection"]')]
        .map((e) => ({ cls: (e.className || '').toString().slice(0, 60),
          w: Math.round(e.getBoundingClientRect().width), h: Math.round(e.getBoundingClientRect().height) })),
      handleRects: [...document.querySelectorAll('[data-handleid]')]
        .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0; })
        .map((e) => ({ id: e.getAttribute('data-handleid'),
          node: e.getAttribute('data-nodeid'), w: Math.round(e.getBoundingClientRect().width) }))
          .slice(0, 6),
    }));
    console.log(`⑤ 按住拖动中：连线类元素 ${dragging.connLines} 个`);
    console.log(`   拖动中有尺寸的连接口：${JSON.stringify(dragging.handleRects)}`);
    await shot(page, 'M-195-连接口-拖拽中.png');
    out.shot = 'M-195-连接口-拖拽中.png';
    gradient.dragging = dragging;
    out.dragRevealsHandles = dragging.handleRects.length > 0;
    await page.mouse.up(); await page.waitForTimeout(2000);
    const after = await page.evaluate(() => document.querySelectorAll('.react-flow__edge').length);
    console.log(`   松手后连线数 ${before} → ${after}`);
    gradient.edgeCount = { before, after };
    out.connected = after > before;
    if (after > before) {
      await page.keyboard.press('Escape'); await page.waitForTimeout(400);
      await page.keyboard.press('Meta+z'); await page.waitForTimeout(2200);
      const back = await page.evaluate(() => document.querySelectorAll('.react-flow__edge').length);
      console.log(`   ⌘Z 撤销后连线数 ${back}`);
      out.undoRestored = back === before;
    }
  }
  out.gradient = gradient;

  // ═══ 2. 从连线几何反推两端是哪两个节点
  console.log('\n--- BG3-2 那条已有连线连的是谁 ---');
  const geo = await page.evaluate(() => {
    const edges = [...document.querySelectorAll('.react-flow__edge')].map((e) => {
      const p = e.querySelector('path');
      return { id: e.getAttribute('data-id'), cls: (e.className || '').toString().slice(0, 60),
        d: (p ? p.getAttribute('d') : '').slice(0, 200),
        attrs: [...e.attributes].map((a) => `${a.name}=${String(a.value).slice(0, 30)}`),
        pathAttrs: p ? [...p.attributes].map((a) => a.name) : [] };
    });
    const nodes = [...document.querySelectorAll('.react-flow__node')].map((n) => {
      const r = n.getBoundingClientRect();
      const hs = [...n.querySelectorAll('[data-handleid]')].map((h) => {
        const q = h.getBoundingClientRect();
        return { id: h.getAttribute('data-handleid'), x: Math.round(q.x + q.width / 2), y: Math.round(q.y + q.height / 2) };
      });
      return { id: n.getAttribute('data-id'), name: ((n.innerText || '').replace(/\s+/g, ' ').trim().split(' ')[0] || '').slice(0, 10),
        left: Math.round(r.x), right: Math.round(r.x + r.width), top: Math.round(r.y), midY: Math.round(r.y + r.height / 2), handles: hs };
    });
    return { edges, nodes };
  });
  for (const e of geo.edges) {
    console.log(`  连线 ${e.id} class="${e.cls}"`);
    console.log(`    属性：${e.attrs.join(' | ')}`);
    console.log(`    path 属性名：${e.pathAttrs.join(', ')}`);
    console.log(`    d（前 120 字）：${e.d.slice(0, 120)}`);
  }
  // 从 d 里抠数字当端点，匹配最近的节点口
  for (const e of geo.edges) {
    const nums = (e.d.match(/-?\d+(\.\d+)?/g) || []).map(Number);
    const pts = [];
    for (let i = 0; i + 1 < nums.length; i += 2) pts.push([nums[i], nums[i + 1]]);
    const cand = [];
    for (const n of geo.nodes) for (const h of n.handles) cand.push({ node: n.id, name: n.name, handle: h.id, x: h.x, y: h.y });
    for (const p of pts.slice(0, 2)) {
      let best = null; let bd = 1e9;
      for (const c of cand) {
        const d2 = Math.hypot(c.x - p[0], c.y - p[1]);
        if (d2 < bd) { bd = d2; best = c; }
      }
      if (best) { console.log(`    端点 (${p[0]},${p[1]}) 最近的口：${best.node} ${best.name}/${best.handle}，距离 ${Math.round(bd)}`); }
    }
  }
  out.edgeGeo = geo;
  // 结论字段
  out.endpoints = geo.edges.map((e) => {
    const nums = (e.d.match(/-?\d+(\.\d+)?/g) || []).map(Number);
    const pts = []; for (let i = 0; i + 1 < nums.length; i += 2) pts.push([nums[i], nums[i + 1]]);
    const cand = []; for (const n of geo.nodes) for (const h of n.handles) cand.push({ node: n.id, name: n.name, handle: h.id, x: h.x, y: h.y });
    return pts.slice(0, 2).map((p) => {
      let best = null; let bd = 1e9;
      for (const c of cand) { const d2 = Math.hypot(c.x - p[0], c.y - p[1]); if (d2 < bd) { bd = d2; best = c; } }
      return best ? { ...best, dist: Math.round(bd) } : null; }).filter(Boolean);
  });

  await logStep(B, {
    id: 'BG3-handle-gradient-and-edge-geometry',
    title: '连接口的状态梯度（悬停/选中/拖动）+ 从连线几何反推两端节点',
    target: 'BG1/BG2 读到「0×0 但 display:block、visibility:visible、class 含 connectable」这个组合，'
      + '分不清是伪元素画的、要悬停才展开、还是只有拖线时才显示。'
      + '这轮做五级状态梯度，全程锚定同一个 data-handleid 元素。'
      + '附带修正：.react-flow__edge 上**没有 data-source/data-target**，id 也是随机串，'
      + '所以「这条连线连的是谁」只能从 path 的 d 坐标反推。',
    evidence: out,
    visible_text: JSON.stringify({
      baseline: { rect: out.gradient?.baseline?.rect, w: out.gradient?.baseline?.w, h: out.gradient?.baseline?.h,
        before: out.gradient?.baseline?.before, after: out.gradient?.baseline?.after, children: out.gradient?.baseline?.childCount },
      hover: { rect: out.gradient?.hover?.rect, w: out.gradient?.hover?.w, h: out.gradient?.hover?.h },
      selected: { rect: out.gradient?.selected?.rect, w: out.gradient?.selected?.w, h: out.gradient?.selected?.h },
      expandedOnHover: out.expandedOnHover, expandedOnSelect: out.expandedOnSelect,
      handleReachable: out.handleReachable, dragRevealsHandles: out.dragRevealsHandles,
      connected: out.connected, undoRestored: out.undoRestored, endpoints: out.endpoints }).slice(0, 3000),
    shot: out.shot,
  });
  console.log('\nBG3 完成');
} finally {
  await browser.close();
}
