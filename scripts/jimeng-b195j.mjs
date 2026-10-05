// 批次 195 j 轮：补拍 191（正在播）与 193（暂停态）。
//
// 🔴 i 轮 191 被守卫拦下，**守卫是对的**：i 轮的顺序是 189（未选中）→ 190（点标题行 = 已选中）
//   → 191（点正文），此时节点**已经处于选中态** ⇒ 读到 `paused: true` / `currentTime: 0`，
//   **根本没起播**。这与 c 轮档 C 的读数一致。
//
// ⇒ 🔴🔴 本轮钉到一条手册没写的契约（**对「选中即播」的必要限定**）：
//   · **未选中** → 点卡片正文 ⇒ **起播**（d 轮臂 1：0.914→3.382，paused 恒 false）
//   · **已选中** → 点卡片正文 ⇒ **不起播、也不重播**（c 轮档 C / i 轮 191，两次复现）
//   「选中即播」这句只在**第一支**成立。
//
// 📌 191 必须先**取消选中**再点正文；193 紧接着点播放钮暂停，两张同一裁切可叠着看。
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
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); const v = n.querySelector('video');
  const tog = n.querySelector('[data-testid="video-node-playback-toggle"]');
  const clk = n.querySelector('[data-testid="video-node-player-clock"]');
  return { 选中: n.classList.contains('selected'), 有video: !!v, paused: v ? v.paused : null,
    currentTime: v ? Math.round(v.currentTime * 1000) / 1000 : null,
    播放钮aria: tog ? tog.getAttribute('aria-label') : null,
    时钟文字: clk ? clk.innerText.replace(/\s+/g, ' ').trim() : null,
    控件行: !!n.querySelector('[data-testid="video-node-player-bar"]'),
    大播放键: !!n.querySelector('[data-testid="video-simple-player"]') };
}, SELF);

const 画框 = (K) => p.evaluate((S) => {
  document.querySelectorAll('[id^="__b195-"]').forEach((e) => e.remove());
  for (const s of S) { const d = document.createElement('div'); d.id = s.id;
    Object.assign(d.style, { position: 'fixed', left: s.x + 'px', top: s.y + 'px', width: s.w + 'px', height: s.h + 'px',
      boxSizing: 'border-box', pointerEvents: 'none', zIndex: 2147483000, borderRadius: '2px',
      border: (s.线型 === 'dashed' ? '2px dashed' : '2px solid') + ' rgb(255, 140, 0)' });
    document.body.appendChild(d); }
  const 读回 = {}; for (const s of S) { const c = getComputedStyle(document.getElementById(s.id));
    读回[s.id] = { 宽: parseFloat(c.width), 高: parseFloat(c.height), borderStyle: c.borderStyle, borderColor: c.borderColor, pointerEvents: c.pointerEvents }; }
  return { 框数: S.length, 读回 };
}, K);
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
const 点正文 = async () => { const s = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); const r = n.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height * 0.55)]; }, SELF);
  if (s) { await p.mouse.click(s[0], s[1]); await p.waitForTimeout(420); } return s; };

const 裁切 = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); const r = n.getBoundingClientRect();
  let t = r.top, bo = r.bottom, le = r.left, ri = r.right;
  for (const sel of ['[data-testid="flow-node-title"]', '[data-testid="video-node-player-bar"]', '[data-testid="video-simple-player"]']) {
    const e = n.querySelector(sel); if (!e) continue; const b = e.getBoundingClientRect();
    t = Math.min(t, b.top); bo = Math.max(bo, b.bottom); le = Math.min(le, b.left); ri = Math.max(ri, b.right); }
  const pad = 26, X = Math.max(2, Math.round(le - pad)), Y = Math.max(62, Math.round(t - pad));
  return { x: X, y: Y, width: Math.min(Math.round(ri + pad) - X, 1280 - X - 2), height: Math.min(Math.round(bo + pad) - Y, 720 - Y - 2),
           节点屏上: [r.x, r.y, r.width, r.height].map((z) => Math.round(z * 100) / 100) };
}, SELF);
const 卡框 = () => { const [x, y, w, h] = 裁切.节点屏上; return { x: Math.round(x - 4), y: Math.round(y - 4), w: Math.round(w + 8), h: Math.round(h + 8) }; };
log('裁切：', JSON.stringify(裁切));
const out = { 轮次: 'b195j', SELF, 裁切, 图: {} };

const 拍 = async (名, 规格, 守卫) => {
  const 画 = await 画框(规格); const 校 = 校验(画, 规格.length); const 断 = await 守卫();
  out.图[名] = { 断言: 断, 守卫: 校 };
  const 全过 = 校.全过 && 断.通过;
  log(名, '：', 断.判据, '→', 断.通过 ? '✅' : '🔴', '| 画框', 校.全过 ? '✅' : '🔴' + JSON.stringify(校));
  if (!全过) { await 清框(); out.图[名].跳过 = '守卫没过 ⇒ 不拍'; return; }
  await p.screenshot({ path: `${OUTDIR}/${名}.png`, clip: 裁切 });
  out.图[名].已拍 = true; await 清框();
};

// ===== 191 正在播：必须**先取消选中**再点正文 =====
await 点空白(); await p.waitForTimeout(700);
log('191 点正文前（应为未选中）：', JSON.stringify(await 状态()));
await 点正文(); await p.waitForTimeout(200);
const g191 = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  const e = n.querySelector('[data-testid="video-node-player-bar"]'); if (!e) return null;
  const r = e.getBoundingClientRect(); return { x: Math.round(r.x - 6), y: Math.round(r.y - 6), w: Math.round(r.width + 12), h: Math.round(r.height + 12) }; }, SELF);
await 拍('191-video-node-playing', [{ id: '__b195-card', ...卡框(), 线型: 'solid' }, ...(g191 ? [{ id: '__b195-bar', ...g191, 线型: 'dashed' }] : [])],
  async () => { const s = await 状态(); return { 判据: '选中=true 且 有<video> 且 paused=false 且 控件行在 且 大播放键不在 且 currentTime>0',
    读数: s, 通过: s.选中 === true && s.有video === true && s.paused === false && s.控件行 === true && s.大播放键 === false && s.currentTime > 0 }; });

// ===== 193 暂停态：点播放钮（先验命中再点）=====
const hit = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  const e = n.querySelector('[data-testid="video-node-playback-toggle"]'); if (!e) return { 找到: false };
  const r = e.getBoundingClientRect(); const x = r.x + r.width / 2, y = r.y + r.height / 2; const h = document.elementFromPoint(x, y);
  return { 找到: true, 屏上: [x, y], 屏上尺寸: [r.width, r.height].map((z) => Math.round(z * 100) / 100),
    中心落点: h ? h.tagName + '[' + (h.getAttribute('data-testid') || h.getAttribute('aria-label') || '') + ']' : null,
    命中: !!(h && (h === e || e.contains(h))) }; }, SELF);
out.点播放钮命中 = hit;
log('点播放钮命中：', JSON.stringify(hit));
if (!hit.命中) {
  out.图193跳过 = '播放钮未命中 ⇒ 无效臂，不拍';
  log('🔴 播放钮未命中 ⇒ 193 标无效臂');
} else {
  const 前 = await 状态();
  await p.mouse.click(hit.屏上[0], hit.屏上[1]); await p.waitForTimeout(500);
  const 后1 = await 状态();
  // 手册判据：暂停后 currentTime 停止走动 ⇒ 连采 4 帧
  const 帧 = []; for (let k = 0; k < 4; k++) { 帧.push(await 状态()); await p.waitForTimeout(400); }
  out.暂停对照 = { 前, 后1, 帧, currentTime集合: [...new Set(帧.map((x) => x.currentTime))], paused集合: [...new Set(帧.map((x) => x.paused))] };
  log('暂停后 currentTime 集合：', JSON.stringify(out.暂停对照.currentTime集合), '| paused 集合：', JSON.stringify(out.暂停对照.paused集合), '| 播放钮 aria：', 后1.播放钮aria);
  await 拍('193-video-node-paused', [{ id: '__b195-card', ...卡框(), 线型: 'solid' }, ...(g191 ? [{ id: '__b195-bar', ...g191, 线型: 'dashed' }] : [])],
    async () => { const s = await 状态(); return { 判据: 'paused=true 且 播放钮aria 读作 Play 且 控件行仍在',
      读数: s, 通过: s.paused === true && /^Play /.test(s.播放钮aria || '') && s.控件行 === true && out.暂停对照.currentTime集合.length === 1 }; });
}

fs.writeFileSync('/tmp/b195j.json', JSON.stringify(out, null, 1));
// 收尾：清选中 + 视口复位 26%
await 点空白(); await p.waitForTimeout(600);
await setZoom(p, 26);
out.收尾 = await endState(p, R, 基线);
log('收尾：', JSON.stringify(out.收尾));
await b.close();
