// 批次 170 d 轮：节点类型分布 + 点开一个音频节点，看 `.max-w-canvas-audio-*` 是否挂载。
//
// ⚠️ 为什么不调 settle()：settle 会连按 Esc 关掉一切浮层（jimeng-b135-lib 里的批注）。
//    本轮要的就是「打开后的读数」⇒ 只 waitForTimeout，读完自己按 Esc 收。
// ⛔ 不点任何生成/扣费按钮；只点节点本体。
import { openCanvas, readers } from './jimeng-b135-lib.mjs';
import { VIEWPORT_CLASSES } from './jimeng-b170a.mjs';

const { b, p } = await openCanvas();
const R = readers(p);

const types = await p.evaluate(() => {
  const c = {};
  for (const n of document.querySelectorAll('.react-flow__node')) {
    const tids = Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid'));
    const kind = (tids.find((x) => /-node-/.test(x) && !/-empty$|-status-icon$|-selected-tag$|-title$/.test(x)) || '?').replace(/-node-.*/, '');
    c[kind] = (c[kind] || 0) + 1;
  }
  return c;
});
console.log('node kinds:', JSON.stringify(types));

// 点第一个音频节点
// 🔴 a/d 轮连续两次的错：先取 rect 再 scrollIntoView ⇒ 坐标是滚动前的，点空了（0 selected）。
//    顺序必须是「先滚动 → 再量 rect → 再点」。
const target = await p.evaluate(() => {
  const n = Array.from(document.querySelectorAll('.react-flow__node'))
    .find((x) => x.querySelector('[data-testid="audio-node-empty"]'));
  if (!n) return null;
  n.scrollIntoView({ block: 'center', inline: 'center' });
  const r0 = n.getBoundingClientRect();
  return { id: n.getAttribute('data-id'), pre: [Math.round(r0.x), Math.round(r0.y)] };
});
await p.waitForTimeout(600);
const pt = await p.evaluate((id) => {
  const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
  if (!n) return null;
  const r = n.getBoundingClientRect();
  return { x: r.x + r.width / 2, y: r.y + 24, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
}, target.id);
if (!pt || !target) { console.log('没有音频节点', target); await b.close(); process.exit(0); }
console.log('click audio node:', target.id, JSON.stringify(pt));
await p.mouse.click(pt.x, pt.y);
await p.waitForTimeout(1800);

const after = await p.evaluate((list) => {
  const res = {};
  for (const [cls, decl] of list) {
    const els = Array.from(document.querySelectorAll('.' + cls));
    const live = els.filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 || r.height > 0; });
    if (!live.length) { res[cls] = { mounted: 0, inDom: els.length, decl }; continue; }
    res[cls] = {
      decl, mounted: live.length,
      d: live.slice(0, 2).map((e) => {
        const cs = getComputedStyle(e); const r = e.getBoundingClientRect();
        return {
          testid: e.getAttribute('data-testid'), rect: [Math.round(r.width), Math.round(r.height)],
          maxW: cs.maxWidth, maxH: cs.maxHeight,
          kids: Array.from(e.children).slice(0, 5).map((c) => {
            const cr = c.getBoundingClientRect(); const cc = getComputedStyle(c);
            return { tag: c.tagName, testid: c.getAttribute('data-testid'),
              cls: (c.getAttribute('class') || '').split(/\s+/).filter((x) => /^(max-w|max-h|w|h)-canvas-/.test(x)).join(' '),
              rect: [Math.round(cr.width), Math.round(cr.height)], w: cc.width, h: cc.height, maxW: cc.maxWidth };
          }),
        };
      }),
    };
  }
  return res;
}, VIEWPORT_CLASSES);

console.log('\n--- after clicking audio node ---');
console.log(JSON.stringify({ status: await R.status(), sel: await R.selCount(), credits: await R.credits() }));
for (const [k, v] of Object.entries(after)) {
  if (v.mounted) { console.log(`\n★ ${k}\n   ${v.decl}\n   ${JSON.stringify(v.d, null, 1)}`); }
}
const anyMounted = Object.values(after).filter((v) => v.mounted).length;
console.log(`\nmounted viewport classes: ${anyMounted} / ${VIEWPORT_CLASSES.length}`);
const allMounted = Object.entries(after).filter(([, v]) => v.inDom).map(([k, v]) => `${k}(inDom=${v.inDom},mounted=${v.mounted})`);
console.log('in-DOM (incl. unrendered):', allMounted.join(' | ') || '(none)');
await b.close();
