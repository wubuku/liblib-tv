// 批次 170 f 轮：那个吞点击的 `canvas-context-menu` 到底是什么。
//
// 现象：静止态下画布上没有任何视口类面板，却有一个
//   `div[data-testid=canvas-context-menu]` 以 `pointer-events:auto; position:fixed`
//   盖在 (256,285,182,182) 的音频节点上，elementFromPoint 命中它而不是节点
//   ⇒ 节点点不动、也不选中。
// 要问：① 它的几何/可见性 ② 是上一轮遗留的悬停态还是常驻 ③ 打开它的手势
import { openCanvas, readers } from './jimeng-b135-lib.mjs';

const { b, p } = await openCanvas();
const R = readers(p);

const inspect = async (tag) => {
  const d = await p.evaluate(() => {
    const out = [];
    for (const e of document.querySelectorAll('[data-testid="canvas-context-menu"]')) {
      const cs = getComputedStyle(e);
      const r = e.getBoundingClientRect();
      out.push({
        rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        display: cs.display, visibility: cs.visibility, opacity: cs.opacity,
        pe: cs.pointerEvents, pos: cs.position, z: cs.zIndex,
        childCount: e.children.length,
        text: (e.innerText || '').trim().slice(0, 60).replace(/\n/g, '⏎'),
        parentTestid: e.parentElement && e.parentElement.getAttribute('data-testid'),
        parentCls: (e.parentElement ? e.parentElement.getAttribute('class') || '' : '').split(/\s+/).slice(0, 4).join(' '),
        dataState: e.getAttribute('data-state'),
        cls: (e.getAttribute('class') || '').split(/\s+/).join(' '),
      });
    }
    return out;
  });
  console.log(`\n[${tag}] count=${d.length}`);
  for (const x of d) console.log('  ', JSON.stringify(x, null, 1).replace(/\n/g, '\n   '));
  return d;
};

await inspect('静止态');

// 移动鼠标到空白处（悬停态应消失）
await p.mouse.move(900, 600);
await p.waitForTimeout(700);
const afterMove = await inspect('鼠标移到空白后');

// 按 Esc
await p.keyboard.press('Escape');
await p.waitForTimeout(700);
const afterEsc = await inspect('按 Esc 后');

// 再点节点
const sel1 = await R.selCount();
console.log(`\nselected before click = ${sel1}`);

console.log(JSON.stringify({ status: await R.status(), credits: await R.credits() }));
await b.close();
