// 批次 170 i 轮：右键菜单**变体普查** —— 宽/高是不是常量？
//
// h 轮两个锚点量到两个不同尺寸：240×172（空白处右键）与 200×292（f/g 轮的「复制/粘贴/…」菜单）
// ⇒ **宽也不是常量**。本轮按「右键上下文」逐个变体量，把 (宽,高,条目,灰条原因) 对齐。
// ⛔ 不点菜单里的任何条目（会复制/删除/下载）。
import { openCanvas, readers } from './jimeng-b135-lib.mjs';

const { b, p } = await openCanvas();
const R = readers(p);

const readMenu = () => p.evaluate(() => {
  const e = document.querySelector('[data-testid="canvas-context-menu"]');
  if (!e) return null;
  const r = e.getBoundingClientRect();
  // 逐条目：文本 / 是否禁用 / 禁用原因
  const rows = [];
  const walk = (node, depth) => {
    for (const c of node.children) {
      if (c.children.length) { walk(c, depth + 1); continue; }
      const t = (c.innerText || '').trim();
      if (!t) continue;
      const cs = getComputedStyle(c);
      const cr = c.getBoundingClientRect();
      rows.push({
        t: t.split('\n').join(' ⏎ ').slice(0, 80),
        w: Math.round(cr.width), h: Math.round(cr.height),
        y: Math.round(cr.y),
        cursor: cs.cursor, opacity: cs.opacity,
        color: cs.color,
        role: c.getAttribute('role'), aria: c.getAttribute('aria-label'),
        testid: c.getAttribute('data-testid'),
      });
    }
  };
  walk(e, 0);
  return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], rows };
});

const blank = () => p.evaluate(() => {
  const W = innerWidth, H = innerHeight;
  for (let y = 40; y < H - 20; y += 20)
    for (let x = 40; x < W - 20; x += 20) {
      const e = document.elementFromPoint(x, y);
      if (e && e.closest('.react-flow__pane') && !e.closest('.react-flow__node')) return [x, y];
    }
  return null;
});
const nodeAt = (tid) => p.evaluate((t) => {
  const e = document.querySelector(`[data-testid="${t}"]`);
  if (!e) return null;
  const n = e.closest('.react-flow__node');
  if (!n) return null;
  const r = n.getBoundingClientRect();
  return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2), n.getAttribute('data-id')];
}, tid);

const CONTEXTS = [
  ['空白画布', null],
  ['音频节点', 'audio-node-empty'],
  ['图片节点', null],   // 占位，下面单独处理
  ['文本节点', 'flow-node-title'],
  ['视频节点', 'flow-node-title'],
];

const variants = [];
for (const [tag, tid] of CONTEXTS) {
  await p.keyboard.press('Escape');
  await p.waitForTimeout(300);
  let pt;
  if (tid === null && tag === '空白画布') pt = await blank();
  else if (tid) pt = await nodeAt(tid);
  else pt = null;
  if (!pt) { console.log(`\n### ${tag}: 没找到目标，跳过`); continue; }
  await p.mouse.move(pt[0], pt[1]);
  await p.waitForTimeout(150);
  await p.mouse.click(pt[0], pt[1], { button: 'right' });
  await p.waitForTimeout(900);
  const m = await readMenu();
  if (!m) { console.log(`\n### ${tag} @${pt.slice(0,2)}: 菜单没开`); continue; }
  const v = { tag, at: pt.slice(0, 2), node: pt[2] || null, size: [m.rect[2], m.rect[3]], rows: m.rows };
  variants.push(v);
  console.log(`\n### ${tag} @(${pt[0]},${pt[1]})  尺寸=${v.size[0]}×${v.size[1]}`);
  for (const r of m.rows) {
    const dis = /not-allowed|default/.test(r.cursor) || Number(r.opacity) < 0.9;
    console.log(`   ${dis ? '[灰]' : '    '} ${String(r.w).padStart(4)}×${String(r.h).padStart(3)}  ${r.t}`);
  }
}

await p.keyboard.press('Escape');
await p.waitForTimeout(400);
// 复原：点空白取消选中
const bp = await blank();
if (bp) { await p.mouse.click(bp[0], bp[1]); }
await p.waitForTimeout(500);
await p.keyboard.press('Escape');
await p.waitForTimeout(300);
console.log('\n收尾:', JSON.stringify({ status: await R.status(), sel: await R.selCount(), credits: await R.credits() }),
  '残留菜单=', await p.evaluate(() => document.querySelectorAll('[data-testid="canvas-context-menu"]').length));
await b.close();
