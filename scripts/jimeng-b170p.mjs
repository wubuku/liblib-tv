// 批次 170 p 轮：查「250 宽下菜单高 584」到底是什么。
//
// 观测（批次 170 o 轮图 131）：视口 250×720 时，空白右键菜单 = **234×584**；
// 同一菜单在 1280×720 下只有 240×172 ⇒ 差 **412**。
// 子菜单（hover 才显形的「新建节点」列表）在 1280 下量过是 **212×404**，
// 404 + 8 = 412 —— **数值对得上，但机制不能靠凑**（立规 41：推广前先找反例 / 别拿数字对得上当证据）。
//
// 三个互斥假设：
//   H1 窄窗下子菜单从 position:absolute 变成流内（static+visible）⇒ 吃掉了 404+间隙
//   H2 菜单换了更大的 data-context-menu-size / 条目更多
//   H3 别的元素（滚动容器/另一个菜单实例）叠进来了
import { openCanvas, readers } from './jimeng-b135-lib.mjs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const { b, p: shared } = await openCanvas();
const R = readers(shared);
const URL_ = shared.url();

const tab = await b.contexts()[0].newPage();
await tab.goto(URL_, { waitUntil: 'domcontentloaded' });
await tab.waitForSelector('.react-flow__node', { timeout: 60000 });
await tab.waitForTimeout(3500);

const readDeep = () => tab.evaluate(() => {
  const e = document.querySelector('[data-testid="canvas-context-menu"]');
  if (!e) return null;
  const r = e.getBoundingClientRect();
  const walk = (el, d) => {
    const b = el.getBoundingClientRect();
    const cs = getComputedStyle(el);
    return {
      d, role: el.getAttribute('role'), disp: cs.display, pos: cs.position, vis: cs.visibility,
      box: [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)],
      own: el.children.length ? null : (el.innerText || '').trim().split('\n')[0].slice(0, 12),
      kids: Array.from(el.children).map((c) => walk(c, d + 1)),
    };
  };
  return {
    盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    sizeAttr: e.getAttribute('data-context-menu-size'),
    scrollable: e.getAttribute('data-context-menu-scrollable'),
    rootClass: e.getAttribute('class'),
    rootStyle: e.getAttribute('style'),
    tree: walk(e, 0),
  };
});

const blank = () => tab.evaluate(() => {
  for (let y = 20; y < innerHeight - 10; y += 10)
    for (let x = 20; x < innerWidth - 10; x += 10) {
      const e = document.elementFromPoint(x, y);
      if (e && e.closest('.react-flow__pane') && !e.closest('.react-flow__node')) return [x, y];
    }
  return null;
});

for (const [w, h] of [[1280, 720], [250, 720]]) {
  await tab.context().newCDPSession(tab).then(async (s) => {
    await s.send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: 2, mobile: false });
  });
  await tab.waitForTimeout(1500);
  await tab.keyboard.press('Escape'); await tab.waitForTimeout(300);
  const pt = await blank();
  await tab.mouse.click(pt[0], pt[1], { button: 'right' });
  await tab.waitForTimeout(1100);
  const d = await readDeep();
  console.log(`\n════ 视口 ${w}×${h}  菜单 ${d.盒.join('×')}  size=${d.sizeAttr} scrollable=${d.scrollable} ════`);
  console.log('  root style:', d.rootStyle);
  const pr = (n, ind = 1) => {
    if (n.d <= 2) {
      console.log(`  ${'  '.repeat(ind)}[${n.d}] ${(n.role || '').padEnd(9)} ${n.pos.padEnd(8)} vis=${n.vis.padEnd(7)} ${n.box.join('×')}${n.own ? ' · ' + n.own : ''}`);
    }
    for (const c of n.kids) pr(c, ind + 1);
  };
  pr(d.tree);
  // 找子菜单
  const sub = await tab.evaluate(() => {
    const e = document.querySelector('[data-testid="canvas-context-menu"]');
    for (const c of e.querySelectorAll('div')) {
      const cs = getComputedStyle(c);
      if (c.querySelectorAll('[role=menuitem]').length >= 5) {
        const r = c.getBoundingClientRect();
        return { pos: cs.position, vis: cs.visibility, disp: cs.display,
          box: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
          className: c.getAttribute('class'), style: c.getAttribute('style'),
          inFlow: c.parentElement !== e ? '在列表里' : '根的直接子' };
      }
    }
    return null;
  });
  console.log('  疑似子菜单容器:', JSON.stringify(sub));
}

await tab.keyboard.press('Escape'); await tab.waitForTimeout(300);
await tab.close();
console.log('\n共享页签复位:', JSON.stringify(await pinViewport(shared)), JSON.stringify({ sel: await R.selCount(), credits: await R.credits() }));
await b.close();
