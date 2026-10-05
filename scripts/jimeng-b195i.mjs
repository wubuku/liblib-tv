// 批次 195 i 轮：用**从没播过**的新节点重拍 189/190/191 三张同裁切对照图。
//
// 与 g 轮的两处差别（都是 g 轮守卫教会的）：
//   ① 189 的断言**放宽**：不再要求「无 <video>」（手册第 32 行已写明取消选中后 <video> 仍留在 DOM 里），
//      只断言「选中=false 且 无大播放键 且 无控件行」，`<video>` 在不在只作读数记录。
//   ② 190 用**从没播过的节点**点标题行，才拿得到手册那一档（5 个按钮、无 <video>）。
//
// 📌 拍摄顺序不能换：先拍未选中 → 再点标题行（未播）→ 最后点正文（起播）。
//    一旦点过正文，这个节点就再也回不到「从没播过」那一档。
import fs from 'node:fs';
import { openCanvas, readers, settle, setZoom, endState } from './jimeng-b135-lib.mjs';

const SELF = 'node_jhe3mm3ayg';
const OUTDIR = 'docs/user-manual/jimeng-canvas/screenshots';
const { b, p } = await openCanvas();
const R = readers(p);
const 基线 = { ids: await R.ids(), testids: await R.testids() };
await settle(p, R);
const log = (...a) => console.log(a.join(' '));
await setZoom(p, 100);

const 状态 = () => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  const v = n.querySelector('video');
  return { 选中: n.classList.contains('selected'), 有video: !!v, paused: v ? v.paused : null,
    currentTime: v ? Math.round(v.currentTime * 1000) / 1000 : null,
    按钮: Array.from(n.querySelectorAll('button')).map((x) => x.getAttribute('aria-label') || x.innerText.trim()),
    控件行: !!n.querySelector('[data-testid="video-node-player-bar"]'),
    大播放键: !!n.querySelector('[data-testid="video-simple-player"]') };
}, SELF);

const 画框 = (规格) => p.evaluate((K) => {
  document.querySelectorAll('[id^="__b195-"]').forEach((e) => e.remove());
  for (const s of K) { const d = document.createElement('div'); d.id = s.id;
    Object.assign(d.style, { position: 'fixed', left: s.x + 'px', top: s.y + 'px', width: s.w + 'px', height: s.h + 'px',
      boxSizing: 'border-box', pointerEvents: 'none', zIndex: 2147483000, borderRadius: '2px',
      border: (s.线型 === 'dashed' ? '2px dashed' : '2px solid') + ' rgb(255, 140, 0)' });
    document.body.appendChild(d); }
  const 读回 = {}; for (const s of K) { const c = getComputedStyle(document.getElementById(s.id));
    读回[s.id] = { 宽: parseFloat(c.width), 高: parseFloat(c.height), borderStyle: c.borderStyle, borderColor: c.borderColor, pointerEvents: c.pointerEvents }; }
  return { 框数: K.length, 读回 };
}, 规格);
const 校验 = (画, 期望) => { const ids = Object.keys(画.读回);
  const r = { 框数对: 画.框数 === 期望, 全非空: ids.every((k) => 画.读回[k].宽 > 0 && 画.读回[k].高 > 0),
    线型都被认: ids.every((k) => ['solid', 'dashed'].includes(画.读回[k].borderStyle)),
    颜色都对: ids.every((k) => 画.读回[k].borderColor === 'rgb(255, 140, 0)'),
    pointerEvents都为none: ids.every((k) => 画.读回[k].pointerEvents === 'none') };
  r.全过 = Object.values(r).every(Boolean); return r; };
const 清框 = () => p.evaluate(() => document.querySelectorAll('[id^="__b195-"]').forEach((e) => e.remove()));

const 点空白 = async () => { const s = await p.evaluate(() => { const ns = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getBoundingClientRect());
  for (let x = 60; x < innerWidth - 340; x += 40) for (let y = 120; y < innerHeight - 140; y += 40) { const h = document.elementFromPoint(x, y);
    if (h && h.classList && h.classList.contains('react-flow__pane') && !ns.some((r) => x >= r.x && x <= r.right && y >= r.y && y <= r.bottom)) return [x, y]; } return null; });
  if (s) { await p.mouse.click(s[0], s[1]); await p.waitForTimeout(800); } return s; };
const 点标题 = async () => { const s = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); const t = n.querySelector('[data-testid="flow-node-title"]'); if (!t) return null; const r = t.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, SELF);
  if (s) { await p.mouse.click(s[0], s[1]); await p.waitForTimeout(900); } return s; };
const 点正文 = async () => { const s = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); const r = n.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height * 0.55)]; }, SELF);
  if (s) { await p.mouse.click(s[0], s[1]); await p.waitForTimeout(450); } return s; };

const 裁切 = await p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  const r = n.getBoundingClientRect();
  let t = r.top, bo = r.bottom, le = r.left, ri = r.right;
  for (const sel of ['[data-testid="flow-node-title"]', '[data-testid="video-node-player-bar"]', '[data-testid="video-simple-player"]']) {
    const e = n.querySelector(sel); if (!e) continue; const b = e.getBoundingClientRect();
    t = Math.min(t, b.top); bo = Math.max(bo, b.bottom); le = Math.min(le, b.left); ri = Math.max(ri, b.right); }
  const pad = 26, X = Math.max(2, Math.round(le - pad)), Y = Math.max(62, Math.round(t - pad));
  return { x: X, y: Y, width: Math.min(Math.round(ri + pad) - X, 1280 - X - 2), height: Math.min(Math.round(bo + pad) - Y, 720 - Y - 2),
           节点屏上: [r.x, r.y, r.width, r.height].map((z) => Math.round(z * 100) / 100) };
}, SELF);
log('裁切：', JSON.stringify(裁切));
const 卡框 = () => { const [x, y, w, h] = 裁切.节点屏上; return { x: Math.round(x - 4), y: Math.round(y - 4), w: Math.round(w + 8), h: Math.round(h + 8) }; };
const out = { 轮次: 'b195i', SELF, 裁切, 图: {} };

const 拍 = async (名, 规格, 守卫) => {
  const 画 = await 画框(规格); const 校 = 校验(画, 规格.length); const 断 = await 守卫();
  out.图[名] = { 断言: 断, 守卫: 校 };
  const 全过 = 校.全过 && 断.通过;
  log(名, '：', 断.判据, '→', 断.通过 ? '✅' : '🔴', '| 画框', 校.全过 ? '✅' : '🔴' + JSON.stringify(校));
  if (!全过) { await 清框(); out.图[名].跳过 = '守卫没过 ⇒ 不拍'; return; }
  await p.screenshot({ path: `${OUTDIR}/${名}.png`, clip: 裁切 });
  out.图[名].已拍 = true; await 清框();
};

// ===== 189 未选中 =====
await 点空白(); await p.waitForTimeout(900);
log('189 前置状态：', JSON.stringify(await 状态()));
await 拍('189-video-node-unselected', [{ id: '__b195-card', ...卡框(), 线型: 'solid' }],
  async () => { const s = await 状态(); return { 判据: '选中=false 且 无大播放键 且 无控件行（<video> 只作读数）',
    读数: s, 通过: s.选中 === false && s.大播放键 === false && s.控件行 === false }; });

// ===== 190 已选中但从没播过 =====
await 点标题(); await p.waitForTimeout(800);
log('190 前置状态：', JSON.stringify(await 状态()));
const g190 = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  const e = n.querySelector('[data-testid="video-simple-player"]'); if (!e) return null;
  const r = e.getBoundingClientRect(); return { x: Math.round(r.x - 18), y: Math.round(r.y - 18), w: Math.round(r.width + 36), h: Math.round(r.height + 36) }; }, SELF);
await 拍('190-video-node-selected-not-played', [{ id: '__b195-card', ...卡框(), 线型: 'solid' }, ...(g190 ? [{ id: '__b195-play', ...g190, 线型: 'dashed' }] : [])],
  async () => { const s = await 状态(); return { 判据: '选中=true 且 无<video> 且 有大播放键 且 按钮数=5',
    读数: s, 通过: s.选中 === true && s.有video === false && s.大播放键 === true && s.按钮.length === 5 }; });

// ===== 191 正在播 =====
await 点正文(); await p.waitForTimeout(450);
log('191 前置状态：', JSON.stringify(await 状态()));
const g191 = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  const e = n.querySelector('[data-testid="video-node-player-bar"]'); if (!e) return null;
  const r = e.getBoundingClientRect(); return { x: Math.round(r.x - 6), y: Math.round(r.y - 6), w: Math.round(r.width + 12), h: Math.round(r.height + 12) }; }, SELF);
await 拍('191-video-node-playing', [{ id: '__b195-card', ...卡框(), 线型: 'solid' }, ...(g191 ? [{ id: '__b195-bar', ...g191, 线型: 'dashed' }] : [])],
  async () => { const s = await 状态(); return { 判据: '选中=true 且 有<video> 且 paused=false 且 控件行在 且 大播放键不在 且 currentTime>0',
    读数: s, 通过: s.选中 === true && s.有video === true && s.paused === false && s.控件行 === true && s.大播放键 === false && s.currentTime > 0 }; });

// ===== 193 取消选中之后：控件行消失、<video> 仍在 DOM 里 =====
const before = await 状态();
await 点空白(); await p.waitForTimeout(700);
const after = await 状态();
out.取消选中对照 = { 前: before, 后: after };
log('取消选中 前：', JSON.stringify(before)); log('取消选中 后：', JSON.stringify(after));
out.取消选中断言 = { 判据: '取消选中后 选中=false 且 控件行消失 且 <video> 仍在 DOM 里',
  通过: after.选中 === false && after.控件行 === false && after.有video === true };
log('取消选中断言：', out.取消选中断言.通过 ? '✅' : '🔴');

fs.writeFileSync('/tmp/b195i.json', JSON.stringify(out, null, 1));
out.收尾 = await endState(p, R, 基线);
log('收尾：', JSON.stringify(out.收尾));
await b.close();
