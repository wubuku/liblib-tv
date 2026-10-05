// 批次 170 m 轮：把「空白变体 240×172」那对不上的 40 px 找出来。
//
// 已知（l 轮，结构级）：
//   menu 240×172  pad=4px  gap=normal
//   └ none 232×164  gap=4px        ← 唯一子列表
//      ├ none   232×36  disp=block   ← 「新建节点」触发器，内含一个 364 高的**子菜单**
//      ├ separator 232×4
//      ├ menuitem 232×36
//      ├ menuitem 232×36
//      └ menuitem 232×36
//   高度按 36/4/4/8 复算 = 8+36+4+36+36+36+3×4 = 168，实测 172 ⇒ **差 4**
//   （l 轮脚本多算了一个 gap，修正后仍差 4）
//
// 本轮用**y 偏移**逐个定位，并读 margin（gap 只算 flex 容器的间隔，margin 不算）。
import { openCanvas, readers } from './jimeng-b135-lib.mjs';

const { b, p } = await openCanvas();
const R = readers(p);

const dump = () => p.evaluate(() => {
  const e = document.querySelector('[data-testid="canvas-context-menu"]');
  if (!e) return null;
  const rr = e.getBoundingClientRect();
  const list = e.firstElementChild;
  const lr = list.getBoundingClientRect();
  const kids = Array.from(list.children).map((c) => {
    const b = c.getBoundingClientRect();
    const cs = getComputedStyle(c);
    return {
      role: c.getAttribute('role'),
      disp: cs.display,
      y: Math.round(b.y - lr.y), h: Math.round(b.height), w: Math.round(b.width),
      mt: cs.marginTop, mb: cs.marginBottom,
      own: c.children.length ? null : (c.innerText || '').trim().split('\n')[0].slice(0, 16),
      sub: Array.from(c.children).map((g) => {
        const gb = g.getBoundingClientRect(); const gs = getComputedStyle(g);
        return { role: g.getAttribute('role'), disp: gs.display, y: Math.round(gb.y - lr.y), h: Math.round(gb.height),
                 w: Math.round(gb.width), pos: gs.position, z: gs.zIndex, vis: gs.visibility, op: gs.opacity,
                 own: g.children.length ? null : (g.innerText || '').trim().split('\n')[0].slice(0, 16) };
      }),
    };
  });
  const lcs = getComputedStyle(list);
  return {
    menu: [Math.round(rr.width), Math.round(rr.height)], menuOverflow: getComputedStyle(e).overflow,
    list: [Math.round(lr.width), Math.round(lr.height)], listGap: lcs.gap, listDisp: lcs.display,
    listPos: lcs.position, listPad: lcs.padding, listOverflow: lcs.overflow,
    kids,
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

await p.keyboard.press('Escape'); await p.waitForTimeout(300);
const pt = await blank();
await p.mouse.click(pt[0], pt[1], { button: 'right' });
await p.waitForTimeout(900);
const d = await dump();
console.log('空白变体 @', pt, JSON.stringify({ menu: d.menu, overflow: d.menuOverflow, list: d.list,
  gap: d.listGap, disp: d.listDisp, pos: d.listPos, pad: d.listPad, ovf: d.listOverflow }, null, 1));
console.log('\n子元素（y 相对列表顶）:');
for (const k of d.kids) {
  console.log(`  ${String(k.role).padEnd(10)} y=${String(k.y).padStart(3)} h=${String(k.h).padStart(3)} w=${String(k.w).padStart(3)} disp=${k.disp} mt=${k.mt} mb=${k.mb}${k.own ? ' · ' + k.own : ''}`);
  for (const s of k.sub) {
    console.log(`      └ ${String(s.role).padEnd(10)} y=${String(s.y).padStart(3)} h=${String(s.h).padStart(3)} w=${String(s.w).padStart(3)} pos=${s.pos} z=${s.z} vis=${s.vis} op=${s.op} disp=${s.disp}${s.own ? ' · ' + s.own : ''}`);
  }
}
const sum = d.kids.reduce((a, k) => a + k.h, 0);
const gaps = (d.kids.length - 1) * 4;
console.log(`\n复算: pad8 + Σ子高${sum} + gap(${d.kids.length}−1)×4=${gaps} = ${8 + sum + gaps}   实测菜单高=${d.menu[1]}  列表高=${d.list[1]}`);

// 顺带：hover「新建节点」看子菜单是否浮出
const trig = await p.evaluate(() => {
  const e = document.querySelector('[data-testid="canvas-context-menu"]');
  const t = e.firstElementChild.firstElementChild;
  const r = t.getBoundingClientRect();
  return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
});
await p.mouse.move(trig[0], trig[1]);
await p.waitForTimeout(900);
const d2 = await dump();
console.log('\nhover 触发器后:', JSON.stringify({ menu: d2.menu, list: d2.list, kids: d2.kids.map((k) => [k.role, k.y, k.h, k.own]) }, null, 1));
if (d2.kids[0].sub && d2.kids[0].sub.length) {
  console.log('子菜单:', JSON.stringify(d2.kids[0].sub, null, 1));
}

await p.keyboard.press('Escape'); await p.waitForTimeout(400);
console.log('\n收尾:', JSON.stringify({ sel: await R.selCount(), credits: await R.credits() }),
  '残留=', await p.evaluate(() => document.querySelectorAll('[data-testid="canvas-context-menu"]').length));
await b.close();
