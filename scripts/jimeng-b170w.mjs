// 批次 170 w 轮：验「子菜单三选一」规则的最后一支 —— **翻到左侧**。
//
// 把前面 13 个数据点代进这一条：
//   ① 右飞：菜单右边界 + 212 ≤ 视口宽          ⇒ 子菜单在菜单右侧
//   ② 左飞：右边界放不下，但 菜单左边界 − 212 ≥ 0 ⇒ 子菜单翻到菜单左侧
//   ③ 内联：两侧都放不下                        ⇒ 子菜单变流内，菜单 172 → 584
//
// 逐点回代（全部自洽）：
//   1280 任意 x            → 右飞（量到 pos=absolute、left:100%、top:−4px）✅
//   700/x=20,120,200       → 右边界 484/584/664 ≤ 700 ✅ 右飞
//   700/x=420              → 右边只剩 40 <212；左边有 420 ≥212 ⇒ **预测：左飞**（此前只读了 pos=absolute，没看左右）
//   640/x=120              → 584 ≤ 640 ⇒ 右飞
//   640/x=200              → 右边 200 <212；左边 200 <212 ⇒ **两侧都不够 ⇒ 预测：内联**（u 轮读到的正是内联）✅
//   400/250/210            → 菜单 x=20/8/8 ⇒ 预测内联 ✅（q 轮已验）
//
// 本轮就差 700/x=420 这一支：读子菜单的 x，看它在菜单**左边**还是右边。
import { openCanvas, readers } from './jimeng-b135-lib.mjs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const { b, p: shared } = await openCanvas();
const p = shared;
const R = readers(p);

const tab = await b.contexts()[0].newPage();
await tab.goto(shared.url(), { waitUntil: 'domcontentloaded' });
await tab.waitForSelector('.react-flow__node', { timeout: 60000 });
await tab.waitForTimeout(3500);

const read = () => tab.evaluate(() => {
  const e = document.querySelector('[data-testid="canvas-context-menu"]');
  if (!e) return null;
  const mr = e.getBoundingClientRect();
  const trig = e.firstElementChild.firstElementChild;
  const tr = trig.getBoundingClientRect();
  let sub = null;
  for (const c of trig.querySelectorAll('div')) {
    if (c.querySelectorAll('[role=menuitem]').length >= 5) {
      const cs = getComputedStyle(c), r = c.getBoundingClientRect();
      sub = {
        pos: cs.position, vis: cs.visibility,
        盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        style: c.getAttribute('style'),
        相对菜单: { 在右: r.x > mr.x, 在左: r.x + r.width <= tr.x },
      };
      break;
    }
  }
  return { 视口宽: innerWidth, 菜单: [Math.round(mr.x), Math.round(mr.width), Math.round(mr.height)],
    右边余: Math.round(innerWidth - (mr.x + mr.width)), 左边余: Math.round(mr.x), 子菜单: sub };
});

const run = async (W, x) => {
  await tab.context().newCDPSession(tab).then(async (s) => {
    await s.send('Emulation.setDeviceMetricsOverride', { width: W, height: 720, deviceScaleFactor: 2, mobile: false });
  });
  await tab.waitForTimeout(1300);
  await tab.keyboard.press('Escape'); await tab.waitForTimeout(250);
  // 找 (x, 180) 附近确实是画布空白的点
  let pt = null;
  for (let dy = 0; dy < 200 && !pt; dy += 8) {
    const cand = await tab.evaluate(([px, py]) => {
      const e = document.elementFromPoint(px, py);
      return !!(e && e.closest('.react-flow__pane') && !e.closest('.react-flow__node'));
    }, [x, 180 + dy]);
    if (cand) pt = [x, 180 + dy];
  }
  if (!pt) return { W, x, 失败: '该列没有画布空白点' };
  await tab.mouse.click(pt[0], pt[1], { button: 'right' });
  await tab.waitForTimeout(800);
  const d = await read();
  if (!d) return { W, x, 失败: '菜单没开' };
  const 态 = !d.子菜单 ? '（这是节点菜单，无子菜单）'
    : d.子菜单.pos !== 'absolute' ? '内联'
    : d.子菜单.相对菜单.在右 ? '右飞' : '左飞';
  const 预测 = d.右边余 >= 212 ? '右飞' : d.左边余 >= 212 ? '左飞' : '内联';
  return { W, x, 点: pt, ...d, 态, 预测, 一致: 态 === 预测 || 态.startsWith('（') };
};

const rows = [];
for (const [W, x] of [[700, 420], [700, 300], [640, 200], [640, 120], [520, 100], [420, 150]]) {
  const r = await run(W, x);
  rows.push(r);
  console.log(`  视口${W} 锚点x=${x} → ${r.失败 || `${(r.态).padEnd(16)} 预测=${r.预测} ${r.一致 ? '✅' : '❌'}  右边余${r.右边余} 左边余${r.左边余}` +
    (r.子菜单 ? `  子菜单x=${r.子菜单.盒[0]} w=${r.子菜单.盒[2]}` : '')}`);
}
const bad = rows.filter((r) => !r.失败 && !r.一致);
console.log(`\n一致 ${rows.length - bad.length}/${rows.filter((r) => !r.失败).length}`);
if (bad.length) console.log('不一致:', JSON.stringify(bad, null, 1));

await tab.keyboard.press('Escape'); await tab.waitForTimeout(300);
await tab.close();
console.log('\n共享页签复位:', JSON.stringify(await pinViewport(shared)), JSON.stringify({ sel: await R.selCount(), credits: await R.credits() }));
const fs = await import('node:fs');
fs.writeFileSync(new URL('./_tmp-b170w.json', import.meta.url), JSON.stringify(rows, null, 1));
await b.close();
