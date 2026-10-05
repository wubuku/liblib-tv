// 批次 170 h 轮：右键菜单的定位规则（1280×720，不动视口）。
//
// g 轮两个观测还不够定规则：
//   右键 (900,620) → 菜单 top=420（292 高，620+292=912 > 720，**翻转了**）
//   右键 (347,376) → 菜单 top=376（376+292=668 < 720，**没翻转**）
// 「420 = 720−292−8」看着像翻转时留 8px，但也可能是别的算法 ⇒ 本轮扫锚点。
// 只读几何，不点菜单项。
import { openCanvas, readers } from './jimeng-b135-lib.mjs';

const { b, p } = await openCanvas();
const R = readers(p);

const readMenu = () => p.evaluate(() => {
  const e = document.querySelector('[data-testid="canvas-context-menu"]');
  if (!e) return null;
  const r = e.getBoundingClientRect();
  return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) };
});

// 找一个确实是「画布空白」的点（elementFromPoint 落在 react-flow pane 里）
const blankPoint = () => p.evaluate(() => {
  const W = innerWidth, H = innerHeight;
  for (let y = 40; y < H - 20; y += 20) {
    for (let x = 40; x < W - 20; x += 20) {
      const e = document.elementFromPoint(x, y);
      if (e && e.closest('.react-flow__pane') && !e.closest('.react-flow__node')) return [x, y];
    }
  }
  return null;
});

const rows = [];
const base = await blankPoint();
console.log('空白点:', JSON.stringify(base), 'inner:', await p.evaluate(() => [innerWidth, innerHeight]));

for (const [ax, ay] of [[base[0], base[1]], [640, 200], [640, 380], [640, 428], [640, 430], [640, 500], [640, 640], [1100, 100], [1230, 640]]) {
  await p.keyboard.press('Escape');
  await p.waitForTimeout(350);
  await p.mouse.move(ax, ay);
  await p.waitForTimeout(150);
  await p.mouse.click(ax, ay, { button: 'right' });
  await p.waitForTimeout(800);
  const m = await readMenu();
  if (!m) { rows.push({ anchor: [ax, ay], menu: null }); continue; }
  const vw = await p.evaluate(() => innerWidth), vh = await p.evaluate(() => innerHeight);
  rows.push({
    anchor: [ax, ay], menu: [m.x, m.y, m.w, m.h],
    dx: m.x - ax, dy: m.y - ay,
    rightEdge: m.x + m.w, bottomEdge: m.y + m.h,
    gapRight: vw - (m.x + m.w), gapBottom: vh - (m.y + m.h),
    flips: m.y < ay ? 'UP' : 'DOWN',
    flipsX: m.x < ax ? 'LEFT' : 'RIGHT',
    vw, vh,
  });
  console.log(JSON.stringify(rows[rows.length - 1]));
}

// 收尾：Esc 关掉菜单，确认没留下挡板
await p.keyboard.press('Escape');
await p.waitForTimeout(500);
const left = await p.evaluate(() => document.querySelectorAll('[data-testid="canvas-context-menu"]').length);
console.log('\n收尾残留菜单数:', left, ' state:', JSON.stringify(await state0()));
async function state0() { return { status: await R.status(), sel: await R.selCount(), credits: await R.credits() }; }
await b.close();
