// 批次 170 n 轮：宽度的**定尺来源**。
//
// 批次 170 的静态侧结论：源站 CSS 里 `.octo-context-menu*` 只有 3 条规则，**没有任何宽度声明**
//   ⇒ 240/200 这两档不可能来自样式表，只能来自「元素自身的 class（Tailwind 任意值）」或「内联 style」。
// 本轮把两个变体的 className / style 属性逐字取回。
import { openCanvas, readers } from './jimeng-b135-lib.mjs';
import fs from 'node:fs';

const { b, p } = await openCanvas();
const R = readers(p);

const attrs = () => p.evaluate(() => {
  const e = document.querySelector('[data-testid="canvas-context-menu"]');
  if (!e) return null;
  const g = (el) => ({
    className: el.getAttribute('class'),
    styleAttr: el.getAttribute('style'),
    w: Math.round(el.getBoundingClientRect().width),
  });
  const list = e.firstElementChild;
  const item = list.querySelector('[role=menuitem]');
  const sub = list.querySelector('div[style], div > div');
  return {
    root: g(e),
    list: g(list),
    item: item ? g(item) : null,
    rootAttrs: Array.from(e.attributes).map((a) => `${a.name}="${a.value}"`),
  };
});

const blank = () => p.evaluate(() => {
  for (let y = 30; y < innerHeight - 30; y += 10)
    for (let x = 30; x < innerWidth - 30; x += 10) {
      const e = document.elementFromPoint(x, y);
      if (e && e.closest('.react-flow__pane') && !e.closest('.react-flow__node')) return [x, y];
    }
  return null;
});
const nodePt = () => p.evaluate(() => {
  const n = document.querySelector('.react-flow__node [data-testid="audio-node-empty"]').closest('.react-flow__node');
  const r = n.getBoundingClientRect();
  return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
});

const out = {};
for (const [tag, get] of [['空白变体', blank], ['节点变体', nodePt]]) {
  await p.keyboard.press('Escape'); await p.waitForTimeout(300);
  const pt = await get();
  await p.mouse.click(pt[0], pt[1], { button: 'right' });
  await p.waitForTimeout(900);
  const a = await attrs();
  out[tag] = { at: pt, ...a };
  console.log(`\n════ ${tag}  根宽=${a.root.w} ════`);
  console.log('  根 class:', a.root.className);
  console.log('  根 style:', JSON.stringify(a.root.styleAttr));
  console.log('  根全部属性:', JSON.stringify(a.rootAttrs));
  console.log('  列表 class:', a.list.className);
  console.log('  列表 style:', JSON.stringify(a.list.styleAttr));
  console.log('  条目 class:', a.item && a.item.className);
}

// hover 出子菜单，量子菜单宽度
await p.keyboard.press('Escape'); await p.waitForTimeout(300);
const pt = await blank();
await p.mouse.click(pt[0], pt[1], { button: 'right' });
await p.waitForTimeout(800);
const trig = await p.evaluate(() => {
  const e = document.querySelector('[data-testid="canvas-context-menu"]');
  const t = e.firstElementChild.firstElementChild.getBoundingClientRect();
  return [Math.round(t.x + t.width / 2), Math.round(t.y + t.height / 2)];
});
await p.mouse.move(trig[0], trig[1]);
await p.waitForTimeout(900);
const sub = await p.evaluate(() => {
  const e = document.querySelector('[data-testid="canvas-context-menu"]');
  for (const c of e.querySelectorAll('div')) {
    const cs = getComputedStyle(c);
    if (cs.position === 'absolute' && cs.visibility === 'visible' && c.getBoundingClientRect().height > 50) {
      const r = c.getBoundingClientRect();
      return {
        w: Math.round(r.width), h: Math.round(r.height),
        className: c.getAttribute('class'), styleAttr: c.getAttribute('style'),
        pad: cs.padding, gap: cs.gap,
        labels: Array.from(c.querySelectorAll('[role=menuitem]')).map((x) => (x.innerText || '').trim().split('\n')[0].slice(0, 12)),
      };
    }
  }
  return null;
});
out['子菜单'] = sub;
console.log('\n════ hover 后的子菜单 ════');
console.log('  尺寸:', sub && [sub.w, sub.h], ' pad=', sub && sub.pad, ' gap=', sub && sub.gap);
console.log('  class:', sub && sub.className);
console.log('  style:', sub && JSON.stringify(sub.styleAttr));
console.log('  条目:', sub && JSON.stringify(sub.labels));

fs.writeFileSync('scripts/_tmp-b170n-attrs.json', JSON.stringify(out, null, 1));
await p.keyboard.press('Escape'); await p.waitForTimeout(400);
console.log('\n收尾:', JSON.stringify({ sel: await R.selCount(), credits: await R.credits() }),
  '残留=', await p.evaluate(() => document.querySelectorAll('[data-testid="canvas-context-menu"]').length));
await b.close();
