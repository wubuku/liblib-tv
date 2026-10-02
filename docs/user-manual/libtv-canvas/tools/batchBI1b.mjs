// Batch BI1b — ⭐ 推翻 BH2 的读数：端口图标到底默认可不可见。
//
// 起因：BI1 实测 `getComputedStyle(icon).opacity === '1'`、rect `11×11`，
// 与 BH2 记的「默认 `opacity: 0`、`20×20`、要选中才显形」**直接矛盾**。
// 拍下的 M-200（未选中）也肉眼可见四个节点的 ⊕ 全部在。
//
// ⭐ 核心怀疑：BH2 读的是 **`innerHTML` 字符串里的 inline `style` 属性**，
//    而 `innerHTML` 给出的是**属性**，不是**生效值** —— React 挂载后
//    应用若改用 class / 其它手段控制显隐，属性就会与实际渲染脱节。
//    所以这轮三种读法**并排**取，同一个元素、同一个时刻：
//      ① 属性：e.getAttribute('style')
//      ② 计算值：getComputedStyle(e)
//      ③ 实际渲染：document.elementFromPoint(该图标中心) 命中的是谁
//    再加 ④ 像素证据：把图标区域裁出来存成图。
//
// ⭐ 判据纪律：全程锚定同一个元素，不重新查找（BG3 的教训）。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBI1b';
const { browser, page } = await launch();

/** 锚定一个节点的 source 口，并把整棵子树的**三种读法**一次性取全。 */
const probe = (nid) => page.evaluate((id) => {
  const n = [...document.querySelectorAll('.react-flow__node')]
    .find((x) => x.getAttribute('data-id') === id);
  if (!n) return { err: 'no node' };
  const h = n.querySelector('[data-handleid="source"]');
  if (!h) return { err: 'no source' };
  window.__h = { node: n, handle: h };

  const layers = [];
  const walk = (e, depth) => {
    const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    layers.push({
      depth, tag: e.tagName,
      cls: (typeof e.className === 'string' ? e.className : (e.className?.baseVal ?? '')).slice(0, 48),
      styleAttr: e.getAttribute('style') || null,          // ① 属性
      computedOpacity: cs.opacity,                          // ② 计算值
      computedVis: cs.visibility, computedDisplay: cs.display,
      computedTransform: cs.transform,
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    });
    for (const c of e.children) walk(c, depth + 1);
  };
  walk(h, 0);

  // ③ 实际渲染：图标中心那个点上命中的是谁
  const svg = h.querySelector('svg');
  const hit = (() => {
    if (!svg) return null;
    const r = svg.getBoundingClientRect();
    const cx = Math.round(r.x + r.width / 2), cy = Math.round(r.y + r.height / 2);
    const o = document.elementFromPoint(cx, cy);
    return { at: [cx, cy], tag: o ? o.tagName : null, inHandle: !!(o && h.contains(o)),
      hitOpacity: o ? getComputedStyle(o).opacity : null };
  })();

  return { nodeId: id, nodeName: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 14),
    selected: n.classList.contains('selected'),
    outerHTML_head: h.outerHTML.slice(0, 700), layers, hit,
    svgOuter: svg ? svg.outerHTML.slice(0, 400) : null };
}, nid);

const sel = () => page.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1600);
  await fitView(page); await page.waitForTimeout(1800);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '三种读法并排：inline 属性 vs 计算值 vs 实际渲染' });

  const out = { unselected: [], selected: null };
  const ID = 'i-9nlG6HdjK2';

  // ═══ A. 未选中态：全 11 个节点逐个取，先确认「有没有一个默认不显示的」
  console.log('══════ A. 未选中态 · 11 个节点逐个读 source 口 ══════');
  await page.mouse.move(120, 120); await page.waitForTimeout(1500);
  const selBefore = await sel();
  const ids = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node')]
    .map((n) => n.getAttribute('data-id')).filter(Boolean));
  console.log(`  视口内节点 ${ids.length} 个；当前选中数=${selBefore}`);
  for (const id of ids) {
    const p = await probe(id);
    if (p.err) { console.log(`  ${id}: ${p.err}`); continue; }
    const svg = p.layers.find((l) => l.tag.toLowerCase() === 'svg');
    const circle = p.layers.find((l) => l.depth === 2) || p.layers[p.layers.length - 1];
    out.unselected.push({ id, name: p.nodeName, selected: p.selected,
      svgRect: svg?.rect, svgAttrOpacity: svg?.styleAttr, svgComputed: svg?.computedOpacity,
      hitTag: p.hit?.tag, hitOpacity: p.hit?.hitOpacity });
    console.log(`  ${p.nodeName.padEnd(14)} 选中=${String(p.selected).padEnd(5)} ` +
      `SVG rect=${JSON.stringify(svg?.rect)} 属性style=${JSON.stringify(svg?.styleAttr)} ` +
      `计算opacity=${svg?.computedOpacity} 该点命中=${p.hit?.tag}`);
  }

  // ═══ B. 打印三层结构的完整读数（属性 vs 计算值）
  console.log('\n══════ B. 图片节点 source 口的三层结构 · 属性 vs 计算值 ══════');
  const p1 = await probe(ID);
  console.log('  outerHTML 头部：', p1.outerHTML_head);
  p1.layers.forEach((l) => {
    console.log(`  L${l.depth} <${l.tag}> ${l.cls}`);
    console.log(`      rect=${JSON.stringify(l.rect)}`);
    console.log(`      ① 属性style=${JSON.stringify(l.styleAttr)}`);
    console.log(`      ② 计算 opacity=${l.computedOpacity} vis=${l.computedVis} display=${l.computedDisplay}`);
    console.log(`      ② 计算 transform=${l.computedTransform}`);
  });
  console.log('  ③ 图标中心实际命中：', JSON.stringify(p1.hit));
  console.log('  SVG outerHTML：', p1.svgOuter);
  out.layers = p1.layers;
  out.hitUnselected = p1.hit;
  out.svgOuter = p1.svgOuter;
  out.outerHTML_head = p1.outerHTML_head;

  // ═══ C. 像素证据：裁出未选中时的口所在区域
  const r = p1.layers.find((l) => l.depth === 2)?.rect || p1.layers.at(-1).rect;
  if (r && r[2] > 0) {
    await page.screenshot({ path: 'screenshots/M-200-连接口-悬停未选中.png',
      clip: { x: Math.max(0, r[0] - 70), y: Math.max(0, r[1] - 40), width: 220, height: 120 } });
    console.log(`\n  📷 已裁剪未选中态的口区域 [${r}] ± 周边 → M-200-连接口-悬停未选中.png`);
    out.shot = 'M-200-连接口-悬停未选中.png';
  }

  // ═══ D. 选中后同元素再读一次，看有没有变
  console.log('\n══════ D. 点选后同元素再读 ══════');
  const body = await page.evaluate(() => { const n = window.__h.node; const b = n.getBoundingClientRect();
    return [Math.round(b.x + b.width / 2), Math.round(b.y + b.height / 2)]; });
  await page.mouse.click(body[0], body[1]); await page.waitForTimeout(2400);
  console.log('  选中数 =', await sel());
  const p2 = await probe(ID);
  const svg2 = p2.layers.find((l) => l.tag.toLowerCase() === 'svg');
  const svg1 = p1.layers.find((l) => l.tag.toLowerCase() === 'svg');
  console.log(`  未选中：SVG rect=${JSON.stringify(svg1?.rect)} opacity=${svg1?.computedOpacity} 命中=${JSON.stringify(p1.hit?.tag)}`);
  console.log(`  已选中：SVG rect=${JSON.stringify(svg2?.rect)} opacity=${svg2?.computedOpacity} 命中=${JSON.stringify(p2.hit?.tag)}`);
  console.log(`  ⭐ 前后 SVG rect 相同？ ${JSON.stringify(svg1?.rect) === JSON.stringify(svg2?.rect)}`);
  out.selected = { selected: p2.selected, svgRect: svg2?.rect, opacity: svg2?.computedOpacity, hit: p2.hit };

  if (r && r[2] > 0) {
    await page.screenshot({ path: 'screenshots/M-201-连接口-选中态同元素复验.png',
      clip: { x: Math.max(0, r[0] - 70), y: Math.max(0, r[1] - 40), width: 220, height: 120 } });
    console.log('  📷 已裁剪选中态同一区域 → M-201-连接口-选中态同元素复验.png');
    out.shot2 = 'M-201-连接口-选中态同元素复验.png';
  }

  // ═══ E. 结论判定
  const visUnselected = out.unselected.filter((u) => u.svgComputed && u.svgComputed !== '0');
  console.log('\n══════ E. 结论 ══════');
  console.log(`  未选中时 SVG 计算 opacity ≠ 0 的节点：${visUnselected.length}/${out.unselected.length}`);
  const attrVsComputed = p1.layers.filter((l) => l.styleAttr && /opacity/.test(l.styleAttr))
    .map((l) => ({ depth: l.depth, attr: l.styleAttr.match(/opacity:\s*[^;"]*/)?.[0], computed: l.computedOpacity }));
  console.log('  「属性里写了 opacity」的层，与计算值对照：', JSON.stringify(attrVsComputed));
  out.attrVsComputed = attrVsComputed;
  out.visibleUnselected = visUnselected.length;

  await logStep(B, {
    id: 'BI1b-handle-opacity-attr-vs-computed',
    title: '推翻 BH2：端口图标默认就是可见的（inline 属性 ≠ 生效值）',
    target: 'BI1 实测 getComputedStyle(icon).opacity=1、rect 11×11，与 BH2 记的「默认 opacity:0、20×20、'
      + '选中才显形」直接矛盾。怀疑 BH2 读的是 innerHTML 字符串里的 inline style **属性**。'
      + '本轮把属性 / 计算值 / 实际命中元素三种读法并排取，同元素同时刻。',
    evidence: out,
    visible_text: JSON.stringify({ unselected: out.unselected, layers: out.layers?.length,
      attrVsComputed: out.attrVsComputed, visibleUnselected: out.visibleUnselected }).slice(0, 3000),
    shot: out.shot,
  });
  console.log('\nBI1b 完成');
} finally {
  await browser.close();
}
