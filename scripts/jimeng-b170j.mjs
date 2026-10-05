// 批次 170 j 轮：右键菜单尺寸是**内容累加**还是**定尺**？
//
// 已有三组实测：(空白)240×172、(选中节点)200×292、(连接中)200×316。
// 叶子节点全高 22px，但 4 行→172、7 行→292 差 3 行 120px（40/行）⇒ 单纯「行高累加」对不上，
// 说明中间有分组间距/分隔线。叶子遍历看不到它们 ⇒ 本轮 dump **盒子树**（非叶子）。
import { openCanvas, readers } from './jimeng-b135-lib.mjs';

const { b, p } = await openCanvas();
const R = readers(p);

const tree = () => p.evaluate(() => {
  const e = document.querySelector('[data-testid="canvas-context-menu"]');
  if (!e) return null;
  const r = e.getBoundingClientRect();
  const node = (el, depth) => {
    const b = el.getBoundingClientRect();
    const cs = getComputedStyle(el);
    return {
      d: depth,
      tag: el.tagName,
      testid: el.getAttribute('data-testid'),
      role: el.getAttribute('role'),
      aria: el.getAttribute('aria-label'),
      disabled: el.getAttribute('aria-disabled') || el.getAttribute('data-disabled'),
      rect: [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)],
      pe: cs.pointerEvents,
      pad: cs.padding, gap: cs.gap, border: cs.borderTopWidth,
      bgi: cs.backgroundImage === 'none' ? '' : 'divider',
      own: el.children.length ? '' : (el.innerText || '').trim().replace(/\n/g, '⏎').slice(0, 40),
      kids: Array.from(el.children).map((c) => node(c, depth + 1)),
    };
  };
  return { size: [Math.round(r.width), Math.round(r.height)], root: node(e, 0) };
});

const print = (n, ind = 0) => {
  const p2 = '  '.repeat(ind);
  console.log(`${p2}${n.tag}${n.testid ? '[' + n.testid + ']' : ''}${n.role ? ' role=' + n.role : ''}${n.disabled ? ' disabled=' + n.disabled : ''} ${n.rect.join('×')} pad=${n.pad} gap=${n.gap} border=${n.border}${n.bgi ? ' ' + n.bgi : ''}${n.own ? ' · "' + n.own + '"' : ''}`);
  for (const c of n.kids) print(c, ind + 1);
};

const blank = () => p.evaluate(() => {
  for (let y = 40; y < innerHeight - 20; y += 20)
    for (let x = 40; x < innerWidth - 20; x += 20) {
      const e = document.elementFromPoint(x, y);
      if (e && e.closest('.react-flow__pane') && !e.closest('.react-flow__node')) return [x, y];
    }
  return null;
});

for (const [tag, mode] of [['空白画布', 'blank'], ['选中节点', 'node']]) {
  await p.keyboard.press('Escape'); await p.waitForTimeout(300);
  const pt = mode === 'blank' ? await blank() : await p.evaluate(() => {
    const n = document.querySelector('.react-flow__node [data-testid="audio-node-empty"]').closest('.react-flow__node');
    const r = n.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
  });
  await p.mouse.click(pt[0], pt[1], { button: 'right' });
  await p.waitForTimeout(900);
  const t = await tree();
  console.log(`\n════ ${tag}  尺寸=${t ? t.size.join('×') : 'null'} ════`);
  if (t) print(t.root);
}

await p.keyboard.press('Escape'); await p.waitForTimeout(300);
const bp = await blank();
if (bp) await p.mouse.click(bp[0], bp[1]);
await p.waitForTimeout(400);
await p.keyboard.press('Escape'); await p.waitForTimeout(300);
console.log('\n收尾:', JSON.stringify({ sel: await R.selCount(), credits: await R.credits() }),
  '残留菜单=', await p.evaluate(() => document.querySelectorAll('[data-testid="canvas-context-menu"]').length));
await b.close();
