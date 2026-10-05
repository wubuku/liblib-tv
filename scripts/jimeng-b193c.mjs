// 批次 193 c 轮：第 184 张拍出来**两个手柄框里也是空的** —— 与搜索面板那个 ⌖ 定位图标（批次 192 e 轮
// 测到 `opacity 0 → 1`）形状一样。本轮验「导演台的两个连接手柄是不是也是 opacity 悬停显影」，
// 若是 ⇒ 把 184 重拍成「悬停态」，图才有信息量；顺带这也是一条**跨组件的共同机制**。
import fs from 'node:fs';
import { openCanvas, readers, setZoom, settle } from './jimeng-b135-lib.mjs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const SHOTS = 'docs/user-manual/jimeng-canvas/screenshots';
const NID = 'node_pxvkay973v';
const 认线型 = ['solid', 'dashed', 'dotted', 'double'];
const 读手柄 = (p) => p.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`); if (!n) return null;
  const 一 = (sel) => { const e = n.querySelector(sel); if (!e) return null; const r = e.getBoundingClientRect();
    const cs = getComputedStyle(e);
    return { 屏上: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      opacity: cs.opacity, visibility: cs.visibility, display: cs.display, background: cs.backgroundColor,
      border: cs.border, 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; };
  return { target: 一('[data-testid="flow-node-target-handle"]'), source: 一('[data-testid="flow-node-source-handle"]'),
    节点hover: n.matches(':hover') };
}, NID);

const { b, p } = await openCanvas();
const R = readers(p);
await pinViewport(p);
await settle(p, R);
const 基线 = { ids: await R.ids(), credits: await R.credits() };
const out = {};

// 取景到 50%（和 b 轮同一档，两张图可直接叠着看）
await setZoom(p, 26); await p.waitForTimeout(600);
{
  const btn = await p.evaluate(() => { const a = Array.from(document.querySelectorAll('BUTTON[data-testid="canvas-panel-launcher"]'))
    .find((x) => (x.getAttribute('aria-label') || '') === '搜索'); const r = a.getBoundingClientRect();
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
  await p.mouse.click(btn[0], btn[1]); await p.waitForTimeout(1100);
  const 点 = await p.evaluate(() => { const i = document.querySelector('input[aria-label="搜索"]'); const r = i.getBoundingClientRect();
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
  await p.mouse.click(点[0], 点[1]); await p.waitForTimeout(300);
  await p.keyboard.press('Meta+a'); await p.keyboard.type('导演台'); await p.waitForTimeout(1500);
  const 行 = await p.evaluate(() => { const r = document.querySelector('[data-testid="canvas-search-result-node_pxvkay973v"]');
    if (!r) return null; const q = r.getBoundingClientRect(); return [Math.round(q.x + q.width / 2), Math.round(q.y + q.height / 2)]; });
  if (行) { await p.mouse.click(行[0], 行[1]); await p.waitForTimeout(2400); }
}
await p.keyboard.press('Escape'); await p.waitForTimeout(700);
const 空 = await p.evaluate(() => { const nodes = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getBoundingClientRect());
  for (let y = 100; y < innerHeight - 100; y += 15) for (let x = 330; x < innerWidth - 350; x += 15) {
    const h = document.elementFromPoint(x, y);
    if (h && h.classList && h.classList.contains('react-flow__pane') && !nodes.some((r) => x >= r.x && x <= r.right && y >= r.y && y <= r.bottom)) return [x, y]; }
  return null; });
if (空) { await p.mouse.click(空[0], 空[1]); await p.waitForTimeout(1000); }
const 静息断言 = { 选中数: await R.selCount(), zoom: await R.zoom() };
console.log('静息断言 =', JSON.stringify(静息断言));
if (静息断言.选中数 !== 0) { console.log('前置不成立，停'); await b.close(); process.exit(1); }

out.未悬停 = await 读手柄(p);
// 悬停到源手柄中心
const H = (await 读手柄(p)).source;
await p.mouse.move(H.中心[0], H.中心[1]); await p.waitForTimeout(900);
out.悬停源手柄 = await 读手柄(p);
// 悬停到目标手柄中心
const T = (await 读手柄(p)).target;
await p.mouse.move(T.中心[0], T.中心[1]); await p.waitForTimeout(900);
out.悬停目标手柄 = await 读手柄(p);
console.log('三态 =', JSON.stringify(out, null, 1));

// 重拍 184：悬停在**目标手柄**上（画两个框，目标是实线=悬停中的那个，源是虚线）
{
  const cur = await 读手柄(p);
  const t = cur.target, s = cur.source;
  const 规格 = [
    { id: '__b193-th', x: t.屏上[0] - 4, y: t.屏上[1] - 4, w: t.屏上[2] + 8, h: t.屏上[3] + 8, 线型: 'solid' },
    { id: '__b193-sh', x: s.屏上[0] - 4, y: s.屏上[1] - 4, w: s.屏上[2] + 8, h: s.屏上[3] + 8, 线型: 'dashed' },
  ];
  const 读 = await p.evaluate((spec) => {
    for (const e of Array.from(document.querySelectorAll('[data-b193]'))) e.remove();
    spec.forEach((sp) => { const d = document.createElement('div'); d.id = sp.id; d.setAttribute('data-b193', '1');
      d.style.cssText = `position:fixed;left:${Math.round(sp.x)}px;top:${Math.round(sp.y)}px;width:${Math.round(sp.w)}px;height:${Math.round(sp.h)}px;` +
        `border:3px ${sp.线型} #ff8c00;border-radius:6px;pointer-events:none;z-index:2147483000;`; document.body.appendChild(d); });
    const 一 = (id) => { const e = document.getElementById(id); if (!e) return null; const cs = getComputedStyle(e); const r = e.getBoundingClientRect();
      return { 宽: Math.round(r.width), 高: Math.round(r.height), borderStyle: cs.borderStyle, borderColor: cs.borderColor, pointerEvents: cs.pointerEvents }; };
    return { th: 一('__b193-th'), sh: 一('__b193-sh') };
  }, 规格);
  const g = { 框数对: !!读.th && !!读.sh, 宽高为正: 读.th && 读.sh ? 读.th.宽 > 2 && 读.th.高 > 2 && 读.sh.宽 > 2 && 读.sh.高 > 2 : false,
    线型都被认: 读.th && 读.sh ? 认线型.includes(读.th.borderStyle) && 认线型.includes(读.sh.borderStyle) : false,
    颜色都对: 读.th && 读.sh ? 读.th.borderColor === 'rgb(255, 140, 0)' && 读.sh.borderColor === 'rgb(255, 140, 0)' : false,
    pointerEvents都为none: 读.th && 读.sh ? 读.th.pointerEvents === 'none' && 读.sh.pointerEvents === 'none' : false };
  console.log('守卫 =', JSON.stringify(g));
  if (Object.values(g).every(Boolean)) {
    const x = t.屏上[0] - 20, y = Math.min(t.屏上[1], s.屏上[1]) - 20;
    const w = (s.屏上[0] + s.屏上[2]) - x + 20, h = Math.max(t.屏上[1] + t.屏上[3], s.屏上[1] + s.屏上[3]) - y + 20;
    await p.screenshot({ path: `${SHOTS}/184-director-handles.png`, clip: { x: Math.round(x), y: Math.round(y), width: Math.round(w), height: Math.round(h) } });
    console.log('184 已重拍（悬停态）');
  } else { console.log('守卫不过，不拍'); }
}
await p.evaluate(() => { for (const e of Array.from(document.querySelectorAll('[data-b193]'))) e.remove(); });
const 空2 = await p.evaluate(() => { const nodes = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getBoundingClientRect());
  for (let y = 100; y < innerHeight - 100; y += 15) for (let x = 330; x < innerWidth - 350; x += 15) {
    const h = document.elementFromPoint(x, y);
    if (h && h.classList && h.classList.contains('react-flow__pane') && !nodes.some((r) => x >= r.x && x <= r.right && y >= r.y && y <= r.bottom)) return [x, y]; }
  return null; });
if (空2) { await p.mouse.click(空2[0], 空2[1]); await p.waitForTimeout(900); }
await setZoom(p, 26); await p.waitForTimeout(600);
const ids = await R.ids();
out.收尾 = { 状态行: await R.status(), 选中: await R.selCount(), zoom: await R.zoom(), credits: await R.credits(), 节点数: ids.length,
  残留: ids.filter((x) => !基线.ids.includes(x)), 丢失: 基线.ids.filter((x) => !ids.includes(x)) };
fs.writeFileSync('/tmp/b193c.json', JSON.stringify(out, null, 1));
console.log('收尾 =', JSON.stringify(out.收尾));
await b.close();
