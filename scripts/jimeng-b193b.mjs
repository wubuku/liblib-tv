// 批次 193 b 轮：给 `director-node.md`（11651 字只有 3 张图，全册最干的一页）补四张图。
// 四张图各自证明手册里**当前没有图**的一条契约：
//   181 静息态：两个连接手柄 + 「进入导演台」是 SPAN[aria]        ← 静息态整节点此前无近景图
//   182 选中态：同裁切；「进入导演台」变成 BUTTON[aria=null]、多出 flow-node-media-stroke
//   183 Rename 导演台 那个**透明命中区**特写（虚线框 = BUTTON，实线框 = flow-node-title，同 y）
//   184 两个连接手柄特写
//
// 🔑 纪律：
//   · 守卫**同时认 solid 与 dashed**（批次 190 a 轮教训）；
//   · 截图放在**所有读数之后**（批次 185 教训）；
//   · 静息那一枪先断言 `选中数 == 0`，否则那张图名不副实；
//   · 不新建、不删除任何节点，只做选中与拍摄。
import fs from 'node:fs';
import { openCanvas, readers, setZoom, settle } from './jimeng-b135-lib.mjs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const SHOTS = 'docs/user-manual/jimeng-canvas/screenshots';
const NID = 'node_pxvkay973v';
const OUT = '/tmp/b193b.json';
const 记 = { 轮次: 'b193b', 收尾: null, 守卫: [] };
const save = () => fs.writeFileSync(OUT, JSON.stringify(记, null, 1));
const 认线型 = ['solid', 'dashed', 'dotted', 'double'];

/** 在页面上画若干高亮框，返回读回结果（立规 56：拍前必须把框读回来）。 */
const 画框 = (p, 规格) => p.evaluate((spec) => {
  for (const e of Array.from(document.querySelectorAll('[data-b193]'))) e.remove();
  const 建 = (id, x, y, w, h, 线型) => { const d = document.createElement('div'); d.id = id; d.setAttribute('data-b193', '1');
    d.style.cssText = `position:fixed;left:${Math.round(x)}px;top:${Math.round(y)}px;width:${Math.round(w)}px;height:${Math.round(h)}px;` +
      `border:3px ${线型} #ff8c00;border-radius:6px;pointer-events:none;z-index:2147483000;`;
    document.body.appendChild(d); };
  spec.forEach((s) => 建(s.id, s.x, s.y, s.w, s.h, s.线型 || 'solid'));
  const 读 = (id) => { const e = document.getElementById(id); if (!e) return null;
    const cs = getComputedStyle(e); const r = e.getBoundingClientRect();
    return { 宽: Math.round(r.width), 高: Math.round(r.height), borderStyle: cs.borderStyle,
      borderWidth: cs.borderWidth, borderColor: cs.borderColor, pointerEvents: cs.pointerEvents, zIndex: cs.zIndex }; };
  return { 读数: Object.fromEntries(spec.map((s) => [s.id, 读(s.id)])) };
}, 规格);

const 守卫 = (读数, 期望个数) => {
  const 键 = Object.keys(读数);
  const 每 = 键.map((k) => 读数[k]);
  return { 框数: 键.length, 框数对: 键.length === 期望个数, 全部非空: 每.every((x) => x && x.宽 > 2 && x.高 > 2),
    线型都被认: 每.every((x) => x && 认线型.includes(x.borderStyle)),
    颜色都对: 每.every((x) => x && x.borderColor === 'rgb(255, 140, 0)'),
    pointerEvents都为none: 每.every((x) => x && x.pointerEvents === 'none') };
};

const { b, p } = await openCanvas();
const R = readers(p);
await pinViewport(p);
await settle(p, R);
const 基线 = { ids: await R.ids(), credits: await R.credits() };
save();

// ① 用搜索面板把导演台取景到画面里（它本来在 canvas [640, 440]，26% 下可能偏）
await setZoom(p, 26); await p.waitForTimeout(700);
{
  const 点 = await p.evaluate(() => { const i = document.querySelector('input[aria-label="搜索"]'); if (!i) return null;
    const r = i.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
  if (!点) { const btn = await p.evaluate(() => { const a = Array.from(document.querySelectorAll('BUTTON[data-testid="canvas-panel-launcher"]'))
      .find((x) => (x.getAttribute('aria-label') || '') === '搜索'); const r = a.getBoundingClientRect();
      return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
    await p.mouse.click(btn[0], btn[1]); await p.waitForTimeout(1100);
    const 点2 = await p.evaluate(() => { const i = document.querySelector('input[aria-label="搜索"]'); const r = i.getBoundingClientRect();
      return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
    await p.mouse.click(点2[0], 点2[1]); await p.waitForTimeout(300);
    await p.keyboard.press('Meta+a'); await p.keyboard.type('导演台'); await p.waitForTimeout(1500);
  }
  const 行 = await p.evaluate(() => { const r = document.querySelector('[data-testid="canvas-search-result-node_pxvkay973v"]');
    if (!r) return null; const q = r.getBoundingClientRect(); return [Math.round(q.x + q.width / 2), Math.round(q.y + q.height / 2)]; });
  if (行) { await p.mouse.click(行[0], 行[1]); await p.waitForTimeout(2400); }
}
await p.keyboard.press('Escape'); await p.waitForTimeout(700);   // 关掉搜索面板（Esc 不清选中）
const 取景后 = { zoom: await R.zoom(), 选中: await R.selCount() };
console.log('取景后 =', JSON.stringify(取景后));
save();

// ② 取消选中 → 静息态
const 空 = await p.evaluate(() => { const nodes = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getBoundingClientRect());
  for (let y = 100; y < innerHeight - 100; y += 15) for (let x = 330; x < innerWidth - 350; x += 15) {
    const h = document.elementFromPoint(x, y);
    if (h && h.classList && h.classList.contains('react-flow__pane') && !nodes.some((r) => x >= r.x && x <= r.right && y >= r.y && y <= r.bottom)) return [x, y]; }
  return null; });
if (空) { await p.mouse.click(空[0], 空[1]); await p.waitForTimeout(1200); }
const 静息断言 = { 选中数: await R.selCount(), 通过: (await R.selCount()) === 0, zoom: await R.zoom() };
console.log('静息断言 =', JSON.stringify(静息断言));
if (!静息断言.通过) { console.log('静息前置不成立，停'); await b.close(); process.exit(1); }

// ── 读全部几何（静息态） ────────────────────────────────────────────
const G = await p.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`); if (!n) return null;
  const r = n.getBoundingClientRect();
  const t = n.querySelector('[data-testid="flow-node-title"]'); const tr = t.getBoundingClientRect();
  const sp = n.querySelector('span[aria-label="进入导演台"]'); const sr = sp ? sp.getBoundingClientRect() : null;
  const th = n.querySelector('[data-testid="flow-node-target-handle"]'); const thr = th.getBoundingClientRect();
  const sh = n.querySelector('[data-testid="flow-node-source-handle"]'); const shr = sh.getBoundingClientRect();
  return { 节点: [r.x, r.y, r.width, r.height], 标题: [tr.x, tr.y, tr.width, tr.height],
    进入: sr ? [sr.x, sr.y, sr.width, sr.height] : null, 目标手柄: [thr.x, thr.y, thr.width, thr.height],
    源手柄: [shr.x, shr.y, shr.width, shr.height],
    完整在视口内: r.x >= 0 && r.y >= 0 && r.right <= innerWidth && r.bottom <= innerHeight };
}, NID);
if (!G || !G.完整在视口内) { console.log('节点不在视口内，停：', JSON.stringify(G)); await b.close(); process.exit(1); }
console.log('静息几何 =', JSON.stringify(G));
save();

// ── 181 静息态 ──────────────────────────────────────────────────────
{
  const o = 8;
  const 规格 = [
    { id: '__b193-node', x: G.节点[0] - o, y: G.节点[1] - o, w: G.节点[2] + 2 * o, h: G.节点[3] + 2 * o, 线型: 'solid' },
    { id: '__b193-enter', x: G.进入[0] - 6, y: G.进入[1] - 6, w: G.进入[2] + 12, h: G.进入[3] + 12, 线型: 'dashed' },
    { id: '__b193-th', x: G.目标手柄[0] - 5, y: G.目标手柄[1] - 5, w: G.目标手柄[2] + 10, h: G.目标手柄[3] + 10, 线型: 'dashed' },
    { id: '__b193-sh', x: G.源手柄[0] - 5, y: G.源手柄[1] - 5, w: G.源手柄[2] + 10, h: G.源手柄[3] + 10, 线型: 'dashed' },
  ];
  const 读 = await 画框(p, 规格);
  const g = 守卫(读.读数, 4);
  记.守卫.push({ 图: 181, ...g, 读数: 读.读数 });
  if (!Object.values(g).every(Boolean)) { console.log('181 守卫不过', JSON.stringify(g)); await b.close(); process.exit(1); }
  const C = G.节点;
  await p.screenshot({ path: `${SHOTS}/181-director-node-rest.png`,
    clip: { x: Math.round(C[0] - 40), y: Math.round(C[1] - 40), width: Math.round(C[2] + 80), height: Math.round(C[3] + 80) } });
  console.log('181 已拍');
}
await p.evaluate(() => { for (const e of Array.from(document.querySelectorAll('[data-b193]'))) e.remove(); });

// ── 选中 → 182 选中态 ───────────────────────────────────────────────
const 落点 = await p.evaluate((nid) => { const t = document.querySelector(`.react-flow__node[data-id="${nid}"] [data-testid="flow-node-title"]`);
  if (!t) return null; const r = t.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, NID);
await p.mouse.click(落点[0], 落点[1]); await p.waitForTimeout(1200);
const 选中断言 = { 选中数: await R.selCount(), 通过: (await R.selCount()) === 1 };
console.log('选中断言 =', JSON.stringify(选中断言));
const G2 = await p.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`); if (!n) return null;
  const r = n.getBoundingClientRect();
  const rn = n.querySelector('[aria-label="Rename 导演台"]'); const rr = rn ? rn.getBoundingClientRect() : null;
  const t = n.querySelector('[data-testid="flow-node-title"]'); const tr = t.getBoundingClientRect();
  const btn = Array.from(n.querySelectorAll('button')).find((e) => (e.innerText || '').trim() === '进入导演台');
  const br = btn ? btn.getBoundingClientRect() : null;
  return { 节点: [r.x, r.y, r.width, r.height],
    Rename: rr ? [rr.x, rr.y, rr.width, rr.height] : null, 标题: [tr.x, tr.y, tr.width, tr.height],
    进入BUTTON: br ? [br.x, br.y, br.width, br.height] : null,
    Rename背景: rn ? getComputedStyle(rn).backgroundColor : null,
    Rename边框: rn ? getComputedStyle(rn).border : null,
    进入aria: btn ? btn.getAttribute('aria-label') : '（没有这个 BUTTON）',
    多出testid: Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')),
    nodeToolbar数: n.querySelectorAll('[data-testid="node-toolbar"]').length };
}, NID);
console.log('选中几何 =', JSON.stringify(G2));
save();
if (!选中断言.通过) { console.log('选中前置不成立，停'); await b.close(); process.exit(1); }
{
  const o = 8;
  const 规格 = [
    { id: '__b193-node', x: G2.节点[0] - o, y: G2.节点[1] - o, w: G2.节点[2] + 2 * o, h: G2.节点[3] + 2 * o, 线型: 'solid' },
    { id: '__b193-rename', x: G2.Rename[0] - 5, y: G2.Rename[1] - 5, w: G2.Rename[2] + 10, h: G2.Rename[3] + 10, 线型: 'dashed' },
    { id: '__b193-enter', x: G2.进入BUTTON[0] - 6, y: G2.进入BUTTON[1] - 6, w: G2.进入BUTTON[2] + 12, h: G2.进入BUTTON[3] + 12, 线型: 'dashed' },
  ];
  const 读 = await 画框(p, 规格);
  const g = 守卫(读.读数, 3);
  记.守卫.push({ 图: 182, ...g, 读数: 读.读数 });
  if (!Object.values(g).every(Boolean)) { console.log('182 守卫不过', JSON.stringify(g)); await b.close(); process.exit(1); }
  const C = G2.节点;
  await p.screenshot({ path: `${SHOTS}/182-director-node-selected.png`,
    clip: { x: Math.round(C[0] - 40), y: Math.round(C[1] - 40), width: Math.round(C[2] + 80), height: Math.round(C[3] + 80) } });
  console.log('182 已拍');
}
await p.evaluate(() => { for (const e of Array.from(document.querySelectorAll('[data-b193]'))) e.remove(); });

// ── 183 Rename 透明命中区特写 ───────────────────────────────────────
{
  const T = G2.标题, R2 = G2.Rename;
  const x = Math.min(T[0], R2[0]) - 14, y = T[1] - 14;
  const w = Math.max(T[0] + T[2], R2[0] + R2[2]) - x + 14, h = Math.max(T[1] + T[3], R2[1] + R2[3]) - y + 14;
  const 规格 = [
    { id: '__b193-rename', x: R2[0] - 4, y: R2[1] - 4, w: R2[2] + 8, h: R2[3] + 8, 线型: 'dashed' },
    { id: '__b193-title', x: T[0] - 4, y: T[1] - 4, w: T[2] + 8, h: T[3] + 8, 线型: 'solid' },
  ];
  const 读 = await 画框(p, 规格);
  const g = 守卫(读.读数, 2);
  记.守卫.push({ 图: 183, ...g, 读数: 读.读数 });
  if (!Object.values(g).every(Boolean)) { console.log('183 守卫不过', JSON.stringify(g)); await b.close(); process.exit(1); }
  await p.screenshot({ path: `${SHOTS}/183-director-rename-hit-area.png`, clip: { x: Math.round(x), y: Math.round(y), width: Math.round(w), height: Math.round(h) } });
  console.log('183 已拍');
}
await p.evaluate(() => { for (const e of Array.from(document.querySelectorAll('[data-b193]'))) e.remove(); });

// ── 184 两个连接手柄特写 ────────────────────────────────────────────
{
  const 静息手柄 = await p.evaluate((nid) => { const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`); if (!n) return null;
    const t = n.querySelector('[data-testid="flow-node-target-handle"]').getBoundingClientRect();
    const s = n.querySelector('[data-testid="flow-node-source-handle"]').getBoundingClientRect();
    return { t: [t.x, t.y, t.width, t.height], s: [s.x, s.y, s.width, s.height] }; }, NID);
  const x = 静息手柄.t[0] - 20, y = Math.min(静息手柄.t[1], 静息手柄.s[1]) - 20;
  const w = (静息手柄.s[0] + 静息手柄.s[2]) - x + 20, h = Math.max(静息手柄.t[1] + 静息手柄.t[3], 静息手柄.s[1] + 静息手柄.s[3]) - y + 20;
  const 规格 = [
    { id: '__b193-th', x: 静息手柄.t[0] - 4, y: 静息手柄.t[1] - 4, w: 静息手柄.t[2] + 8, h: 静息手柄.t[3] + 8, 线型: 'dashed' },
    { id: '__b193-sh', x: 静息手柄.s[0] - 4, y: 静息手柄.s[1] - 4, w: 静息手柄.s[2] + 8, h: 静息手柄.s[3] + 8, 线型: 'dashed' },
  ];
  const 读 = await 画框(p, 规格);
  const g = 守卫(读.读数, 2);
  记.守卫.push({ 图: 184, ...g, 读数: 读.读数, 手柄: 静息手柄 });
  if (!Object.values(g).every(Boolean)) { console.log('184 守卫不过', JSON.stringify(g)); await b.close(); process.exit(1); }
  await p.screenshot({ path: `${SHOTS}/184-director-handles.png`, clip: { x: Math.round(x), y: Math.round(y), width: Math.round(w), height: Math.round(h) } });
  console.log('184 已拍');
}
await p.evaluate(() => { for (const e of Array.from(document.querySelectorAll('[data-b193]'))) e.remove(); });

// 收尾：取消选中 + 视口归位
const 空2 = await p.evaluate(() => { const nodes = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getBoundingClientRect());
  for (let y = 100; y < innerHeight - 100; y += 15) for (let x = 330; x < innerWidth - 350; x += 15) {
    const h = document.elementFromPoint(x, y);
    if (h && h.classList && h.classList.contains('react-flow__pane') && !nodes.some((r) => x >= r.x && x <= r.right && y >= r.y && y <= r.bottom)) return [x, y]; }
  return null; });
if (空2) { await p.mouse.click(空2[0], 空2[1]); await p.waitForTimeout(1000); }
await setZoom(p, 26); await p.waitForTimeout(700);
const ids = await R.ids();
记.收尾 = { 状态行: await R.status(), 选中: await R.selCount(), zoom: await R.zoom(), credits: await R.credits(), 节点数: ids.length,
  残留: ids.filter((x) => !基线.ids.includes(x)), 丢失: 基线.ids.filter((x) => !ids.includes(x)) };
save();
console.log('收尾 =', JSON.stringify(记.收尾));
await b.close();
console.log('写出', OUT);
